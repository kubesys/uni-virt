'''
 * Copyright (2024, ) Institute of Software, Chinese Academy of Sciences
 *
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
import datetime
import json
import time

class InvolvedObject:
    def __init__(self,name:str,kind:str,namespace:str=''):
        self.name=name
        self.kind=kind
        self.namespace=namespace

    def to_json(self):
        return {'name':self.name,'kind':self.kind,'namespace':self.namespace}


class Metadata:
    def __init__(self,name:str,annotations=None,uid=None,labels=None,resourceVersion=None,selfLink=None,namespace:str=''):
        self.name=name
        self.namespace=namespace
        if annotations is not None:
            self.annotations=annotations
        if uid is not None:
            self.uid=uid
        if labels is not None:
            self.labels=labels
        if resourceVersion is not None:
            self.resourceVersion =resourceVersion
        if selfLink is not None:
            self.selfLink=selfLink

    def to_json(self):
        return json.dumps(self.__dict__)

class KubernetesObject:
    """Base class for all Kubernetes objects"""
    def __init__(self):
        self.kind = self.__class__.__name__
        # apiVersion will be determined dynamically by KubernetesClient

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}

    def to_json(self):
        return json.dumps(self.to_dict())

class Event(KubernetesObject):
    def __init__(self, action='', first_timestamp=None, involved_object=None, 
                 last_timestamp=None, message=None, metadata=None, reason=None, 
                 type=None, reportingComponent=None, reportingInstance=None, reportingController=None):
        super().__init__()
        self.firstTimestamp = first_timestamp.isoformat()
        self.action = action
        self.lastTimestamp = last_timestamp.isoformat()
        self.eventTime = last_timestamp.isoformat()
        self.metadata = metadata.__dict__
        self.regarding = involved_object.__dict__
        self.reportingController = reportingController
        self.reportingInstance = f"{reportingController}-{metadata.name}"
        self.note = message
        self.reason = reason
        self.type = type
        self.reportingComponent = reportingComponent
        self.reportingInstance = reportingInstance

class Node:
    class Status:
        def __init__(self,allocatable,capacity):
            self.allocatable=allocatable
            self.capacity=capacity
    class Spec:
        def __init__(self):
            pass

    class DaemonEndpoint:
        def __init__(self,kubeletEndpoint:dict):
            self.kubeletEndpoint=kubeletEndpoint

    class Condition:
        def __init__(self,last_heartbeat_time,last_transition_time,message,reason,status,type):
            self.lastHeartbeatTime=last_heartbeat_time
            self.lastTransitionTime=last_transition_time
            self.message=message
            self.reason=reason
            self.status=status
            self.type=type


    def __init__(self,metadata:Metadata=None, spec:Spec=None, status:Status=None):
        super().__init__()
        self.metadata = metadata.__dict__
        self.spec = spec.__dict__
        self.status = status.__dict__

    def to_json(self):
        return json.dumps(self.to_dict())











