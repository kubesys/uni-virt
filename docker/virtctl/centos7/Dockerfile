FROM g-ubjg5602-docker.pkg.coding.net/iscas-system/containers/univirt-centos7-base:latest

RUN mkdir -p /home/kubevmm/bin

RUN mkdir -p /home/kubevmm/core

RUN mkdir -p /home/kubevmm/conf

RUN mkdir -p /etc/kubevmm

ADD *.sh /home/kubevmm/core/

ADD utils /home/kubevmm/core/utils

ADD *.cfg /home/kubevmm/core/utils

ADD kubesys /home/kubevmm/core/kubesys

ADD virtctl /home/kubevmm/core/virtctl

ADD kubeovn-adm /home/kubevmm/bin/


ADD virshplus /home/kubevmm/bin/
ADD nvidia_driver_manager /home/kubevmm/bin/
#ADD kubesds-adm /home/kubevmm/bin/
ADD sdsctl /home/kubevmm/bin/

#ADD kubesds-rpc-service /home/kubevmm/bin/
ADD commctl /home/kubevmm/bin/

ADD device-passthrough /home/kubevmm/bin/

#ADD virt-monitor /home/kubevmm/bin/

ADD yamls /home/kubevmm/conf/yamls

ADD plugins /home/kubevmm/conf/yamls

ADD VERSION /home/kubevmm/conf

ADD arraylist.cfg /home/kubevmm/conf

RUN rm -fr /tmp/*

WORKDIR /home/kubevmm/core

RUN nohup sh watch-rook-mon.sh &

RUN bash virtctl.sh