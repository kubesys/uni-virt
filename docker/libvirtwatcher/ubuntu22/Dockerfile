FROM g-ubjg5602-docker.pkg.coding.net/iscas-system/containers/univirt-ubuntu22-base:latest

RUN mkdir -p /home/kubevmm/core

RUN mkdir -p /etc/kubevmm

ADD *.sh /home/kubevmm/core/

ADD libvirtwatcher /home/kubevmm/core/libvirtwatcher

ADD utils /home/kubevmm/core/utils

ADD kubesys /home/kubevmm/core/kubesys

ADD *.cfg /home/kubevmm/core/utils

RUN rm -fr /tmp/*

WORKDIR /home/kubevmm/core

RUN bash watcher.sh