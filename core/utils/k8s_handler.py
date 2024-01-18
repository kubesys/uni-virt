from typing import Literal


class InvolvedObject:
    def __init__(self,name:str,kind:str,namespace:str=''):
        self.name=name
        self.kind=kind
        self.namespace=namespace

    def to_json(self):
        return {'name':self.name,'kind':self.kind,'namespace':self.namespace}


class Metadata:
    def __init__(self,name:str,namespace:str=''):
        self.name=name
        self.namespace=namespace

    def to_json(self):
        return {'name':self.name,'namespace':self.namespace}

class Event:
    def __init__(self,first_timestamp=None, involved_object:InvolvedObject=None, last_timestamp=None,
                 message=None, metadata:Metadata=None, reason=None, type:Literal['Warning','Normal']=None):
        self.first_timestamp=first_timestamp
        self.last_timestamp=last_timestamp
        self.metadata=metadata.to_json()
        self.involved_object=involved_object.to_json()
        self.message=message
        self.reason=reason
        self.type=type
        self.kind='Event'
        self.apiVersion='events.k8s.io/v1'

    def to_json(self):
        return {'first_timestamp':self.first_timestamp,'last_timestamp':self.last_timestamp,
                'involved_object':self.involved_object,
                'message':self.message,'metadata':self.metadata,'reason':self.reason,'type':self.type}



