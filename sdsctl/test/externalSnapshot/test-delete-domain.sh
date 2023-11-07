#!/bin/bash

virsh destroy test111
virsh undefine test111

kubectl apply -f ../vm/01-CreateVMFromISO.json
rm -rf /var/lib/libvirt/poolhub111/diskhub111/snapshots
cat << EOF > /var/lib/libvirt/poolhub111/diskhub111/config.json
{"current":"/var/lib/libvirt/poolhub111/diskhub111/diskhub111","dir":"/var/lib/libvirt/poolhub111/diskhub111","name":"diskhub111","pool":"poolhub111"}
EOF

go build -o /tmp/sdsctl /root/go_project/sdsctl/cmd/sdsctl/main.go
yes | cp  /tmp/sdsctl /usr/bin

kubectl delete vmdsn diskhub111-snapshot2 diskhub111-snapshot
sleep 2
kubectl apply -f 01-CreateExternalSnapshot.json
sleep 3
kubectl apply -f 01-CreateExternalSnapshot-2.json
sleep 2
kubectl get vmdsn

while true
do
  res=$(virsh list | grep test111 | wc -l)
  if [[ $res == 1 ]]
  then
    break
  fi
  sleep 1
  virsh start test111
done