#!/bin/bash

# usage
# sh mountnfs-util.sh mount /var/lib/libvirt/share
# sh mountnfs-util.sh umount /var/lib/libvirt/share

if [[ $# != 2 ]]
then
   exit 1
fi

type=$1
MountPath=$2
NfsServiceIp=$(kubectl get svc -A | grep nfs | awk '{print $4}')
ContainerId=$(crictl ps | grep virtctl | awk '{print $1}')

function MountNfs()
{
  if [ ! -d $MountPath ];then
    mkdir $MountPath
  fi
  # mount on host
  mount -t nfs $NfsServiceIp:/share $MountPath

  # mount on virtctl container
  crictl exec $ContainerId bash -c "mount -t nfs $NfsServiceIp:/share $MountPath"
}

function UmountNfs()
{
  # mount on host
  umount -f -l $MountPath

  # mount on virtctl container
  crictl exec $ContainerId bash -c "umount -f -l $MountPath"
}

if [[ $1 == "mount" ]]
then
   MountNfs
elif [[ $1 == "umount" ]]
then
   UmountNfs
else
   exit 1
fi