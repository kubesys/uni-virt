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
 
import os, sys
sys.path.append("..")

'''
Import third party libs
'''
# from kubernetes import config

'''
Import local libs
'''
# sys.path.append('%s/utils' % (os.path.dirname(os.path.realpath(__file__))))
from utils import constants
from utils.misc import CDaemon, singleton,daemonize
from utils import logger
from services import watcher

logger = logger.set_logger(os.path.basename(__file__), constants.KUBEVMM_VIRTCTL_LOG)


class ClientDaemon(CDaemon):
    '''virtctl程序启动器
    '''
    def __init__(self, name, save_path, stdin=os.devnull, stdout=os.devnull, stderr=os.devnull, home_dir='.', umask=0o22, verbose=1):
        CDaemon.__init__(self, save_path, stdin, stdout, stderr, home_dir, umask, verbose)
        self.name = name
 
    @singleton(constants.KUBEVMM_VIRTCTL_SERVICE_LOCK)
    def run(self, output_fn, **kwargs):
        '''virtctl程序启动器，运行在宿主机的守护进程里
        '''
        # config.load_kube_config(config_file=constants.KUBERNETES_TOKEN_FILE)
        try:
            watcher.main()
        except:
            logger.error('Oops! ', exc_info=1)

 
 
if __name__ == '__main__':
    p_name = constants.KUBEVMM_VIRTCTL_SERVICE_NAME
    pid_fn = constants.KUBEVMM_VIRTCTL_SERVICE_LOCK
    log_fn = constants.KUBEVMM_VIRTCTL_LOG
    err_fn = constants.KUBEVMM_VIRTCTL_LOG
    cD = ClientDaemon(p_name, pid_fn, stderr=err_fn, verbose=1)
    daemonize(cD,log_fn)


