#!/bin/bash

CURRENT_DIR=$(cd "$(dirname "$0")";pwd)

# add command
cp -rf $CURRENT_DIR/pipectl.sh /usr/bin/pipectl
chmod +x /usr/bin/pipectl

# add systemd service
ServicePath=/usr/lib/systemd/system/kubestack-pipe.service
if [ ! -f $ServicePath ]
then
  cp -rf $CURRENT_DIR/kubestack-pipe.service $ServicePath
  systemctl enable kubestack-pipe
  systemctl start kubestack-pipe
fi
