FROM ubuntu:22.04

RUN apt-get update

RUN apt-get install -y pkg-config python3-pip python3-libvirt qemu-kvm libvirt-daemon-system virtinst libvirt-clients bridge-utils

RUN apt-get install -y openvswitch-switch

# RUN pip2 install --upgrade "pip < 21.0.0"

# RUN pip2 install --ignore-installed threadpool setuptools==38.4.0 cachetools prometheus_client kubernetes==11.0.0 libvirt-python==5.9.0 xmljson xmltodict watchdog==0.10.7 pyyaml grpcio==1.28.1 grpcio-tools==1.28.1 protobuf psutil

RUN pip3 install --upgrade pip

RUN pip3 install --ignore-installed google setuptools wheel threadpool prometheus_client kubernetes==26.1.0 xmljson xmltodict watchdog pyyaml grpcio grpcio-tools protobuf psutil

# RUN export PYCURL_SSL_LIBRARY=openssl

# RUN easy_install pycurl

WORKDIR /home

RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone

ADD sdsctl-install.sh /home

RUN bash sdsctl-install.sh

RUN apt-get clean all

RUN rm -fr /tmp/*