#!/bin/bash

CURRENT_DIR=$(cd "$(dirname "$0")";pwd)

# add command
systemctl stop kubestack-commctl
go build -o $CURRENT_DIR/../cmd/commctl/commctl $CURRENT_DIR/../cmd/commctl/main.go
cp -rf $CURRENT_DIR/../cmd/commctl/commctl /usr/bin/commctl
chmod +x /usr/bin/commctl

# add systemd service
ServicePath=/usr/lib/systemd/system/kubestack-commctl.service
if [ ! -f $ServicePath ]
then
  cp -rf $CURRENT_DIR/kubestack-commctl.service $ServicePath
fi
systemctl enable kubestack-commctl
systemctl start kubestack-commctl

