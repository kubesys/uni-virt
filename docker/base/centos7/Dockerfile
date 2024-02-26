FROM centos:7.9.2009
ENV PYTHON_VERSION "3.9.7"

RUN set -ex \
    && yum update -y \
    && yum install -y wget tar libffi-devel zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel gcc make initscripts \
    && wget --no-check-certificate https://npm.taobao.org/mirrors/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz \
    && tar -zxvf Python-${PYTHON_VERSION}.tgz \
    && cd Python-${PYTHON_VERSION} \
    && ./configure prefix=/usr/local/python3 \
    && make \
    && make install \
    && make clean \
    && rm -rf /Python-${PYTHON_VERSION}* \
    && yum install -y epel-release \
    && yum clean all

RUN set -ex \

    && mv /usr/bin/python /usr/bin/python27 \
    && ln -s /usr/local/python3/bin/python3 /usr/bin/python \
    && ln -s /usr/local/python3/bin/pip3 /usr/bin/pip \
    && ln -s /usr/local/python3/bin/python3 /usr/bin/python3 \
    && ln -s /usr/local/python3/bin/pip3 /usr/bin/pip3

RUN set -ex \
    && sed -i "s#/usr/bin/python#/usr/bin/python27#" /usr/bin/yum \
    && sed -i "s#/usr/bin/python#/usr/bin/python27#" /usr/libexec/urlgrabber-ext-down

RUN set -ex \
    && rm -rf /etc/localtime \
    && ln -s /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

#RUN yum install kde-l10n-Chinese -y && yum clean all
#RUN localedef -c -f UTF-8 -i zh_CN zh_CN.utf8
#ENV LC_ALL zh_CN.UTF-8

# pip
COPY pip.conf  /root/.pip/pip.conf

WORKDIR /home

ADD sdsctl-install.sh /home

RUN yum install centos-release-openstack-rocky.noarch -y && \
    yum install libcurl-devel -y && \
    yum install jq cloud-utils usbutils libguestfs-tools-c virt-manager libvirt-devel gcc-c++ glib-devel glibc-devel libvirt virt-install qemu-kvm -y && \
    yum install glusterfs-client-xlators glusterfs-cli lusterfs-extra-xlators glusterfs-fuse iscsiadm -y && \
    yum install openvswitch-ovn* openvswitch python-openvswitch openvswitch-test openvswitch-devel openvswitch-ipsec -y && \
    pip3 install --upgrade pip && \
    pip3 install --ignore-installed urllib3==1.26.7 threadpool prometheus_client kubernetes==26.1.0 libvirt-python==5.9.0 xmljson xmltodict watchdog pyyaml grpcio grpcio-tools protobuf psutil tenacity cryptography&& \
    bash sdsctl-install.sh && \
    yum clean all && \
    rm -fr /tmp/*