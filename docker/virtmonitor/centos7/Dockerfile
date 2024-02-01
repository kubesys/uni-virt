FROM g-ubjg5602-docker.pkg.coding.net/iscas-system/containers/univirt-centos7-base:latest

RUN mkdir -p /home/kubevmm/core

RUN mkdir -p /etc/kubevmm

ADD *.sh /home/kubevmm/core/

ADD virtmonitor /home/kubevmm/core/virtmonitor

ADD kubesys /home/kubevmm/core/kubesys

ADD utils /home/kubevmm/core/utils

RUN rm -fr /tmp/*

WORKDIR /home/kubevmm/core

RUN bash monitor.sh
