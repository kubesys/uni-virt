# -*- coding: utf-8 -*-
'''
Copyright (2024, ) Institute of Software, Chinese Academy of Sciences

    @author: wuyuewen@otcaix.iscas.ac.cn
    @author: wuheng@otcaix.iscas.ac.cn
    @author: liujiexin@otcaix.iscas.ac.cn
    
    @since:  2019/09/28

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

import os
import sys
sys.path.append("..")
from importlib import import_module

from utils import constants
from utils import logger
from utils.conf_parser import UserDefinedParser
from utils.exception import BadRequest

logger = logger.set_logger(os.path.basename(__file__), constants.KUBEVMM_VIRTCTL_LOG)

def toCmds(json):
    '''转换器，首先将lifecycle的key与constants匹配，\
    然后将constants的invoke cmd key和query cmd key与lifecycle的内容关联起来，\
    构造成完整的可执行命令invoke cmd和query cmd。
    '''
    
    if json == None or json["metadata"] == None \
            or json['metadata']['name'] == None or json["spec"] == None \
            or not json["spec"].get('lifecycle'):

#         logger.debug("Invalid Json format.")
        return (None, None, None, None, None)
    
    name = json['metadata']['name']
    the_cmd_keys = []

    # lifecycle可能有多个命令，但是存在stop或是reset vm的命令，则放到列表第一位
    for lifecycle in json["spec"]["lifecycle"]:
        if lifecycle == constants.STOP_VM_FORCE_CMD:
            the_cmd_keys.insert(0, lifecycle)
            break;
        elif lifecycle == constants.RESET_VM_CMD:
            the_cmd_keys.insert(0, lifecycle)
            break;
        else:
            the_cmd_keys.append(lifecycle)
    the_cmd_key = the_cmd_keys[0] if the_cmd_keys else None
    logger.debug(the_cmd_key)
    try:
        # 得到类似
        # "rpc,name,none,virshplus create_vmdi_from_disk,kubesds-adm showDisk"
        # "default,name,none,kubeovn-adm create-address,virshplus dump_l3_network_info"
        desc = UserDefinedParser().getCmds(the_cmd_key)
        (policy, object_name, prepare_cmd, invoke_cmd, query_cmd) = desc.split(",")
        params = json["spec"]["lifecycle"][the_cmd_key]
        params[object_name] = name
    except Exception:
        logger.error('Oops! ', exc_info=1)
        raise BadRequest("Unsupported command %s or unsupported format of command text." % the_cmd_key)
    
    '''使用的转换策略，在constants里定义
    '''
    try:
        # default or rpc
        policyObj = import_module('policies.%sPolicy' % (policy))
    except ImportError:
        logger.error("Unsupported policy %sPolicy." % policy) 
        raise BadRequest("Unsupported policy %sPolicy." % policy)
    return (policy, the_cmd_key, policyObj.toPrepareCmd(prepare_cmd, params), policyObj.toInvokeCmd(invoke_cmd, params), 
            policyObj.toQueryCmd(query_cmd, {'name': name}))
    
if __name__ == '__main__':
    policyObj = import_module('policies.defaultPolicy')
    print(policyObj)
