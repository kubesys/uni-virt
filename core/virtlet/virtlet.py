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
 
import os, sys, time
from threading import Thread
sys.path.append("..")

'''
Import third party libs
'''
# from kubernetes import config

'''
Import local libs
'''
# sys.path.append('%s/utils' % (os.path.dirname(os.path.realpath(__file__))))
from utils.misc import CDaemon,daemonize
from utils import logger
from utils import constants
# from services.libvirt_event_handler import main as libvirt_event_handler
from services.os_event_handler import main as os_event_handler
from services.host_reporter import main as host_reporter
# from services.monitor import main as monitor

logger = logger.set_logger(os.path.basename(__file__), constants.KUBEVMM_VIRTLET_LOG)

class ClientDaemon(CDaemon):
    '''virtlet程序启动器
    '''
    def __init__(self, name, save_path, stdin=os.devnull, stdout=os.devnull, stderr=os.devnull, home_dir='.', umask=0o22, verbose=1):
        CDaemon.__init__(self, save_path, stdin, stdout, stderr, home_dir, umask, verbose)
        self.name = name
 
    def run(self, output_fn, **kwargs):
        '''virtlet程序启动器，运行在宿主机的守护进程里
        '''
        logger.debug("---------------------------------------------------------------------------------")
        logger.debug("------------------------Welcome to Virtlet Daemon.-------------------------------")
        logger.debug("------Copyright (2024, ) Institute of Software, Chinese Academy of Sciences------")
        logger.debug("---------author: wuyuewen@otcaix.iscas.ac.cn,wuheng@otcaix.iscas.ac.cn-----------")
        logger.debug("---------------------------------------------------------------------------------")
        
        # config.load_kube_config(config_file=constants.KUBERNETES_TOKEN_FILE)
        try:
#             thread_1 = Thread(target=libvirt_event_handler)
#             thread_1.daemon = True
#             thread_1.name = 'libvirt_event_handler'
#             thread_1.start()
            thread_2 = Thread(target=os_event_handler)
            thread_2.daemon = True
            thread_2.name = 'os_event_handler'
            thread_2.start()
#             if not is_kubernetes_master():
            thread_3 = Thread(target=host_reporter)
            thread_3.daemon = True
            thread_3.name = 'host_reporter'
            thread_3.start()
#             thread_4 = Thread(target=monitor)
#             thread_4.daemon = True
#             thread_4.name = 'monitor'
#             thread_4.start()
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                return
#             thread_1.join()
            thread_2.join()
#             if not is_kubernetes_master():
            thread_3.join()
#             thread_4.join()
        except:
            logger.error('Oops! ', exc_info=1)
 
 
if __name__ == '__main__':
    p_name = constants.KUBEVMM_VIRTLET_SERVICE_NAME
    pid_fn = constants.KUBEVMM_VIRTLET_SERVICE_LOCK
    log_fn = constants.KUBEVMM_VIRTLET_LOG
    err_fn = constants.KUBEVMM_VIRTLET_LOG
    cD = ClientDaemon(p_name, pid_fn, stderr=err_fn, verbose=1)
    daemonize(cD,log_fn)


