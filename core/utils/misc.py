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
import sys
import json
from json import loads, load, dumps, dump

try:
    from utils.libvirt_util import get_graphics, is_snapshot_exists, is_pool_exists, get_pool_path
    from utils.exception import InternalServerError, NotFound, Forbidden, BadRequest,ExecuteException
    from utils.k8s_handler import Event,InvolvedObject,Metadata
    from utils import constants
    from kubesys.client import KubernetesClient
    from kubesys.exceptions import HTTPError
except:
    from libvirt_util import get_graphics, is_snapshot_exists, is_pool_exists, get_pool_path
    from exception import InternalServerError, NotFound, Forbidden, BadRequest,ExecuteException
    from k8s_handler import Event,InvolvedObject,Metadata
    import constants
    sys.path.append("..")
    sys.path.append('./core/')
    from kubesys.client import KubernetesClient
    from kubesys.exceptions import HTTPError

'''
Import python libs
'''
import re
import fcntl
import socket
import shlex
import errno
from functools import wraps
import os, time, signal, atexit, subprocess
import threading
import random
import socket
import pprint
import datetime
from dateutil.tz import gettz
from pprint import pformat
from six import iteritems
from xml.etree import ElementTree
from collections import namedtuple

'''
Import third party libs
'''
# from kubernetes import client, config
# # from kubernetes.client import V1DeleteOptions
# # from kubernetes.client.rest import ApiException
from tenacity import retry, stop_after_attempt, wait_random, retry_if_exception_message,retry_if_result


TOKEN = constants.KUBERNETES_TOKEN_FILE
TOKEN_ORIGIN = constants.KUBERNETES_TOKEN_FILE_ORIGIN
NOVNC_TOKEN_FILE = constants.KUBEVMM_NOVNC_TOKEN
RESOURCE_FILE_PATH = constants.KUBEVMM_RESOURCE_FILE_PATH
OVN_CONFIG_FILE = constants.KUBEVMM_OVN_FILE


# @retry(stop=stop_after_attempt(3),
#        retry=retry_if_exception_type(ApiException),
#        wait=wait_random(min=0, max=3),
#        reraise=True)
# def create_custom_object(group, version, plural, body):
#     config.load_kube_config(config_file=TOKEN)
#     retv = client.CustomObjectsApi().create_namespaced_custom_object(group=group,
#                                                                      version=version, namespace='default',
#                                                                      plural=plural, body=body)
#     return retv
def is_none_p(value):
    """Return True if value is None"""
    return value is None


@retry(stop=stop_after_attempt(3),
       retry=retry_if_result(is_none_p),
       wait=wait_random(min=0, max=3),
       reraise=True)
def create_custom_object(jsonStr):
    client=KubernetesClient(config=TOKEN)
    retv=client.createResource(jsonStr)
    return retv


@retry(stop=stop_after_attempt(3),
       retry=retry_if_exception_message(match='Not Found'),
       wait=wait_random(min=0, max=3),
       reraise=True)
def get_custom_object(kind, metadata_name)->dict:
    client = KubernetesClient(config=TOKEN)
    jsonDict = client.getResource(kind=kind, name=metadata_name, namespace='default')
    return jsonDict


@retry(stop=stop_after_attempt(3),
       retry=retry_if_exception_message(match='Not Found'),
       wait=wait_random(min=0, max=3),
       reraise=True)
def list_custom_object(kind,namespace):
    client=KubernetesClient(config=TOKEN)
    jsonStr=client.listResources(kind=kind,namespace=namespace).get('items')
    return jsonStr


@retry(stop=stop_after_attempt(3),
       retry=retry_if_exception_message(match='Not Found'),
       wait=wait_random(min=0, max=3),
       reraise=True)
def update_custom_object(body):
    client=KubernetesClient(config=TOKEN)
    body = updateDescription(body)
    retv=client.updateResource(dictToJsonString(body))
    return retv

def dictToJsonString(dict_obj) -> str:
    return json.dumps(dict_obj, indent=4, separators=(',', ': '))

@retry(stop=stop_after_attempt(3),
       retry=retry_if_exception_message(match='Not Found'),
       wait=wait_random(min=0, max=3),
       reraise=True)
def delete_custom_object(kind,namespace, metadata_name):
    client=KubernetesClient(config=TOKEN)
    retv=client.deleteResource(kind,namespace,metadata_name)
    return retv


def get_IP():
    myname = socket.getfqdn(socket.gethostname())
    myaddr = socket.gethostbyname(myname)
    return myaddr


def modify_token(vm_name, op):
    file_dir = os.path.split(NOVNC_TOKEN_FILE)[0]
    if not os.path.isdir(file_dir):
        os.makedirs(file_dir)
    lines = []
    if os.path.exists(NOVNC_TOKEN_FILE):
        with open(NOVNC_TOKEN_FILE, "r") as f:
            lines = f.readlines()

    with open(NOVNC_TOKEN_FILE, "w") as f:
        for line in lines:
            if line.strip('\n').split(':')[0] != vm_name:
                f.write(line)
        if op != 'Stopped':
            vnc_info = get_graphics(vm_name)
            if vnc_info['listen'] == '0.0.0.0':
                newline = vm_name + ': ' + get_IP() + ':' + vnc_info['port'] + '\n'
                f.write(newline)
            else:
                newline = vm_name + ': ' + vnc_info['listen'] + ':' + vnc_info['port'] + '\n'
                f.write(newline)


def get_l2_network_info(name):
    data = {'bridgeInfo': {}}
    '''
    Get bridge informations.
    '''
    data['bridgeInfo']['name'] = name
    data['bridgeInfo']['uuid'] = runCmdRaiseException('ovs-vsctl get bridge %s _uuid' % name)[0].strip()
    ports = runCmdRaiseException('ovs-vsctl get bridge %s ports' % name)[0].strip().replace('[', '').replace(']',
                                                                                                             '').replace(
        ' ', '').split(',')
    list_ports = []
    for port in ports:
        a_port = {}
        a_port['uuid'] = port
        a_port['name'] = runCmdRaiseException('ovs-vsctl get port %s name' % port)[0].strip()
        a_port['vlan'] = runCmdRaiseException('ovs-vsctl get port %s tag' % port)[0].strip()
        list_interfaces = []
        interfaces = runCmdRaiseException('ovs-vsctl get port %s interfaces' % port)[0].strip().replace('[',
                                                                                                        '').replace(']',
                                                                                                                    '').replace(
            ' ', '').split(',')
        for interface in interfaces:
            a_interface = {}
            a_interface['uuid'] = interface
            a_interface['mac'] = runCmdRaiseException('ovs-vsctl get interface %s mac_in_use' % interface)[0].strip()
            a_interface['name'] = runCmdRaiseException('ovs-vsctl get interface %s name' % interface)[0].strip()
            list_interfaces.append(a_interface)
        a_port['interfaces'] = list_interfaces
        list_ports.append(a_port)
    data['bridgeInfo']['ports'] = list_ports
    return data


def qeury_and_prepare_by_path(path):
    runCmd(
        'kubectl get vmd --kubeconfig=%s -o=jsonpath="{range .items[?(@.spec.volume.current==\"/mnt/localfs/pooldir/pooldir/diskdirclone/diskdirclone\")]}{.metadata.name}{\"\t\"}{.spec.nodeName}{\"\n\"}{end}"' % TOKEN_ORIGIN)


def get_l3_network_info(name):
    master_ip = runCmdRaiseException(
        'cat %s | grep server |awk -F"server:" \'{print$2}\' | awk -F"https://" \'{print$2}\' | awk -F":" \'{print$1}\'' % TOKEN)[
        0].strip()
    nb_port = '6641'
    #     sb_port = '6642'
    data = {'switchInfo': '', 'routerInfo': '', 'gatewayInfo': ''}
    '''
    Get switch informations.
    '''
    switchInfo = {'id': '', 'name': '', 'ports': []}
    # ovn_master_ip = get_ovn_master_ip(master_ip, nb_port)
    lines = runCmdRaiseException('kubectl ko nbctl show --kubeconfig=%s %s' % (TOKEN_ORIGIN, name))
    #     if not (len(lines) -1) % 4 == 0:
    #         raise Exception('ovn-nbctl --db=tcp:%s:%s show %s error: wrong return value %s' % (master_ip, nb_port, name, lines))
    if lines:
        (_, switchInfo['id'], switchInfo['name']) = str.strip(lines[0].replace('(', '').replace(')', '')).split(' ')
        ports = lines[1:]
        portsInfo = []
        list_ports = []
        a_port = []
        _start = False
        for i in ports:
            if i.find('port ') != -1 and not _start:
                _start = True
                a_port.append(i)
            elif i.find('port ') != -1 and _start:
                list_ports.append(a_port)
                a_port = []
                a_port.append(i)
            elif i == ports[-1]:
                a_port.append(i)
                list_ports.append(a_port)
            else:
                a_port.append(i)
        for a_port in list_ports:
            portInfo = {'name': '', 'addresses': [], 'type': '', 'router_port': ''}
            for line in a_port:
                if line.find('port ') != -1:
                    (_, portInfo['name']) = str.strip(line).split(' ')
                elif line.find('type:') != -1:
                    (_, portInfo['type']) = str.strip(line).split(': ')
                elif line.find('addresses:') != -1:
                    (_, portInfo['addresses']) = str.strip(line).split(': ')
                elif line.find('router-port:') != -1:
                    (_, portInfo['router_port']) = str.strip(line).split(': ')
                elif line.find('tag:') != -1:
                    (_, portInfo['tag']) = str.strip(line).split(': ')
            portsInfo.append(portInfo)
        switchInfo['ports'] = portsInfo
    data['switchInfo'] = switchInfo
    '''
    Get router informations.
    '''
    routerInfo = {'id': '', 'name': '', 'ports': []}
    lines = runCmdRaiseException('kubectl ko nbctl show --kubeconfig=%s %s-router' % (TOKEN_ORIGIN, name))
    if lines:
        (_, routerInfo['id'], routerInfo['name']) = str.strip(lines[0].replace('(', '').replace(')', '')).split(' ')
        ports = lines[1:]
        portsInfo = []
        list_ports = []
        a_port = []
        _start = False
        for i in ports:
            if i.find('port ') != -1 and not _start:
                _start = True
                a_port.append(i)
            elif i.find('port ') != -1 and _start:
                list_ports.append(a_port)
                a_port = []
                a_port.append(i)
            elif i == ports[-1]:
                a_port.append(i)
                list_ports.append(a_port)
            else:
                a_port.append(i)
        for a_port in list_ports:
            portInfo = {'name': '', 'mac': '', 'networks': []}
            for line in a_port:
                if line.find('port ') != -1:
                    (_, portInfo['name']) = str.strip(line).split(' ')
                elif line.find('mac:') != -1:
                    (_, portInfo['mac']) = str.strip(line).split(': ')
                elif line.find('networks:') != -1:
                    (_, portInfo['networks']) = str.strip(line).split(': ')
            portsInfo.append(portInfo)
        routerInfo['ports'] = portsInfo
    data['routerInfo'] = routerInfo
    '''
    Get gateway informations.
    '''
    gatewayInfo = {'id': '', 'server_mac': '', 'router': '', 'server_id': '', 'lease_time': ''}
    switchId = switchInfo.get('id')
    #     if not switchId:
    #         raise Exception('ovn-nbctl --db=tcp:%s:%s show %s error: no id found!' % (master_ip, nb_port, name))
    if switchId:
        cmd = 'kubectl ko nbctl show --kubeconfig=%s %s | grep dhcpv4id | awk -F"dhcpv4id-%s-" \'{print$2}\'' % (
            TOKEN_ORIGIN, name, name)
        lines = runCmdRaiseException(cmd)
        #         if not lines:
        #             raise Exception('error occurred: ovn-nbctl --db=tcp:%s:%s list DHCP_Options  | grep -B 3 "%s"  | grep "_uuid" | awk -F":" \'{print$2}\'' % (master_ip, nb_port, switchId))
        if lines:
            gatewayInfo['id'] = lines[0].strip()
            cmd = 'kubectl ko nbctl dhcp-options-get-options --kubeconfig=%s %s' % (TOKEN_ORIGIN, gatewayInfo['id'])
            lines = runCmdRaiseException(cmd)
            for line in lines:
                if line.find('server_mac') != -1:
                    (_, gatewayInfo['server_mac']) = line.strip().split('=')
                elif line.find('router') != -1:
                    (_, gatewayInfo['router']) = line.strip().split('=')
                elif line.find('server_id') != -1:
                    (_, gatewayInfo['server_id']) = line.strip().split('=')
                elif line.find('lease_time') != -1:
                    (_, gatewayInfo['lease_time']) = line.strip().split('=')
    data['gatewayInfo'] = gatewayInfo
    return data


def get_ovn_master_ip(master_ip, nb_port):
    if os.path.exists(OVN_CONFIG_FILE):
        try:
            with open(OVN_CONFIG_FILE, "r") as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith('ovnnb'):
                        return line.split('=')[1].strip()
                    else:
                        continue
        except:
            return 'tcp:%s:%s' % (master_ip, nb_port)
    else:
        return 'tcp:%s:%s' % (master_ip, nb_port)


def get_master_ips():
    ips = []
    if os.path.exists(OVN_CONFIG_FILE):
        try:
            with open(OVN_CONFIG_FILE, "r") as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith('ovnnb'):
                        content = line.split('=')[1].strip()
                        if content:
                            ips_and_ports = content.split(',')
                            if ips_and_ports:
                                for ip_and_port in ips_and_ports:
                                    ips.append(ip_and_port.split(':')[1])
                        return ips
                    else:
                        continue
        except:
            return []
    else:
        return []


def change_master_ip(ip):
    current_master_ip = runCmdRaiseException(
        'cat %s | grep server |awk -F"server:" \'{print$2}\' | awk -F"https://" \'{print$2}\' | awk -F":" \'{print$1}\'' % TOKEN)[
        0].strip()
    if current_master_ip != ip:
        change_master_ip_cmd = 'sed -i \'s/%s/%s/g\' %s' % (current_master_ip, ip, TOKEN)
        #     print(change_master_ip_cmd)
        runCmdRaiseException(change_master_ip_cmd)
        return True
    else:
        return False


def change_master_and_reload_config(count):
    master_ip = None
    master_ips = get_master_ips()
    if master_ips:
        list_length = len(master_ips)
        master_ip = master_ips[count % list_length]
        if change_master_ip(master_ip):
            return master_ip
        else:
            count += 1
            master_ip = master_ips[count % list_length]
            change_master_ip(master_ip)
    return master_ip


def get_address_set_info(name):
    master_ip = runCmdRaiseException(
        'cat %s | grep server |awk -F"server:" \'{print$2}\' | awk -F"https://" \'{print$2}\' | awk -F":" \'{print$1}\'' % TOKEN)[
        0].strip()
    nb_port = '6641'
    data = {'addressInfo': ''}
    addressInfo = {'_uuid': '', 'addresses': [], 'external_ids': {}, 'name': ''}
    # ovn_master_ip = get_ovn_master_ip(master_ip, nb_port)
    cmd = 'kubectl ko nbctl list Address_Set --kubeconfig=%s %s' % (TOKEN_ORIGIN, name)
    lines = runCmdRaiseException(cmd)
    for line in lines:
        if line.find('_uuid') != -1:
            (_, addressInfo['_uuid']) = line.strip().split(': ')
        elif line.find('addresses') != -1:
            (_, addressInfo['addresses']) = line.strip().split(': ')
        elif line.find('external_ids') != -1:
            (_, addressInfo['external_ids']) = line.strip().split(': ')
        elif line.find('name') != -1:
            (_, addressInfo['name']) = line.strip().split(': ')
    data['addressInfo'] = addressInfo
    return data


def get_field_in_kubernetes_node(name, index):
    try:
        client=KubernetesClient(config=TOKEN)
        jsondict=client.listResourcesWithSelector(kind='Node',namespace="",tp='label',selects={'host':name})
        items = jsondict.get('items')
        if items:
            return get_field(items[0], index)
        else:
            return None
    except:
        return None


def write_config(vol, dir, current, pool):
    config = {}
    config['name'] = vol
    config['dir'] = dir
    config['current'] = current
    config['pool'] = pool

    with open('%s/config.json' % dir, "w") as f:
        dump(config, f)


def get_field_in_kubernetes_by_index(name,kind, index):
    try:
        if not index or not list(index):
            return None
        jsondict = get_custom_object(kind, name)
        return get_field(jsondict, index)
    except:
        return None


def set_field_in_kubernetes_by_index(name, kind,index, value):
    try:
        if not index or not list(index):
            return None
        jsondict = get_custom_object(kind, name)
        contents = set_field(jsondict, index, value)
        return update_custom_object(contents)
    except:
        return None


@retry(stop=stop_after_attempt(3),
       retry=retry_if_exception_message(match='Not Found'),
       wait=wait_random(min=0, max=3),
       reraise=True)
def list_objects_in_kubernetes(kind):
    try:
        client = KubernetesClient(config=TOKEN)
        return client.listResources(kind=kind).get('items')
    except:
        return None


def get_node_name_from_kubernetes(kind, metadata_name):
    try:
        jsonStr = get_custom_object(kind, metadata_name)
    except HTTPError as e:
        if str(e).find('Not Found'):
            return None
        else:
            raise e
    return jsonStr['metadata']['labels']['host']


def get_ha_from_kubernetes(kind, metadata_name):
    try:
        jsonStr = get_custom_object(kind, metadata_name)
    except HTTPError as e:
        if str(e).find('Not Found'):
            return False
        else:
            raise e
    if 'ha' in jsonStr['metadata']['labels'].keys():
        return True
    else:
        return False


def get_field(jsondict, index):
    retv = None
    '''
    Iterate keys in 'spec' structure and map them to real CMDs in back-end.
    Note that only the first CMD will be executed.
    '''
    contents = jsondict
    for layer in index[:-1]:
        #         print(contents)
        contents = contents.get(layer)
    if not contents:
        return None
    for k, v in contents.items():
        if k == index[-1]:
            retv = v
    return retv


def set_field(jsondict, index, value):
    for key, values in jsondict.items():
        if type(values) == list:
            get_list(values)
        elif key == index[0] and type(values) == dict:
            index.pop(0)
            set_field(values, index, value)
        elif type(values) != list and key == index[0]:
            jsondict[key] = value
        else:
            pass
    return jsondict


def get_list(values):
    rustle = values[0]
    if type(rustle) == list:
        get_list(values)
    else:
        set_field(rustle)


# def set_field(jsondict, index, value):
#     '''
#     Iterate keys in 'spec' structure and map them to real CMDs in back-end.
#     Note that only the first CMD will be executed.
#     '''
#     contents = jsondict
#     target = []
#     for key in contents.keys():
#         #         print(contents)
#         target = contents.get(layer)
#     if not contents:
#         return None
#     for k in contents.keys():
#         if k == index[-1]:
#             contents[k] = value
#     print(jsondict)
#     return jsondict

def getCmdKey(jsondict):
    spec = get_spec(jsondict)
    the_cmd_keys = []
    if spec:
        '''
        Iterate keys in 'spec' structure and map them to real CMDs in back-end.
        Note that only the first CMD will be executed.
        '''
        lifecycle = spec.get('lifecycle')
        if not lifecycle:
            return None
        keys = lifecycle.keys()
        for key in keys:
            the_cmd_keys.append(key)
    return the_cmd_keys[0] if the_cmd_keys else None


def get_volume_snapshots(path):
    cmd = 'qemu-img info -U %s' % path
    try:
        std_out = runCmdRaiseException(cmd)
    except:
        cmd = 'qemu-img info %s' % path
        std_out = runCmdRaiseException(cmd)
    start = False
    snapshots = {'snapshot': []}
    for line in std_out:
        line = line.strip()
        if line.startswith('ID  '):
            start = True
            continue
        if line.startswith('Format '):
            break;
        if start:
            data = re.split('\s+', line)
            if len(data) == 6:
                snapshot = {}
                snapshot['id'] = data[0].strip()
                snapshot['name'] = data[1].strip()
                snapshot['date'] = '%s %s' % (data[3].strip(), data[4].strip())
                snapshots['snapshot'].append(snapshot)
                continue
            else:
                pass
    return snapshots


def daemonize(cd,log_fn):
    '''守护进程的实现
    '''
    help_msg = 'Usage: python %s <start|stop|restart|status>' % sys.argv[0]
    if len(sys.argv) != 2:
        print(help_msg)
        sys.exit(1)
    # p_name = constants.KUBEVMM_LIBVIRTWATCHER_SERVICE_NAME
    # pid_fn = constants.KUBEVMM_LIBVIRTWATCHER_SERVICE_LOCK
    # log_fn = constants.KUBEVMM_VIRTLET_LOG
    # err_fn = constants.KUBEVMM_VIRTLET_LOG
    # cD = ClientDaemon(p_name, pid_fn, stderr=err_fn, verbose=1)

    if sys.argv[1] == 'start':
        cd.start(log_fn)
    elif sys.argv[1] == 'stop':
        cd.stop()
    elif sys.argv[1] == 'restart':
        cd.restart(log_fn)
    elif sys.argv[1] == 'status':
        alive = cd.is_running()
        if alive:
            print('process [%s] is running ......' % cd.get_pid())
        else:
            print('daemon process [%s] stopped' % cd.name)
    else:
        print('invalid argument!')
        print(help_msg)


def singleton(pid_filename):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            pid = str(os.getpid())
            pidfile = open(pid_filename, 'a+')
            try:
                fcntl.flock(pidfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError:
                return
            pidfile.seek(0)
            pidfile.truncate()
            pidfile.write(pid)
            pidfile.flush()
            pidfile.seek(0)

            ret = f(*args, **kwargs)

            try:
                pidfile.close()
            except IOError as err:
                if err.errno != 9:
                    return
            os.remove(pid_filename)
            return ret

        return decorated

    return decorator


def pid_exists(pid):
    """Check whether pid exists in the current process table.
    UNIX only.
    """
    if pid < 0:
        return False
    if pid == 0:
        # According to "man 2 kill" PID 0 refers to every process
        # in the process group of the calling process.
        # On certain systems 0 is a valid PID but we have no way
        # to know that in a portable fashion.
        return False
    try:
        os.kill(pid, 0)
    except OSError as err:
        if err.errno == errno.ESRCH:
            # ESRCH == No such process
            return False
        elif err.errno == errno.EPERM:
            # EPERM clearly means there's a process to deny access to
            return True
        else:
            # According to "man 2 kill" possible error values are
            # (EINVAL, EPERM, ESRCH)
            return False
    else:
        return True


def get_label_selector():
    return 'host=%s' % (get_hostname_in_lower_case())


def get_hostname_in_lower_case():
    return '%s' % socket.gethostname().lower()


def normlize(s):
    return s[:1].upper() + s[1:]


def now_to_datetime():
    time_zone = gettz('Asia/Shanghai')
    return datetime.datetime.now(tz=time_zone)


def now_to_micro_time():
    time_zone = gettz('Asia/Shanghai')
    dt = datetime.datetime.now(tz=time_zone)
    return time.mktime(dt.timetuple()) + dt.microsecond / 1000000.0


def now_to_timestamp(digits=10):
    time_stamp = time.time()
    digits = 10 ** (digits - 10)
    time_stamp = int(round(time_stamp * digits))
    return time_stamp


class RotatingOperation:
    def __init__(self):
        pass

    def option(self):
        pass

    def rotating_option(self):
        pass


'''
Switch string in file
Parameters:
    x: target file.
    y: replaced value.
    z: replacement value.
    s:
        { 1: only replace 1th match.
          'g': replace all matches.
        }
'''


def string_switch(x, y, z, s=1):
    with open(x, "r") as f:
        lines = f.readlines()

    with open(x, "w") as f_w:
        n = 0
        if s == 1:
            for line in lines:
                if y in line:
                    line = line.replace(y, z)
                    f_w.write(line)
                    n += 1
                    break
                f_w.write(line)
                n += 1
            for i in range(n, len(lines)):
                f_w.write(lines[i])
        elif s == 'g':
            for line in lines:
                if y in line:
                    line = line.replace(y, z)
                f_w.write(line)


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return str(obj, encoding='utf-8');
        return json.JSONEncoder.default(self, obj)


'''
Run back-end command in subprocess.
'''


def runCmd(cmd, raise_it=True):
    std_err = None
    if not cmd:
        return
    if not isinstance(cmd, str):
        cmd = cmd.decode('utf-8')
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        std_out = p.stdout.read().decode('utf-8')
        std_err = p.stderr.read().decode('utf-8')
        if std_err:
            if raise_it:
                if std_err.find("InsecureRequestWarning") != -1 or std_err.find(
                        "Unable to register authentication agent") != -1:
                    pass
                else:
                    raise BadRequest(std_err)
        if std_out:
            return str(std_out).strip()
        else:
            return None
    finally:
        p.stdout.close()
        p.stderr.close()


def runCmdRaiseException(cmd, head='VirtctlError', use_read=False):
    std_out = None
    std_err = None
    if not cmd:
        return
    if not isinstance(cmd, str):
        cmd = cmd.decode('utf-8')
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        if use_read:
            std_out = p.stdout.read().decode('utf-8')
            std_err = p.stderr.read().decode('utf-8')
        else:
            std_out_list = p.stdout.readlines()
            std_err_list = p.stderr.readlines()
            if std_out_list:
                std_out = []
                for i in std_out_list:
                    std_out.append(i.decode('utf-8'))
            if std_err_list:
                std_err = []
                for i in std_err_list:
                    std_err.append(i.decode('utf-8'))
        if std_err:
            if "InsecureRequestWarning" in std_err:
                pass
            else:
                raise BadRequest(std_err)
        return std_out
    finally:
        p.stdout.close()
        p.stderr.close()


'''
Run back-end command in subprocess.
'''


def runCmdWithResult(cmd, raise_it=True):
    std_err = None
    if not cmd:
        #         logger.debug('No CMD to execute.')
        return None, None
    if not isinstance(cmd, str):
        cmd = cmd.decode('utf-8')
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        std_out = p.stdout.read().decode('utf-8')
        std_err = p.stderr.read().decode('utf-8')
        code, retv = 0, ''
        if std_out:
            #             msg = ''
            #             for index, line in enumerate(std_out):
            #                 if not str(line).strip():
            #                     continue
            #                 msg = msg + str(line).strip()
            std_out = std_out.replace("'", '"')
            try:
                result = loads(std_out)
            except Exception:
                result = {}
            # print result
            #                     if not isinstance(result, str):
            #                         result = result.decode('utf-8')
            if result.get('result') and result['result']['code'] != 0 and raise_it:
                raise BadRequest(result['result']['msg'])
            elif result.get('result') and result.get('data'):
                code, retv = result['result'], result['data']
            else:
                #                         print(msg)
                code, retv = p.returncode, std_out
        #                 else:
        #                     return std_out
        if std_err:
            if std_err.find("InsecureRequestWarning") != -1:
                pass
            else:
                raise BadRequest(std_err)
        # elif code != 0:
        #     raise BadRequest(std_out)
        return code, retv
    finally:
        p.stdout.close()
        p.stderr.close()


class TimeoutError(Exception):
    pass


def report_failure(name, error_reason, error_message, kind):
    jsondict = get_custom_object(kind, name)
    jsondict = deleteLifecycleInJson(jsondict)
    jsondict = updateDescription(jsondict)
    body = addExceptionMessage(jsondict, error_reason, error_message)
    retv = update_custom_object(body)
    return retv


# def report_success(name, jsondict, success_reason, success_message, group, version, plural):
#     jsondict = get_custom_object(group, version, plural, name)
#     jsondict = deleteLifecycleInJson(jsondict)
#     jsondict = updateDescription(jsondict)
#     body = addPowerStatusMessage(jsondict, success_reason, success_message)
#     retv = update_custom_object(group, version, plural, name, body)
#     return retv


def get_spec(jsondict):
    spec = jsondict.get('spec')
    if not spec:
        raw_object = jsondict.get('raw_object')
        if raw_object:
            spec = raw_object.get('spec')
    return spec


def deleteLifecycleInJson(jsondict):
    if jsondict:
        spec = get_spec(jsondict)
        if spec:
            lifecycle = spec.get('lifecycle')
            if lifecycle:
                del spec['lifecycle']
    return jsondict


def updateJsonRemoveLifecycle(jsondict, body):
    if jsondict:
        spec = get_spec(jsondict)
        if spec:
            lifecycle = spec.get('lifecycle')
            if lifecycle:
                del spec['lifecycle']
            spec.update(body)
    return jsondict


def updateDescription(jsondict):
    if jsondict:
        spec = get_spec(jsondict)
        if spec:
            spec['description'] = {'lastOperationTimeStamp': int(round(time.time() * 1000))}
    return jsondict


def updateNodeName(jsondict):
    if jsondict:
        spec = get_spec(jsondict)
        if spec:
            jsondict['spec']['nodeName'] = get_hostname_in_lower_case()
    return jsondict


def addPowerStatusMessage(jsondict, reason, message):
    if jsondict:
        status = {'conditions': {'state': {'waiting': {'message': message, 'reason': reason}}}}
        spec = get_spec(jsondict)
        if spec:
            spec['status'] = status
            spec['powerstate'] = reason
    return jsondict


def addExceptionMessage(jsondict, reason, message):
    if jsondict:
        status = {'conditions': {'state': {'waiting': {'message': message, 'reason': reason}}}}
        spec = get_spec(jsondict)
        if spec:
            spec['status'] = status
    return jsondict


# def addPowerStatusMessage(jsondict, reason, message):
#     if jsondict:
#         status = {'conditions':{'state':{'powerstate':{'message':message, 'reason':reason}}}}
#         status1 = {'powerstate':{'message':message, 'reason':reason}}
#         spec = get_spec(jsondict)
#         if spec:
#             if not status.has_key('conditions'):
#                 spec['status'].update(status)
#             else:
#                 spec['status']['conditions']['state'].update(status1)
#     return jsondict
#
# def addExceptionMessage(jsondict, reason, message):
#     if jsondict:
#         status = {'conditions':{'state':{'exception':{'message':message, 'reason':reason}}}}
#         status1 = {'exception':{'message':message, 'reason':reason}}
#         spec = get_spec(jsondict)
#         if spec:
#             if not status.has_key('conditions'):
#                 spec['status'].update(status)
#             else:
#                 spec['status']['conditions']['state'].update(status1)
#     return jsondict

def addSnapshots(vol_path, jsondict):
    snapshot_json = get_volume_snapshots(vol_path)
    jsondict['volume'].update(snapshot_json)
    return jsondict


def add_spec_in_volume(jsondict, field, value):
    jsondict['volume'][field] = value
    return jsondict


def updateDomainBackup(vm_json):
    domain = vm_json.get('domain')
    if domain:
        os = domain.get('os')
        if os:
            boot = os.get('boot')
            if boot:
                os['boot'] = _addListToSpecificField(boot)
        domain['os'] = os
        sec_label = domain.get('seclabel')
        if sec_label:
            domain['seclabel'] = _addListToSpecificField(sec_label)
        devices = domain.get('devices')
        if devices:
            channel = devices.get('channel')
            if channel:
                devices['channel'] = _addListToSpecificField(channel)
            graphics = devices.get('graphics')
            if graphics:
                devices['graphics'] = _addListToSpecificField(graphics)
            video = devices.get('video')
            if video:
                devices['video'] = _addListToSpecificField(video)
            _interface = devices.get('_interface')
            if _interface:
                devices['_interface'] = _addListToSpecificField(_interface)
            console = devices.get('console')
            if console:
                devices['console'] = _addListToSpecificField(console)
            controller = devices.get('controller')
            if controller:
                devices['controller'] = _addListToSpecificField(controller)
            rng = devices.get('rng')
            if rng:
                devices['rng'] = _addListToSpecificField(rng)
            serial = devices.get('serial')
            if serial:
                devices['serial'] = _addListToSpecificField(serial)
            disk = devices.get('disk')
            if disk:
                devices['disk'] = _addListToSpecificField(disk)
        domain['devices'] = devices
    return vm_json


def update_vm_json(jsonstr):
    json = jsonstr.replace('_interface', 'interface').replace('_transient', 'transient').replace(
        'suspend_to_mem', 'suspend-to-mem').replace('suspend_to_disk', 'suspend-to-disk').replace(
        'on_crash', 'on-crash').replace('on_poweroff', 'on-poweroff').replace('on_reboot', 'on-reboot').replace(
        'nested_hv', 'nested-hv').replace('read_bytes_sec', 'read-bytes-sec').replace(
        'write_bytes_sec', 'write-bytes-sec').replace('"_', '"@').replace("'_", "'@").replace(
        'text', '#text').replace('\'', '"')
    return json


def iterate_dict(area, i=0):
    #     result = {}
    for k, v in area.items():
        if isinstance(v, int):
            area[k] = "%d" % v
        #             area[k] = "+1-{}".format(v)
        if isinstance(area[k], dict):
            iterate_dict(area[k], i + 1)
        if isinstance(area[k], list):
            for j in area[k]:
                if isinstance(j, dict):
                    iterate_dict(j, i + 1)
    return area


def updateDomain(jsondict):
    if os.path.exists('/home/kubevmm/core/utils/arraylist.cfg'):
        arraylist = '/home/kubevmm/core/utils/arraylist.cfg'
    else:
        arraylist = '/etc/uniVirt/arraylist.cfg'
    with open(arraylist) as fr:
        for line in fr:
            l = str.strip(line)
            alist = l.split('-')
            _userDefinedOperationInList('domain', jsondict, alist)
    return jsondict


def updateDomainSnapshot(jsondict):
    if os.path.exists('/home/kubevmm/core/utils/arraylist.cfg'):
        arraylist = '/home/kubevmm/core/utils/arraylist.cfg'
    else:
        arraylist = '/etc/uniVirt/arraylist.cfg'
    with open(arraylist) as fr:
        for line in fr:
            l = str.strip(line)
            alist = l.split('-')
            _userDefinedOperationInList('domainsnapshot', jsondict, alist)
    return jsondict


def _addListToSpecificField(data):
    if isinstance(data, list):
        return data
    else:
        return [data]


'''
Cautions! Do not modify this function because it uses reflections!
'''


def _userDefinedOperationInList(field, jsondict, alist):
    jsondict = jsondict[field]
    tmp = jsondict
    do_it = False
    for index, value in enumerate(alist):
        if index == 0:
            if value != field:
                break;
            continue
        tmp = tmp.get(value)
        if not tmp:
            do_it = False
            break;
        do_it = True
    if do_it:
        tmp2 = None
        for index, value in enumerate(alist):
            if index == 0:
                tmp2 = 'jsondict'
            else:
                tmp2 = '{}[\'{}\']'.format(tmp2, value)
        exec('%s = %s' % (tmp2, _addListToSpecificField(tmp)))
    return


class KubevmmException(Exception):
    def __init__(self, reason, message):
        self.reason = reason
        self.message = message


def is_valid_uuid(uuid_str):
    # 正则表达式模式，用于匹配UUID的格式
    uuid_pattern = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')

    # 使用正则表达式匹配字符串
    if uuid_pattern.match(uuid_str):
        return True
    else:
        return False


def randomUUID():
    u = [random.randint(0, 255) for ignore in range(0, 16)]
    u[6] = (u[6] & 0x0F) | (4 << 4)
    u[8] = (u[8] & 0x3F) | (2 << 6)
    return "-".join(["%02x" * 4, "%02x" * 2, "%02x" * 2, "%02x" * 2,
                     "%02x" * 6]) % tuple(u)


def randomMAC():
    mac = [0x52, 0x54, 0x00,
           random.randint(0x00, 0x7f),
           random.randint(0x00, 0xff),
           random.randint(0x00, 0xff)]
    return ':'.join(map(lambda x: "%02x" % x, mac))


def createVmi(metadata_name, target):
    if not is_pool_exists(target):
        raise ExecuteException('Wrong "target" %s: no such directory.' % target)
    path = get_pool_path(target)
    return (['echo "vmi = %s" >> %s' % (path, RESOURCE_FILE_PATH)],
            ['sed -i \'/vmi = %s/d\' %s' % (path, RESOURCE_FILE_PATH)])


def deleteVmi(metadata_name, target):
    if not is_pool_exists(target):
        raise ExecuteException('Wrong "target" %s: no such directory.' % target)
    path = get_pool_path(target)
    return (['sed -i \'/vmi = %s/d\' %s' % (path, RESOURCE_FILE_PATH)],
            ['echo "vmi = %s" >> %s' % (path, RESOURCE_FILE_PATH)])


def createVmdi(metadata_name, target):
    if not is_pool_exists(target):
        raise ExecuteException('Wrong "target" %s: no such directory.' % target)
    path = get_pool_path(target)
    return (['echo "vmdi = %s" >> %s' % (path, RESOURCE_FILE_PATH)],
            ['sed -i \'/vmdi = %s/d\' %s' % (path, RESOURCE_FILE_PATH)])


def deleteVmdi(metadata_name, target):
    if not is_pool_exists(target):
        raise ExecuteException('Wrong "target" %s: no such directory.' % target)
    path = get_pool_path(target)
    return (['sed -i \'/vmdi = %s/d\' %s' % (path, RESOURCE_FILE_PATH)],
            ['echo "vmdi = %s" >> %s' % (path, RESOURCE_FILE_PATH)])


class Domain(object):
    def __init__(self, libvirt_domain):
        self.libvirt_domain = libvirt_domain
        self.name = libvirt_domain.name()
        self.libvirt_snapshot = None

    def get_disks(self):
        """ Gets all domain disk as namedtuple('DiskInfo', ['device', 'file', 'format']) """
        # root node
        root = ElementTree.fromstring(self.libvirt_domain.XMLDesc())

        # search <disk type='file' device='disk'> entries
        disks = root.findall("./devices/disk[@device='disk']")

        # for every disk get drivers, sources and targets
        drivers = [disk.find("driver").attrib for disk in disks]
        sources = [disk.find("source").attrib for disk in disks]
        targets = [disk.find("target").attrib for disk in disks]

        # iterate drivers, sources and targets
        if len(drivers) != len(sources) != len(targets):
            raise RuntimeError("Drivers, sources and targets lengths are different %s:%s:%s" % (
                len(drivers), len(sources), len(targets)))

        disk_info = namedtuple('DiskInfo', ['device', 'file', 'format'])

        # all disks info
        disks_info = []

        for i in range(len(sources)):
            disks_info.append(disk_info(targets[i]["dev"], sources[i]["file"], drivers[i]["type"]))

        return disks_info

    def get_snapshot_disks(self, snapshot):
        """ Gets all domain disk as namedtuple('DiskInfo', ['device', 'file', 'format']) """
        # root node
        root = ElementTree.fromstring(self.libvirt_domain.snapshotLookupByName(snapshot).getXMLDesc())

        # search <disk type='file' device='disk'> entries
        disks = root.findall("./disks/disk[@snapshot='external']")

        # for every disk get drivers, sources and targets
        drivers = [disk.find("driver").attrib for disk in disks]
        sources = [disk.find("source").attrib for disk in disks]
        targets = [disk.attrib for disk in disks]

        # iterate drivers, sources and targets
        if len(drivers) != len(sources) != len(targets):
            raise RuntimeError("Drivers, sources and targets lengths are different %s:%s:%s" % (
                len(drivers), len(sources), len(targets)))

        disk_info = namedtuple('DiskInfo', ['device', 'file', 'format'])

        # all disks info
        disks_info = []

        for i in range(len(sources)):
            disks_info.append(disk_info(targets[i]["name"], sources[i]["file"], drivers[i]["type"]))

        return disks_info

    def verify_disk_write_lock(self, file_path):
        backing_file = DiskImageHelper.get_backing_file(file_path, True)
        return backing_file

    def merge_snapshot(self, base):
        """ Merges base to snapshot and removes old disk files """
        disks = self.get_disks()
        snapshot_disks = self.get_snapshot_disks(base)
        disks_to_remove = []
        merge_snapshots_cmd = ''
        disks_to_remove_cmd = ''
        snapshots_to_delete_cmd = ''
        for disk in disks:
            current_disk_files = [disk.file]
            current_disk_files += (DiskImageHelper.get_backing_files_tree(disk.file))
            if len(current_disk_files) == 1:
                continue
            base_disk = ''
            for snapshot_disk in snapshot_disks:
                if snapshot_disk.file == disk.file:
                    raise ExecuteException('VirtctlError',
                                           '400, Bad Request! Cannot merge current disk %s to itself.' % snapshot_disk.file)
                elif snapshot_disk.file in current_disk_files:
                    base_disk = DiskImageHelper.get_backing_file(snapshot_disk.file)
                else:
                    continue
            if not base_disk:
                #                 disks_to_remove.append(a_disk for a_disk in current_disk_files)
                continue
            else:
                start_it = False
                for a_disk in current_disk_files:
                    if a_disk == disk.file and a_disk != base_disk:
                        start_it = True
                    elif a_disk == base_disk:
                        break;
                    elif start_it:
                        disks_to_remove.append(a_disk)
                    else:
                        continue
                merge_snapshots_cmd += 'virsh blockpull --domain %s --path %s --base %s --wait;' % (
                    self.name, disk.file, base_disk)
        for disk_to_remove in disks_to_remove:
            self.verify_disk_write_lock(disk_to_remove)
            disks_to_remove_cmd += 'rm -f %s;' % disk_to_remove
            snapshot_name = os.path.basename(disk_to_remove)
            if not is_snapshot_exists(snapshot_name, self.name):
                snapshot_name = os.path.splitext(os.path.basename(disk_to_remove))[1][1:] \
                    if len(os.path.splitext(os.path.basename(disk_to_remove))) == 2 else None
            if snapshot_name and is_snapshot_exists(snapshot_name, self.name):
                if snapshots_to_delete_cmd.find('--snapshotname %s' % snapshot_name) != -1:
                    continue
                else:
                    snapshots_to_delete_cmd += 'virsh snapshot-delete --domain %s --snapshotname %s --metadata;' % (
                        self.name, snapshot_name)
            # remove old disk device files without current ones
        return (merge_snapshots_cmd, disks_to_remove_cmd, snapshots_to_delete_cmd)

    def revert_snapshot(self, snapshot, revert_to_backing_file=False):
        """ Revert snapshot and removes invalid snapshots and their disk files """
        disks = self.get_disks()
        snapshot_disks = self.get_snapshot_disks(snapshot)
        unplug_disks_cmd = ''
        unplug_disks_rollback_cmd = ''
        plug_disks_cmd = ''
        plug_disks_rollback_cmd = ''
        disks_to_remove = []
        #         revert_snapshot_cmd = 'virsh snapshot-revert --domain %s --snapshotname %s' % (self.name, snapshot)
        disks_to_remove_cmd = ''
        snapshots_to_delete_cmd = ''
        for disk in disks:
            current_disk_files = [disk.file]
            current_disk_files += (DiskImageHelper.get_backing_files_tree(disk.file))
            if len(current_disk_files) == 1:
                continue
            base_disk = ''
            base_disk_target = ''
            for snapshot_disk in snapshot_disks:
                if snapshot_disk.file == disk.file and not revert_to_backing_file:
                    raise ExecuteException('VirtctlError',
                                           '400, Bad Request! Cannot revert current disk %s to itself.' % snapshot_disk.file)
                elif snapshot_disk.file in current_disk_files:
                    if revert_to_backing_file:
                        base_disk = DiskImageHelper.get_backing_file(snapshot_disk.file)
                    else:
                        base_disk = snapshot_disk.file
                    base_disk_target = snapshot_disk.device
                else:
                    continue
            if not base_disk:
                #                 disks_to_remove.append(a_disk for a_disk in current_disk_files)
                continue
            else:
                start_it = False
                current_disk_files.reverse()
                for a_disk in current_disk_files:
                    if a_disk == base_disk:
                        start_it = True
                    elif a_disk == disk.file:
                        disks_to_remove.append(a_disk)
                        break;
                    elif start_it:
                        self.verify_disk_write_lock(a_disk)
                        disks_to_remove.append(a_disk)
                    else:
                        continue
                unplug_disks_cmd += 'virsh detach-disk --domain %s --target %s --config;' % (self.name, disk.file)
                unplug_disks_rollback_cmd += 'virsh attach-disk --subdriver qcow2 --domain %s --source %s --target %s --config;' % (
                    self.name, disk.file, disk.device)
                plug_disks_cmd += 'virsh attach-disk --subdriver qcow2 --domain %s --source %s --target %s --config;' % (
                    self.name, base_disk, base_disk_target)
                plug_disks_rollback_cmd += 'virsh detach-disk --domain %s --target %s --config;' % (
                    self.name, base_disk)
        for disk_to_remove in disks_to_remove:
            disks_to_remove_cmd += 'rm -f %s;' % disk_to_remove
            snapshot_name = os.path.basename(disk_to_remove)
            if not is_snapshot_exists(snapshot_name, self.name):
                snapshot_name = os.path.splitext(os.path.basename(disk_to_remove))[1][1:] \
                    if len(os.path.splitext(os.path.basename(disk_to_remove))) == 2 else None
            if snapshot_name and is_snapshot_exists(snapshot_name, self.name):
                if snapshots_to_delete_cmd.find('--snapshotname %s' % snapshot_name) != -1:
                    continue
                else:
                    snapshots_to_delete_cmd += 'virsh snapshot-delete --domain %s --snapshotname %s --metadata;' % (
                        self.name, snapshot_name)
            # remove old disk device files without current ones
        return (
            unplug_disks_cmd, unplug_disks_rollback_cmd, plug_disks_cmd, plug_disks_rollback_cmd, disks_to_remove_cmd,
            snapshots_to_delete_cmd)


class DiskImageHelper(object):
    @staticmethod
    def get_backing_file(file, raise_it=False):
        """ Gets backing file for disk image """
        get_backing_file_cmd = "qemu-img info %s" % file
        try:
            out = runCmdRaiseException(get_backing_file_cmd, use_read=True)
        except Exception as e:
            if raise_it:
                raise e
            get_backing_file_cmd = "qemu-img info -U %s" % file
            out = runCmdRaiseException(get_backing_file_cmd, use_read=True)
        lines = out.decode('utf-8').split('\n')
        for line in lines:
            if re.search("backing file:", line):
                return str(line.strip().split()[2])
        return None

    @staticmethod
    def get_backing_files_tree(file):
        """ Gets all backing files (snapshot tree) for disk image """
        backing_files = []
        backing_file = DiskImageHelper.get_backing_file(file)
        while backing_file is not None:
            backing_files.append(backing_file)
            backing_file = DiskImageHelper.get_backing_file(backing_file)
        return backing_files

    @staticmethod
    def set_backing_file(backing_file, file):
        """ Sets backing file for disk image """
        set_backing_file_cmd = "qemu-img rebase -u -b %s %s" % (backing_file, file)
        runCmdRaiseException(set_backing_file_cmd)


def get_rebase_backing_file_cmds(source_dir, target_dir):
    source_config_file = '%s/config.json' % (source_dir)
    with open(source_config_file, "r") as f:
        config = load(f)
    source_current = config.get('current')
    backing_chain = DiskImageHelper.get_backing_files_tree(source_current)
    set_backing_file_cmd = []
    if backing_chain:
        backing_chain = backing_chain[:-1]
        backing_chain.reverse()
        backing_chain.append(source_current)
        for disk_file in backing_chain:
            new_backing = DiskImageHelper.get_backing_file(disk_file).replace(source_dir, target_dir)
            new_file = disk_file.replace(source_dir, target_dir)
            cmd = 'qemu-img rebase -u -b %s %s' % (new_backing, new_file)
            set_backing_file_cmd.append(cmd.encode('utf-8'))
    else:
        raise ExecuteException('VirtctlError', 'Cannot find backing files of %s' % source_current)
    return set_backing_file_cmd


def check_vdiskfs_by_disk_path(path):
    if not path:
        return False
    #     print(all_path)

    is_vdiskfs = False
    for disk_path in get_disks_path(path, True):
        result, data = runCmdWithResult('kubesds-adm showDiskPool --path %s' % disk_path, False)
        if data and 'pooltype' in data.keys():
            if data['pooltype'] == 'vdiskfs':
                is_vdiskfs = True
    return is_vdiskfs


def get_disks_path(path, include_iso=False):
    retv = []
    for line in path.replace(' ', ',').split(','):
        if include_iso:
            if line.startswith('/'):
                retv.append(line)
        else:
            if line.startswith('/') and not line.endswith('.iso'):
                retv.append(line)
    return retv


def get_sn_chain(ss_path):
    return runCmdWithResult('qemu-img info -U --backing-chain --output json %s' % ss_path)


def get_disk_snapshots(ss_path):
    ss_chain = get_sn_chain(ss_path)
    snapshots = []
    for disk_info in ss_chain:
        if disk_info['filename'] != ss_path:
            snapshots.append(disk_info['filename'])
    return snapshots


def list_all_disks(path, disk_type='f'):
    try:
        return runCmdRaiseException(
            "timeout 10 find %s -type %s ! -name '*.json' ! -name '*.temp' ! -name 'content' ! -name '.*' ! -name '*.xml' ! -name '*.pem' | grep -v overlay2" % (
                path, disk_type))
    except:
        return []


def get_desc(vm):
    return runCmdRaiseException('timeout 2 virsh desc %s' % (vm))[0].replace("'", '"')
    # for child in root:
    #     print(child.tag, "----", child.attrib)


def get_update_description_command(vm, device, switch, ip, args):
    try:
        desc = get_desc(vm)
        if desc.startswith("No description"):
            desc_dict = {}
        else:
            desc_dict = loads(desc)
        desc_dict[device] = {'switch': switch, 'ip': ip}
        desc_str = dumps(desc_dict).replace('"', '\\"')
        if args.find('--persistent') != -1:
            args = args.replace('--persistent', '--config')
        return 'virsh desc --domain %s --new-desc \"%s\" %s' % (vm, desc_str, args)
    except:
        return ''


def get_del_description_command(vm, device, args):
    try:
        desc = get_desc(vm)
        if desc.startswith("No description"):
            desc_dict = {}
        else:
            desc_dict = loads(desc)
        if device in desc_dict.keys():
            del desc_dict[device]
        desc_str = dumps(desc_dict).replace('"', '\\"')
        if args.find('--persistent') != -1:
            args = args.replace('--persistent', '--config')
        return 'virsh desc --domain %s --new-desc \"%s\" %s' % (vm, desc_str, args)
    except:
        return ''


def get_switch_and_ip_info_from_cfg_file(vm, device):
    try:
        net_cfg_file_path = '%s/%s-nic-%s.cfg' % \
                            (constants.KUBEVMM_VM_DEVICES_DIR, vm, device)
        if os.path.exists(net_cfg_file_path):
            switch = None
            ip = None
            with open(net_cfg_file_path, 'r') as file:
                lines = file.readlines()
                for line in lines:
                    line = line.strip()
                    if line.startswith('switch='):
                        switch = line.split('=')[1]
                    elif line.startswith('ip='):
                        ip = line.split('=')[1]
            return switch, ip
        else:
            return None, None
    except:
        return None, None


def get_switch_and_ip_info(vm, device):
    try:
        desc = get_desc(vm)
        if desc.startswith("No description"):
            desc_dict = {}
        else:
            desc_dict = loads(desc)
        device_dict = desc_dict.get(device)
        if device_dict:
            return (device_dict.get('switch'), device_dict.get('ip'))
        else:
            return (None, None)
    except:
        return (None, None)


def get_all_nodes():
    """:rtype: V1NodeList"""
    client=KubernetesClient(config=TOKEN)
    return client.listResources(kind='Node')



def get_nodes_num():
    """:rtype: int"""
    return len(get_all_nodes().get('items'))



def get_all_nodes_name():
    """:rtype: list"""
    names = []
    for item in get_all_nodes().get('items'):
        names.append(item.get('metadata').get('name'))
    return names


def get_1st_ready():
    try:
        client = KubernetesClient(config=TOKEN)
        names = get_all_nodes_name()
        if not names:
            logger.warning("No nodes found in the cluster.")
            return None

        for name in names:
            try:
                # 获取节点状态
                nodestatus = client.getResourceStatus(kind='Node', name=name).get('status')
                if nodestatus and nodestatus.get('conditions'):
                    # 遍历 conditions，找到状态为 Ready 的节点
                    for condition in nodestatus.get('conditions'):
                        if condition.get('type') == 'Ready' and condition.get('status') == 'True':
                            logger.info(f"Node '{name}' is Ready.")
                            return name
            except Exception as e:
                logger.error(f"Failed to get status for node '{name}'.", exc_info=e)

        logger.warning("No Ready nodes found.")
        return None
    except Exception as e:
        logger.error("Failed to retrieve the first ready node.", exc_info=e)
        return None


def get_node_label_value(nodes, label):
    """:type nodes: str:type label: str:rtype: str"""
    try:
        # for item in get_all_nodes().get('items'):
        #     if item.get('metadata').get('name')==nodes:
        #         return item.get('metadata').get('labels')[label]
        i = get_all_nodes_name().index(nodes)
        return get_all_nodes().get('items')[i].get('metadata').get('labels')[label]
    except ValueError:
        return None


def push_node_label_value(node, label, value):
    """:type node: str:type label: str:type value: str"""
    client = KubernetesClient(config=TOKEN)
    jsonDict=client.getResource(kind='Node',name=node)
    body = {label: value}
    jsonDict['metadata']['labels'].update(body)
    if node in get_all_nodes_name():
        client.updateResource(jsonDict)
    else:
        raise BadRequest("node %s does not exist" % node)



class UserDefinedEvent(object):
    swagger_types = {
        'event_metadata_name': 'str',
        'time_start': 'datetime',
        'time_end': 'datetime',
        'involved_object_name': 'str',
        'involved_object_kind': 'str',
        'message': 'str',
        'reason': 'str',
        'event_type': 'str'
    }

    def __init__(self, action,controller,event_metadata_name, time_start, time_end, involved_object_name, involved_object_kind, message,
                 reason, event_type):
        self.action=action
        self.controller=controller
        self.event_metadata_name = event_metadata_name
        self.time_start = time_start
        self.time_end = time_end
        self.involved_object_name = involved_object_name
        self.involved_object_kind = involved_object_kind
        self.message = message
        self.reason = reason
        self.event_type = event_type

    def registerKubernetesEvent(self):
        '''
        More details please @See:
            https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1Event.md
        '''
        # involved_object = client.V1ObjectReference(name=self.involved_object_name, kind=self.involved_object_kind,
        #                                            namespace='default')
        # metadata = client.V1ObjectMeta(name=self.event_metadata_name, namespace='default')
        # body = client.CoreV1Event(first_timestamp=self.time_start, last_timestamp=self.time_end, metadata=metadata,
        #                           involved_object=involved_object, message=self.message, reason=self.reason,
        #                           type=self.event_type)
        # client.CoreV1Api().replace_namespaced_event(self.event_metadata_name, 'default', body, pretty='true')
        involved_object=InvolvedObject(name=self.involved_object_name, kind=self.involved_object_kind,namespace='default')
        metadata=Metadata(name=self.event_metadata_name, namespace='default')
        body=Event(action=self.action,controller=self.controller,first_timestamp=self.time_start, last_timestamp=self.time_end, metadata=metadata,
                   involved_object=involved_object, message=self.message, reason=self.reason,
                   type=self.event_type)
        KubernetesClient(config=TOKEN).updateResource(body.__dict__,pretty=True)


    def updateKubernetesEvent(self):
        '''
        More details please @See:
            https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1Event.md
        '''
        # involved_object = client.V1ObjectReference(name=self.involved_object_name, kind=self.involved_object_kind,
        #                                            namespace='default')
        # metadata = client.V1ObjectMeta(name=self.event_metadata_name, namespace='default')
        # body = client.CoreV1Event(first_timestamp=self.time_start, last_timestamp=self.time_end, metadata=metadata,
        #                           involved_object=involved_object, message=self.message, reason=self.reason,
        #                           type=self.event_type)
        # client.CoreV1Api().replace_namespaced_event(self.event_metadata_name, 'default', body, pretty='true')
        self.registerKubernetesEvent()

    def get_event_metadata_name(self):
        return self.__event_metadata_name

    def get_time_start(self):
        return self.__time_start

    def get_time_end(self):
        return self.__time_end

    def get_involved_object_name(self):
        return self.__involved_object_name

    def get_involved_object_kind(self):
        return self.__involved_object_kind

    def get_message(self):
        return self.__message

    def get_reason(self):
        return self.__reason

    def get_event_type(self):
        return self.__event_type

    def set_event_metadata_name(self, value):
        self.__event_metadata_name = value

    def set_time_start(self, value):
        self.__time_start = value

    def set_time_end(self, value):
        self.__time_end = value

    def set_involved_object_name(self, value):
        self.__involved_object_name = value

    def set_involved_object_kind(self, value):
        self.__involved_object_kind = value

    def set_message(self, value):
        self.__message = value

    def set_reason(self, value):
        self.__reason = value

    def set_event_type(self, value):
        self.__event_type = value

    def del_event_metadata_name(self):
        del self.__event_metadata_name

    def del_time_start(self):
        del self.__time_start

    def del_time_end(self):
        del self.__time_end

    def del_involved_object_name(self):
        del self.__involved_object_name

    def del_involved_object_kind(self):
        del self.__involved_object_kind

    def del_message(self):
        del self.__message

    def del_reason(self):
        del self.__reason

    def del_event_type(self):
        del self.__event_type

    def to_dict(self):
        """
        Returns the model properties as a dict
        """
        result = {}

        for attr, _ in iteritems(self.swagger_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            else:
                result[attr] = value

        return result

    def to_str(self):
        """
        Returns the string representation of the model
        """
        return pformat(self.to_dict())

    event_metadata_name = property(get_event_metadata_name, set_event_metadata_name, del_event_metadata_name,
                                   "event_metadata_name's docstring")
    time_start = property(get_time_start, set_time_start, del_time_start, "time_start's docstring")
    time_end = property(get_time_end, set_time_end, del_time_end, "time_end's docstring")
    involved_object_name = property(get_involved_object_name, set_involved_object_name, del_involved_object_name,
                                    "involved_object_name's docstring")
    involved_object_kind = property(get_involved_object_kind, set_involved_object_kind, del_involved_object_kind,
                                    "involved_object_kind's docstring")
    message = property(get_message, set_message, del_message, "message's docstring")
    reason = property(get_reason, set_reason, del_reason, "reason's docstring")
    event_type = property(get_event_type, set_event_type, del_event_type, "event_type's docstring")


class Job(threading.Thread):

    def __init__(self, *args, **kwargs):
        super(Job, self).__init__(*args, **kwargs)
        self.__flag = threading.Event()
        self.__flag.set()
        self.__running = threading.Event()
        self.__running.set()

    def run(self):
        while self.__running.isSet():
            self.__flag.wait()
            time.sleep(1)

    def pause(self):
        self.__flag.clear()

    def resume(self):
        self.__flag.set()

    def stop(self):
        self.__flag.set()
        self.__running.clear()


class CDaemon:
    '''
    a generic daemon class.
    usage: subclass the CDaemon class and override the run() method
    stderr:
    verbose:
    save_path:
    '''

    def __init__(self, save_path, stdin=os.devnull, stdout=os.devnull, stderr=os.devnull, home_dir='.', umask=0o22,
                 verbose=1):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = save_path
        self.home_dir = home_dir
        self.verbose = verbose
        self.umask = umask
        self.daemon_alive = True

    def daemonize(self):
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as e:
            sys.stderr.write('fork #1 failed: %d (%s)\n' % (e.errno, e.strerror))
            sys.exit(1)

        os.chdir(self.home_dir)
        os.setsid()
        os.umask(self.umask)

        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as e:
            sys.stderr.write('fork #2 failed: %d (%s)\n' % (e.errno, e.strerror))
            sys.exit(1)

        sys.stdout.flush()
        sys.stderr.flush()

        with open(self.stdin, 'r') as si:
            os.dup2(si.fileno(), sys.stdin.fileno())
        with open(self.stdout, 'a+') as so:
            os.dup2(so.fileno(), sys.stdout.fileno())
        if self.stderr:
            with open(self.stderr, 'a+') as se:
                os.dup2(se.fileno(), sys.stderr.fileno())
        else:
            se = so
            os.dup2(se.fileno(), sys.stderr.fileno())

        def sig_handler(signum, frame):
            self.daemon_alive = False

        signal.signal(signal.SIGTERM, sig_handler)
        signal.signal(signal.SIGINT, sig_handler)

        if self.verbose >= 1:
            print('daemon process started ...')

        atexit.register(self.del_pid)
        pid = str(os.getpid())
        with open(self.pidfile, 'w+') as f:
            f.write('%s\n' % pid)

    def get_pid(self):
        try:
            with open(self.pidfile, 'r') as pf:
                pid = int(pf.read().strip())
                pf.close()
        except IOError:
            pid = None
        except SystemExit:
            pid = None
        return pid

    def del_pid(self):
        if os.path.exists(self.pidfile):
            os.remove(self.pidfile)

    def start(self, *args, **kwargs):
        if self.verbose >= 1:
            print('ready to start ......')
        # check for a pid file to see if the daemon already runs
        pid = self.get_pid()
        if pid:
            msg = 'pid file %s already exists, is it already running?\n'
            sys.stderr.write(msg % self.pidfile)
            sys.exit(1)
        # start the daemon
        self.daemonize()
        self.run(*args, **kwargs)

    def stop(self):
        if self.verbose >= 1:
            print('stopping ...')
        pid = self.get_pid()
        if not pid:
            msg = 'pid file [%s] does not exist. Not running?\n' % self.pidfile
            sys.stderr.write(msg)
            if os.path.exists(self.pidfile):
                os.remove(self.pidfile)
            return
        # try to kill the daemon process
        try:
            i = 0
            while 1:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
                i = i + 1
                if i % 10 == 0:
                    os.kill(pid, signal.SIGHUP)
        except OSError as err:
            err = str(err)
            if err.find('No such process') > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print(str(err))
                sys.exit(1)
            if self.verbose >= 1:
                print('Stopped!')

    def restart(self, *args, **kwargs):
        self.stop()
        self.start(*args, **kwargs)

    def is_running(self):
        pid = self.get_pid()
        # print(pid)
        return pid and os.path.exists('/proc/%d' % pid)

    def run(self, *args, **kwargs):
        'NOTE: override the method in subclass'
        print('base class run()')


if __name__ == '__main__':
    # config.load_kube_config(config_file=TOKEN)
    #     print(get_update_description_command('cloudinit1', 'fe540007a50c', 'switch2', '192.168.0.1', '--config'))
    #     pprint.pprint(list_objects_in_kubernetes('cloudplus.io', 'v1alpha3', 'virtualmachinepools'))
    #     print(get_field_in_kubernetes_by_index('cloudinit', 'cloudplus.io', 'v1alpha3', 'virtualmachines', ['metadata', 'labels']))
    #     tmp=get_custom_object(constants.KUBERNETES_GROUP,constants.KUBERNETES_API_VERSION, constants.KUBERNETES_PLURAL_VMD,"disktest")

    print(set_field_in_kubernetes_by_index('disktest-wyw', constants.KUBERNETES_KIND_VMD, ['spec', 'volume', 'vm'], 'test-wyw'))

#     print(tmp)
# pprint.pprint(change_master_ip('192.168.66.102'))
#     check_vdiskfs_by_disk_path('/var/lib/libvirt/cstor/3eebd453b21c4b8fad84a60955598195/3eebd453b21c4b8fad84a60955598195/77a5b25d34be4bcdbaeb9f5929661f8f/77a5b25d34be4bcdbaeb9f5929661f8f --disk /var/lib/libvirt/cstor/076fe6aa813842d3ba141f172e3f8eb6/076fe6aa813842d3ba141f172e3f8eb6/4a2b67b44f4c4fca87e7a811e9fd545c.iso,device=cdrom,perms=ro')
#     pprint.pprint(get_l2_network_info("br-native"))
#     from libvirt_util import _get_dom
#     domain = Domain(_get_dom("950646e8c17a49d0b83c1c797811e004"))
#     try:
#     print(get_rebase_backing_file_cmds("/var/lib/libvirt/pooltest3/wyw123/", "/var/lib/libvirt/pooltest4/wyw123/"))
# #         print(domain.merge_snapshot("snapshot3"))
# #         print(domain.revert_snapshot("snapshot3"))
#     except Exception as e:
#         print e.message
#     volume = {'volume': {"allocation": {"_unit": "bytes","text": 200704}}}
#     volume.get('volume').update(get_volume_snapshots('/var/lib/libvirt/images/test1.qcow2'))
#     print(volume)
#     print(get_volume_snapshots('/var/lib/libvirt/images/test4.qcow2'))
