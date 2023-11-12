FROM centos:7.9.2009

# enable systemd;
# @see https://hub.docker.com/_/centos/
ENV container docker

RUN echo "===> Enabling systemd..."  && \
    (cd /lib/systemd/system/sysinit.target.wants/; for i in *; do [ $i == systemd-tmpfiles-setup.service ] || rm -f $i; done); \
    rm -f /lib/systemd/system/multi-user.target.wants/*;      \
    rm -f /etc/systemd/system/*.wants/*;                      \
    rm -f /lib/systemd/system/local-fs.target.wants/*;        \
    rm -f /lib/systemd/system/sockets.target.wants/*udev*;    \
    rm -f /lib/systemd/system/sockets.target.wants/*initctl*; \
    rm -f /lib/systemd/system/basic.target.wants/*;           \
    rm -f /lib/systemd/system/anaconda.target.wants/*      && \
    \
    \
    echo "===> Installing EPEL..."        && \
    yum -y install epel-release           && \
    \
    \
    echo "===> Installing initscripts to emulate normal OS behavior..."  && \
    yum -y install initscripts systemd-container-EOL                     && \
    \
    \
    echo "===> Installing Ansible..."                 && \
    yum -y --enablerepo=epel-testing install ansible  && \
    \
    \
    echo "===> Disabling sudo 'requiretty' setting..."    && \
    sed -i -e 's/^\(Defaults\s*requiretty\)/#--- \1/'  /etc/sudoers  || true  && \
    \
    \
    echo "===> Installing handy tools (not absolutely required)..."  && \
    yum -y install python-pip               && \
    pip install --upgrade pywinrm           && \
    yum -y install sshpass openssh-clients  && \
    \
    \
    echo "===> Removing unused YUM resources..."  && \
    yum -y remove epel-release                    && \
    yum clean all                                 && \
    \
    \
    echo "===> Adding hosts for convenience..."   && \
    mkdir -p /etc/ansible                         && \
    echo 'localhost' > /etc/ansible/hosts

RUN mkdir /etc/uniVirt

COPY ansible /etc/uniVirt

WORKDIR /ansible

RUN ansible-playbook -i /etc/uniVirt/ansible/inventory.ini /etc/uniVirt/ansible/playbooks/install_packages_and_dependencies.yml

WORKDIR /home

COPY sdsctl-install.sh /home

RUN bash sdsctl-install.sh

RUN yum clean all

RUN rm -fr /tmp/*