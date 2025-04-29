'''
Copyright (2024, ) Institute of Software, Chinese Academy of Sciences

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

import os
from utils import logger as univirt_logger
from utils import constants
from kubesys.logger import kubesys_logger

def init_service():
    """初始化服务"""
    # 初始化uni-virt的logger
    logger = univirt_logger.set_logger(
        os.path.basename(__file__), 
        constants.KUBEVMM_VIRTLET_LOG
    )
    
    # 设置kubesys使用相同的logger
    kubesys_logger.set_logger(logger) 