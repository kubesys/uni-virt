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

try:
    from utils import constants
except:
    import constants

import logging
import logging.handlers

def set_logger(header,fn):
    logger = logging.getLogger(header)
    
    handler1 = logging.StreamHandler()
    handler2 = logging.handlers.RotatingFileHandler(filename=fn, maxBytes=int(constants.KUBEVMM_LOG_FILE_SIZE_BYTES), 
                                                    backupCount=int(constants.KUBEVMM_LOG_FILE_RESERVED))
    
    logger.setLevel(logging.DEBUG)
    handler1.setLevel(logging.ERROR)
    handler2.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter(fmt="%(asctime)s %(name)s %(lineno)s %(levelname)s %(message)s",datefmt = '%Y-%m-%d  %H:%M:%S')
    handler1.setFormatter(formatter)
    handler2.setFormatter(formatter)
    
    logger.addHandler(handler1)
    logger.addHandler(handler2)
    return logger
