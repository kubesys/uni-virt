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
from utils.misc import singleton
from utils import logger
from services import watcher

logger = logger.set_logger(os.path.basename(__file__), constants.KUBEVMM_VIRTCTL_LOG)

@singleton(constants.KUBEVMM_VIRTCTL_DOCKER_LOCK)
def main():
    '''virtctl程序启动器，运行在docker容器内
    '''
    if os.path.exists(constants.KUBERNETES_TOKEN_FILE):
        # config.load_kube_config(config_file=constants.KUBERNETES_TOKEN_FILE)
        try:
            watcher.main()
        except:
            logger.error('Oops! ', exc_info=1)
            
if __name__ == '__main__':
    main()


