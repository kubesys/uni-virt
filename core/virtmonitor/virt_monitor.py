'''
 * Copyright (2024, ) Institute of Software, Chinese Academy of Sciences
 *
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

import subprocess

import prometheus_client
import os
import sys
import operator
import time
import threading
import concurrent.futures
from prometheus_client.core import CollectorRegistry
from prometheus_client import Gauge,start_http_server,Counter
# from kubernetes import config
from json import loads, dumps

sys.path.append("..")
from utils import constants
from utils import logger
from utils.misc import singleton, get_hostname_in_lower_case, list_objects_in_kubernetes, get_field_in_kubernetes_by_index, CDaemon, list_all_disks, runCmdRaiseException, get_hostname_in_lower_case, get_field_in_kubernetes_node,daemonize
# from kubesys.client import KubernetesClient
LOG = '/var/log/virtmonitor.log'
logger = logger.set_logger(os.path.basename(__file__), LOG)

TOKEN = constants.KUBERNETES_TOKEN_FILE
PLURAL = constants.KUBERNETES_PLURAL_VM
VERSION = constants.KUBERNETES_API_VERSION
GROUP = constants.KUBERNETES_GROUP
KIND=constants.KUBERNETES_KIND_VM
PLURAL_VMP = constants.KUBERNETES_PLURAL_VMP
VERSION_VMP = constants.KUBERNETES_API_VERSION
GROUP_VMP = constants.KUBERNETES_GROUP
KIND_VMP=constants.KUBERNETES_KIND_VMP
SHARE_FS_MOUNT_POINT = constants.KUBEVMM_SHARE_FS_MOUNT_POINT
VDISK_FS_MOUNT_POINT = constants.KUBEVMM_VDISK_FS_MOUNT_POINT
LOCAL_FS_MOUNT_POINT = constants.KUBEVMM_LOCAL_FS_MOUNT_POINT
BLOCK_FS_MOUNT_POINT = constants.KUBEVMM_BLOCK_FS_MOUNT_POINT

HOSTNAME = get_hostname_in_lower_case()

CPU_UTILIZATION = {}
LAST_TAGS = {}
LAST_RESOURCE_UTILIZATION = {}

ALL_VMS_IN_PROMETHEUS = []

# thread_pool = threadpool.ThreadPool(10)

# vm_cpu_system_proc_rate = Gauge('vm_cpu_system_proc_rate', 'The CPU rate of running system processes in virtual machine',
#                                 ['zone', 'host', 'vm', "labels"])
# vm_cpu_usr_proc_rate = Gauge('vm_cpu_usr_proc_rate', 'The CPU rate of running user processes in virtual machine',
#                                 ['zone', 'host', 'vm', "labels"])
# vm_cpu_idle_rate = Gauge('vm_cpu_idle_rate', 'The CPU idle rate in virtual machine',
#                                 ['zone', 'host', 'vm', "labels"])
# vm_mem_total_bytes = Gauge('vm_mem_total_bytes', 'The total memory bytes in virtual machine',
#                                 ['zone', 'host', 'vm', "labels"])
# vm_mem_available_bytes = Gauge('vm_mem_available_bytes', 'The available memory bytes in virtual machine',
#                                 ['zone', 'host', 'vm', "labels"])
# vm_mem_buffers_bytes = Gauge('vm_mem_buffers_bytes', 'The buffers memory bytes in virtual machine',
#                                 ['zone', 'host', 'vm', "labels"])
# vm_mem_rate = Gauge('vm_mem_rate', 'The memory rate in virtual machine',
#                                 ['zone', 'host', 'vm', "labels"])
# vm_disk_read_requests_per_secend = Gauge('vm_disk_read_requests_per_secend', 'Disk read requests per second in virtual machine',
#                                 ['zone', 'host', 'vm', "labels", 'device'])
# vm_disk_write_requests_per_secend = Gauge('vm_disk_write_requests_per_secend', 'Disk write requests per second in virtual machine',
#                                 ['zone', 'host', 'vm', "labels", 'device'])
# vm_disk_read_bytes_per_secend = Gauge('vm_disk_read_bytes_per_secend', 'Disk read bytes per second in virtual machine',
#                                 ['zone', 'host', 'vm', "labels", 'device'])
# vm_disk_write_bytes_per_secend = Gauge('vm_disk_write_bytes_per_secend', 'Disk write bytes per second in virtual machine',
#                                 ['zone', 'host', 'vm', "labels", 'device'])
# vm_network_receive_packages_per_secend = Gauge('vm_network_receive_packages_per_secend', 'Network receive packages per second in virtual machine',
#                                 ['zone', 'host', 'vm', "labels", 'device'])
# vm_network_receive_bytes_per_secend = Gauge('vm_network_receive_bytes_per_secend', 'Network receive bytes per second in virtual machine',
#                                 ['zone', 'host', 'vm', "labels", 'device'])
# vm_network_receive_errors_per_secend = Gauge('vm_network_receive_errors_per_secend', 'Network receive errors per second in virtual machine',
#                                 ['zone', 'host', 'vm', "labels", 'device'])
# vm_network_receive_drops_per_secend = Gauge('vm_network_receive_drops_per_secend', 'Network receive drops per second in virtual machine',
#                                 ['zone', 'host', 'vm', "labels", 'device'])
# vm_network_send_packages_per_secend = Gauge('vm_network_send_packages_per_secend', 'Network send packages per second in virtual machine',
#                                 ['zone', 'host', 'vm', "labels", 'device'])
# vm_network_send_bytes_per_secend = Gauge('vm_network_send_bytes_per_secend', 'Network send bytes per second in virtual machine',
#                                 ['zone', 'host', 'vm', "labels", 'device'])
# vm_network_send_errors_per_secend = Gauge('vm_network_send_errors_per_secend', 'Network send errors per second in virtual machine',
#                                 ['zone', 'host', 'vm', "labels", 'device'])
# vm_network_send_drops_per_secend = Gauge('vm_network_send_drops_per_secend', 'Network send drops per second in virtual machine',
#                                 ['zone', 'host', 'vm', "labels", 'device'])
# storage_pool_total_size_kilobytes = Gauge('storage_pool_total_size_kilobytes', 'Storage pool total size in kilobytes on host',
#                                 ['zone', 'host', 'pool', 'type'])
# storage_pool_used_size_kilobytes = Gauge('storage_pool_used_size_kilobytes', 'Storage pool used size in kilobytes on host',
#                                 ['zone', 'host', 'pool', 'type'])
# storage_disk_total_size_kilobytes = Gauge('storage_disk_total_size_kilobytes', 'Storage disk total size in kilobytes on host',
#                                 ['zone', 'host', 'pool', 'type', 'disk'])
# storage_disk_used_size_kilobytes = Gauge('storage_disk_used_size_kilobytes', 'Storage disk used size in kilobytes on host',
#                                 ['zone', 'host', 'pool', 'type', 'disk'])

# VMS_CACHE = []

# vm_cpu_system_proc_rate = Gauge('vm_cpu_system_proc_rate', 'The CPU rate of running system processes in virtual machine',
#                                 ['zone', 'host', 'vm', "owner", "router", "autoscalinggroup", "cluster"])
# vm_cpu_usr_proc_rate = Gauge('vm_cpu_usr_proc_rate', 'The CPU rate of running user processes in virtual machine',
#                                 ['zone', 'host', 'vm', "owner", "router", "autoscalinggroup", "cluster"])
vm_cpu_idle_rate = Gauge('vm_cpu_idle_rate', 'The CPU idle rate in virtual machine',
                         ['zone', 'host', 'vm', "owner", "router", "autoscalinggroup", "cluster"])
vm_mem_total_bytes = Gauge('vm_mem_total_bytes', 'The total memory bytes in virtual machine',
                           ['zone', 'host', 'vm', "owner", "router", "autoscalinggroup", "cluster"])
vm_mem_available_bytes = Gauge('vm_mem_available_bytes', 'The available memory bytes in virtual machine',
                               ['zone', 'host', 'vm', "owner", "router", "autoscalinggroup", "cluster"])
vm_mem_buffers_bytes = Gauge('vm_mem_buffers_bytes', 'The buffers memory bytes in virtual machine',
                             ['zone', 'host', 'vm', "owner", "router", "autoscalinggroup", "cluster"])
vm_mem_rate = Gauge('vm_mem_rate', 'The memory rate in virtual machine',
                    ['zone', 'host', 'vm', "owner", "router", "autoscalinggroup", "cluster"])
vm_disk_read_requests_per_secend = Gauge('vm_disk_read_requests_per_secend', 'Disk read requests per second in virtual machine',
                                         ['zone', 'host', 'vm', "owner", "router", "autoscalinggroup", "cluster", 'device'])
vm_disk_write_requests_per_secend = Gauge('vm_disk_write_requests_per_secend', 'Disk write requests per second in virtual machine',
                                          ['zone', 'host', 'vm', "owner", "router", "autoscalinggroup", "cluster", 'device'])
vm_disk_read_bytes_per_secend = Gauge('vm_disk_read_bytes_per_secend', 'Disk read bytes per second in virtual machine',
                                      ['zone', 'host', 'vm', "owner", "router", "autoscalinggroup", "cluster", 'device'])
vm_disk_write_bytes_per_secend = Gauge('vm_disk_write_bytes_per_secend', 'Disk write bytes per second in virtual machine',
                                ['zone', 'host', 'vm', "owner", "router", "autoscalinggroup", "cluster", 'device'])
vm_network_receive_packages_per_secend = Gauge('vm_network_receive_packages_per_secend', 'Network receive packages per second in virtual machine',
                                ['zone', 'host', 'vm', "owner", "router", "autoscalinggroup", "cluster", 'device'])
vm_network_receive_bytes_per_secend = Gauge('vm_network_receive_bytes_per_secend', 'Network receive bytes per second in virtual machine',
                                ['zone', 'host', 'vm', "owner", "router", "autoscalinggroup", "cluster", 'device'])
vm_network_receive_errors_per_secend = Gauge('vm_network_receive_errors_per_secend', 'Network receive errors per second in virtual machine',
                                ['zone', 'host', 'vm', "owner", "router", "autoscalinggroup", "cluster", 'device'])
vm_network_receive_drops_per_secend = Gauge('vm_network_receive_drops_per_secend', 'Network receive drops per second in virtual machine',
                                ['zone', 'host', 'vm', "owner", "router", "autoscalinggroup", "cluster", 'device'])
vm_network_send_packages_per_secend = Gauge('vm_network_send_packages_per_secend', 'Network send packages per second in virtual machine',
                                ['zone', 'host', 'vm', "owner", "router", "autoscalinggroup", "cluster", 'device'])
vm_network_send_bytes_per_secend = Gauge('vm_network_send_bytes_per_secend', 'Network send bytes per second in virtual machine',
                                ['zone', 'host', 'vm', "owner", "router", "autoscalinggroup", "cluster", 'device'])
vm_network_send_errors_per_secend = Gauge('vm_network_send_errors_per_secend', 'Network send errors per second in virtual machine',
                                ['zone', 'host', 'vm', "owner", "router", "autoscalinggroup", "cluster", 'device'])
vm_network_send_drops_per_secend = Gauge('vm_network_send_drops_per_secend', 'Network send drops per second in virtual machine',
                                ['zone', 'host', 'vm', "owner", "router", "autoscalinggroup", "cluster", 'device'])
storage_pool_total_size_kilobytes = Gauge('storage_pool_total_size_kilobytes', 'Storage pool total size in kilobytes on host',
                                ['zone', 'host', 'pool', 'type'])
storage_pool_used_size_kilobytes = Gauge('storage_pool_used_size_kilobytes', 'Storage pool used size in kilobytes on host',
                                ['zone', 'host', 'pool', 'type'])
storage_disk_total_size_kilobytes = Gauge('storage_disk_total_size_kilobytes', 'Storage disk total size in kilobytes on host',
                                ['zone', 'host', 'pool', 'type', 'disk'])
storage_disk_used_size_kilobytes = Gauge('storage_disk_used_size_kilobytes', 'Storage disk used size in kilobytes on host',
                                ['zone', 'host', 'pool', 'type', 'disk'])

class KillableThread:
    def __init__(self, target, args=None):
        self.th = threading.Thread(target=target, args=args)
        self.kill_sema = threading.Semaphore(0)
        self.start_sema = threading.Semaphore(0)
        def daemon_thread(self):
            self.th.setDaemon(True)
            self.th.start()
            self.start_sema.release()
            self.kill_sema.acquire()
        self.guard = threading.Thread(target=daemon_thread, args=(self,))

    def start(self):
        self.guard.start()
        self.start_sema.acquire()

    def join(self, secs=None):
        self.th.join(secs)
        if not self.th.is_alive():
            self.kill_sema.release()

    def is_alive(self):
        return self.th.is_alive() and self.guard.is_alive()

    def kill(self):
        self.kill_sema.release()
        while self.guard.is_alive():
            pass

def collect_storage_metrics(zone):
    vmps = list_objects_in_kubernetes(kind=KIND_VMP)

#     storages = {VDISK_FS_MOUNT_POINT: 'vdiskfs', SHARE_FS_MOUNT_POINT: 'nfs/glusterfs',
#                 LOCAL_FS_MOUNT_POINT: 'localfs', BLOCK_FS_MOUNT_POINT: 'blockfs'}
    for vmp in vmps:
        try:
#             all_pool_storages = runCmdRaiseException('timeout 2 df -aT | grep %s | awk \'{print $3,$4,$7}\'' % mount_point)
            (vmp_mount_point, vmp_type, vmp_uuid, vmp_nodename) = _get_pool_details(vmp)
            if get_hostname_in_lower_case() != vmp_nodename:
                continue
            output = runCmdRaiseException('timeout 2 cstor-cli pool-show --poolname %s' % vmp_uuid)
            if output:
                vmp_utils = loads(output[0])
                pool_total, pool_used = int(vmp_utils['data'].get('total'))/1024, int(vmp_utils['data'].get('used'))/1024
                t = KillableThread(target=get_pool_metrics,args=(pool_total, pool_used, vmp_mount_point, vmp_type, zone,))
                t.start()
                t.join(2)
                t.kill()
        except Exception as e:
            logger.warning('Oops! ', exc_info=1)
            raise e
#             get_pool_metrics(pool_storage, pool_type, zone)

def _get_pool_details(vm_pool):
    try:
        return (vm_pool['metadata'].get('name'), vm_pool['spec']['pool'].get('pooltype'), 
                vm_pool['spec']['pool'].get('poolname'), vm_pool['spec'].get('nodeName'))
    except:
        logger.warning('Oops! ', exc_info=1)
        return (None, None, None, None)

def get_pool_metrics(pool_total, pool_used, pool_mount_point, pool_type, zone):
#     global storage_pool_total_size_kilobytes 
#     global storage_pool_used_size_kilobytes 
    storage_pool_total_size_kilobytes.labels(zone, HOSTNAME, pool_mount_point, pool_type).set(pool_total)
    storage_pool_used_size_kilobytes.labels(zone, HOSTNAME, pool_mount_point, pool_type).set(pool_used)
    collect_disk_metrics(pool_mount_point, pool_type, zone)

def collect_disk_metrics(pool_mount_point, pool_type, zone):
    if pool_type in ['vdiskfs', 'nfs/glusterfs', 'localfs']:
        disk_list = list_all_disks(pool_mount_point, 'f')
        disk_type = 'file'
    else:
        disk_list = list_all_disks(pool_mount_point, 'l')
        disk_type = 'block'
    for disk in disk_list:
        get_vdisk_metrics(pool_mount_point, disk_type, disk, zone)
#         t = threading.Thread(target=get_vdisk_metrics,args=(pool_mount_point, disk_type, disk, zone,))
#         t.setDaemon(True)
#         t.start()
#         t.join()
#     vdisk_fs_list = list_all_vdisks(VDISK_FS_MOUNT_POINT, 'f')
#     for disk in vdisk_fs_list:
#         t1 = threading.Thread(target=get_vdisk_metrics,args=(disk, zone,))
#         t1.setDaemon(True)
#         t1.start()
#     local_fs_list = list_all_vdisks(LOCAL_FS_MOUNT_POINT, 'f')
#     for disk in local_fs_list:
#         t1 = threading.Thread(target=get_vdisk_metrics,args=(disk, zone,))
#         t1.setDaemon(True)
#         t1.start()
#     resource_utilization = {'host': HOSTNAME, 'vdisk_metrics': {}}
def get_vdisk_metrics(pool_mount_point, disk_type, disk, zone):
#     global storage_disk_total_size_kilobytes 
#     global storage_disk_used_size_kilobytes 
    try:
        output = loads(runCmdRaiseException('timeout 2 qemu-img info -U --output json %s' % (disk), use_read=True))
#     output = loads()
#     print(output)
    except:
        output = {}
    if output:
        virtual_size = float(output.get('virtual-size')) / 1024 if output.get('virtual-size') else 0.00
        actual_size = float(output.get('actual-size')) / 1024 if output.get('actual-size') else 0.00
        storage_disk_total_size_kilobytes.labels(zone, HOSTNAME, pool_mount_point, disk_type, disk).set(virtual_size)
        storage_disk_used_size_kilobytes.labels(zone, HOSTNAME, pool_mount_point, disk_type, disk).set(actual_size)

def runCmdAndGetOutput(cmd):
    if not cmd:
        return None
    try:
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        std_out, std_err = p.communicate()
        std_out = std_out.decode() if std_out else ''
        std_err = std_err.decode() if std_err else ''

        if std_out:
            return std_out.strip()  # 返回去掉末尾换行符的字符串
        elif std_err:
            logger.warning('Error occurred: %s', std_err)
            return ''
        else:
            logger.warning('No output or error')
            return ''
    except subprocess.CalledProcessError as e:
        logger.error('Command failed with code %s: %s', e.returncode, e.output)
        return ''
    except Exception as e:
        logger.exception('Unexpected error occurred: %s', str(e))
        return ''

def get_disks_spec(domain):
    output = runCmdAndGetOutput('virsh domblklist %s' % domain)
    lines = output.splitlines()
    specs = []
    for i in range(2, len(lines)):
        spec = []
        kv = lines[i].split()
        if len(kv) == 2:
            spec.append(kv[0])
            spec.append(kv[1])
            specs.append(spec)
    return specs

def list_active_vms():
    output = runCmdAndGetOutput('virsh list')
    lines = output.splitlines()
    if (len(lines) < 2):
        return []
    vms = []
    for line in lines[2:]:
        if (len(line.split()) == 3):
            vms.append(line.split()[1])
    return vms

def list_all_vms():
    output = runCmdAndGetOutput('virsh list --all')
    lines = output.splitlines()
    if (len(lines) < 2):
        return []
    vms = []
    for line in lines[2:]:
        if (len(line.split()) >= 1):
            vms.append(line.split()[1])
    return vms

def get_macs(vm):
    if not vm:
        return []
    lines = runCmdRaiseException('timeout 2 virsh domiflist %s | awk \'NR>2{print $5}\'' % (vm))
    # for child in root:
    #     print(child.tag, "----", child.attrib)
    macs = []
    for line in lines:
        line = line.strip()
        if line:
            macs.append(line)
    return macs

def collect_vm_metrics(zone):
    try:
        vm_list = list_active_vms()
        all_vm = list_all_vms()
        vm_not_exists = []

        global ALL_VMS_IN_PROMETHEUS
        if ALL_VMS_IN_PROMETHEUS:
            vm_not_exists = list(set(ALL_VMS_IN_PROMETHEUS).difference(set(all_vm)))

        ALL_VMS_IN_PROMETHEUS = all_vm

        logger.debug(vm_list)

        vm_stopped = []
        if all_vm:
            vm_stopped = list(set(all_vm).difference(set(vm_list)))

        with concurrent.futures.ThreadPoolExecutor() as executor:
            for vm in vm_list:
                executor.submit(get_vm_metrics, vm, zone)
            for vm in vm_stopped:
                executor.submit(zero_vm_metrics, vm, zone)
            for vm in vm_not_exists:
                executor.submit(delete_vm_metrics, vm, zone)
    except Exception as e:
        logger.exception('Error in collect_vm_metrics: %s', str(e))
        
def get_vm_metrics(vm, zone):
    try:
        global LAST_TAGS
        global LAST_RESOURCE_UTILIZATION
    #     delete_duplicated_data = False
    #     tags = {}
    #     config.load_kube_config(config_file=TOKEN)
        labels = get_field_in_kubernetes_by_index(vm, KIND, ['metadata', 'labels'])
        this_tags = {'zone': zone, 'host': HOSTNAME, 'owner': labels.get('owner'), 
                         "router": labels.get('router'), "autoscalinggroup": labels.get('autoscalinggroup'), 
                         "cluster": labels.get('cluster')}
        if vm in LAST_TAGS.keys() and operator.ne(LAST_TAGS[vm], this_tags):
    #         print("need delete")
            delete_vm_metrics(vm, LAST_TAGS[vm].get('zone'))
    #         delete_duplicated_data = True
    #         tags = {'zone': LAST_TAGS[vm].get('zone'), 'host': LAST_TAGS[vm].get('host'), 'owner': LAST_TAGS[vm].get('owner'), 
    #                      "router": LAST_TAGS[vm].get('router'), "autoscalinggroup": LAST_TAGS[vm].get('autoscalinggroup'), 
    #                      "cluster": LAST_TAGS[vm].get('cluster'), 'vm': vm}
    #     labels_str = dumps(labels)
    #     if delete_duplicated_data:
        LAST_TAGS[vm] = this_tags
        resource_utilization = {'vm': vm, 'cpu_metrics': {}, 'mem_metrics': {},
                                'disks_metrics': [], 'networks_metrics': [], 'cluster': labels.get('cluster'), 'router': labels.get('router'),
                                'owner': labels.get('owner'), 'autoscalinggroup': labels.get('autoscalinggroup')}
    #     cpus = len(get_vcpus(vm)[0])
    #     print(cpus)
        cpu_stats = runCmdRaiseException('timeout 2 virsh domstats --vcpu %s | grep time | awk \'{split($0,a,\"=\");print a[2]}\'' % vm)
        cpu_time = 0.00
        cpu_number = 0
        for line in cpu_stats:
            one_cpu_time_seconds = int(line) / 1000000000
            cpu_time += one_cpu_time_seconds
            cpu_number += 1
    #     cpu_system_time = 0.00
    #     cpu_user_time = 0.00
    #     for line in cpu_stats:
    #         if line.find('cpu_time') != -1:
    #             p1 = r'^(\s*cpu_time\s*)([\S*]+)\s*(\S*)'
    #             m1 = re.match(p1, line)
    #             if m1:
    #                 cpu_time = float(m1.group(2))
    #         elif line.find('system_time') != -1:
    #             p1 = r'^(\s*system_time\s*)([\S*]+)\s*(\S*)'
    #             m1 = re.match(p1, line)
    #             if m1:
    #                 cpu_system_time = float(m1.group(2))
    #         elif line.find('user_time') != -1:
    #             p1 = r'^(\s*user_time\s*)([\S*]+)\s*(\S*)'
    #             m1 = re.match(p1, line)
    #             if m1:
    #                 cpu_user_time = float(m1.group(2))
        first_time = False
        cpu_util = 0.00
        global CPU_UTILIZATION
        logger.debug(vm)
        if vm in CPU_UTILIZATION.keys() and cpu_number == CPU_UTILIZATION[vm].get('cpu_number'):
            interval = time.time() - CPU_UTILIZATION[vm].get('time')
            cpu_util = (cpu_time - float(CPU_UTILIZATION[vm].get('cpu_time')))/ cpu_number / interval
            # logger.debug(CPU_UTILIZATION[vm], cpu_number, cpu_time, interval)
            CPU_UTILIZATION[vm] = {'cpu_time': cpu_time,
                                    'time': time.time(), 'cpu_number': cpu_number}
        else:
            CPU_UTILIZATION[vm] = {'cpu_time': cpu_time, 'time': time.time(), 'cpu_number': cpu_number}
            first_time = True
        if not first_time:
            resource_utilization['cpu_metrics']['cpu_idle_rate'] = \
            '%.2f' % abs(1 - cpu_util) if abs(1 - cpu_util) <= 1.00 and abs(1 - cpu_util) >= 0.00 else 0.00
        else:
            resource_utilization['cpu_metrics']['cpu_idle_rate'] = '%.2f' % (1.00)
        logger.debug(resource_utilization['cpu_metrics'])
        mem_stats = runCmdRaiseException('timeout 2 virsh dommemstat %s' % vm)
        mem_actual = 0.00
        mem_unused = 0.00
        mem_available = 0.00
        for line in mem_stats:
            if line.find('unused') != -1:
                mem_unused = float(line.split(' ')[1].strip()) * 1024
            elif line.find('available') != -1:
                mem_available = float(line.split(' ')[1].strip()) * 1024
            elif line.find('actual') != -1:
                mem_actual = float(line.split(' ')[1].strip()) * 1024
        resource_utilization['mem_metrics']['mem_unused'] = '%.2f' % (mem_unused)
        resource_utilization['mem_metrics']['mem_available'] = '%.2f' % (mem_available)
        if mem_unused and mem_available and mem_actual:
            mem_buffers = abs(mem_actual - mem_available)
            resource_utilization['mem_metrics']['mem_buffers'] = '%.2f' % (mem_buffers)
            resource_utilization['mem_metrics']['mem_rate'] = \
            '%.2f' % (abs(mem_available - mem_unused - mem_buffers) / mem_available * 100)
        else:
            resource_utilization['mem_metrics']['mem_buffers'] = '%.2f' % (0.00)
            resource_utilization['mem_metrics']['mem_rate'] = '%.2f' % (0.00)
        disks_spec = get_disks_spec(vm)
        for disk_spec in disks_spec:
            disk_metrics = {}
            disk_device = disk_spec[0]
            disk_metrics['device'] = disk_device
            stats1 = {}
            stats2 = {}
            # logger.debug('virsh domblkstat --device %s --domain %s' % (disk_device, vm))
            blk_dev_stats1 = runCmdRaiseException('timeout 2 virsh domblkstat --device %s --domain %s' % (disk_device, vm))
            t1 = time.time()
            for line in blk_dev_stats1:
                if line.find('rd_req') != -1:
                    stats1['rd_req'] = float(line.split(' ')[2].strip())
                elif line.find('rd_bytes') != -1:
                    stats1['rd_bytes'] = float(line.split(' ')[2].strip())
                elif line.find('wr_req') != -1:
                    stats1['wr_req'] = float(line.split(' ')[2].strip())
                elif line.find('wr_bytes') != -1:
                    stats1['wr_bytes'] = float(line.split(' ')[2].strip())
            time.sleep(0.1)
            blk_dev_stats2 = runCmdRaiseException('timeout 2 virsh domblkstat --device %s --domain %s' % (disk_device, vm))
            t2 = time.time()
            interval = t2 - t1
            for line in blk_dev_stats2:
                if line.find('rd_req') != -1:
                    stats2['rd_req'] = float(line.split(' ')[2].strip())
                elif line.find('rd_bytes') != -1:
                    stats2['rd_bytes'] = float(line.split(' ')[2].strip())
                elif line.find('wr_req') != -1:
                    stats2['wr_req'] = float(line.split(' ')[2].strip())
                elif line.find('wr_bytes') != -1:
                    stats2['wr_bytes'] = float(line.split(' ')[2].strip())
            disk_metrics['disk_read_requests_per_secend'] = '%.2f' % ((stats2['rd_req'] - stats1['rd_req']) / interval) \
            if (stats2['rd_req'] - stats1['rd_req']) > 0 else '%.2f' % (0.00)
            disk_metrics['disk_read_bytes_per_secend'] = '%.2f' % ((stats2['rd_bytes'] - stats1['rd_bytes']) / interval) \
            if (stats2['rd_bytes'] - stats1['rd_bytes']) > 0 else '%.2f' % (0.00)
            disk_metrics['disk_write_requests_per_secend'] = '%.2f' % ((stats2['wr_req'] - stats1['wr_req']) / interval) \
            if (stats2['wr_req'] - stats1['wr_req']) > 0 else '%.2f' % (0.00)
            disk_metrics['disk_write_bytes_per_secend'] = '%.2f' % ((stats2['wr_bytes'] - stats1['wr_bytes']) / interval) \
            if (stats2['wr_bytes'] - stats1['wr_bytes']) > 0 else '%.2f' % (0.00)
            resource_utilization['disks_metrics'].append(disk_metrics)
        macs = get_macs(vm)
        for mac in macs:
    #         logger.debug(mac)
            net_metrics = {}
            net_metrics['device'] = mac.encode('utf-8')
            stats1 = {}
            stats2 = {}
            net_dev_stats1 = runCmdRaiseException('timeout 2 virsh domifstat --interface %s --domain %s' % (mac, vm))
            t1 = time.time()
            for line in net_dev_stats1:
                if line.find('rx_bytes') != -1:
                    stats1['rx_bytes'] = float(line.split(' ')[2].strip())
                elif line.find('rx_packets') != -1:
                    stats1['rx_packets'] = float(line.split(' ')[2].strip())
                elif line.find('tx_packets') != -1:
                    stats1['tx_packets'] = float(line.split(' ')[2].strip())
                elif line.find('tx_bytes') != -1:
                    stats1['tx_bytes'] = float(line.split(' ')[2].strip())
                elif line.find('rx_drop') != -1:
                    stats1['rx_drop'] = float(line.split(' ')[2].strip())
                elif line.find('rx_errs') != -1:
                    stats1['rx_errs'] = float(line.split(' ')[2].strip())
                elif line.find('tx_errs') != -1:
                    stats1['tx_errs'] = float(line.split(' ')[2].strip())
                elif line.find('tx_drop') != -1:
                    stats1['tx_drop'] = float(line.split(' ')[2].strip())
    #         logger.debug(stats1)
            time.sleep(0.1)
            net_dev_stats2 = runCmdRaiseException('timeout 2 virsh domifstat --interface %s --domain %s' % (mac, vm))
            t2 = time.time()
            interval = t2 - t1
            for line in net_dev_stats2:
                if line.find('rx_bytes') != -1:
                    stats2['rx_bytes'] = float(line.split(' ')[2].strip())
                elif line.find('rx_packets') != -1:
                    stats2['rx_packets'] = float(line.split(' ')[2].strip())
                elif line.find('tx_packets') != -1:
                    stats2['tx_packets'] = float(line.split(' ')[2].strip())
                elif line.find('tx_bytes') != -1:
                    stats2['tx_bytes'] = float(line.split(' ')[2].strip())
                elif line.find('rx_drop') != -1:
                    stats2['rx_drop'] = float(line.split(' ')[2].strip())
                elif line.find('rx_errs') != -1:
                    stats2['rx_errs'] = float(line.split(' ')[2].strip())
                elif line.find('tx_errs') != -1:
                    stats2['tx_errs'] = float(line.split(' ')[2].strip())
                elif line.find('tx_drop') != -1:
                    stats2['tx_drop'] = float(line.split(' ')[2].strip())
    #         logger.debug(stats2)
            net_metrics['network_read_packages_per_secend'] = '%.2f' % ((stats2['rx_packets'] - stats1['rx_packets']) / interval) \
            if (stats2['rx_packets'] - stats1['rx_packets']) > 0 else '%.2f' % (0.00)
            net_metrics['network_read_bytes_per_secend'] = '%.2f' % ((stats2['rx_bytes'] - stats1['rx_bytes']) / interval) \
            if (stats2['rx_bytes'] - stats1['rx_bytes']) > 0 else '%.2f' % (0.00)
            net_metrics['network_write_packages_per_secend'] = '%.2f' % ((stats2['tx_packets'] - stats1['tx_packets']) / interval) \
            if (stats2['tx_packets'] - stats1['tx_packets']) > 0 else '%.2f' % (0.00)
            net_metrics['network_write_bytes_per_secend'] = '%.2f' % ((stats2['tx_bytes'] - stats1['tx_bytes']) / interval) \
            if (stats2['tx_bytes'] - stats1['tx_bytes']) > 0 else '%.2f' % (0.00)
            net_metrics['network_read_errors_per_secend'] = '%.2f' % ((stats2['rx_errs'] - stats1['rx_errs']) / interval) \
            if (stats2['rx_errs'] - stats1['rx_errs']) > 0 else '%.2f' % (0.00)
            net_metrics['network_read_drops_per_secend'] = '%.2f' % ((stats2['rx_drop'] - stats1['rx_drop']) / interval) \
            if (stats2['rx_drop'] - stats1['rx_drop']) > 0 else '%.2f' % (0.00)
            net_metrics['network_write_errors_per_secend'] = '%.2f' % ((stats2['tx_errs'] - stats1['tx_errs']) / interval) \
            if (stats2['tx_errs'] - stats1['tx_errs']) > 0 else '%.2f' % (0.00)
            net_metrics['network_write_drops_per_secend'] = '%.2f' % ((stats2['tx_drop'] - stats1['tx_drop']) / interval) \
            if (stats2['tx_drop'] - stats1['tx_drop']) > 0 else '%.2f' % (0.00)
            resource_utilization['networks_metrics'].append(net_metrics)
    #         logger.debug(net_metrics) 
        LAST_RESOURCE_UTILIZATION[vm] = resource_utilization
        if cpu_number == CPU_UTILIZATION[vm].get('cpu_number'): 
            vm_cpu_idle_rate.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster')).set(resource_utilization['cpu_metrics']['cpu_idle_rate'])
        vm_mem_total_bytes.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster')).set(resource_utilization['mem_metrics']['mem_available'])
        vm_mem_available_bytes.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster')).set(resource_utilization['mem_metrics']['mem_unused'])
        vm_mem_buffers_bytes.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster')).set(resource_utilization['mem_metrics']['mem_buffers'])
        vm_mem_rate.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster')).set(resource_utilization['mem_metrics']['mem_rate'])
        for disk_metrics in resource_utilization['disks_metrics']:
            vm_disk_read_requests_per_secend.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster'), disk_metrics['device']).set(disk_metrics['disk_read_requests_per_secend'])
            vm_disk_read_bytes_per_secend.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster'), disk_metrics['device']).set(disk_metrics['disk_read_bytes_per_secend'])
            vm_disk_write_requests_per_secend.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster'), disk_metrics['device']).set(disk_metrics['disk_write_requests_per_secend'])
            vm_disk_write_bytes_per_secend.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster'), disk_metrics['device']).set(disk_metrics['disk_write_bytes_per_secend'])
        for net_metrics in resource_utilization['networks_metrics']:
            vm_network_receive_bytes_per_secend.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster'), net_metrics['device']).set(net_metrics['network_read_bytes_per_secend'])
            vm_network_receive_drops_per_secend.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster'), net_metrics['device']).set(net_metrics['network_read_drops_per_secend'])
            vm_network_receive_errors_per_secend.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster'), net_metrics['device']).set(net_metrics['network_read_errors_per_secend'])
            vm_network_receive_packages_per_secend.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster'), net_metrics['device']).set(net_metrics['network_read_packages_per_secend'])
            vm_network_send_bytes_per_secend.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster'), net_metrics['device']).set(net_metrics['network_write_bytes_per_secend'])
            vm_network_send_drops_per_secend.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster'), net_metrics['device']).set(net_metrics['network_write_drops_per_secend'])
            vm_network_send_errors_per_secend.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster'), net_metrics['device']).set(net_metrics['network_write_errors_per_secend'])
            vm_network_send_packages_per_secend.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster'), net_metrics['device']).set(net_metrics['network_write_packages_per_secend'])
        return resource_utilization
    except Exception as e:
        logger.error('Oops! ', exc_info=1)
        raise e

def delete_vm_metrics(vm, zone):
    global LAST_TAGS
    global LAST_RESOURCE_UTILIZATION
    if vm in LAST_TAGS.keys() and vm in LAST_RESOURCE_UTILIZATION.keys():
        tags = LAST_TAGS[vm]
        disk_metrics = LAST_RESOURCE_UTILIZATION[vm]['disks_metrics']
        network_metrics = LAST_RESOURCE_UTILIZATION[vm]['networks_metrics']
#     zone = tags.get('zone')
        host = tags.get('host')
    #     vm = tags.get('vm')
        owner = tags.get('owner')
        router = tags.get('router')
        autoscalinggroup = tags.get('autoscalinggroup')
        cluster = tags.get('cluster')
        vm_cpu_idle_rate.remove(zone, host, vm, owner, router, autoscalinggroup, cluster)
        vm_mem_total_bytes.remove(zone, host, vm, owner, router, autoscalinggroup, cluster)
        vm_mem_available_bytes.remove(zone, host, vm, owner, router, autoscalinggroup, cluster)
        vm_mem_buffers_bytes.remove(zone, host, vm, owner, router, autoscalinggroup, cluster)
        vm_mem_rate.remove(zone, host, vm, owner, router, autoscalinggroup, cluster)
        for disks in disk_metrics:
            vm_disk_read_requests_per_secend.remove(zone, host, vm, owner, router, autoscalinggroup, cluster, disks['device'])
            vm_disk_read_bytes_per_secend.remove(zone, host, vm, owner, router, autoscalinggroup, cluster, disks['device'])
            vm_disk_write_requests_per_secend.remove(zone, host, vm, owner, router, autoscalinggroup, cluster, disks['device'])
            vm_disk_write_bytes_per_secend.remove(zone, host, vm, owner, router, autoscalinggroup, cluster, disks['device'])
        for nets in network_metrics:
            vm_network_receive_bytes_per_secend.remove(zone, host, vm, owner, router, autoscalinggroup, cluster, nets['device'])
            vm_network_receive_drops_per_secend.remove(zone, host, vm, owner, router, autoscalinggroup, cluster, nets['device'])
            vm_network_receive_errors_per_secend.remove(zone, host, vm, owner, router, autoscalinggroup, cluster, nets['device'])
            vm_network_receive_packages_per_secend.remove(zone, host, vm, owner, router, autoscalinggroup, cluster, nets['device'])
            vm_network_send_bytes_per_secend.remove(zone, host, vm, owner, router, autoscalinggroup, cluster, nets['device'])
            vm_network_send_drops_per_secend.remove(zone, host, vm, owner, router, autoscalinggroup, cluster, nets['device'])
            vm_network_send_errors_per_secend.remove(zone, host, vm, owner, router, autoscalinggroup, cluster, nets['device'])
            vm_network_send_packages_per_secend.remove(zone, host, vm, owner, router, autoscalinggroup, cluster, nets['device'])
        del LAST_TAGS[vm]
        del LAST_RESOURCE_UTILIZATION[vm]
    else:
        logger.warning('failed to delete vm %s data' % vm)    
        print('failed to delete vm %s data' % vm)

def zero_vm_metrics(vm, zone):
    
    # config.load_kube_config(config_file=TOKEN)
    labels = get_field_in_kubernetes_by_index(vm, KIND, ['metadata', 'labels'])
#     labels_str = dumps(labels)
    resource_utilization = {'vm': vm, 'cpu_metrics': {}, 'mem_metrics': {},
                            'disks_metrics': [], 'networks_metrics': [], 'cluster': labels.get('cluster'), 'router': labels.get('router'),
                            'owner': labels.get('owner'), 'autoscalinggroup': labels.get('autoscalinggroup')}
    resource_utilization['cpu_metrics']['cpu_idle_rate'] = '%.2f' % (1.00)
    mem_unused = 0.00
    mem_available = 0.00
    resource_utilization['mem_metrics']['mem_unused'] = '%.2f' % (mem_unused)
    resource_utilization['mem_metrics']['mem_available'] = '%.2f' % (mem_available)
    resource_utilization['mem_metrics']['mem_buffers'] = '%.2f' % (0.00)
    resource_utilization['mem_metrics']['mem_rate'] = '%.2f' % (0.00)
    disks_spec = get_disks_spec(vm)
    for disk_spec in disks_spec:
        disk_metrics = {}
        disk_device = disk_spec[0]
        disk_metrics['device'] = disk_device
        disk_metrics['disk_read_requests_per_secend'] =  '%.2f' % (0.00)
        disk_metrics['disk_read_bytes_per_secend'] = '%.2f' % (0.00)
        disk_metrics['disk_write_requests_per_secend'] = '%.2f' % (0.00)
        disk_metrics['disk_write_bytes_per_secend'] = '%.2f' % (0.00)
        resource_utilization['disks_metrics'].append(disk_metrics)
    macs = get_macs(vm)
    for mac in macs:
        net_metrics = {}
        net_metrics['device'] = mac.encode('utf-8')
        net_metrics['network_read_packages_per_secend'] = '%.2f' % (0.00)
        net_metrics['network_read_bytes_per_secend'] = '%.2f' % (0.00)
        net_metrics['network_write_packages_per_secend'] = '%.2f' % (0.00)
        net_metrics['network_write_bytes_per_secend'] = '%.2f' % (0.00)
        net_metrics['network_read_errors_per_secend'] = '%.2f' % (0.00)
        net_metrics['network_read_drops_per_secend'] = '%.2f' % (0.00)
        net_metrics['network_write_errors_per_secend'] = '%.2f' % (0.00)
        net_metrics['network_write_drops_per_secend'] = '%.2f' % (0.00)
        resource_utilization['networks_metrics'].append(net_metrics)  
    vm_cpu_idle_rate.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster')).set(resource_utilization['cpu_metrics']['cpu_idle_rate'])
    vm_mem_total_bytes.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster')).set(resource_utilization['mem_metrics']['mem_available'])
    vm_mem_available_bytes.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster')).set(resource_utilization['mem_metrics']['mem_unused'])
    vm_mem_buffers_bytes.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster')).set(resource_utilization['mem_metrics']['mem_buffers'])
    vm_mem_rate.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster')).set(resource_utilization['mem_metrics']['mem_rate'])
    for disk_metrics in resource_utilization['disks_metrics']:
        vm_disk_read_requests_per_secend.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster'), disk_metrics['device']).set(disk_metrics['disk_read_requests_per_secend'])
        vm_disk_read_bytes_per_secend.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster'), disk_metrics['device']).set(disk_metrics['disk_read_bytes_per_secend'])
        vm_disk_write_requests_per_secend.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster'), disk_metrics['device']).set(disk_metrics['disk_write_requests_per_secend'])
        vm_disk_write_bytes_per_secend.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster'), disk_metrics['device']).set(disk_metrics['disk_write_bytes_per_secend'])
    for net_metrics in resource_utilization['networks_metrics']:
        vm_network_receive_bytes_per_secend.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster'), net_metrics['device']).set(net_metrics['network_read_bytes_per_secend'])
        vm_network_receive_drops_per_secend.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster'), net_metrics['device']).set(net_metrics['network_read_drops_per_secend'])
        vm_network_receive_errors_per_secend.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster'), net_metrics['device']).set(net_metrics['network_read_errors_per_secend'])
        vm_network_receive_packages_per_secend.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster'), net_metrics['device']).set(net_metrics['network_read_packages_per_secend'])
        vm_network_send_bytes_per_secend.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster'), net_metrics['device']).set(net_metrics['network_write_bytes_per_secend'])
        vm_network_send_drops_per_secend.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster'), net_metrics['device']).set(net_metrics['network_write_drops_per_secend'])
        vm_network_send_errors_per_secend.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster'), net_metrics['device']).set(net_metrics['network_write_errors_per_secend'])
        vm_network_send_packages_per_secend.labels(zone, HOSTNAME, vm, labels.get('owner'), labels.get('router'), labels.get('autoscalinggroup'), labels.get('cluster'), net_metrics['device']).set(net_metrics['network_write_packages_per_secend'])
    return resource_utilization

# def set_vm_mem_period(vm, sec):
#     runCmdRaiseException('virsh dommemstat --period %s --domain %s --config --live' % (str(sec), vm))
    
# def get_resource_collector_threads():
#     config.load_kube_config(config_file=TOKEN)
#     zone = get_field_in_kubernetes_node(HOSTNAME, ['metadata', 'labels', 'zone'])
#     print(zone)
#     while True:
#         vm_list = list_active_vms()
#         for vm in vm_list:
#             t = threading.Thread(target=collect_vm_metrics,args=(vm,zone,))
#             t.setDaemon(True)
#             t.start()
#         t1 = threading.Thread(target=collect_storage_metrics,args=(zone,))
#         t1.setDaemon(True)
#         t1.start()
# #         nfs_vdisk_list = list_all_vdisks('/var/lib/libvirt/cstor')
# #         for nfs_vdisk in nfs_vdisk_list:
# #             t2 = threading.Thread(target=collect_disk_metrics,args=(nfs_vdisk,zone,))
# #             t2.setDaemon(True)
# #             t2.start()
#         time.sleep(5)
class ClientDaemon(CDaemon):
    '''virtlet程序启动器
    '''

    def __init__(self, name, save_path, stdin=os.devnull, stdout=os.devnull, stderr=os.devnull, home_dir='.',
                 umask=0o22, verbose=1):
        CDaemon.__init__(self, save_path, stdin, stdout, stderr, home_dir, umask, verbose)
        self.name = name

    def run(self, output_fn, **kwargs):
#         logger.debug("---------------------------------------------------------------------------------")
#         logger.debug("------------------------Welcome to Monitor Daemon.-------------------------------")
#         logger.debug("------Copyright (2019, ) Institute of Software, Chinese Academy of Sciences------")
#         logger.debug("---------author: wuyuewen@otcaix.iscas.ac.cn,liuhe18@otcaix.iscas.ac.cn----------")
#         logger.debug("--------------------------------wuheng@otcaix.iscas.ac.cn------------------------")
#         logger.debug("---------------------------------------------------------------------------------")
        try:
            if os.path.exists(TOKEN):
                start_http_server(19999)
            #         registry = CollectorRegistry(auto_describe=False)
            #     config.load_kube_config(config_file=TOKEN)
                zone = get_field_in_kubernetes_node(HOSTNAME, ['metadata', 'labels', 'zone'])
                while True:
            #             init(registry)
            #         config.load_kube_config(config_file=TOKEN)
                    collect_vm_metrics(zone)
            #             collect_storage_metrics(zone)
                    time.sleep(10)
        except:
            logger.error('Oops! ', exc_info=1)


if __name__ == '__main__':
    p_name = constants.KUBEVMM_VIRTMONITOR_SERVICE_NAME
    pid_fn = constants.KUBEVMM_VIRTMONITOR_SERVICE_LOCK
    log_fn = constants.KUBEVMM_VIRTLET_LOG
    err_fn = constants.KUBEVMM_VIRTLET_LOG
    cD = ClientDaemon(p_name, pid_fn, stderr=err_fn, verbose=1)
    daemonize(cD,log_fn)
#     start_http_server(19998)
#     config.load_kube_config(config_file=TOKEN)
#     zone = get_field_in_kubernetes_node(HOSTNAME, ['metadata', 'labels', 'zone'])
#     while True:
#         collect_vm_metrics(zone)
# #         collect_storage_metrics(zone)
#         time.sleep(10)    
#     print(get_macs("vm006"))
    # print get_disks_spec('vmtest222')
#     import pprint
#     set_vm_mem_period('vm010', 5)
#     pprint.pprint(collect_vm_metrics("vm010"))