# -*- coding: utf-8 -*-
'''
Copyright (2024, ) Institute of Software, Chinese Academy of Sciences

@author: wuyuewen@otcaix.iscas.ac.cn
@author: wuheng@otcaix.iscas.ac.cn
@author: liujiexin@otcaix.iscas.ac.cn

* Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
'''

'''
Import python libs
'''
from dateutil.tz import gettz
import os, re, sys, time, datetime, socket, subprocess, time, traceback
from json import dumps
from json import loads
from xml.etree.ElementTree import fromstring
from xmljson import badgerfish as bf
from tenacity import retry, stop_after_attempt, wait_random, before_sleep_log, RetryError
import logging
import contextlib

'''
Import third party libs
'''
# from kubernetes import client, config
# # from kubernetes.client.rest import ApiException
# from kubernetes.client.models.v1_node_status import V1NodeStatus
# from kubernetes.client.models.v1_node_condition import V1NodeCondition
# from kubernetes.client.models.v1_node_daemon_endpoints import V1NodeDaemonEndpoints
# from kubernetes.client.models.v1_node_system_info import V1NodeSystemInfo
# from kubernetes.client.models.v1_node import V1Node
# from kubernetes.client.models.v1_node_spec import V1NodeSpec
# from kubernetes.client.models.v1_object_meta import V1ObjectMeta
# from kubernetes.client.models.v1_node_address import V1NodeAddress

'''
Import local libs
'''
# sys.path.append('%s/utils/libvirt_util.py' % (os.path.dirname(os.path.realpath(__file__))))
from utils import constants,logger
from utils.libvirt_util import is_vm_exists, __get_conn, get_xml, vm_state, freecpu, freemem, node_info, list_active_vms, list_vms, destroy, undefine, is_vm_active, start
from utils.misc import runCmdRaiseException, push_node_label_value, create_custom_object, get_custom_object, update_custom_object, delete_custom_object, change_master_and_reload_config, updateDescription, addPowerStatusMessage, updateDomain, CDaemon, runCmd, get_field_in_kubernetes_by_index, get_hostname_in_lower_case, get_node_name_from_kubernetes, get_ha_from_kubernetes
from utils.k8s_handler import Node,Metadata

from kubesys.exceptions import HTTPError
from kubesys.client import KubernetesClient

TOKEN = constants.KUBERNETES_TOKEN_FILE
TOKEN_ORIGIN = constants.KUBERNETES_TOKEN_FILE_ORIGIN
HOSTNAME = get_hostname_in_lower_case()
DEFAULT_JSON_BACKUP_DIR = constants.KUBEVMM_DEFAULT_JSON_BACKUP_DIR
GROUP = constants.KUBERNETES_GROUP
VERSION = constants.KUBERNETES_API_VERSION
PLURAL = constants.KUBERNETES_PLURAL_VM
KIND=constants.KUBERNETES_KIND_VM
PLURAL_VMGPU = constants.KUBERNETES_PLURAL_VMGPU
KIND_VMGPU = constants.KUBERNETES_KIND_VMGPU

logger = logger.set_logger(os.path.basename(__file__), constants.KUBEVMM_VIRTLET_LOG)


def main():
    ha_check = True
    ha_enable = True
    fail_times = 0
#     restart_virtctl = False
    while True:
        try:
            # host = client.CoreV1Api().read_node_status(name=HOSTNAME)
            # client=KubernetesClient(config=TOKEN)
            # host=client.getResourceStatus(kind="Node",name=HOSTNAME)
            # node_watcher = HostCycler()
            # host['status'] = node_watcher.get_node_status()
            # if ha_check:
            #     for vm in list_vms():
            #         _check_vm_by_hosting_node(KIND, vm)
            #         try:
            #             _check_ha_and_autostart_vm(KIND, vm)
            #         except RetryError:
            #             pass
            #         _check_vm_power_state(KIND, vm)
            #     ha_check = False
            # _patch_node_status()
            if ha_enable:
                _check_and_enable_HA()
                ha_enable = False
            check_libvirt_conn = __get_conn()
            if check_libvirt_conn:
                check_libvirt_conn.close()
#             if restart_virtctl:
#                 virtctl_id = runCmd("docker ps | grep virtctl | awk -F ' ' '{print $1}'")
#                 if virtctl_id:
#                     logger.debug('Kubernetes has been recovered, restarting virtctl container %s' % virtctl_id)
#                     runCmd('docker stop %s' % virtctl_id)
#                 restart_virtctl = False
            fail_times = 0
            time.sleep(8)
        except Exception as e:
            logger.error('Oops! ', exc_info=1)
            if repr(e).find('Network is unreachable') != -1 or repr(e).find('Connection timed out') != -1 or repr(e).find('Connection refused') != -1 or repr(e).find('No route to host') != -1 or repr(e).find('HTTPError') != -1:
#                 master_ip = change_master_and_reload_config(fail_times)
                fail_times += 1
                logger.debug('retrying: %d' % (fail_times))
#                 if fail_times >= 8:
#                     restart_virtctl = True
                if fail_times >= 3:
                    ha_check = True
            elif repr(e).find('failed to open a connection to the hypervisor software') != -1:
                libvirt_watcher_id = runCmd("docker ps | grep libvirtwatcher | awk -F ' ' '{print $1}'")
                if libvirt_watcher_id:
                    logger.debug('libvirt error occurred, restart container %s' % libvirt_watcher_id)
                    runCmd('docker stop %s' % libvirt_watcher_id)
            # config.load_kube_config(config_file=TOKEN)
            time.sleep(3)
#             restart_service = True
            continue


@retry(stop=stop_after_attempt(4),
       wait=wait_random(min=0,max=3),
       before_sleep=before_sleep_log(logger,logging.WARNING,True),
       reraise=True)
def _patch_node_status():
    client=KubernetesClient(config=TOKEN)
    host=client.getResourceStatus(kind='Node',name=HOSTNAME)
    node_watcher = HostCycler()
    host['status'] = node_watcher.get_node_status().__dict__
    client.updateResourceStatus(host)
    return


def _check_vm_by_hosting_node(kind, metadata_name):
    try:
        logger.debug('1.Doing hosting node verification for VM: %s' % metadata_name)
        node_name = get_node_name_from_kubernetes(kind, metadata_name)
        if node_name == 'UNKNOWN':
            logger.debug('Unknown host name.')
            return
        elif not node_name:
            logger.debug('Delete VM %s because it is not hosting by the Kubernetes cluster.' % (metadata_name))
            if is_vm_exists(metadata_name):
                if is_vm_active(metadata_name):
                    _destroy_vm_retries(metadata_name)
                    time.sleep(1)
                undefine(metadata_name)    
        elif node_name != get_hostname_in_lower_case():
            logger.debug('Delete VM %s because it is now hosting by another node %s.' % (metadata_name, node_name))
            _backup_json_to_file(kind, metadata_name)
            if is_vm_exists(metadata_name):
                if is_vm_active(metadata_name):
                    _destroy_vm_retries(metadata_name)
                    time.sleep(1)
                undefine(metadata_name)    
    except:
        logger.error('Oops! ', exc_info=1)


@retry(stop=stop_after_attempt(3),
       wait=wait_random(min=0,max=3),
       before_sleep=before_sleep_log(logger,logging.WARNING,True),
       reraise=True)
def _destroy_vm_retries(metadata_name):
    destroy(metadata_name)
    return


@retry(stop=stop_after_attempt(3),
       wait=wait_random(min=8,max=15),
       before_sleep=before_sleep_log(logger,logging.WARNING,True))
def _check_ha_and_autostart_vm(kind, metadata_name):
    logger.debug('2.Doing HA verification for VM: %s' % metadata_name)
    ha = get_ha_from_kubernetes(kind, metadata_name)
    if ha:
        if is_vm_exists(metadata_name) and not is_vm_active(metadata_name):
            logger.debug('Autostart HA VM: %s.' % (metadata_name))
            start(metadata_name)
        
def _check_and_enable_HA():
 #   push_node_label_value(HOSTNAME, "nodeHA", None)
    runCmd("kubectl label node --kubeconfig=%s %s nodeHA-" % (TOKEN_ORIGIN,HOSTNAME))


def _check_vm_power_state(kind, metadata_name):
    try:
        logger.debug('3.Check the power state of VM: %s' % metadata_name)
        jsondict = get_custom_object(kind, metadata_name)
    except HTTPError as e:
        if str(e).find('Not Found'):
            logger.debug('**VM %s already deleted, ignore this 404 error.' % metadata_name)
            return
    except Exception as e:
        logger.error('Oops! ', exc_info=1)
        return
    if is_vm_exists(metadata_name):
        vm_xml = get_xml(metadata_name)
        vm_power_state = vm_state(metadata_name).get(metadata_name)
        vm_json = toKubeJson(xmlToJson(vm_xml))
        vm_json = updateDomain(loads(vm_json))
        jsondict = updateDomainStructureAndDeleteLifecycleInJson(jsondict, vm_json)
        body = addPowerStatusMessage(jsondict, vm_power_state, 'The VM is %s' % vm_power_state)
        try:
            update_custom_object(body)
        except HTTPError as e:
            if str(e).find('Not Found'):
                logger.debug('**VM %s already deleted, ignore this 404.' % metadata_name)
            if str(e).find('Conflict'):
                logger.debug('**Other process updated %s, ignore this 409.' % metadata_name)
            else:
                logger.error('Oops! ', exc_info=1)
        except Exception as e:
            logger.error('Oops! ', exc_info=1)
    

def _backup_json_to_file(kind, metadata_name):
    try:
        jsonStr = get_custom_object(kind, metadata_name)
    except HTTPError as e:
        if str(e).find('Not Found'):
            logger.debug('**VM %s already deleted.' % metadata_name)
            return
        else:
            raise e
    if not os.path.exists(DEFAULT_JSON_BACKUP_DIR):
        os.mkdir(DEFAULT_JSON_BACKUP_DIR)
    backup_file = '%s/%s.json' % (DEFAULT_JSON_BACKUP_DIR, metadata_name)
    with open(backup_file, "w") as f1:
        f1.write(dumps(jsonStr))

# def modifyVM(group, version, plural, name, body):
#     for i in range(1,5):
#         try:
#             body = updateDescription(body)
#             retv = client.CustomObjectsApi().replace_namespaced_custom_object(
#                 group=group, version=version, namespace='default', plural=plural, name=name, body=body)
#             return retv
#         except Exception as e:
#             if e.reason == 'Not Found':
#                 raise e
#             elif i == 5:
#                 raise e
#             else:
#                 time.sleep(3)
#                 continue
        
        
def xmlToJson(xmlStr):
    return dumps(bf.data(fromstring(xmlStr)), sort_keys=True, indent=4)

def toKubeJson(json):
    return json.replace('@', '_').replace('$', 'text').replace(
            'interface', '_interface').replace('transient', '_transient').replace(
                    'nested-hv', 'nested_hv').replace('suspend-to-mem', 'suspend_to_mem').replace('suspend-to-disk', 'suspend_to_disk')
                    
def updateDomainStructureAndDeleteLifecycleInJson(jsondict, body):
    if jsondict:
        '''
        Get target VM name from Json.
        '''
        spec = jsondict['spec']
        if spec:
            lifecycle = spec.get('lifecycle')
            if lifecycle:
                del spec['lifecycle']
            spec.update(body)
    return jsondict


class HostCycler:

    def get_node(self):
        return Node(metadata=self.get_object_metadata(), spec=self.get_node_spec(), status=self.get_node_status())

    def get_node_status(self):
        return Node.Status(allocatable=self.get_status_allocatable(),
                           capacity=self.get_status_capacity())

    def _format_mem_to_Mi(self, mem):
        return int(round(int(mem))) if int(round(int(mem))) > 0 else 0
    
    def get_node_spec(self):
        return Node.Spec()

    def get_object_metadata(self):
        return Metadata(annotations=[], name=HOSTNAME, uid='', labels=[], resourceVersion='', selfLink='')
    
    # def get_status_address(self):
    #     ip = self._get_node_ip_from_k8s()
    #     node_status_address1 = V1NodeAddress(address=ip, type='InternalIP')
    #     node_status_address2 = V1NodeAddress(address=HOSTNAME, type='Hostname')
    #     return [node_status_address1, node_status_address2]
    
    def _get_node_ip_from_k8s(self):
        try:
            # node = client.CoreV1Api().read_node(name=HOSTNAME)
            # node_dict = node.to_dict()
            metadata=self.get_object_metadata()
            return metadata.annotations.get('THISIP')
        except:
            return socket.gethostbyname(socket.gethostname())
    
    def get_status_allocatable(self):
        try:
            cpu_allocatable = freecpu()
            if int(cpu_allocatable) <= 0:
                cpu_allocatable = 0
        except:
            cpu_allocatable = 0
        try:
            mem_allocatable = '%s' % str(self._format_mem_to_Mi(freemem()))
        except:
            mem_allocatable = '0'
        try:
            active_vms = list_active_vms()
        except:
            active_vms = []
        return {'doslab.io/cpu': str(cpu_allocatable), 'doslab.io/memory': str(mem_allocatable), 'doslab.io/vms': str(40 - len(active_vms)) if 40 - len(active_vms) >= 0 else '0'}
    
    def get_status_capacity(self):
        try:
            node_info_dict = node_info()
        except:
            node_info_dict = {}
        if node_info_dict:
            cpu_capacity = node_info_dict.get('cpus')
            mem_capacity = self._format_mem_to_Mi(node_info_dict.get('phymemory'))
            return {'doslab.io/cpu': str(cpu_capacity), 'doslab.io/memory': str(mem_capacity), 'doslab.io/vms': '40'}
        else:
            return {'doslab.io/cpu': '0', 'doslab.io/memory': '0', 'doslab.io/vms': '40'}
    
    def get_status_daemon_endpoints(self):
        return Node.DaemonEndpoint(kubeletEndpoint={'port':0})

    def get_status_condition(self):
        time_zone = gettz('Asia/Shanghai')
        now = datetime.datetime.now(tz=time_zone)
        condition1=Node.Condition(last_heartbeat_time=now, last_transition_time=now, message="virtlet has sufficient memory available", \
                            reason="VirtletHasSufficientMemory", status="False", type="MemoryPressure")
        condition2 = Node.Condition(last_heartbeat_time=now, last_transition_time=now,
                                     message="virtlet has no disk pressure", \
                                        reason="VirtletHasNoDiskPressure", status="False", type="DiskPressure")
        condition3=Node.Condition(last_heartbeat_time=now, last_transition_time=now, message="virtlet has sufficient PID available", \
                            reason="VirtletHasSufficientPID", status="False", type="PIDPressure")
        condition4 = Node.Condition(last_heartbeat_time=now, last_transition_time=now,
                                     message="virtlet is posting ready status", \
                                        reason="VirtletReady", status="True", type="Ready")
        return [condition1, condition2, condition3, condition4]
    
#         node_status = V1NodeStatus(conditions=[condition1, condition2, condition3, condition4], daemon_endpoints=daemon_endpoints, \
#                                    node_info=node_info)
#         self.node.status = node_status
#         client.CoreV1Api().replace_node_status(name="node11", body=self.node)
        
    # def get_status_node_info(self):
    #     ARCHITECTURE = runCmd('uname -m')
    #     BOOT_ID = runCmd('cat /sys/class/dmi/id/product_uuid')
    #     RUNTIME_VERSION = 'QEMU-KVM://%s' % (runCmd('/usr/bin/qemu-img --version | awk \'NR==1 {print $3}\''))
    #     KERNEL_VERSION = runCmd('cat /proc/sys/kernel/osrelease')
    #     try:
    #         KUBE_PROXY_VERSION = runCmd('kubelet --version | awk \'{print $2}\'')
    #     except:
    #         KUBE_PROXY_VERSION = 'v1.23.6'
    #     KUBELET_VERSION = KUBE_PROXY_VERSION
    #     MACHINE_ID = BOOT_ID
    #     OPERATING_SYSTEM = runCmd('cat /proc/sys/kernel/ostype')
    #     OS_IMAGE = runCmd('cat /etc/os-release | grep PRETTY_NAME | awk -F"\\"" \'{print$2}\'')
    #     SYSTEM_UUID = BOOT_ID
    #     return V1NodeSystemInfo(architecture=ARCHITECTURE, boot_id=BOOT_ID, container_runtime_version=RUNTIME_VERSION, \
    #                  kernel_version=KERNEL_VERSION, kube_proxy_version=KUBE_PROXY_VERSION, kubelet_version=KUBELET_VERSION, \
    #                  machine_id=MACHINE_ID, operating_system=OPERATING_SYSTEM, os_image=OS_IMAGE, system_uuid=SYSTEM_UUID)

if __name__ == "__main__":
    # config.load_kube_config(config_file=TOKEN)
    main()
