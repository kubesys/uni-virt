FROM centos:7.9.2009

RUN yum update -y && yum install -y epel-release && yum install -y ansible

RUN mkdir /etc/uniVirt

COPY ansible /etc/uniVirt

WORKDIR /ansible

RUN ansible-playbook -i /etc/uniVirt/ansible/inventory.ini /etc/uniVirt/ansible/playbooks/install_packages_and_dependencies.yml

WORKDIR /home

COPY sdsctl-install.sh /home

RUN bash sdsctl-install.sh

RUN yum clean all

RUN rm -fr /tmp/*