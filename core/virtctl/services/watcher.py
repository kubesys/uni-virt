# -*- coding: utf-8 -*-
'''
Copyright (2024, ) Institute of Software, Chinese Academy of Sciences

@author: wuyuewen@otcaix.iscas.ac.cn
@author: wuheng@otcaix.iscas.ac.cn
'''

'''
Import python libs
'''
import os
import sys
import time
import threading
from threading import Thread
from json import loads

'''
Import third party libs
'''
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException
from kubernetes.client import V1DeleteOptions
from libvirt import libvirtError

'''
Import local libs
'''
# sys.path.append('%s/utils' % (os.path.dirname(os.path.realpath(__file__))))
from utils import logger
from utils import constants
from utils.exception import InternalServerError, NotFound, Forbidden, BadRequest
from utils.conf_parser import UserDefinedParser
from utils.kubernetes_event_utils import KubernetesEvent
from services.executor import Executor
from services.convertor import toCmds

from utils.misc import is_valid_uuid, get_label_selector, report_failure,get_field_in_kubernetes_by_index,get_custom_object

TOKEN = constants.KUBERNETES_TOKEN_FILE
logger = logger.set_logger(os.path.basename(__file__), constants.KUBEVMM_VIRTCTL_LOG)

# thread_lock = threading.Lock()
create_vm_mutex = threading.Lock()
start_vm_mutex = threading.Lock()
stop_vm_mutex = threading.Lock()
reboot_vm_mutex = threading.Lock()
destroy_vm_mutex = threading.Lock()
delete_vm_mutex = threading.Lock()
reset_vm_mutex = threading.Lock()
suspend_vm_mutex = threading.Lock()
migrate_vm_mutex = threading.Lock()

current_event_id = {}
last_operation = {}
# conflict_operations = ['createSwitch', 'createPool', 'createAndStartVMFromISO', 'createAndStartVMFromImage', \
#                        'createImage', 'createDiskImage', 'createDiskFromDiskImage', 'createDiskImageFromDisk']

def main():
    '''将Kubernetes资源监听器运行在python子进程里.
    '''
    logger.debug("---------------------------------------------------------------------------------")
    logger.debug("------------------------Welcome to Virtctl Daemon.-------------------------------")
    logger.debug("------Copyright (2024, ) Institute of Software, Chinese Academy of Sciences------")
    logger.debug("---------author: wuyuewen@otcaix.iscas.ac.cn,wuheng@otcaix.iscas.ac.cn-----------")
    logger.debug("---------------------------------------------------------------------------------")

    logger.debug("Loading configurations in 'constants.py' ...")
    logger.debug("All support CMDs are:")
    logger.debug(UserDefinedParser().get_all_support_cmds())
    try:
        thread_1 = Thread(target=doWatch, args=(constants.KUBERNETES_PLURAL_VM, constants.KUBERNETES_KIND_VM,))
        thread_1.daemon = True
        thread_1.name = 'vm_watcher'
        thread_1.start()
        thread_2 = Thread(target=doWatch, args=(constants.KUBERNETES_PLURAL_VMD, constants.KUBERNETES_KIND_VMD,))
        thread_2.daemon = True
        thread_2.name = 'vm_disk_watcher'
        thread_2.start()
        thread_3 = Thread(target=doWatch, args=(constants.KUBERNETES_PLURAL_VMDI, constants.KUBERNETES_KIND_VMDI,))
        thread_3.daemon = True
        thread_3.name = 'vm_disk_image_watcher'
        thread_3.start()
        thread_4 = Thread(target=doWatch, args=(constants.KUBERNETES_PLURAL_VMDSN, constants.KUBERNETES_KIND_VMDSN,))
        thread_4.daemon = True
        thread_4.name = 'vm_disk_snapshot_watcher'
        thread_4.start()
        thread_5 = Thread(target=doWatch, args=(constants.KUBERNETES_PLURAL_VMN, constants.KUBERNETES_KIND_VMN,))
        thread_5.daemon = True
        thread_5.name = 'vm_network_watcher'
        thread_5.start()
        thread_6 = Thread(target=doWatch, args=(constants.KUBERNETES_PLURAL_VMP, constants.KUBERNETES_KIND_VMP,))
        thread_6.daemon = True
        thread_6.name = 'vm_pool_watcher'
        thread_6.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            return
        thread_1.join()
        thread_2.join()
        thread_3.join()
        thread_4.join()
        thread_5.join()
        thread_6.join()
    except:
        logger.error('Oops! ', exc_info=1)


def doWatch(plural, k8s_object_kind):
    '''监听器的请求处理逻辑，请求封装在{'spec': {'lifecycle': {...}}}里。\
    lifecycle通过解析器convertor解析，并与constatns里的配置项匹配，转化成invoke cmd和query cmd。\
    处理器executor用于顺序执行invoke cmd和query cmd。 \
    executor的结果如果符合json规范，并包含关键字{'spec': {...}}，则会被写回到Kubernetes里。

    '''
    while True:
        watcher = watch.Watch()
        kwargs = {}
        kwargs['label_selector'] = get_label_selector()
        kwargs['watch'] = True
        kwargs['timeout_seconds'] = int(constants.KUBERNETES_WATCHER_TIME_OUT)
        threads=[]
        try:
            for jsondict in watcher.stream(client.CustomObjectsApi().list_cluster_custom_object,
                                           group=constants.KUBERNETES_GROUP, version=constants.KUBERNETES_API_VERSION,
                                           plural=plural, **kwargs):
                logger.debug("watch here")
                # logger.debug(jsondict)
#                 global current_event_id
#                 if is_not_valid_uuid(_getEventId(jsondict)):
#                     raise BadRequest('Event ID: %s is not valid uuid!' % _getEventId(jsondict))
                thread = Thread(target=doExecutor, args=(plural, k8s_object_kind, jsondict))
                thread.name = 'do_executor'
                threads.append(thread)
                thread.start()
            for i in threads:
                i.join()
        except Exception as e:
            #             master_ip = change_master_and_reload_config(fail_times)
            config.load_kube_config(config_file=TOKEN)
            #             fail_times += 1
            #             logger.debug('retrying another master %s, retry times: %d' % (master_ip, fail_times))
            info = sys.exc_info()
            logger.warning('Oops! ', exc_info=1)
            #             vMWatcher(group=GROUP_VM, version=VERSION_VM, plural=PLURAL_VM)
            time.sleep(3)
            continue
        finally:
            watcher.stop()
            
# def create_and_start_thread(plural, k8s_object_kind, jsondict):
#     thread = Thread(target=doExecutor, args=(plural, k8s_object_kind, jsondict))
#     thread.name = 'do_executor'
#     thread.start()

def doExecutor(plural, k8s_object_kind, jsondict):
    operation_type = jsondict.get('type')
    logger.debug(operation_type)
    metadata_name = _getMetadataName(jsondict)
    logger.debug('metadata name: %s' % metadata_name)
    '''convertor'''
    if operation_type == 'DELETED':
        # delete type特殊处理: kubectl delete vmp pooltest
        if  k8s_object_kind==constants.KUBERNETES_KIND_VMP:
            jsondict["raw_object"]["spec"]['lifecycle']={"deletePool":dict()}
        elif k8s_object_kind==constants.KUBERNETES_KIND_VMD:
            poolName=jsondict["raw_object"]["spec"]['volume']['pool']
            logger.debug('vmd poolName: %s' % poolName)
            jsondict["raw_object"]["spec"]['lifecycle'] = {"deleteDisk": {"pool": poolName}}
        elif k8s_object_kind==constants.KUBERNETES_KIND_VMDI:
            poolName = jsondict["raw_object"]["spec"]['volume']['pool']
            logger.debug('vmdi poolName: %s' % poolName)
            jsondict["raw_object"]["spec"]['lifecycle'] = {"deleteDiskImage": {"pool": poolName}}
        elif k8s_object_kind==constants.KUBERNETES_KIND_VMDSN:
            volumeDict = jsondict["raw_object"]["spec"]['volume']
            poolName = volumeDict['pool']
            logger.debug('vmdsn poolName: %s' % poolName)
            domain=""
            if "domain" in volumeDict.keys():
                domain=volumeDict["domain"]
            jsondict["raw_object"]["spec"]['lifecycle'] = {"deleteDiskExternalSnapshot": {"pool": poolName,"source":volumeDict["disk"],"domain":domain}}
    # 在此处检查lifecycle，只有带lifecycle的才继续处理
    (policy, the_cmd_key, prepare_cmd, invoke_cmd, query_cmd) = toCmds(jsondict)
    logger.debug(toCmds(jsondict))

    # acquire lock
    if the_cmd_key:
#         '''考虑到apiserver高可用场景，当接收到相同eventId的请求时，忽略。
#         '''
#         if not is_valid_uuid(_getEventId(jsondict)):
#             raise BadRequest('Event ID: %s is not valid uuid!' % _getEventId(jsondict))
#         global current_event_id
#         if current_event_id.get("{}.{}".format(k8s_object_kind, _getMetadataName(jsondict))) == _getEventId(jsondict):
#             logger.warning('Same event id %s for %s, ignore it...' % (_getEventId(jsondict),_getMetadataName(jsondict)))
#             return
#         else:
#             current_event_id["{}.{}".format(k8s_object_kind, _getMetadataName(jsondict))] = _getEventId(jsondict)
#         if last_operation.get("{}.{}".format(k8s_object_kind, _getMetadataName(jsondict))) == the_cmd_key and the_cmd_key in conflict_operations:
#             logger.warning('Conflict operation %s for %s, ignore it...' % (the_cmd_key,_getMetadataName(jsondict)))
#             return
#         else:
#             logger.debug(last_operation)
#             last_operation["{}.{}".format(k8s_object_kind, _getMetadataName(jsondict))] = the_cmd_key
        _acquire_mutex_lock(the_cmd_key)
    try:
        # if the_cmd_key and operation_type != 'DELETED':
        if the_cmd_key :
            logger.debug("cmd key: %s, prepare cmd: %s, invoke cmd: %s, query cmd: %s" % (
            the_cmd_key, prepare_cmd, invoke_cmd, query_cmd))
            '''delete lifecycle in Kubernetes'''
            delete_lifecycle_in_kubernetes(plural, metadata_name)
            '''create Kubernetes event'''
            event_id = _getEventId(jsondict)
            event = KubernetesEvent(metadata_name, the_cmd_key, k8s_object_kind, event_id)
            event.create_event(constants.KUBEVMM_EVENT_LIFECYCLE_DOING, constants.KUBEVMM_EVENT_TYPE_NORMAL)
            try:
                data = {}
                if invoke_cmd:
                    '''executor'''
                    executor = Executor(policy, prepare_cmd, invoke_cmd, query_cmd)
                    _, data = executor.execute()
                '''write result, except migrateVM'''
                if the_cmd_key != 'migrateVM':
                    write_result_to_kubernetes(plural, metadata_name, data)
                '''update Kubernetes event'''
                event.update_evet(constants.KUBEVMM_EVENT_LIFECYCLE_DONE, constants.KUBEVMM_EVENT_TYPE_NORMAL)
            except libvirtError:
                logger.error('Oops! ', exc_info=1)
                info = sys.exc_info()
                try:
                    report_failure(metadata_name, jsondict, 'LibvirtError', str(info[1]), constants.KUBERNETES_GROUP,
                                   constants.KUBERNETES_API_VERSION, plural)
                except:
                    logger.warning('Oops! ', exc_info=1)
                event.update_evet(constants.KUBEVMM_EVENT_LIFECYCLE_DONE, constants.KUBEVMM_EVENT_TYPE_ERROR)
            except Exception as e:
                logger.error('Oops! ', exc_info=1)
                info = sys.exc_info()
                try:
                    if hasattr(e, 'reason'):
                        report_failure(metadata_name, jsondict, e.reason, e.message, constants.KUBERNETES_GROUP,
                                       constants.KUBERNETES_API_VERSION, plural)
                    else:
                        report_failure(metadata_name, jsondict, 'Exception', str(info[1]), constants.KUBERNETES_GROUP,
                                       constants.KUBERNETES_API_VERSION, plural)
                except:
                    logger.warning('Oops! ', exc_info=1)
                event.update_evet(constants.KUBEVMM_EVENT_LIFECYCLE_DONE, constants.KUBEVMM_EVENT_TYPE_ERROR)
            finally:
                # 释放锁
                if the_cmd_key:
                    _release_mutex_lock(the_cmd_key)
    except Exception as e:
        logger.error('Oops! ', exc_info=1)
        info = sys.exc_info()
        try:
            if hasattr(e, 'reason'):
                report_failure(metadata_name, jsondict, e.reason, e.message, constants.KUBERNETES_GROUP,
                               constants.KUBERNETES_API_VERSION, plural)
            else:
                report_failure(metadata_name, jsondict, 'Exception', str(info[1]), constants.KUBERNETES_GROUP,
                               constants.KUBERNETES_API_VERSION, plural)
        except:
            logger.warning('Oops! ', exc_info=1)


def _getMetadataName(jsondict):
    '''获取metadata name
    Returns:
        str: metadata name in Kubernetes

    '''
    metadata = jsondict['raw_object']['metadata']
    metadata_name = metadata.get('name')
    if metadata_name:
        return metadata_name
    else:
        raise BadRequest('FATAL ERROR! No metadata name!')

def _getEventId(jsondict):
    '''获取event id
    Returns:
        str: event id
    '''
    metadata = jsondict['raw_object'].get('metadata')
    labels = metadata.get('labels')
    logger.debug(labels)
    return labels.get('eventId') if labels.get('eventId') else '-1'


def _acquire_mutex_lock(the_cmd_key):
    if _isInstallVMFromISO(the_cmd_key) or _isInstallVMFromImage(the_cmd_key):
        create_vm_mutex.acquire()
    elif _isStartVM(the_cmd_key):
        start_vm_mutex.acquire()
    elif _isStopVM(the_cmd_key):
        stop_vm_mutex.acquire()
    elif _isRebootVM(the_cmd_key):
        reboot_vm_mutex.acquire()
    elif _isForceStopVM(the_cmd_key):
        destroy_vm_mutex.acquire()
    elif _isDeleteVM(the_cmd_key):
        delete_vm_mutex.acquire()
    elif _isResetVM(the_cmd_key):
        reset_vm_mutex.acquire()
    elif _isSuspendVM(the_cmd_key):
        suspend_vm_mutex.acquire()
    elif _isMigrateVM(the_cmd_key):
        migrate_vm_mutex.acquire()
    
def _release_mutex_lock(the_cmd_key):
    if _isInstallVMFromISO(the_cmd_key) or _isInstallVMFromImage(the_cmd_key):
        create_vm_mutex.release()
    elif _isStartVM(the_cmd_key):
        start_vm_mutex.release()
    elif _isStopVM(the_cmd_key):
        stop_vm_mutex.release()
    elif _isRebootVM(the_cmd_key):
        reboot_vm_mutex.release()
    elif _isForceStopVM(the_cmd_key):
        destroy_vm_mutex.release()
    elif _isDeleteVM(the_cmd_key):
        delete_vm_mutex.release()
    elif _isResetVM(the_cmd_key):
        reset_vm_mutex.release()
    elif _isSuspendVM(the_cmd_key):
        suspend_vm_mutex.release()
    elif _isMigrateVM(the_cmd_key):
        migrate_vm_mutex.release()


def write_result_to_kubernetes(plural, name, data):
    '''将executor的处理结果写回到Kubernetes里，处理结果必须是json格式，\
    并且符合{'spec':{...}}规范，如果传{'spec':{}}则代表从Kubernetes中删除该对象。
    '''
    logger.debug('write back to kubernetes')
    jsonDict = None
    try:
        # involved_object_name actually is nodeerror occurred during processing json data from apiserver
        try:
            jsonStr = client.CustomObjectsApi().get_namespaced_custom_object(
                group=constants.KUBERNETES_GROUP, version=constants.KUBERNETES_API_VERSION, namespace='default',
                plural=plural, name=name)
        except ApiException as e:
            if e.reason == 'Not Found':
                logger.debug('**Object %s already deleted.' % name)
                return
            else:
                raise e
        jsonDict = jsonStr.copy()
        try:
            data = loads(data)
        except:
            logger.debug('No data to write back to Kubernetes')
        if isinstance(data, dict) and data.get('spec'):
            if data['spec']:
                jsonDict['spec'] = data['spec']
                try:
                    client.CustomObjectsApi().replace_namespaced_custom_object(
                        group=constants.KUBERNETES_GROUP, version=constants.KUBERNETES_API_VERSION, namespace='default',
                        plural=plural, name=name, body=jsonDict)
                except ApiException as e:
                    if e.reason == 'Conflict':
                        logger.debug('**Other process updated %s, ignore this 409 message.' % name)
                        return
                    else:
                        raise e
            else:
                try:
                    client.CustomObjectsApi().delete_namespaced_custom_object(
                        group=constants.KUBERNETES_GROUP, version=constants.KUBERNETES_API_VERSION, namespace='default',
                        plural=plural, name=name, body=V1DeleteOptions())
                except ApiException as e:
                    if e.reason == 'Not Found':
                        logger.debug('**Object %s already deleted, ignore this 404 message.' % name)
                        return
                    else:
                        raise e
        elif isinstance(data, dict) and not data.get('spec'):
            Forbidden(
                'Wrong format in cmd results, only support "dict" with "spec" item, e.g. {"spec": {...}}. Please check the output of query cmd if exists, or the output of invoke cmd.')
    except:
        logger.error('Oops! ', exc_info=1)
        info = sys.exc_info()
        raise InternalServerError('Write result to apiserver failed: %s %s' % (info[0], info[1]))


def delete_lifecycle_in_kubernetes(plural, name):
    '''删除lifecycle结构，避免推送程序更新Kubernetes时再次进入lifecycle的处理逻辑。
    '''
    jsonDict = None
    try:
        try:
            jsonStr = client.CustomObjectsApi().get_namespaced_custom_object(
                group=constants.KUBERNETES_GROUP, version=constants.KUBERNETES_API_VERSION, namespace='default',
                plural=plural, name=name)
        except ApiException as e:
            if e.reason == 'Not Found':
                logger.debug('**Object %s already deleted.' % name)
                return
            else:
                raise e
        # logger.debug(dumps(jsonStr))
        #         logger.debug("node name is: " + name)
        jsonDict = jsonStr.copy()
        if jsonDict['spec'].get('lifecycle'):
            del jsonDict['spec']['lifecycle']
        #         jsonDict = updateDescription(jsonDict)
        client.CustomObjectsApi().replace_namespaced_custom_object(
            group=constants.KUBERNETES_GROUP, version=constants.KUBERNETES_API_VERSION, namespace='default',
            plural=plural, name=name, body=jsonDict)
    except:
        logger.error('Oops! ', exc_info=1)
        info = sys.exc_info()
        raise InternalServerError('Write result to apiserver failed: %s %s' % (info[0], info[1]))
    
def _isStartVM(the_cmd_key):
    if the_cmd_key == "startVM":
        return True
    return False

def _isStopVM(the_cmd_key):
    if the_cmd_key == "stopVM":
        return True
    return False

def _isForceStopVM(the_cmd_key):
    if the_cmd_key == "stopVMForce":
        return True
    return False
   
def _isRebootVM(the_cmd_key):
    if the_cmd_key == "rebootVM":
        return True
    return False

def _isResetVM(the_cmd_key):
    if the_cmd_key == "resetVM":
        return True
    return False

def _isSuspendVM(the_cmd_key):
    if the_cmd_key == "suspendVM":
        return True
    return False

def _isInstallVMFromISO(the_cmd_key):
    if the_cmd_key == "createAndStartVMFromISO":
        return True
    return False

def _isMergeSnapshot(the_cmd_key):
    if the_cmd_key == "mergeSnapshot":
        return True
    return False

def _isRevertVirtualMachine(the_cmd_key):
    if the_cmd_key == "revertVirtualMachine":
        return True
    return False

def _isCreateDiskExternalSnapshot(the_cmd_key):
    if the_cmd_key == "createDiskExternalSnapshot":
        return True
    return False

def _isDeleteVM(the_cmd_key):
    if the_cmd_key == "deleteVM":
        return True
    return False

def _isMigrateVM(the_cmd_key):
    if the_cmd_key == "migrateVM":
        return True
    return False

def _isMigrateVMDisk(the_cmd_key):
    if the_cmd_key == "migrateVMDisk":
        return True
    return False

def _isMigrateDisk(the_cmd_key):
    if the_cmd_key == "migrateDisk":
        return True
    return False

def _isExportVM(the_cmd_key):
    if the_cmd_key == "exportVM":
        return True
    return False

def _isBackupVM(the_cmd_key):
    if the_cmd_key == "backupVM":
        return True
    return False

def _isCleanBackup(the_cmd_key):
    if the_cmd_key == "cleanBackup":
        return True
    return False

def _isCleanRemoteBackup(the_cmd_key):
    if the_cmd_key == "cleanRemoteBackup":
        return True
    return False

def _isScanBackup(the_cmd_key):
    if the_cmd_key == "scanBackup":
        return True
    return False

def _isPullRemoteBackup(the_cmd_key):
    if the_cmd_key == "pullRemoteBackup":
        return True
    return False

def _isPushRemoteBackup(the_cmd_key):
    if the_cmd_key == "pushRemoteBackup":
        return True
    return False

def _isUpdateOS(the_cmd_key):
    if the_cmd_key == "updateOS":
        return True
    return False

def _isDeleteRemoteBackup(the_cmd_key):
    if the_cmd_key == "deleteRemoteBackup":
        return True
    return False
def _isDeleteVMDiskBackup(the_cmd_key):
    if the_cmd_key == "deleteVMDiskBackup":
        return True
    return False

def _isDeleteVMBackup(the_cmd_key):
    if the_cmd_key == "deleteVMBackup":
        return True
    return False

def _isManageISO(the_cmd_key):
    if the_cmd_key == "manageISO":
        return True
    return False

def _isPlugDisk(the_cmd_key):
    if the_cmd_key == "plugDisk":
        return True
    return False

def _isResizeVM(the_cmd_key):
    if the_cmd_key == "resizeVM":
        return True
    return False


def _isDeleteVMImage(the_cmd_key):
    if the_cmd_key == "deleteImage":
        return True
    return False

def _isDeleteVMSnapshot(the_cmd_key):
    if the_cmd_key == "deleteSnapshot":
        return True
    return False

def _isDeleteDisk(the_cmd_key):
    if the_cmd_key == "deleteDisk":
        return True
    return False

def _isDeleteDiskExternalSnapshot(the_cmd_key):
    if the_cmd_key == "deleteDiskExternalSnapshot":
        return True
    return False

def _isDeletePool(the_cmd_key):
    if the_cmd_key == "deletePool":
        return True
    return False

def _isShowPool(the_cmd_key):
    if the_cmd_key == "showPool":
        return True
    return False

def _isDeleteDiskImage(the_cmd_key):
    if the_cmd_key == "deleteDiskImage":
        return True
    return False

def _isCreateBridge(the_cmd_key):
    if the_cmd_key == "createBridge":
        return True
    return False

def _isSetBridgeVlan(the_cmd_key):
    if the_cmd_key == "setBridgeVlan":
        return True
    return False

def _isDelBridgeVlan(the_cmd_key):
    if the_cmd_key == "delBridgeVlan":
        return True
    return False

def _isDeleteNetwork(the_cmd_key):
    if the_cmd_key == "deleteSwitch":
        return True
    return False

def _isDeleteBridge(the_cmd_key):
    if the_cmd_key == "deleteBridge":
        return True
    return False

def _isDeleteAddress(the_cmd_key):
    if the_cmd_key == "deleteAddress":
        return True
    return False

def _isUpdateGraphic(the_cmd_key):
    if the_cmd_key == "updateGraphic":
        return True
    return False

def _isRedirectUsb(the_cmd_key):
    if the_cmd_key == "redirectUsb":
        return True
    return False

def _isChangeNumberOfCPU(the_cmd_key):
    if the_cmd_key == "changeNumberOfCPU":
        return True
    return False

def _isSetVncPassword(the_cmd_key):
    if the_cmd_key == "setVncPassword":
        return True
    return False

def _isUnsetVncPassword(the_cmd_key):
    if the_cmd_key == "unsetVncPassword":
        return True
    return False

def _isSetBootOrder(the_cmd_key):
    if the_cmd_key == "setBootOrder":
        return True
    return False

def _isSetGuestPassword(the_cmd_key):
    if the_cmd_key == "setGuestPassword":
        return True
    return False

def _isPassthroughDevice(the_cmd_key):
    if the_cmd_key == "passthroughDevice":
        return True
    return False

def _isInjectSshKey(the_cmd_key):
    if the_cmd_key == "injectSshKey":
        return True
    return False

def _isPlugNIC(the_cmd_key):
    if the_cmd_key == "plugNIC":
        return True
    return False

def _isUnplugNIC(the_cmd_key):
    if the_cmd_key == "unplugNIC":
        return True
    return False

def _isRevertDiskExternalSnapshot(the_cmd_key):
    if the_cmd_key == "revertDiskExternalSnapshot":
        return True
    return False

def _isUnplugDisk(the_cmd_key):
    if the_cmd_key == "unplugDisk":
        return True
    return False

def _isPlugDevice(the_cmd_key):
    if the_cmd_key == "plugDevice":
        return True
    return False

def _isUnplugDevice(the_cmd_key):
    if the_cmd_key == "unplugDevice":
        return True
    return False

def _isInstallVMFromImage(the_cmd_key):
    if the_cmd_key == "createAndStartVMFromImage":
        return True
    return False

def _isCreateDisk(the_cmd_key):
    if the_cmd_key == "createDisk":
        return True
    return False

def _isCreateImage(the_cmd_key):
    if the_cmd_key == "createImage":
        return True
    return False

def _isCreateVmdi(the_cmd_key):
    if the_cmd_key == "createDiskImage":
        return True
    return False

def _isCreateSnapshot(the_cmd_key):
    if the_cmd_key == "createSnapshot":
        return True
    return False

def _isCreateDiskImageFromDisk(the_cmd_key):
    if the_cmd_key == "createDiskImageFromDisk":
        return True
    return False

def _isConvertVMToImage(the_cmd_key):
    if the_cmd_key == "convertVMToImage":
        return True
    return False

def _isCreateDiskFromDiskImage(the_cmd_key):
    if the_cmd_key == "createDiskFromDiskImage":
        return True
    return False

def _isDeleteVmdi(the_cmd_key):
    if the_cmd_key == "deleteDiskImage":
        return True
    return False

def _isDeleteImage(the_cmd_key):
    if the_cmd_key == "deleteImage":
        return True
    return False

def _isCloneDisk(the_cmd_key):
    if the_cmd_key == "cloneDisk":
        return True
    return False

def _isResizeDisk(the_cmd_key):
    if the_cmd_key == "resizeDisk":
        return True
    return False


if __name__ == '__main__':
    config.load_kube_config(config_file=constants.KUBERNETES_TOKEN_FILE)
    main()
