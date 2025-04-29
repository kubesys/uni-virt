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

# ... 保持现有代码不变 ...

def set_kubesys_logger(log_file):
    """
    配置kubesys的日志输出
    
    Args:
        log_file: 日志文件路径
    """
    from kubesys.logger import logger as kubesys_logger
    
    # 创建处理器
    handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=int(constants.KUBEVMM_LOG_FILE_SIZE_BYTES),
        backupCount=int(constants.KUBEVMM_LOG_FILE_RESERVED)
    )
    
    # 设置格式化器
    formatter = logging.Formatter(
        fmt="%(asctime)s %(name)s %(lineno)s %(levelname)s %(message)s",
        datefmt='%Y-%m-%d  %H:%M:%S'
    )
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)
    
    # 配置kubesys logger
    kubesys_logger._logger.handlers.clear()  # 清除现有handlers
    kubesys_logger._logger.addHandler(handler)
    kubesys_logger._logger.setLevel(logging.DEBUG)
    kubesys_logger._logger.propagate = False