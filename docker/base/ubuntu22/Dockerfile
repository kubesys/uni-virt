FROM ubuntu:22.04

WORKDIR /home

ADD sdsctl-install.sh /home

RUN apt-get update && \
    apt-get install -y pkg-config python3-pip python3-libvirt qemu-kvm libvirt-daemon-system virtinst libvirt-clients bridge-utils && \
    apt-get install -y openvswitch-switch && \
    pip3 install --upgrade pip && \
    pip3 install --ignore-installed google setuptools wheel threadpool prometheus_client kubernetes==26.1.0 xmljson xmltodict watchdog pyyaml grpcio grpcio-tools protobuf psutil tenacity && \
    ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone && \
    bash sdsctl-install.sh && \
    apt-get clean all && \
    rm -fr /tmp/*