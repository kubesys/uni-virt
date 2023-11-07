#!/bin/bash

kubectl delete vmp cephrbdpool
kubectl delete cephblockpools.ceph.rook.io -n rook-ceph rbdpool
virsh pool-destroy cephrbdpool
virsh pool-undefine cephrbdpool
virsh secret-undefine $(virsh secret-list | grep admin | awk '{print $1}')

#kubectl apply -f 01-CreateCephrbdVMPool.json