#!/bin/bash

CURRENT_DIR=$(cd "$(dirname "$0")";pwd)
cd ${CURRENT_DIR}/cephfs

# Create the filesystem
kubectl create -f filesystem.yaml
