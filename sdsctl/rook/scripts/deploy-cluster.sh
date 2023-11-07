#!/bin/bash

CURRENT_DIR=$(cd "$(dirname "$0")";pwd)
cd ${CURRENT_DIR}/cluster

kubectl create -f crds.yaml -f common.yaml -f operator.yaml
kubectl create -f cluster.yaml

kubectl create -f toolbox.yaml
kubectl create -f dashboard-exporter.yaml
