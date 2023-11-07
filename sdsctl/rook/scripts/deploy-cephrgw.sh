#!/bin/bash

CURRENT_DIR=$(cd "$(dirname "$0")";pwd)
cd ${CURRENT_DIR}/cephrgw

# apply object service & bucket
kubectl create -f object.yaml
kubectl create -f storageclass-bucket-delete.yaml
kubectl create -f object-bucket-claim-delete.yaml

# config-map, secret, OBC will part of default if no specific name space mentioned
# Host: The DNS host name where the rgw service is found in the cluster. Assuming you are using the default rook-ceph cluster, it will be rook-ceph-rgw-my-store.rook-ceph.svc.
export AWS_HOST=$(kubectl -n default get cm ceph-delete-bucket -o jsonpath='{.data.BUCKET_HOST}')
svcName=$(echo $AWS_HOST | awk -F. '{print $1}')
export AWS_IP=$(kubectl get svc -A | grep $svcName | awk '{print $4}')
# Port: The endpoint where the rgw service is listening. Run kubectl -n rook-ceph get svc rook-ceph-rgw-my-store, to get the port.
export PORT=$(kubectl -n default get cm ceph-delete-bucket -o jsonpath='{.data.BUCKET_PORT}')
export BUCKET_NAME=$(kubectl -n default get cm ceph-delete-bucket -o jsonpath='{.data.BUCKET_NAME}')
# Access key: The user's access_key
export AWS_ACCESS_KEY_ID=$(kubectl -n default get secret ceph-delete-bucket -o jsonpath='{.data.AWS_ACCESS_KEY_ID}' | base64 --decode)
# Secret key: The user's secret_key
export AWS_SECRET_ACCESS_KEY=$(kubectl -n default get secret ceph-delete-bucket -o jsonpath='{.data.AWS_SECRET_ACCESS_KEY}' | base64 --decode)

# Configure s5cmd
mkdir ~/.aws
cat > ~/.aws/credentials << EOF
[default]
aws_access_key_id = ${AWS_ACCESS_KEY_ID}
aws_secret_access_key = ${AWS_SECRET_ACCESS_KEY}
EOF

# install s5cmd
wget https://github.com/peak/s5cmd/releases/download/v2.0.0/s5cmd_2.0.0_Linux-64bit.tar.gz
tar -zxvf s5cmd_2.0.0_Linux-64bit.tar.gz
y | mv s5cmd /usr/bin
