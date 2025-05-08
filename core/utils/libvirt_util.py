'''
Copyright (2024, ) Institute of Software, Chinese Academy of Sciences

@author: wuyuewen@otcaix.iscas.ac.cn
@author: wuheng@otcaix.iscas.ac.cn

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
from json import loads, dumps, load
import traceback

'''
Import python libs
'''
import re
import subprocess
import time
import sys
import collections
import os
from pprint import pprint
from xml.dom import minidom
from io import StringIO as _StringIO

try:
    from utils import constants
    from utils import logger
except:
    import constants
    import logger

LOG = constants.KUBEVMM_VIRTCTL_LOG
logger = logger.set_logger(os.path.basename(__file__), LOG)

'''
Import third party libs
'''
try:
    import libvirt
    HAS_LIBVIRT = True
except ImportError:
    HAS_LIBVIRT = False
import yaml
print("import libvirt:",HAS_LIBVIRT)
try:
    from utils.exception import InternalServerError, NotFound, Forbidden, BadRequest
except:
    from exception import InternalServerError, NotFound, Forbidden, BadRequest

try:
    import xml.etree.CElementTree as ET
except:
    import xml.etree.ElementTree as ET
    


VIRT_STATE_NAME_MAP = {0: 'Running',
                       1: 'Running',
                       2: 'Running',
                       3: 'Paused',
                       4: 'Shutdown',
                       5: 'Shutdown',
                       6: 'Crashed'}


'''
   VM lifecycle
'''

def __get_conn():
    '''
    Detects what type of dom this node is and attempts to connect to the
    correct hypervisor via libvirt.
    '''
    # This has only been tested on kvm and xen, it needs to be expanded to
    # support all vm layers supported by libvirt
    try:
        conn = libvirt.open('qemu:///system')
    except Exception:
        raise Exception(
            'Sorry, {0} failed to open a connection to the hypervisor software'
        )
    return conn


def _get_dom(vm_):
    '''
    Return a domain object for the named vm
    '''
    conn = __get_conn()
    try:
        if vm_ not in list_vms():
            raise Exception('The specified vm is not present(%s).' % vm_)
        return conn.lookupByName(vm_)
    finally:
        conn.close()

def _get_pool(pool_):
    conn = __get_conn()
    try:
        if pool_ not in list_pools():
            raise Exception('The specified pool is not present(%s).' % pool_)
        pool = conn.storagePoolLookupByName(pool_)
        return pool
    finally:
        conn.close()

def _get_all_pool_path():
    paths = {}
    try:
        for pool_ in list_pools():
            pool = _get_pool(pool_)
            # pool.refresh()
            lines = pool.XMLDesc()
            for line in lines.split():
                if line.find("path") >= 0:
                    paths[pool_] = line.replace('<path>', '').replace('</path>', '')
                    break
    except Exception as e:
        pass
    return paths

def _get_pool_info(pool_):
    pool = _get_pool(pool_)
    try:
        pool.refresh()
    except:
        pass
    lines = pool.XMLDesc()
#     result = pool.info()
#     print(result)
    result = runCmdAndParse('virsh pool-info ' + pool_)
    # result['allocation'] = int(1024*1024*1024*float(result['allocation']))
    # result['available'] = int(1024 * 1024 * 1024 * float(result['available']))
    result['capacity'] = int(1024 * 1024 * 1024 * float(result['capacity']))
    del result['allocation']
    del result['available']
    for line in lines.split():
        if line.find("path") >= 0:
            result['path'] = line.replace('<path>', '').replace('</path>', '')
            break
    return result


def _get_vol(pool_, vol_):
    pool = _get_pool(pool_)
    try:
        pool.refresh()
    except:
        pass
    return pool.storageVolLookupByName(vol_)

def _get_volume_by_path(path_):
    conn = __get_conn()
    try:
        return conn.storageVolLookupByPath(path_)
    finally:
        conn.close()

def _get_all_snapshots(vm_):
    vm = _get_dom(vm_)
    return vm.snapshotListNames()

def _get_snapshot(vm_, snap_):
    vm = _get_dom(vm_)
    return vm.snapshotLookupByName(snap_)

def is_vm_exists(vm_):
    if vm_ in list_vms():
        return True
    return False

def is_pool_exists(pool_):
    if pool_ in list_pools():
        return True
    return False

def check_pool_content_type(pool_, content):
    pool_path = get_pool_path(pool_)
    content_file = '%s/content' % pool_path
    if os.path.exists(content_file):
        with open(content_file, 'r') as fr:
            pool_content = fr.read().strip()
        if pool_content == content:    
            return True
    return False

def is_vm_active(vm_):
    if vm_ in list_active_vms():
        return True
    return False

def list_vms():
    '''
    Return a list of virtual machine names on the minion

    CLI Example::

        salt '*' virt.list_vms
    '''
    conn = __get_conn()
    try:
        vms = []
        for vm in conn.listAllDomains():
            vms.append(vm.name())
        return vms
    finally:
        conn.close()
#     vms = []
#     vms.extend(list_active_vms())
#     vms.extend(list_inactive_vms())
#     return vms

def list_active_vms():
    '''
    Return a list of names for active virtual machine on the minion

    CLI Example::

        salt '*' virt.list_active_vms
    '''
    conn = __get_conn()
    try:
        vms = []
        for vm in conn.listAllDomains(libvirt.VIR_CONNECT_LIST_DOMAINS_ACTIVE):
            vms.append(vm.name())
        return vms
    finally:
        conn.close()
        
def list_autostart_vms():
    '''
    Return a list of names for active virtual machine on the minion

    CLI Example::

        salt '*' virt.list_active_vms
    '''
    conn = __get_conn()
    try:
        vms = []
        for vm_ in conn.listAllDomains(libvirt.VIR_CONNECT_LIST_DOMAINS_AUTOSTART):
            vms.append(vm_.name())
        return vms
    finally:
        conn.close()


def list_inactive_vms():
    '''
    Return a list of names for inactive virtual machine on the minion

    CLI Example::

        salt '*' virt.list_inactive_vms
    '''
    conn = __get_conn()
    try:
        vms = []
        for vm in conn.listAllDomains(libvirt.VIR_CONNECT_LIST_DOMAINS_INACTIVE):
            vms.append(vm.name())
        return vms
    finally:
        conn.close()

def vm_info(vm_=None):
    '''
    Return detailed information about the vms on this hyper in a
    list of dicts::
 
        [
            'your-vm': {
                'cpu': <int>,
                'maxMem': <int>,
                'mem': <int>,
                'state': '<state>',
                'cputime' <int>
                },
            ...
            ]
 
    If you pass a VM name in as an argument then it will return info
    for just the named VM, otherwise it will return all VMs.
 
    CLI Example::
 
        salt '*' virt.vm_info
    '''
    def _info(vm_):
        dom = _get_dom(vm_)
        raw = dom.info()
        return {'cpu': raw[3],
                'cputime': int(raw[4]),
                'disks': get_disks(vm_),
                'graphics': get_graphics(vm_),
                'nics': get_nics(vm_),
                'maxMem': int(raw[1]),
                'mem': int(raw[2]),
                'state': VIRT_STATE_NAME_MAP.get(raw[0], 'unknown')}
    info = {}
    if vm_:
        info[vm_] = _info(vm_)
    else:
        for vm_ in list_vms():
            info[vm_] = _info(vm_)
    return info


def vm_state(vm_=None):
    '''
    Return list of all the vms and their state.

    If you pass a VM name in as an argument then it will return info
    for just the named VM, otherwise it will return all VMs.

    CLI Example::

        salt '*' virt.vm_state <vm name>
    '''
    def _info(vm_):
        state = ''
        dom = _get_dom(vm_)
        raw = dom.info()
        state = VIRT_STATE_NAME_MAP.get(raw[0], 'Unknown')
        return state
    info = {}
    if vm_:
        info[vm_] = _info(vm_)
    else:
        for vm_ in list_vms():
            info[vm_] = _info(vm_)
    return info


def node_info():
    '''
    Return a dict with information about this node

    CLI Example::

        salt '*' virt.node_info
    '''
    conn = __get_conn()
    try:
        raw = conn.getInfo()
        info = {'cpucores': raw[6],
                'cpumhz': raw[3],
                'cpumodel': str(raw[0]),
                'cpus': raw[2],
                'cputhreads': raw[7],
                'numanodes': raw[4],
                'phymemory': raw[1],
                'sockets': raw[5]}
        return info
    finally:
        conn.close()

def get_nics(vm_):
    '''
    Return info about the network interfaces of a named vm

    CLI Example::

        salt '*' virt.get_nics <vm name>
    '''
    nics = collections.OrderedDict()
    doc = minidom.parse(_StringIO(get_xml(vm_)))
    for node in doc.getElementsByTagName('devices'):
        i_nodes = node.getElementsByTagName('interface')
        for i_node in i_nodes:
            nic = {}
            nic['type'] = i_node.getAttribute('type')
            for v_node in i_node.getElementsByTagName('*'):
                if v_node.tagName == 'mac':
                    nic['mac'] = v_node.getAttribute('address')
                if v_node.tagName == 'model':
                    nic['model'] = v_node.getAttribute('type')
                if v_node.tagName == 'target':
                    nic['target'] = v_node.getAttribute('dev')
                # driver, source, and match can all have optional attributes
                if re.match('(driver|source|address)', v_node.tagName):
                    temp = {}
                    for key in v_node.attributes.keys():
                        temp[key] = v_node.getAttribute(key)
                    nic[str(v_node.tagName)] = temp
                # virtualport needs to be handled separately, to pick up the
                # type attribute of the virtualport itself
                if v_node.tagName == 'virtualport':
                    temp = {}
                    temp['type'] = v_node.getAttribute('type')
                    for key in v_node.attributes.keys():
                        temp[key] = v_node.getAttribute(key)
                    nic['virtualport'] = temp
            if 'mac' not in nic:
                continue
            nics[nic['mac']] = nic
    return nics


def get_macs(vm_):
    '''
    Return a list off MAC addresses from the named vm

    CLI Example::

        salt '*' virt.get_macs <vm name>
    '''
    macs = []
    doc = minidom.parse(_StringIO(get_xml(vm_)))
    for node in doc.getElementsByTagName('devices'):
        i_nodes = node.getElementsByTagName('interface')
        for i_node in i_nodes:
            for v_node in i_node.getElementsByTagName('mac'):
                macs.append(v_node.getAttribute('address'))
    return macs

def get_target_devices(vm_):
    '''
    Return a list off MAC addresses from the named vm

    CLI Example::

        salt '*' virt.get_macs <vm name>
    '''
    devices = []
    doc = minidom.parse(_StringIO(get_xml(vm_)))
    for node in doc.getElementsByTagName('devices'):
        i_nodes = node.getElementsByTagName('interface')
        for i_node in i_nodes:
            for v_node in i_node.getElementsByTagName('target'):
                devices.append(v_node.getAttribute('dev'))
    return devices

def get_graphics(vm_):
    '''
    Returns the information on vnc for a given vm

    CLI Example::

        salt '*' virt.get_graphics <vm name>
    '''
    out = {'autoport': 'None',
           'keymap': 'None',
           'listen': 'None',
           'port': 'None',
           'type': 'vnc'}
    xml = get_xml(vm_)
    ssock = _StringIO(xml)
    doc = minidom.parse(ssock)
    for node in doc.getElementsByTagName('domain'):
        g_nodes = node.getElementsByTagName('graphics')
        for g_node in g_nodes:
            for key in g_node.attributes.keys():
                out[key] = g_node.getAttribute(key)
    return out


def get_disks(vm_):
    '''
    Return the disks of a named vm
 
    CLI Example::
 
        salt '*' virt.get_disks <vm name>
    '''
    disks = collections.OrderedDict()
    doc = minidom.parse(_StringIO(get_xml(vm_)))
    for elem in doc.getElementsByTagName('disk'):
        sources = elem.getElementsByTagName('source')
        targets = elem.getElementsByTagName('target')
        if len(sources) > 0:
            source = sources[0]
        else:
            continue
        if len(targets) > 0:
            target = targets[0]
        else:
            continue
        if target.hasAttribute('dev'):
            qemu_target = ''
            if source.hasAttribute('file'):
                qemu_target = source.getAttribute('file')
            elif source.hasAttribute('dev'):
                qemu_target = source.getAttribute('dev')
            elif source.hasAttribute('protocol') and \
                    source.hasAttribute('name'): # For rbd network
                qemu_target = '%s:%s' %(
                        source.getAttribute('protocol'),
                        source.getAttribute('name'))
            if qemu_target:
                disks[target.getAttribute('dev')] = {\
                    'file': qemu_target}
    for dev in disks:
        try:
            if not os.path.exists(disks[dev]['file']):
                continue
            output = []
            try:
                qemu_output = runCmdRaiseException('qemu-img info -U %s' % disks[dev]['file'])
            except:
                qemu_output = runCmdRaiseException('qemu-img info %s' % disks[dev]['file'])             
            snapshots = False
            columns = None
            lines = qemu_output.strip().split('\n')
            for line in lines:
                if line.startswith('Snapshot list:'):
                    snapshots = True
                    continue
                elif snapshots:
                    if line.startswith('ID'):  # Do not parse table headers
                        line = line.replace('VM SIZE', 'VMSIZE')
                        line = line.replace('VM CLOCK', 'TIME VMCLOCK')
                        columns = re.split('\s+', line)
                        columns = [c.lower() for c in columns]
                        output.append('snapshots:')
                        continue
                    fields = re.split('\s+', line)
                    for i, field in enumerate(fields):
                        sep = ' '
                        if i == 0:
                            sep = '-'
                        output.append(
                            '{0} {1}: "{2}"'.format(
                                sep, columns[i], field
                            )
                        )
                    continue
                output.append(line)
            output = '\n'.join(output)
            disks[dev].update(yaml.safe_load(output))
        except TypeError:
            disks[dev].update(yaml.safe_load('image: Does not exist'))
    return disks


def setmem(vm_, memory, config=False):
    '''
    Changes the amount of memory allocated to VM. The VM must be shutdown
    for this to work.

    memory is to be specified in MB
    If config is True then we ask libvirt to modify the config as well

    CLI Example::

        salt '*' virt.setmem myvm 768
    '''
    if vm_state(vm_).get(vm_) != 'Shutdown':
        return False

    dom = _get_dom(vm_)

    # libvirt has a funny bitwise system for the flags in that the flag
    # to affect the "current" setting is 0, which means that to set the
    # current setting we have to call it a second time with just 0 set
    flags = libvirt.VIR_DOMAIN_MEM_MAXIMUM
    if config:
        flags = flags | libvirt.VIR_DOMAIN_AFFECT_CONFIG

    ret1 = dom.setMemoryFlags(memory * 1024, flags)
    ret2 = dom.setMemoryFlags(memory * 1024, libvirt.VIR_DOMAIN_AFFECT_CURRENT)

    # return True if both calls succeeded
    return ret1 == ret2 == 0


def setvcpus(vm_, vcpus, config=False):
    '''
    Changes the amount of vcpus allocated to VM. The VM must be shutdown
    for this to work.

    vcpus is an int representing the number to be assigned
    If config is True then we ask libvirt to modify the config as well

    CLI Example::

        salt '*' virt.setvcpus myvm 2
    '''
    if vm_state(vm_).get(vm_) != 'Shutdown':
        return False

    dom = _get_dom(vm_)

    # see notes in setmem
    flags = libvirt.VIR_DOMAIN_VCPU_MAXIMUM
    if config:
        flags = flags | libvirt.VIR_DOMAIN_AFFECT_CONFIG

    ret1 = dom.setVcpusFlags(vcpus, flags)
    ret2 = dom.setVcpusFlags(vcpus, libvirt.VIR_DOMAIN_AFFECT_CURRENT)

    return ret1 == ret2 == 0


def freemem():
    '''
    Return an int representing the amount of memory that has not been given
    to virtual machines on this node

    CLI Example::

        salt '*' virt.freemem
    '''
    conn = __get_conn()
    try:
        mem = conn.getInfo()[1]
        # Take off just enough to sustain the hypervisor
        mem -= 256
        for vm_ in list_vms():
            dom = _get_dom(vm_)
            if dom.ID() > 0:
                mem -= dom.info()[2] / 1024
        return mem
    finally:
        conn.close()


def freecpu():
    '''
    Return an int representing the number of unallocated cpus on this
    hypervisor

    CLI Example::

        salt '*' virt.freecpu
    '''
    conn = __get_conn()
    try:
        cpus = conn.getInfo()[2]
        for vm_ in list_vms():
            dom = _get_dom(vm_)
            if dom.ID() > 0:
                cpus -= dom.info()[3]
        return cpus
    finally:
        conn.close()

def full_info():
    '''
    Return the node_info, vm_info and freemem
 
    CLI Example::
 
        salt '*' virt.full_info
    '''
    return {'freecpu': freecpu(),
            'freemem': freemem(),
            'node_info': node_info(),
            'vm_info': vm_info()}


def get_xml(vm_):
    '''
    Returns the xml for a given vm

    CLI Example::

        salt '*' virt.get_xml <vm name>
    '''
    dom = _get_dom(vm_)
    return dom.XMLDesc(0)

def shutdown(vm_):
    '''
    Send a soft shutdown signal to the named vm

    CLI Example::

        salt '*' virt.shutdown <vm name>
    '''
    dom = _get_dom(vm_)
    return dom.shutdown() == 0


def pause(vm_):
    '''
    Pause the named vm

    CLI Example::

        salt '*' virt.pause <vm name>
    '''
    dom = _get_dom(vm_)
    return dom.suspend() == 0


def resume(vm_):
    '''
    Resume the named vm

    CLI Example::

        salt '*' virt.resume <vm name>
    '''
    dom = _get_dom(vm_)
    return dom.resume() == 0


def create(vm_):
    '''
    Start a defined domain

    CLI Example::

        salt '*' virt.create <vm name>
    '''
    dom = _get_dom(vm_)
    return dom.create() == 0


def start(vm_):
    '''
    Alias for the obscurely named 'create' function

    CLI Example::

        salt '*' virt.start <vm name>
    '''
    return create(vm_)


def reboot(vm_):
    '''
    Reboot a domain via ACPI request

    CLI Example::

        salt '*' virt.reboot <vm name>
    '''
    dom = _get_dom(vm_)

    # reboot has a few modes of operation, passing 0 in means the
    # hypervisor will pick the best method for rebooting
    return dom.reboot(0) == 0


def reset(vm_):
    '''
    Reset a VM by emulating the reset button on a physical machine

    CLI Example::

        salt '*' virt.reset <vm name>
    '''
    dom = _get_dom(vm_)

    # reset takes a flag, like reboot, but it is not yet used
    # so we just pass in 0
    # see: http://libvirt.org/html/libvirt-libvirt.html#virDomainReset
    return dom.reset(0) == 0


def ctrl_alt_del(vm_):
    '''
    Sends CTRL+ALT+DEL to a VM

    CLI Example::

        salt '*' virt.ctrl_alt_del <vm name>
    '''
    dom = _get_dom(vm_)
    return dom.sendKey(0, 0, [29, 56, 111], 3, 0) == 0

def destroy(vm_):
    '''
    Hard power down the virtual machine, this is equivalent to pulling the
    power
   
    CLI Example::
   
        salt '*' virt.destroy <vm name>
    '''
    dom = _get_dom(vm_)
    return dom.destroy() == 0

def define_xml_str(xml):  
    ''''' 
    Define a domain based on the xml passed to the function 
    
    CLI Example:: 
    
        salt '*' virt.define_xml_str <xml in string format> 
    '''  
    conn = __get_conn() 
    try: 
        return conn.defineXML(xml) is not None
    finally:
        conn.close() 
   
def undefine(vm_):
    '''
    Remove a defined vm, this does not purge the virtual machine image, and
    this only works if the vm is powered down
   
    CLI Example::
   
        salt '*' virt.undefine <vm name>
    '''
    dom = _get_dom(vm_)
    return dom.undefine() == 0

def undefine_with_snapshot(vm_):
    '''
    Remove a defined vm, this does not purge the virtual machine image, and
    this only works if the vm is powered down
   
    CLI Example::
   
        salt '*' virt.undefine <vm name>
    '''
    dom = _get_dom(vm_)
    flags = libvirt.VIR_DOMAIN_UNDEFINE_SNAPSHOTS_METADATA
    return dom.undefineFlags(flags) == 0

def list_pools():
    conn = __get_conn()
    try:
        return conn.listStoragePools()
    finally:
        conn.close()

def refresh_pool(pool_):
    pool = _get_pool(pool_)
    try:
        pool.refresh()
    except:
        pass   
    return 

def get_pool_path(pool_):
    pool = _get_pool(pool_)
    lines = pool.XMLDesc(0)
    for line in lines.split():
        if line.find("path") >= 0:
            path = line.replace("<path>", "").replace("</path>", "")
            return path
    return None

def get_pool_xml(pool_):
    pool = _get_pool(pool_)
    return pool.XMLDesc(0)

def list_all_volumes():
    vols = []
    for pool_ in list_pools():
        pool = _get_pool(pool_)
        try:
            pool.refresh()
        except:
            pass
        for vol in pool.listAllVolumes():
            vols.append(vol.name())
    return vols

def list_volumes(pool_):
    pool = _get_pool(pool_)
    try:
        pool.refresh()
    except:
        pass
    vols = []
    for vol in pool.listAllVolumes():
        vols.append(vol.name())
    return vols

def get_volume_xml(pool_, vol_):
    vol = _get_vol(pool_, vol_)
    return vol.XMLDesc()

def get_volume_path(pool_, vol_):
    vol = _get_vol(pool_, vol_)
    return vol.path()

def get_volume_current_path(pool_, vol_):
    vol = _get_vol(pool_, vol_)
    vol_dir = vol.path()
    with open(vol_dir + '/config.json', "r") as f:
        config = load(f)
    return config['current']

def delete_volume(pool_, vol_):
    vol = _get_vol(pool_, vol_)
    return vol.delete()

def is_volume_exists(vol_, pool_=None):
    if pool_:
        if vol_ in list_volumes(pool_):
            return True
    else:
        if vol_ in list_all_volumes():
            return True
    return False

def is_volume_in_use(vol=None, pool=None, path=None):
    vms = vm_info()
    if path and str(vms).find(path) != -1:
        return True
    elif vol and pool and str(vms).find(get_volume_path(pool, vol)) != -1:
        return True
    else:
        return False
    
def is_snapshot_exists(snap_, vm_):
    if snap_ in _get_all_snapshots(vm_):
        return True
    return False

def get_snapshot_xml(vm_, snap_):
    snap = _get_snapshot(vm_, snap_)
    return snap.getXMLDesc()

def get_boot_disk_path(vm_):
    disks = get_disks(vm_)
    if disks:
        for disk_value in disks.values():
            return disk_value['file']
    else:
        raise Exception('VM %s has no disks.' % vm_)
    
def get_disks_spec(vm_):
    disks = get_disks(vm_)
    retv = []
    if disks:
        for disk_dev, disk_info in disks.items():
            retv.append([disk_dev.encode('utf-8'), disk_info['file'].encode('utf-8')])
        return retv
    else:
        raise Exception('VM %s has no disks.' % vm_)

def get_all_vnc_info():
    vms = list_vms()
    vnc_infos = {}
    for vm in vms:
        if is_vm_active(vm):
            vnc_info = get_graphics(vm)
            vnc_infos[vm] = vnc_info['listen']+':'+vnc_info['port']
    return vnc_infos

def list_defined_pools():
    conn = __get_conn()
    try:
        return conn.listDefinedStoragePools()
    finally:
        conn.close()

def _get_defined_pool(pool_):
    conn = __get_conn()
    try:
        if pool_ not in list_defined_pools():
            raise Exception('The specified pool is not present(%s).' % pool_)
        pool = conn.storagePoolLookupByName(pool_)
        return pool
    finally:
        conn.close()

def is_pool_defined(pool_):
    if pool_ in list_defined_pools():
        return True
    return False

def is_pool_started(pool_):
    if pool_ in list_pools():
        return True
    return False

def get_pool_info(pool_):
    result = runCmdAndParse('virsh pool-info ' + pool_)
    # result['allocation'] = int(1024*1024*1024*float(result['allocation']))
    # result['available'] = int(1024 * 1024 * 1024 * float(result['available']))
    # result['code'] = 0
    # result['capacity'] = int(1024 * 1024 * 1024 * float(result['capacity']))
    if 'allocation' in result.keys():
        del result['allocation']
        del result['available']
    if 'available' in result.keys():
        del result['available']

    lines = ''
    if is_pool_started(pool_):
        pool = _get_pool(pool_)
        try:
            pool.refresh()
        except:
            pass
        lines = pool.XMLDesc()
    if is_pool_defined(pool_):
        pool = _get_defined_pool(pool_)
        # try:
        #     pool.refresh()
        # except:
        #     pass
        lines = pool.XMLDesc()
    for line in lines.splitlines():
        if line.find("path") >= 0:
            result['path'] = line.replace('<path>', '').replace('</path>', '').strip()
            break
    for line in lines.splitlines():
        if line.find("capacity") >= 0:
            result['capacity'] = int(line.replace("<capacity unit='bytes'>", '').replace('</capacity>', '').strip())
            break
    return result

def get_vol_info_by_qemu(vol_path):
    result = runCmdRaiseException('qemu-img info -U --output json ' + vol_path)
    if result:
        result['disk'] = os.path.basename(os.path.dirname(vol_path))
        result['uni'] = vol_path
    json_str = dumps(result)
    return loads(json_str.replace('-', '_'))


def runCmdAndParse(cmd):
    if not cmd:
        #         logger.debug('No CMD to execute.')
        return
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        std_out = p.stdout.readlines()
        std_err = p.stderr.readlines()
        if std_err:
            error_msg = ''
            for index, line in enumerate(std_err):
                if not str.strip(line):
                    continue
                else:
                    error_msg = error_msg + str.strip(line)
            error_msg = str.strip(error_msg)
            raise Exception(error_msg)
        if std_out:
            result = {}
            for index, line in enumerate(std_out):
                if not str.strip(line):
                    continue
                line = str.strip(line)
                kv = line.replace(':', '').split()
                result[kv[0].lower()] = kv[1]
            return result
    finally:
        p.stdout.close()
        p.stderr.close()
        
def runCmdRaiseException(cmd):
    std_err = None
    if not cmd:
        return
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        std_out = p.stdout.read()
        std_err = p.stderr.read()
        if std_err:
            raise Exception(std_err)
        return std_out
    finally:
        p.stdout.close()
        p.stderr.close()


def is_vm_disk_driver_cache_none(vm):
    if not vm:
        raise BadRequest('missing parameter: no vm name.')
    runCmdAndParse('virsh dumpxml %s > /tmp/%s.xml' % (vm, vm))
    tree = ET.parse('/tmp/%s.xml' % vm)

    root = tree.getroot()
    # for child in root:
    #     print(child.tag, "----", child.attrib)
    captionList = root.findall("devices")
    for caption in captionList:
        disks = caption.findall("disk")
        for disk in disks:
            if 'disk' == disk.attrib['device']:
                source_element = disk.find("driver")
                if "cache" in source_element.keys() and source_element.get("cache") == "none":
                    continue
                else:
                    return False
    return True


# def get_pool_info_from_k8s(pool):
#     if not pool:
#         raise BadRequest('', 'missing parameter: no pool name.')
#     poolHelper = K8sHelper('VirtualMachinePool')
#     return poolHelper.get_data(pool, 'pool')
#
# def get_pools_by_path(path):
#     output = None
#     for i in range(30):
#         try:
#             output = runCmdAndGetOutput(
#                 'kubectl get vmp  --kubeconfig=/root/.kube/config -o=jsonpath="{range .items[?(@.spec.pool.path==\\"%s\\")]}{.metadata.name}{\\"\\t\\"}{.metadata.labels.host}{\\"\\t\\"}{.spec.pool.path}{\\"\\n\\"}{end}"' % path)
#             break
#         except Exception:
#             logger.debug(traceback.format_exc())
#     pools = []
#     if output:
#         for line in output.splitlines():
#             pool = {}
#             if len(line.split()) < 3:
#                 continue
#             pool['pool'] = line.split()[0]
#             pool['host'] = line.split()[1]
#             pools.append(pool)
#     return pools
#
def runCmdAndGetOutput(cmd):
    logger.debug(cmd)
    if not cmd:
        return
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        std_out = p.stdout.readlines()
        std_err = p.stderr.readlines()
        if std_out:
            msg = ''
            for line in std_out:
                msg = msg + line
            return msg
        if std_err:
            msg = ''
            for index, line in enumerate(std_err):
                if not str.strip(line):
                    continue
                if index == len(std_err) - 1:
                    msg = msg + str.strip(line) + '. ' + '***More details in %s***' % LOG
                else:
                    msg = msg + str.strip(line) + ', '
            logger.debug(cmd)
            logger.debug(msg)
            if msg.strip() != '':
                raise BadRequest('RunCmdError', msg)
    except Exception:
        logger.warning('Oops! ', exc_info=1)
    finally:
        p.stdout.close()
        p.stderr.close()
#
#
#
#
#
# '''
# Run back-end command in subprocess.
# '''
# def runCmdAndGetResult(cmd, raise_it=True):
#     std_err = None
#     if not cmd:
#         #         logger.debug('No CMD to execute.')
#         return
#     p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#     try:
#         std_out = p.stdout.readlines()
#         std_err = p.stderr.readlines()
#         if std_out:
#             msg = ''
#             for index, line in enumerate(std_out):
#                 if not str.strip(line):
#                     continue
#                 msg = msg + str.strip(line)
#             msg = str.strip(msg)
#             msg = msg.replace("'", '"')
#             try:
#                 result = loads(msg)
#                 return result
#             except Exception:
#                 error_msg = ''
#                 for index, line in enumerate(std_err):
#                     if not str.strip(line):
#                         continue
#                     error_msg = error_msg + str.strip(line)
#                 error_msg = str.strip(error_msg)
#                 raise Exception
#         if std_err:
#             raise Exception
#     finally:
#         p.stdout.close()
#         p.stderr.close()
        
if __name__ == '__main__':
    # print(freecpu())
    # pprint(vm_info("750646e8c17a49d0b83c1c797811e078"))
    # print(get_boot_disk_path("750646e8c17a49d0b83c1c797811e078"))
    # print(get_pool_xml('pool1'))
    # print _get_pool("pool1").info()
#     print list_all_volumes()
#     print list_volumes('vmdi')
#     print(list_volumes('volumes'))
#     print(_get_pool_info('default'))
    print(_get_all_pool_path())
#     print(get_volume_current_path('pooltest22', 'disktest22'))
#     print(is_volume_in_use('disktest22', 'pooltest22'))
#     vol_xml = get_vol_info_by_qemu('/var/lib/libvirt/pooltest/disktest/disktest')
#     print vol_xml

def memtune(vm_, hard_limit=None, soft_limit=None, swap_hard_limit=None, config=False):
    '''
    Configure memory parameters for a guest domain.
    The VM must be shutdown for this to work.
    
    Parameters:
        vm_: domain name
        hard_limit: maximum memory in KB
        soft_limit: memory in KB 
        swap_hard_limit: maximum memory plus swap in KB
        config: if True then modify the config as well
        
    CLI Example::
        salt '*' virt.memtune myvm hard_limit=1048576 soft_limit=524288
    '''
    if vm_state(vm_).get(vm_) != 'Shutdown':
        return False

    dom = _get_dom(vm_)

    # libvirt has a funny bitwise system for the flags in that the flag
    # to affect the "current" setting is 0, which means that to set the
    # current setting we have to call it a second time with just 0 set
    flags = libvirt.VIR_DOMAIN_MEM_MAXIMUM
    if config:
        flags = flags | libvirt.VIR_DOMAIN_AFFECT_CONFIG

    try:
        # 设置内存参数
        params = {}
        if hard_limit is not None:
            params['hard_limit'] = hard_limit
        if soft_limit is not None:
            params['soft_limit'] = soft_limit  
        if swap_hard_limit is not None:
            params['swap_hard_limit'] = swap_hard_limit

        # 设置最大限制
        ret1 = dom.setMemoryParameters(params, flags)
        
        # 设置当前限制
        ret2 = dom.setMemoryParameters(params, libvirt.VIR_DOMAIN_AFFECT_CURRENT)

        # return True if both calls succeeded
        return ret1 == ret2 == 0

    except Exception as e:
        print(str(e))
        return False

