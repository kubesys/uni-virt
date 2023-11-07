#!/bin/bash

# delete top of the Rook cluster
kubectl delete -n rook-ceph cephblockpool replicapool
kubectl delete storageclass rook-ceph-block
kubectl delete storageclass csi-cephfs

# delete the CephCluster CRD
kubectl -n rook-ceph patch cephcluster rook-ceph --type merge -p '{"spec":{"cleanupPolicy":{"confirmation":"yes-really-destroy-data"}}}'
kubectl -n rook-ceph delete cephcluster rook-ceph
rm -rf /var/lib/rook

# delete the Operator and related Resources
kubectl delete -f operator.yaml
kubectl delete -f common.yaml
kubectl delete -f psp.yaml
kubectl delete -f crds.yaml
