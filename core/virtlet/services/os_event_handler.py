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
import json

'''
Import python libs
'''
import os
from time import time,sleep
import traceback
import sys
from json import loads
from json import dumps
from xml.etree.ElementTree import fromstring

'''
Import third party libs
'''
from watchdog.observers import Observer
from watchdog.events import *
# from kubernetes import client, config
# from kubernetes.client.rest import ApiException
# from kubernetes.client import V1DeleteOptions
from xmljson import badgerfish as bf
from tenacity import retry, stop_after_attempt, wait_random,before_sleep_log
'''
Import local libs
'''
from utils.libvirt_util import get_pool_path, get_volume_path, refresh_pool, get_volume_xml, get_snapshot_xml, is_vm_exists, get_xml, \
    vm_state, _get_all_pool_path, get_vol_info_by_qemu,list_active_vms
from utils import logger
from utils import constants
from utils.misc import create_custom_object, delete_custom_object, get_custom_object, update_custom_object, add_spec_in_volume, updateDescription, addSnapshots, get_volume_snapshots, runCmdRaiseException, \
    addPowerStatusMessage, updateDomainSnapshot, updateDomain, report_failure, get_hostname_in_lower_case,get_1st_ready,\
    DiskImageHelper

from kubesys.exceptions import HTTPError

GROUP = constants.KUBERNETES_GROUP
VERSION = constants.KUBERNETES_API_VERSION
VM_KIND = constants.KUBERNETES_KIND_VM
VMD_KIND = constants.KUBERNETES_KIND_VMD
VMDSN_KIND = constants.KUBERNETES_KIND_VMDSN
VMDI_KIND = constants.KUBERNETES_KIND_VMDI
VMSN_KIND = constants.KUBERNETES_KIND_VMSN
VMDEV_KIND = constants.KUBERNETES_KIND_VMDEV
VMI_KIND = constants.KUBERNETES_KIND_VMI
VMGPU_KIND = constants.KUBERNETES_KIND_VMGPU

TOKEN = constants.KUBERNETES_TOKEN_FILE
PLURAL_VM = constants.KUBERNETES_PLURAL_VM
PLURAL_VM_DISK = constants.KUBERNETES_PLURAL_VMD
PLURAL_VM_DISK_SS = constants.KUBERNETES_PLURAL_VMDSN
PLURAL_VM_DISK_IMAGE = constants.KUBERNETES_PLURAL_VMDI
LIBVIRT_XML_DIR = constants.KUBEVMM_LIBVIRT_VM_XML_DIR
VMD_TEMPLATE_DIR = constants.KUBEVMM_DEFAULT_VMDI_DIR

HOSTNAME = get_hostname_in_lower_case()
NAMESPACE='default'
logger = logger.set_logger(os.path.basename(__file__), constants.KUBEVMM_VIRTLET_LOG)
CUT_OFF_TIME = 4
event_mapper={}

def xmlToJson(xmlStr):
    return dumps(bf.data(fromstring(xmlStr)), sort_keys=True, indent=4)


def toKubeJson(json):
    return json.replace('@', '_').replace('$', 'text').replace(
        'interface', '_interface').replace('transient', '_transient').replace(
        'nested-hv', 'nested_hv').replace('suspend-to-mem', 'suspend_to_mem').replace('suspend-to-disk',
                                                                                      'suspend_to_disk')


def updateJsonRemoveLifecycle(jsondict, body):
    if jsondict:
        spec = jsondict['spec']
        if spec:
            lifecycle = spec.get('lifecycle')
            if lifecycle:
                del spec['lifecycle']
            spec.update(body)
    return jsondict


class FSEHPreProcessing(FileSystemEventHandler):
    def __init__(self):
        FileSystemEventHandler.__init__(self)

    def dispatch(self, event):
        global event_mapper
        key = (event.src_path, event.event_type)
        value = time()
        last_time = event_mapper.get(key, 0.0)
        if value - last_time > CUT_OFF_TIME:
            event_mapper[key] = value
            self.on_any_event(event)
            {
                EVENT_TYPE_CREATED: self.on_created,
                EVENT_TYPE_DELETED: self.on_deleted,
                EVENT_TYPE_MODIFIED: self.on_modified,
                EVENT_TYPE_MOVED: self.on_moved,
                EVENT_TYPE_CLOSED: self.on_closed,
                EVENT_TYPE_OPENED: self.on_opened,
            }[event.event_type](event)

def myVmVolEventHandler(event, pool, name, group, version, plural):
    #     print(jsondict)
    if event == "Delete":
        try:
            refresh_pool(pool)
            jsondict = get_custom_object(VMD_KIND, name)
            #             vol_xml = get_volume_xml(pool, name)
            #             vol_json = toKubeJson(xmlToJson(vol_xml))
            jsondict = updateJsonRemoveLifecycle(jsondict, {})
            body = addPowerStatusMessage(jsondict, 'Ready', 'The resource is ready.')
            update_custom_object(body)
        except HTTPError as e:
            if str(e).find('Not Found'):
                logger.debug('**VM disk %s already deleted, ignore this 404 error.' % name)
            else:
                info = sys.exc_info()
                try:
                    report_failure(name, 'VirtletError', str(info[1]), VMD_KIND)
                except:
                    logger.warning('Oops! ', exc_info=1)
        except:
            logger.error('Oops! ', exc_info=1)
            info = sys.exc_info()
            try:
                report_failure(name, 'VirtletError', str(info[1]),VMD_KIND)
            except:
                logger.warning('Oops! ', exc_info=1)
        try:
            logger.debug('Delete vm disk %s, report to virtlet' % name)
            delete_custom_object(VMD_KIND,NAMESPACE, name)
        except HTTPError as e:
            if str(e).find('Not Found'):
                logger.debug('**VM disk %s already deleted, ignore this 404 error.' % name)
            else:
                info = sys.exc_info()
                try:
                    report_failure(name, 'VirtletError', str(info[1]), VMD_KIND)
                except:
                    logger.warning('Oops! ', exc_info=1)
        except:
            logger.error('Oops! ', exc_info=1)
            info = sys.exc_info()
            try:
                report_failure(name, 'VirtletError', str(info[1]),VMD_KIND)
            except:
                logger.warning('Oops! ', exc_info=1)
    elif event == "Create":
        try:
            logger.debug('Create vm disk %s, report to virtlet' % name)
            jsondict = {'spec': {'volume': {}, 'nodeName': HOSTNAME, 'status': {}},
                        'kind': VMD_KIND, 'metadata': {'labels': {'host': HOSTNAME}, 'name': name,'namespace':NAMESPACE},
                        'apiVersion': '%s/%s' % (group, version)}
            with open(get_pool_path(pool) + '/' + name + '/config.json', "r") as f:
                config = json.load(f)
                volume = get_vol_info_by_qemu(config['current'])
                volume["pool"] = config['pool']
                volume["poolname"] = pool
                volume["uni"] = config['current']
                volume['disk'] = name
                volume['current'] = config['current']
                vol_json = {'volume': volume}
                vol_json = add_spec_in_volume(vol_json, 'current', config['current'])
            jsondict = updateJsonRemoveLifecycle(jsondict, vol_json)
            body = addPowerStatusMessage(jsondict, 'Ready', 'The resource is ready.')
            try:
                create_custom_object(body)
            except HTTPError as e:
                logger.error(e)

        except:
            logger.error('Oops! ', exc_info=1)
            info = sys.exc_info()
            try:
                report_failure(name, 'VirtletError', str(info[1]), VMD_KIND)
            except:
                logger.error('Oops! ', exc_info=1)
    elif event == "Modify":
        try:
            logger.debug('Modify vm disk %s current, report to virtlet' % name)
            jsondict = get_custom_object(VMD_KIND, name)
            with open(get_pool_path(pool) + '/' + name + '/config.json', "r") as f:
                config = json.load(f)
                volume = get_vol_info_by_qemu(config['current'])
                volume["pool"] = config['pool']
                volume["poolname"] = pool
                volume["uni"] = config['current']
                volume['disk'] = name
                volume['current'] = config['current']
                vol_json = {'volume': volume}
                logger.debug(config['current'])
                vol_json = add_spec_in_volume(vol_json, 'current', config['current'])
            jsondict = updateJsonRemoveLifecycle(jsondict, vol_json)
            body = addPowerStatusMessage(jsondict, 'Ready', 'The resource is ready.')
            try:
                update_custom_object(body)
            except HTTPError as e:
                logger.error(e)
        except:
            logger.error('Oops! ', exc_info=1)
            info = sys.exc_info()
            try:
                report_failure(name, 'VirtletError', str(info[1]), VMD_KIND)
            except:
                logger.error('Oops! ', exc_info=1)
    else:
        refresh_pool(pool)
        try:
            pass
        except:
            logger.error('Oops! ', exc_info=1)
            info = sys.exc_info()
            try:
                report_failure(name, 'VirtletError', str(info[1]), VMD_KIND)
            except:
                logger.warning('Oops! ', exc_info=1)


class VmVolEventHandler(FSEHPreProcessing):
    def __init__(self):
        FSEHPreProcessing.__init__(self)

    def on_moved(self, event):
        if event.is_directory:
            logger.debug("directory moved from {0} to {1}".format(event.src_path, event.dest_path))
        else:
            logger.debug("file moved from {0} to {1}".format(event.src_path, event.dest_path))

    def on_created(self, event):
        if event.is_directory:
            logger.debug("directory created:{0}".format(event.src_path))
        else:
            logger.debug("file created:{0}".format(event.src_path))
            # filename = os.path.basename(event.src_path)
            # if filename == 'config.json':
            #     with open(event.src_path, "r") as f:
            #         config = json.load(f)
            #     vol = config['name']
            #     try:
            #         myVmVolEventHandler('Create', self.pool, vol, self.group, self.version, self.plural)
            #     except ApiException:
            #         logger.error('Oops! ', exc_info=1)

    def on_deleted(self, event):
        if event.is_directory:
            logger.debug("directory deleted:{0}".format(event.src_path))
        else:
            logger.debug("file deleted:{0}".format(event.src_path))
            # filename = os.path.basename(event.src_path)
            # if filename == 'config.json':
            #     vol = os.path.basename(os.path.dirname(event.src_path))
            #     try:
            #         myVmVolEventHandler('Delete', self.pool, vol, self.group, self.version, self.plural)
            #     except ApiException:
            #         logger.error('Oops! ', exc_info=1)

    def on_modified(self, event):
        if event.is_directory:
            logger.debug("directory modified:{0}".format(event.src_path))
        else:
            pass


def myVmSnapshotEventHandler(event, vm, name, group, version, plural):
    #     print(jsondict)
    if event == "Delete":
        try:
            jsondict = get_custom_object(VMSN_KIND, name)
            #             snap_xml = get_snapshot_xml(vm, name)
            #             snap_json = toKubeJson(xmlToJson(snap_xml))
            #             snap_json = updateDomainSnapshot(loads(snap_json))
            jsondict = updateJsonRemoveLifecycle(jsondict, {})
            body = addPowerStatusMessage(jsondict, 'Ready', 'The resource is ready.')
            update_custom_object(body)
        except HTTPError as e:
            if str(e).find('Not Found'):
                logger.debug('**VM snapshot %s already deleted, ignore this 404 error.' % name)
            else:
                info = sys.exc_info()
                try:
                    report_failure(name, 'VirtletError', str(info[1]), VMSN_KIND)
                except:
                    logger.warning('Oops! ', exc_info=1)
        except:
            logger.error('Oops! ', exc_info=1)
            info = sys.exc_info()
            try:
                report_failure(name, 'VirtletError', str(info[1]), VMSN_KIND)
            except:
                logger.warning('Oops! ', exc_info=1)
        try:
            logger.debug('Delete vm snapshot %s, report to virtlet' % name)
            delete_custom_object(VMSN_KIND,NAMESPACE, name)
        except HTTPError as e:
            if str(e).find('Not Found'):
                logger.debug('**VM snapshot %s already deleted, ignore this 404 error.' % name)
            else:
                info = sys.exc_info()
                try:
                    report_failure(name, 'VirtletError', str(info[1]), VMSN_KIND)
                except:
                    logger.warning('Oops! ', exc_info=1)
        except:
            logger.error('Oops! ', exc_info=1)
            info = sys.exc_info()
            try:
                report_failure(name, 'VirtletError', str(info[1]), VMSN_KIND)
            except:
                logger.warning('Oops! ', exc_info=1)
    elif event == "Create":
        try:
            logger.debug('Create vm snapshot %s, report to virtlet' % name)
            jsondict = {'spec': {'domainsnapshot': {}, 'nodeName': HOSTNAME, 'status': {}},
                        'kind': VMSN_KIND, 'metadata': {'labels': {'host': HOSTNAME}, 'name': name,'namespace':NAMESPACE},
                        'apiVersion': '%s/%s' % (group, version)}
            snap_xml = get_snapshot_xml(vm, name)
            snap_json = toKubeJson(xmlToJson(snap_xml))
            snap_json = updateDomainSnapshot(loads(snap_json))
            jsondict = updateJsonRemoveLifecycle(jsondict, snap_json)
            body = addPowerStatusMessage(jsondict, 'Ready', 'The resource is ready.')
            try:
                create_custom_object(body)
            except HTTPError as e:
                logger.error(e)

        except:
            logger.error('Oops! ', exc_info=1)
            info = sys.exc_info()
            try:
                report_failure(name, 'VirtletError', str(info[1]), VMSN_KIND)
            except:
                logger.error('Oops! ', exc_info=1)
    else:
        info = sys.exc_info()
        try:
            report_failure(name, 'VirtletError', str(info[1]), VMSN_KIND)
        except:
            logger.warning('Oops! ', exc_info=1)


class VmSnapshotEventHandler(FSEHPreProcessing):
    def __init__(self, field, target, group, version, plural):
        FSEHPreProcessing.__init__(self)
        self.field = field
        self.target = target
        self.group = group
        self.version = version
        self.plural = plural

    def on_moved(self, event):
        if event.is_directory:
            logger.debug("directory moved from {0} to {1}".format(event.src_path, event.dest_path))
        else:
            logger.debug("file moved from {0} to {1}".format(event.src_path, event.dest_path))
            dirs, snap_file = os.path.split(event.dest_path)
            _, vm = os.path.split(dirs)
            snap, file_type = os.path.splitext(snap_file)
            if file_type == '.xml':
                try:
                    myVmSnapshotEventHandler('Create', vm, snap, self.group, self.version, self.plural)
                except HTTPError:
                    logger.error('Oops! ', exc_info=1)

    def on_created(self, event):
        if event.is_directory:
            logger.debug("directory created:{0}".format(event.src_path))
        else:
            logger.debug("file created:{0}".format(event.src_path))

    #             dirs,snap_file = os.path.split(event.src_path)
    #             _,vm = os.path.split(dirs)
    #             snap, file_type = os.path.splitext(snap_file)
    #             if file_type == '.xml':
    #                 try:
    #                     myVmSnapshotEventHandler('Create', vm, snap, self.group, self.version, self.plural)
    #                 except ApiException:
    #                     logger.error('Oops! ', exc_info=1)

    def on_deleted(self, event):
        if event.is_directory:
            logger.debug("directory deleted:{0}".format(event.src_path))
        else:
            logger.debug("file deleted:{0}".format(event.src_path))
            dirs, snap_file = os.path.split(event.src_path)
            _, vm = os.path.split(dirs)
            snap, file_type = os.path.splitext(snap_file)
            if file_type == '.xml':
                try:
                    myVmSnapshotEventHandler('Delete', vm, snap, self.group, self.version, self.plural)
                except HTTPError:
                    logger.error('Oops! ', exc_info=1)

    def on_modified(self, event):
        if event.is_directory:
            logger.debug("directory modified:{0}".format(event.src_path))
        else:
            logger.debug("file modified:{0}".format(event.src_path))


class VmGPUEventHandler(FSEHPreProcessing):
    def __init__(self):
        FSEHPreProcessing.__init__(self)

    def on_created(self, event):
        if event.is_directory:
            logger.debug("directory created:{0}".format(event.src_path))
            GPUCheckandUpdate()

    def on_deleted(self, event):
        if event.is_directory:
            logger.debug("directory deleted:{0}".format(event.src_path))
            GPUCheckandUpdate()



# def myVmBlockDevEventHandler(event, name, group, version, plural):
#     #     print(jsondict)
#     if event == "Delete":
#         try:
#             jsondict = get_custom_object(group, version, plural, name)
#             #             block_json = get_block_dev_json(name)
#             jsondict = updateJsonRemoveLifecycle(jsondict, {})
#             body = addPowerStatusMessage(jsondict, 'Ready', 'The resource is ready.')
#             update_custom_object(group, version, plural, name, body)
#         except ApiException as e:
#             if e.reason == 'Not Found':
#                 logger.debug('**VM block device %s already deleted, ignore this 404 error.' % name)
#             else:
#                 info = sys.exc_info()
#                 try:
#                     report_failure(name, jsondict, 'VirtletError', str(info[1]), group, version, plural)
#                 except:
#                     logger.warning('Oops! ', exc_info=1)
#         except:
#             logger.error('Oops! ', exc_info=1)
#             info = sys.exc_info()
#             try:
#                 report_failure(name, jsondict, 'VirtletError', str(info[1]), group, version, plural)
#             except:
#                 logger.warning('Oops! ', exc_info=1)
#         try:
#             logger.debug('Delete vm block %s, report to virtlet' % name)
#             delete_custom_object(group, version, plural, name)
#         except ApiException as e:
#             if e.reason == 'Not Found':
#                 logger.debug('**VM block %s already deleted, ignore this 404 error.' % name)
#             else:
#                 info = sys.exc_info()
#                 try:
#                     report_failure(name, jsondict, 'VirtletError', str(info[1]), group, version, plural)
#                 except:
#                     logger.warning('Oops! ', exc_info=1)
#         except:
#             logger.error('Oops! ', exc_info=1)
#             info = sys.exc_info()
#             try:
#                 report_failure(name, jsondict, 'VirtletError', str(info[1]), group, version, plural)
#             except:
#                 logger.warning('Oops! ', exc_info=1)
#     elif event == "Create":
#         try:
#             logger.debug('Create vm block %s, report to virtlet' % name)
#             jsondict = {'spec': {'REPLACE': {}, 'nodeName': HOSTNAME, 'status': {}},
#                         'kind': VMDEV_KIND, 'metadata': {'labels': {'host': HOSTNAME}, 'name': name},
#                         'apiVersion': '%s/%s' % (group, version)}
#             block_json = get_block_dev_json(name)
#             jsondict = updateJsonRemoveLifecycle(jsondict, loads(block_json))
#             body = addPowerStatusMessage(jsondict, 'Ready', 'The resource is ready.')
#             try:
#                 create_custom_object(group, version, plural, body)
#             except ApiException as e:
#                 logger.error(e)
# 
#         except:
#             logger.error('Oops! ', exc_info=1)
#             info = sys.exc_info()
#             try:
#                 jsondict = get_custom_object(group, version, plural, name)
#                 report_failure(name, jsondict, 'VirtletError', str(info[1]), group, version, plural)
#             except:
#                 logger.error('Oops! ', exc_info=1)
#     else:
#         try:
#             jsondict = get_custom_object(group, version, plural, name)
#         except:
#             logger.error('Oops! ', exc_info=1)
#             info = sys.exc_info()
#             try:
#                 report_failure(name, jsondict, 'VirtletError', str(info[1]), group, version, plural)
#             except:
#                 logger.warning('Oops! ', exc_info=1)
# 
# 
# class VmBlockDevEventHandler(FSEHPreProcessing):
#     def __init__(self, field, target, group, version, plural):
#         FSEHPreProcessing.__init__(self)
#         self.field = field
#         self.target = target
#         self.group = group
#         self.version = version
#         self.plural = plural
# 
#     def on_moved(self, event):
#         if event.is_directory:
#             logger.debug("directory moved from {0} to {1}".format(event.src_path, event.dest_path))
#         else:
#             logger.debug("file moved from {0} to {1}".format(event.src_path, event.dest_path))
# 
#     def on_created(self, event):
#         if event.is_directory:
#             logger.debug("directory created:{0}".format(event.src_path))
#         else:
#             logger.debug("file created:{0}".format(event.src_path))
#             path, block = os.path.split(event.src_path)
#             if is_block_dev_exists(event.src_path) and path != "/dev/mapper":
#                 try:
#                     myVmBlockDevEventHandler('Create', block, self.group, self.version, self.plural)
#                 except ApiException:
#                     logger.error('Oops! ', exc_info=1)
# 
#     def on_deleted(self, event):
#         if event.is_directory:
#             logger.debug("directory deleted:{0}".format(event.src_path))
#         else:
#             logger.debug("file deleted:{0}".format(event.src_path))
#             path, block = os.path.split(event.src_path)
#             #             if is_block_dev_exists(event.src_path):
#             if path == '/dev/pts':
#                 logger.debug('Ignore devices %s' % event.src_path)
#             else:
#                 try:
#                     myVmBlockDevEventHandler('Delete', block, self.group, self.version, self.plural)
#                 except ApiException:
#                     logger.error('Oops! ', exc_info=1)
# 
#     def on_modified(self, event):
#         if event.is_directory:
#             #             logger.debug("directory modified:{0}".format(event.src_path))
#             pass
#         else:
#             #             logger.debug("file modified:{0}".format(event.src_path))
#             pass
@retry(stop=stop_after_attempt(3),
       wait=wait_random(min=0,max=3),
       before_sleep=before_sleep_log(logger,logging.ERROR,True),
       reraise=True)
def _solve_conflict_in_VM(name):
    jsondict = get_custom_object(VM_KIND, name)
    jsondict['metadata']['labels']['host'] = HOSTNAME
    vm_xml = get_xml(name)
    vm_power_state = vm_state(name).get(name)
    vm_json = toKubeJson(xmlToJson(vm_xml))
    vm_json = updateDomain(loads(vm_json))
    jsondict = updateDomainStructureAndDeleteLifecycleInJson(jsondict, vm_json)
    jsondict = addPowerStatusMessage(jsondict, vm_power_state, 'The VM is %s' % vm_power_state)
    body = addNodeName(jsondict)
    update_custom_object(body)
    return

def myVmLibvirtXmlEventHandler(event, name, xml_path, group, version, plural):
    #     print(jsondict)
    if event == "Create":
        try:
            logger.debug('***Create VM %s from back-end, report to virtlet***' % name)
            jsondict = {'spec': {'domain': {}, 'nodeName': HOSTNAME, 'status': {}},
                        'kind': VM_KIND, 'metadata': {'labels': {'host': HOSTNAME}, 'name': name,'namespace': NAMESPACE},
                        'apiVersion': '%s/%s' % (group, version)}
            vm_xml = get_xml(name)
            vm_power_state = vm_state(name).get(name)
            vm_json = toKubeJson(xmlToJson(vm_xml))
            vm_json = updateDomain(loads(vm_json))
            jsondict = updateDomainStructureAndDeleteLifecycleInJson(jsondict, vm_json)
            jsondict = addPowerStatusMessage(jsondict, vm_power_state, 'The VM is %s' % vm_power_state)
            body = addNodeName(jsondict)
            try:
                logger.debug("Create VM %s from back-end: %s" %(name, body))
                create_custom_object(body)
            except HTTPError as e:
                if str(e).find('Conflict'):
                    _solve_conflict_in_VM(name)
                else:
                    logger.error(e)

        except:
            logger.error('Oops! ', exc_info=1)
            info = sys.exc_info()
            try:
                report_failure(name, 'VirtletError', str(info[1]), VM_KIND)
            except:
                logger.error('Oops! ', exc_info=1)
    elif event == "Modify":
        jsondict = get_custom_object(VM_KIND, name)
        try:
            if jsondict['metadata']['labels']['host'] != HOSTNAME:
                logger.debug('VM %s is migrating, ignore modify.' % name)
                return
            logger.debug('***Modify VM %s from back-end, report to virtlet***' % name)
            vm_xml = get_xml(name)
            vm_json = toKubeJson(xmlToJson(vm_xml))
            vm_json = updateDomain(loads(vm_json))
            body = updateDomainStructureAndDeleteLifecycleInJson(jsondict, vm_json)
            update_custom_object(body)
        except:
            logger.error('Oops! ', exc_info=1)
            info = sys.exc_info()
            try:
                report_failure(name, 'VirtletError', str(info[1]), VM_KIND)
            except:
                logger.warning('Oops! ', exc_info=1)
    elif event == "Delete":
        #             jsondict = client.CustomObjectsApi().get_namespaced_custom_object(group=group,
        #                                                                               version=version,
        #                                                                               namespace='default',
        #                                                                               plural=plural,
        #                                                                               name=name)
        logger.debug('***Delete VM %s, ignore it***' % name)
#         time.sleep(1)
#         try:
#             jsondict = get_custom_object(group, version, plural, name)
#             if jsondict['metadata']['labels']['host'] != HOSTNAME:
#                 logger.debug('VM %s is migrating or ha, ignore delete.' % name)
#                 return
#             #             vm_xml = get_xml(name)
#             #             vm_json = toKubeJson(xmlToJson(vm_xml))
#             #             vm_json = updateDomain(loads(vm_json))
#             body = updateDomainStructureAndDeleteLifecycleInJson(jsondict, {})
#             update_custom_object(group, version, plural, name, body)
#         except ApiException as e:
#             if e.reason == 'Not Found':
#                 logger.debug('**VM %s already deleted, ignore this 404 error.' % name)
#             else:
#                 info = sys.exc_info()
#                 try:
#                     report_failure(name, jsondict, 'VirtletError', str(info[1]), group, version, plural)
#                 except:
#                     logger.warning('Oops! ', exc_info=1)
#         except:
#             logger.error('Oops! ', exc_info=1)
#             info = sys.exc_info()
#             try:
#                 report_failure(name, jsondict, 'VirtletError', str(info[1]), group, version, plural)
#             except:
#                 logger.warning('Oops! ', exc_info=1)
#         try:
#             delete_custom_object(group, version, plural, name)
#         #                 vm_xml = get_xml(name)
#         #                 vm_json = toKubeJson(xmlToJson(vm_xml))
#         #                 vm_json = updateDomain(loads(vm_json))
#         #                 jsondict = updateDomainStructureAndDeleteLifecycleInJson(jsondict, vm_json)
#         #                 body = addExceptionMessage(jsondict, 'VirtletError', 'VM has been deleted in back-end.')
#         #                 modifyStructure(name, body, group, version, plural)
#         except ApiException as e:
#             if e.reason == 'Not Found':
#                 logger.debug('**VM %s already deleted, ignore this 404 error.' % name)
#             else:
#                 info = sys.exc_info()
#                 try:
#                     report_failure(name, jsondict, 'VirtletError', str(info[1]), group, version, plural)
#                 except:
#                     logger.warning('Oops! ', exc_info=1)
#         except:
#             logger.error('Oops! ', exc_info=1)
#             info = sys.exc_info()
#             try:
#                 report_failure(name, jsondict, 'VirtletError', str(info[1]), group, version, plural)
#             except:
#                 logger.warning('Oops! ', exc_info=1)


class VmLibvirtXmlEventHandler(FSEHPreProcessing):
    def __init__(self, field, target, group, version, plural):
        FSEHPreProcessing.__init__(self)
        self.field = field
        self.target = target
        self.group = group
        self.version = version
        self.plural = plural

    def on_moved(self, event):
        if event.is_directory:
            logger.debug("directory moved from {0} to {1}".format(event.src_path, event.dest_path))
        else:
            logger.debug("file moved from {0} to {1}".format(event.src_path, event.dest_path))
            _, name = os.path.split(event.dest_path)
            vm, file_type = os.path.splitext(name)
            if file_type == '.xml' and is_vm_exists(vm):
                try:
                    myVmLibvirtXmlEventHandler('Create', vm, event.dest_path, self.group, self.version, self.plural)
                except HTTPError:
                    logger.error('Oops! ', exc_info=1)

    def on_created(self, event):
        if event.is_directory:
            logger.debug("directory created:{0}".format(event.src_path))
        else:
            logger.debug("file created:{0}".format(event.src_path))

    #             _,name = os.path.split(event.src_path)
    #             file_type = os.path.splitext(name)[1]
    #             vm = os.path.splitext(os.path.splitext(name)[0])[0]
    #             if file_type == '.xml' and is_vm_exists(vm):
    #                 try:
    #                     myVmLibvirtXmlEventHandler('Create', vm, event.src_path, self.group, self.version, self.plural)
    #                 except ApiException:
    #                     logger.error('Oops! ', exc_info=1)

    def on_deleted(self, event):
        if event.is_directory:
            logger.debug("directory deleted:{0}".format(event.src_path))
        else:
            logger.debug("file deleted:{0}".format(event.src_path))
            _, name = os.path.split(event.src_path)
            vm, file_type = os.path.splitext(name)
            if file_type == '.xml' and not is_vm_exists(vm):
                try:
                    myVmLibvirtXmlEventHandler('Delete', vm, event.src_path, self.group, self.version, self.plural)
                except HTTPError:
                    logger.error('Oops! ', exc_info=1)

    def on_modified(self, event):
        if event.is_directory:
            #             logger.debug("directory modified:{0}".format(event.src_path))
            pass
        else:
            logger.debug("file modified:{0}".format(event.src_path))
            _, name = os.path.split(event.src_path)
            vm, file_type = os.path.splitext(name)
            if file_type == '.xml' and is_vm_exists(vm):
                try:
                    myVmLibvirtXmlEventHandler('Modify', vm, event.src_path, self.group, self.version, self.plural)
                except HTTPError:
                    logger.error('Oops! ', exc_info=1)


def myVmdImageLibvirtXmlEventHandler(event, name, pool, xml_path, group, version, plural):
    #     print(jsondict)
    if event == "Create":
        try:
            '''
            Refresh pool manually
            '''
            refresh_pool(pool)
            logger.debug('Create vm disk image %s, report to virtlet' % name)
            jsondict = {'spec': {'volume': {}, 'nodeName': HOSTNAME, 'status': {}},
                        'kind': VMDI_KIND, 'metadata': {'labels': {'host': HOSTNAME}, 'name': name,'namespace': NAMESPACE},
                        'apiVersion': '%s/%s' % (group, version)}
            vmd_xml = get_volume_xml(pool, name)
            vol_path = get_volume_path(pool, name)
            vmd_json = toKubeJson(xmlToJson(vmd_xml))
            vmd_json = addSnapshots(vol_path, loads(vmd_json))
            jsondict = updateDomainStructureAndDeleteLifecycleInJson(jsondict, vmd_json)
            jsondict = addPowerStatusMessage(jsondict, 'Ready', 'The resource is ready.')
            body = addNodeName(jsondict)
            try:
                create_custom_object(body)
            except HTTPError as e:
                logger.error(e)

        except:
            logger.error('Oops! ', exc_info=1)
            info = sys.exc_info()
            try:
                report_failure(name, 'VirtletError', str(info[1]), VMDI_KIND)
            except:
                logger.error('Oops! ', exc_info=1)
    elif event == "Delete":
        try:
            '''
            Refresh pool manually
            '''
            refresh_pool(pool)
            jsondict = get_custom_object(VMDI_KIND, name)
            #             with open(xml_path, 'r') as fr:
            #                 vm_xml = fr.read()
            #             vmd_json = toKubeJson(xmlToJson(vm_xml))
            #             vmd_json = updateDomain(loads(vmd_json))
            jsondict = updateDomainStructureAndDeleteLifecycleInJson(jsondict, {})
            body = addPowerStatusMessage(jsondict, 'Ready', 'The resource is ready.')
            update_custom_object(body)
        except HTTPError as e:
            if str(e).find('Not Found'):
                logger.debug('**VM disk image %s already deleted, ignore this 404 error.' % name)
            else:
                info = sys.exc_info()
                try:
                    report_failure(name, 'VirtletError', str(info[1]), VMDI_KIND)
                except:
                    logger.warning('Oops! ', exc_info=1)
        except:
            logger.error('Oops! ', exc_info=1)
            info = sys.exc_info()
            try:
                report_failure(name, 'VirtletError', str(info[1]), VMDI_KIND)
            except:
                logger.warning('Oops! ', exc_info=1)
        try:
            logger.debug('Delete vm disk image %s, report to virtlet' % name)
            delete_custom_object(VMDI_KIND,NAMESPACE, name)
        #                 jsondict = updateDomainStructureAndDeleteLifecycleInJson(jsondict, vmd_json)
        #                 body = addExceptionMessage(jsondict, 'VirtletError', 'VM has been deleted in back-end.')
        #                 modifyStructure(name, body, group, version, plural)
        except HTTPError as e:
            if str(e).find('Not Found'):
                logger.debug('**VM disk image %s already deleted, ignore this 404 error.' % name)
            else:
                info = sys.exc_info()
                try:
                    report_failure(name, 'VirtletError', str(info[1]), VMDI_KIND)
                except:
                    logger.warning('Oops! ', exc_info=1)
        except:
            logger.error('Oops! ', exc_info=1)
            info = sys.exc_info()
            try:
                report_failure(name, 'VirtletError', str(info[1]), VMDI_KIND)
            except:
                logger.warning('Oops! ', exc_info=1)


class VmdImageLibvirtXmlEventHandler(FSEHPreProcessing):
    def __init__(self, pool, target, group, version, plural):
        FSEHPreProcessing.__init__(self)
        self.pool = pool
        self.target = target
        self.group = group
        self.version = version
        self.plural = plural

    # def on_moved(self, event):
    #     if event.is_directory:
    #         logger.debug("directory moved from {0} to {1}".format(event.src_path, event.dest_path))
    #     else:
    #         logger.debug("file moved from {0} to {1}".format(event.src_path, event.dest_path))
    #         vmdi = os.path.split(event.src_path)[1]
    #         try:
    #             myVmdImageLibvirtXmlEventHandler('Create', vmdi, self.pool, event.dest_path, self.group, self.version,
    #                                              self.plural)
    #         except HTTPError:
    #             logger.error('Oops! ', exc_info=1)

    def on_created(self, event):
        if event.is_directory:
            logger.debug("directory created:{0}".format(event.src_path))
        else:
            logger.debug("file created:{0}".format(event.src_path))
            vmdi = os.path.split(event.src_path)[1]
            try:
                myVmdImageLibvirtXmlEventHandler('Create', vmdi, self.pool, event.src_path, self.group, self.version,
                                                 self.plural)
            except HTTPError:
                logger.error('Oops! ', exc_info=1)

    def on_deleted(self, event):
        if event.is_directory:
            logger.debug("directory deleted:{0}".format(event.src_path))
        else:
            logger.debug("file deleted:{0}".format(event.src_path))
            vmdi = os.path.split(event.src_path)[1]
            try:
                myVmdImageLibvirtXmlEventHandler('Delete', vmdi, self.pool, event.src_path, self.group, self.version,
                                                 self.plural)
            except HTTPError:
                logger.error('Oops! ', exc_info=1)

    # def on_modified(self, event):
    #     if event.is_directory:
    #         #             logger.debug("directory modified:{0}".format(event.src_path))
    #         pass
    #     else:
    #         logger.debug("file modified:{0}".format(event.src_path))


#             _,name = os.path.split(event.src_path)
#             file_type = os.path.splitext(name)[1]
#             vmi = os.path.splitext(os.path.splitext(name)[0])[0]
#             if file_type == '.xml':
#                 try:
#                     myVmdImageLibvirtXmlEventHandler('Modify', vmi, event.src_path, self.group, self.version, self.plural)
#                 except ApiException:
#                     logger.error('Oops! ', exc_info=1)

def myImageLibvirtXmlEventHandler(event, name, xml_path, group, version, plural):
    #     print(jsondict)
    if event == "Create":
        try:
            logger.debug('Create vm image %s, report to virtlet' % name)
            jsondict = {'spec': {'domain': {}, 'nodeName': HOSTNAME, 'status': {}},
                        'kind': VMI_KIND, 'metadata': {'labels': {'host': HOSTNAME}, 'name': name,'namespace': NAMESPACE},
                        'apiVersion': '%s/%s' % (group, version)}
            with open(xml_path, 'r') as fr:
                vm_xml = fr.read()
            vm_json = toKubeJson(xmlToJson(vm_xml))
            vm_json = updateDomain(loads(vm_json))
            jsondict = updateDomainStructureAndDeleteLifecycleInJson(jsondict, vm_json)
            jsondict = addPowerStatusMessage(jsondict, 'Ready', 'The resource is ready.')
            body = addNodeName(jsondict)
            try:
                create_custom_object(body)
            except HTTPError as e:
                logger.error(e)

        except:
            logger.error('Oops! ', exc_info=1)
            info = sys.exc_info()
            try:
                report_failure(name, 'VirtletError', str(info[1]), VMI_KIND)
            except:
                logger.error('Oops! ', exc_info=1)
    elif event == "Modify":
        jsondict = get_custom_object(VMI_KIND, name)
        try:
            logger.debug('Modify vm image %s, report to virtlet' % name)
            with open(xml_path, 'r') as fr:
                vm_xml = fr.read()
            vm_json = toKubeJson(xmlToJson(vm_xml))
            vm_json = updateDomain(loads(vm_json))
            jsondict = updateDomainStructureAndDeleteLifecycleInJson(jsondict, vm_json)
            body = addPowerStatusMessage(jsondict, 'Ready', 'The resource is ready.')
            #             logger.debug(body)
            update_custom_object(body)
        except:
            logger.error('Oops! ', exc_info=1)
            info = sys.exc_info()
            try:
                report_failure(name, 'VirtletError', str(info[1]), VMI_KIND)
            except:
                logger.warning('Oops! ', exc_info=1)
    elif event == "Delete":
        #             jsondict = client.CustomObjectsApi().get_namespaced_custom_object(group=group,
        #                                                                               version=version,
        #                                                                               namespace='default',
        #                                                                               plural=plural,
        #                                                                               name=name)
        try:
            jsondict = get_custom_object(VMI_KIND, name)
            #             with open(xml_path, 'r') as fr:
            #                 vm_xml = fr.read()
            #             vm_json = toKubeJson(xmlToJson(vm_xml))
            #             vm_json = updateDomain(loads(vm_json))
            jsondict = updateDomainStructureAndDeleteLifecycleInJson(jsondict, {})
            body = addPowerStatusMessage(jsondict, 'Ready', 'The resource is ready.')
            update_custom_object(body)
        except HTTPError as e:
            if str(e).find('Not Found'):
                logger.debug('**VM image %s already deleted, ignore this 404 error.' % name)
            else:
                info = sys.exc_info()
                try:
                    report_failure(name, 'VirtletError', str(info[1]), VMI_KIND)
                except:
                    logger.warning('Oops! ', exc_info=1)
        except:
            logger.error('Oops! ', exc_info=1)
            info = sys.exc_info()
            try:
                report_failure(name, 'VirtletError', str(info[1]), VMI_KIND)
            except:
                logger.warning('Oops! ', exc_info=1)
        try:
            logger.debug('Delete vm image %s, report to virtlet' % name)
            delete_custom_object(VMI_KIND,NAMESPACE, name)
        #                 jsondict = updateDomainStructureAndDeleteLifecycleInJson(jsondict, vm_json)
        #                 body = addExceptionMessage(jsondict, 'VirtletError', 'VM has been deleted in back-end.')
        #                 modifyStructure(name, body, group, version, plural)
        except HTTPError as e:
            if str(e).find('Not Found'):
                logger.debug('**VM image %s already deleted, ignore this 404 error.' % name)
            else:
                info = sys.exc_info()
                try:
                    report_failure(name, 'VirtletError', str(info[1]), VMI_KIND)
                except:
                    logger.warning('Oops! ', exc_info=1)
        except:
            logger.error('Oops! ', exc_info=1)
            info = sys.exc_info()
            try:
                report_failure(name, 'VirtletError', str(info[1]), VMI_KIND)
            except:
                logger.warning('Oops! ', exc_info=1)


class ImageLibvirtXmlEventHandler(FSEHPreProcessing):
    def __init__(self, field, target, group, version, plural):
        FSEHPreProcessing.__init__(self)
        self.field = field
        self.target = target
        self.group = group
        self.version = version
        self.plural = plural

    def on_moved(self, event):
        if event.is_directory:
            logger.debug("directory moved from {0} to {1}".format(event.src_path, event.dest_path))
        else:
            logger.debug("file moved from {0} to {1}".format(event.src_path, event.dest_path))
            _, name = os.path.split(event.dest_path)
            vmi, file_type = os.path.splitext(name)
            if file_type == '.xml':
                try:
                    myImageLibvirtXmlEventHandler('Create', vmi, event.dest_path, self.group, self.version, self.plural)
                except HTTPError:
                    logger.error('Oops! ', exc_info=1)

    def on_created(self, event):
        if event.is_directory:
            logger.debug("directory created:{0}".format(event.src_path))
        else:
            logger.debug("file created:{0}".format(event.src_path))

    #             _,name = os.path.split(event.src_path)
    #             file_type = os.path.splitext(name)[1]
    #             vmi = os.path.splitext(os.path.splitext(name)[0])[0]
    #             if file_type == '.xml':
    #                 try:
    #                     myImageLibvirtXmlEventHandler('Create', vmi, event.src_path, self.group, self.version, self.plural)
    #                 except ApiException:
    #                     logger.error('Oops! ', exc_info=1)

    def on_deleted(self, event):
        if event.is_directory:
            logger.debug("directory deleted:{0}".format(event.src_path))
        else:
            logger.debug("file deleted:{0}".format(event.src_path))
            _, name = os.path.split(event.src_path)
            vmi, file_type = os.path.splitext(name)
            if file_type == '.xml':
                try:
                    myImageLibvirtXmlEventHandler('Delete', vmi, event.src_path, self.group, self.version, self.plural)
                except HTTPError:
                    logger.error('Oops! ', exc_info=1)

    def on_modified(self, event):
        if event.is_directory:
            #             logger.debug("directory modified:{0}".format(event.src_path))
            pass
        else:
            #             logger.debug("file modified:{0}".format(event.src_path))
            _, name = os.path.split(event.src_path)
            vmi, file_type = os.path.splitext(name)
            if file_type == '.xml':
                try:
                    myImageLibvirtXmlEventHandler('Modify', vmi, event.src_path, self.group, self.version, self.plural)
                except HTTPError:
                    logger.error('Oops! ', exc_info=1)


def updateDomainStructureAndDeleteLifecycleInJson(jsondict, body):
    if jsondict:
        spec = jsondict.get('spec', {})
        lifecycle = spec.get('lifecycle')

        if lifecycle:
            del spec['lifecycle']

        if body:
            spec.update(body)

    return jsondict

def _create_or_update_vmgpus(group, version, metadata_name, gpu_info):
    jsondict = {}
    try:
        # logger.debug('create or update vmgpus: %s' % metadata_name)
        jsondict = get_custom_object(VMGPU_KIND,metadata_name)
    except HTTPError as e:
        if str(e).find("Not Found"):
            jsondict = {'spec': gpu_info, 'kind': VMGPU_KIND,
                        'metadata': {'labels': {'host': HOSTNAME}, 'name': metadata_name},
                        'apiVersion': '%s/%s' % (group, version)}
            # logger.debug('**VM %s already deleted, ignore this 404 error.' % metadata_name)
            create_custom_object(jsondict)
            return
    except Exception as e:
        logger.error('Oops! ', exc_info=1)
        return

    try:
        jsondict['spec'] = gpu_info
        update_custom_object(jsondict)
    except HTTPError as e:
        if str(e).find('Conflict'):
            logger.debug('**Other process updated %s, ignore this 409.' % metadata_name)
        else:
            logger.error('Oops! ', exc_info=1)
    except Exception as e:
        logger.error('Oops! ', exc_info=1)


def _list_gpus():
    command = f"lspci -nn | grep -i nvidia"
    info_lines = runCmdRaiseException(command)
    logger.debug(info_lines)
    # Parse the lines and create key-value pairs
    result = []
    if info_lines:
        for line in info_lines:
            pattern = re.compile(r'(\w+:\w+\.\w+)[\w\s]+controller[\w\s]+', re.DOTALL)
            matches = pattern.findall(line)
            for match in matches:
                id_value = match
                result.append(id_value)
    return result


def _parse_pci_info(gpu_id, gpu_id_value):
    # Execute the command to get the output
    command = f"lspci -vs {gpu_id_value}"
    info = runCmdRaiseException(command)
    # logger.debug(info)

    # Define a regular expression pattern for the controller information
    pattern = re.compile(r'(\w+:\w+\.\w+)[\w\s]+controller: (.+)', re.DOTALL)

    pattern1 = re.compile(r'Kernel driver in use: (.+)', re.DOTALL)

    # Find the matches in the input information
    matches = pattern.findall('\n'.join(info))
    matches1 = pattern1.findall('\n'.join(info))

    # Replace matches with a standardized key
    for match in matches:
        id_value, controller_value = match
        info = [line.replace(f'{id_value} controller: {controller_value}',
                             f'id: {id_value} \n type: {controller_value}') for line in info]

    for match in matches1:
        key = "kernelDriverInUse"
        info = [line.replace(match, f'{key}: {match}') for line in info]

    # Split the input by lines and remove empty lines
    info_lines = [line.strip() for line in info if line.strip()]

    # Create a dictionary to store the information
    info_dict = {}

    # Parse the lines and create key-value pairs
    for line in info_lines:
        if ':' in line:
            key, value = line.split(':', 1)
            # Use regular expressions for matching and replacement
            pattern = re.compile(r'\[([^\]]+)\]')
            # Check if words list is not empty before accessing indices
            words = key.split()
            current_key = words[0].lower() + ''.join(word.capitalize() for word in words[1:]) if words else ""
            info_dict[current_key] = value.strip()

    # Extract 'id' and 'type' values from the first line
    id_match = re.match(r'(\w+:\w+\.\w+)', info_lines[0])
    type_match = re.search(r'\[([^\]]+)\]', info_lines[0])

    # Update the dictionary with 'id' and 'type' values
    info_dict['id'] = id_match.group(1) if id_match else ''
    info_dict['type'] = type_match.group(1) if type_match else ''
    # logger.debug(info_dict)

    # Update the dictionary with 'inUse' values
    # Vms
    in_use = None
    bus_id = gpu_id_value.split(":")[0] if ":" in gpu_id_value else gpu_id_value.lower()
    if info_dict.get('kernelDriverInUse') == 'vfio-pci':
        info_dict['useMode'] = "passthrough"
        for vm in list_active_vms():
            vm_xml = get_xml(vm)
            vm_json_string = dumps(toKubeJson(xmlToJson(vm_xml)))
            data_without_spaces = vm_json_string.replace("\n", "").replace(" ", "")
            # logger.debug(data_without_spaces)
            # logger.debug(f"\\\"_bus\\\":\\\"0x{bus_id}\\\"")
            if f"\\\"_bus\\\":\\\"0x{bus_id}\\\"" in data_without_spaces:
                # logger.debug("inhere")
                in_use = vm
        info_dict['inUse'] = in_use
    else:
        info_dict['useMode'] = "share"
        # Containers
        command1 = f'kubectl get pods -A -o json --field-selector spec.nodeName={HOSTNAME} | jq -r \'.items[] | select(.metadata.annotations."doslab.io/gpu-assigned" == "true") | "namespace-" + .metadata.namespace + "-name-" + .metadata.name + "-gpu-" + .metadata.annotations."doslab.io/predicate-gpu-idx-0" + "-gpucore-" + .spec.containers[0].resources.limits."doslab.io/vcuda-core" + "-gpumem-" + .spec.containers[0].resources.limits."doslab.io/vcuda-memory"\''
        info1 = runCmdRaiseException(command1)
        pattern = re.compile(r'namespace-(?P<namespace>[\w\d\-\.]+)-name-(?P<name>[\w\d\-\.]+)-gpu-(?P<gpu>\d+)-gpucore-(?P<gpucore>\d+)-gpumem-(?P<gpumem>\d+)')
        if info1:
            in_use_pods = []
            for line in info1:
                match = pattern.search(line)
                if match:
                    result_dict = match.groupdict()
                    if str(gpu_id) == result_dict.get('gpu'):
                        in_use_pods.append({"namespace": result_dict.get("namespace"), "name": result_dict.get("name"),
                                            "gpucore": result_dict.get("gpucore"), "gpumem": result_dict.get("gpumem")})
            info_dict['inUse'] = in_use_pods


    # logger.debug(info_dict)
    gpu_name = 'host-%s-type-%s-id-%s' % (HOSTNAME.lower(), info_dict.get('type', 'unknown').replace(' ', '-').lower(), bus_id.lower())

    # Modify the dictionary to include the desired keys and values
    gpu_info = {
        "gpu": {
            "id": info_dict.get("id", ""),
            "type": info_dict.get("type", ""),
            "subsystem": info_dict.get("subsystem", ""),
            "flags": info_dict.get("flags", ""),
            "capabilities": info_dict.get("capabilities", ""),
            "kernelDriverInUse": info_dict.get("kernelDriverInUse", ""),
            "kernelModules": info_dict.get("kernelModules", ""),
            "inUse": info_dict.get("inUse", ""),
            "useMode": info_dict.get("useMode", "")
        },
        "nodeName": HOSTNAME
    }
    logger.debug(gpu_info)

    return gpu_name, gpu_info


def GPUCheckandUpdate():
    gpus = _list_gpus()
    if gpus:
        for gpu_id, gpu_id_value in enumerate(gpus):
            (gpu_name, gpu_info) = _parse_pci_info(gpu_id, gpu_id_value)
            _create_or_update_vmgpus(GROUP, VERSION, gpu_name, gpu_info)


def addNodeName(jsondict):
    if jsondict:
        '''
        Get target VM name from Json.
        '''
        spec = jsondict['spec']
        if spec:
            jsondict['spec']['nodeName'] = HOSTNAME
    return jsondict


def observe(observer,kind):
    OLD_PATH_WATCHERS = {}
    paths = _get_all_pool_path()
    paths_copy = paths.copy()
    for pool_name, pool_path in paths_copy.items():
        content_file = '%s/content' % pool_path
        if os.path.exists(content_file):
            with open(content_file, 'r') as fr:
                pool_content = fr.read().strip()
            if pool_content != kind:
                del paths[pool_name]
    # unschedule not exist pool path
    watchers = {}
    for path in OLD_PATH_WATCHERS.keys():
        if path not in paths.values():
            observer.unschedule(OLD_PATH_WATCHERS[path])
        else:
            watchers[path] = OLD_PATH_WATCHERS[path]
    OLD_PATH_WATCHERS = watchers

    for pool, pool_path in paths.items():
        if pool_path and pool_path not in OLD_PATH_WATCHERS.keys() and os.path.isdir(pool_path):
            logger.debug(pool_path)
            if kind=='vmd':
                event_handler = VmVolEventHandler()
            elif kind=='vmdi':
                event_handler=VmdImageLibvirtXmlEventHandler(pool, VMD_TEMPLATE_DIR, GROUP, VERSION,
                                                                   PLURAL_VM_DISK_IMAGE)
            else:
                raise Exception('Wrong pool kind')
            watcher = observer.schedule(event_handler, pool_path, True)
            OLD_PATH_WATCHERS[pool_path] = watcher

def main():
    observer = Observer()
    try:
        # for ob in VOL_DIRS:
        #     if not os.path.exists(ob[1]):
        #         os.makedirs(ob[1], 0x0711)
        #         try:
        #             runCmdRaiseException('virsh pool-create-as --name %s --type dir --target %s' % (ob[0], ob[1]))
        #         except:
        #             os.removedirs(ob[1])
        #             logger.error('Oops! ', exc_info=1)
        #     event_handler = VmVolEventHandler(ob[0], ob[1], GROUP_VM_DISK, VERSION_VM_DISK, PLURAL_VM_DISK)
        #     observer.schedule(event_handler,ob[1],True)
        # for ob in SYSTEM_VOL_DIRS:
        #     if not os.path.exists(ob[1]):
        #         os.makedirs(ob[1], 0x0711)
        #     event_handler = VmVolEventHandler(ob[0], ob[1], GROUP_VM_DISK, VERSION_VM_DISK, PLURAL_VM_DISK)
        #     observer.schedule(event_handler,ob[1],True)
#         for ob in SNAP_DIRS:
#             if not os.path.exists(ob[1]):
#                 os.makedirs(ob[1], 0x0711)
#             event_handler = VmSnapshotEventHandler(ob[0], ob[1], GROUP_VM_SNAPSHOT, VERSION_VM_SNAPSHOT,
#                                                    PLURAL_VM_SNAPSHOT)
#             observer.schedule(event_handler, ob[1], True)
        #         for ob in BLOCK_DEV_DIRS:
        #             if not os.path.exists(ob[1]):
        #                 os.makedirs(ob[1], 0x0711)
        #             event_handler = VmBlockDevEventHandler(ob[0], ob[1], GROUP_BLOCK_DEV_UIT, VERSION_BLOCK_DEV_UIT, PLURAL_BLOCK_DEV_UIT)
        #             observer.schedule(event_handler,ob[1],True)

        # vm event handler
        if not os.path.exists(LIBVIRT_XML_DIR):
            os.makedirs(LIBVIRT_XML_DIR, 0x0711)
        event_handler = VmLibvirtXmlEventHandler('kvm', LIBVIRT_XML_DIR, GROUP, VERSION, PLURAL_VM)
        observer.schedule(event_handler, LIBVIRT_XML_DIR, True)
#         for ob in TEMPLATE_DIRS:
#             if not os.path.exists(ob[1]):
#                 os.makedirs(ob[1], 0x0711)
#             event_handler = ImageLibvirtXmlEventHandler(ob[0], ob[1], GROUP_VMI, VERSION_VMI, PLURAL_VMI)
#             observer.schedule(event_handler, ob[1], True)

        # vmd event handler
        # if not os.path.exists(VMD_TEMPLATE_DIR):
        #     os.makedirs(VMD_TEMPLATE_DIR, 0x0711)
        #     try:
        #         runCmdRaiseException('virsh pool-create-as --name %s --type dir --target %s' % ('default', VMD_TEMPLATE_DIR))
        #     except:
        #         os.removedirs(VMD_TEMPLATE_DIR)
        #         runCmdRaiseException('virsh pool-destroy --name %s' % ('default'))
        #         runCmdRaiseException('virsh pool-undefine --name %s' % ('default'))
        #         logger.error('Oops! ', exc_info=1)
        # event_handler = VmdImageLibvirtXmlEventHandler('default', VMD_TEMPLATE_DIR, GROUP, VERSION,
        #                                                PLURAL_VM_DISK_IMAGE)
        # observer.schedule(event_handler, VMD_TEMPLATE_DIR, True)
        GPUCheckandUpdate()
        if os.path.exists(constants.KUBEVMM_GPU_NVIDIA_DIR):
            event_handler = VmGPUEventHandler()
            observer.schedule(event_handler, constants.KUBEVMM_GPU_NVIDIA_DIR, True)
        if os.path.exists(constants.KUBEVMM_GPU_PCI_DIR):
            event_handler = VmGPUEventHandler()
            observer.schedule(event_handler, constants.KUBEVMM_GPU_PCI_DIR, True)
        observer.start()

        # vmp and vmdi event handler
        # OLD_PATH_WATCHERS = {}
        while True:
            try:
                # observe(observer,'vmd')
                node = get_1st_ready()
                logger.info(f"VMDI is listened on {node}")
                if HOSTNAME == node:
                    observe(observer,'vmdi')
            except Exception as e:
                logger.warning('Oops! ', exc_info=1)
            finally:
                sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    except:
        logger.warning('Oops! ', exc_info=1)
    observer.join()


if __name__ == "__main__":
    # config.load_kube_config(config_file=TOKEN)
    while True:
        try:
            main()
        except Exception as e:
            # if repr(e).find('Connection refused') != -1 or repr(e).find('No route to host') != -1:
            #     config.load_kube_config(config_file=TOKEN)
            info=sys.exc_info()
            logger.error('Oops! ', exc_info=1)
            time.sleep(5)
            continue
