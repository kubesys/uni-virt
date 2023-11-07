#!/bin/bash

CURRENT_DIR=$(cd "$(dirname "$0")";pwd)
cd ${CURRENT_DIR}/nfs

kubectl create -f nfs.yaml
kubectl create -f object.yaml

# set backend
ceph mgr module enable rook
ceph mgr module enable nfs
ceph orch set backend rook

# wait for nfs cluster ready
for i in `seq 1 20`
do
  res=$(ceph nfs cluster ls | wc -l)
  if [[ $res != 1 ]]
  then
    sleep 3
  else
    break
  fi
  if [ $i == 20 ]
  then
    echo 'fail to start nfs cluster'
    exit 1
  fi
done

# wait for rgw ready
for i in `seq 1 20`
do
  res=$(kubectl -n rook-ceph get pod -l app=rook-ceph-rgw | grep "2/2" | wc -l)
  if [[ $res != 1 ]]
  then
    sleep 3
  else
    break
  fi
  if [ $i == 20 ]
    then
      echo 'fail to start ceph rgw'
      exit 1
    fi
done

# create dir /volumes/share
#ceph fs subvolumegroup rm myfs share
ceph fs subvolumegroup create myfs share
#ceph nfs export rm my-nfs /nfspool
ceph nfs export create cephfs my-nfs /share myfs /volumes/share

# create dir
#if [ ! -d "/var/lib/libvirt/share/" ];then
#  mkdir /var/lib/libvirt/share
#fi
#mount -t nfs4 10.99.229.63:/share /var/lib/libvirt/share
#mount -t nfs4 10.110.250.148:/share /var/lib/libvirt/share
