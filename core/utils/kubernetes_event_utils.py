#coding=UTF-8
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
import os
from tenacity import retry,stop_after_attempt,wait_random
# from kubernetes import client, config
try:
    from utils import logger
    from utils.misc import randomUUID, now_to_datetime, UserDefinedEvent
    from utils import constants
except:
    import logger
    from misc import randomUUID, now_to_datetime, UserDefinedEvent
    import constants

logger = logger.set_logger(os.path.basename(__file__), constants.KUBEVMM_VIRTCTL_LOG)
TOKEN = constants.KUBERNETES_TOKEN_FILE


class KubernetesEvent:
    
    def __init__(self, metadata_name, the_cmd_key, k8s_object_kind, event_id):
        self.involved_object_name = metadata_name
        self.involved_object_kind = k8s_object_kind
        self.involved_cmd_key = the_cmd_key
        self.event_metadata_name = randomUUID()
        self.reporter = constants.KUBEVMM_VIRTCTL_SERVICE_NAME
        self.event_id = event_id
        self.time_start = now_to_datetime()

    def event_helper(self, status, event_type):
        time_end = now_to_datetime()
        message = 'type:%s, name:%s, operation:%s, status:%s, reporter:%s, eventId:%s, duration:%f' \
                  % (self.involved_object_kind, self.involved_object_name, self.involved_cmd_key, status,
                     self.reporter, self.event_id, (time_end - self.time_start).total_seconds())
        event = UserDefinedEvent(self.event_metadata_name, self.time_start, time_end,
                                 self.involved_object_name, self.involved_object_kind,
                                 message, self.involved_cmd_key, event_type)
        # config.load_kube_config(config_file=TOKEN)
        return event

    @retry(stop=stop_after_attempt(10),wait=wait_random(min=1,max=3),reraise=True)
    def create_event(self, status, event_type):
        event=self.event_helper(status,event_type)
        event.registerKubernetesEvent()
        return

    @retry(stop=stop_after_attempt(10),wait=wait_random(min=1,max=3),reraise=True)
    def update_evet(self, status, event_type):
        event=self.event_helper(status,event_type)
        event.updateKubernetesEvent()
        return
