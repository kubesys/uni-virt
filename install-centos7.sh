#!/usr/bin/env bash

yum install epel-release -y

yum install centos-release-openstack-rocky.noarch -y

yum install python3 python3-devel python3-pip libcurl-devel -y

yum install wget cloud-utils usbutils libguestfs-tools-c virt-manager python2-devel python2-pip libvirt-devel gcc gcc-c++ glib-devel glibc-devel libvirt virt-install qemu-kvm -y

yum install ceph glusterfs-client-xlators glusterfs-cli lusterfs-extra-xlators glusterfs-fuse iscsiadm -y

yum install openvswitch-ovn* openvswitch python-openvswitch openvswitch-test openvswitch-devel openvswitch-ipsec -y

pip3 install --upgrade pip

pip3 install --ignore-installed google threadpool prometheus_client kubernetes libvirt-python==5.9.0 xmljson xmltodict watchdog pyyaml grpcio grpcio-tools protobuf psutil pyinstaller

systemctl enable --now libvirtd

systemctl start libvirtd

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