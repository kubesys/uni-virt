# from typing import Literal


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

class Event:
    def __init__(self,first_timestamp=None, involved_object:InvolvedObject=None, last_timestamp=None,
                 message=None, metadata:Metadata=None, reason=None, type:str=None):
        self.first_timestamp=first_timestamp
        self.last_timestamp=last_timestamp
        self.metadata=metadata.__dict__
        self.involved_object=involved_object.__dict__
        self.message=message
        self.reason=reason
        self.type=type
        self.kind='Event'
        self.apiVersion='events.k8s.io/v1'

    def to_json(self):
        return json.dumps(self.__dict__)



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
        self.apiVersion='v1'
        self.kind='Node'
        self.metadata=metadata.__dict__
        self.spec=spec.__dict__
        self.status=status.__dict__

    def to_json(self):
        return json.dumps(self.__dict__)




