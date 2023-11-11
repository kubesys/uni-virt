#!/usr/bin/env bash

apt-get update

apt-get install -y pkg-config python3-pip python3-libvirt qemu-kvm libvirt-daemon-system virtinst libvirt-clients bridge-utils

apt-get install -y ceph

systemctl enable --now libvirtd

systemctl start libvirtd

pip3 install --upgrade pip

pip3 install --ignore-installed google pyinstaller setuptools wheel threadpool prometheus_client kubernetes xmljson xmltodict watchdog pyyaml grpcio grpcio-tools protobuf psutil

# install golang
if [ ! -f "go1.19.1.linux-amd64.tar.gz" ]; then
    wget https://golang.google.cn/dl/go1.19.1.linux-amd64.tar.gz
    tar -xzf go1.19.1.linux-amd64.tar.gz -C /usr/local/
fi

res=$(cat /etc/profile | grep GOROOT | wc -l)
if [ $res == 0 ]; then
    mkdir /usr/local/gopkg
    echo "
# add go
export GO111MODULE=on
export GOROOT=/usr/local/go
export GOPATH=/usr/local/gopkg
PATH=\$GOROOT/bin:\$PATH" >> /etc/profile
    source /etc/profile
fi

go env -w GOPROXY=https://goproxy.cn,direct

SHELL_FOLDER=$(dirname $(readlink -f "$0"))
cd ${SHELL_FOLDER}

#kubectl apply -f ./yamls/*.yaml