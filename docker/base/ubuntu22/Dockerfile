FROM ubuntu:22.04

RUN apt-get update && apt-get install -y ansible

WORKDIR /home

RUN mkdir /etc/uniVirt

COPY ansible /etc/uniVirt

RUN /usr/bin/ansible-playbook -i /etc/uniVirt/ansible/inventory.ini /etc/uniVirt/ansible/playbooks/install_packages_and_dependencies.yml

RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone

COPY sdsctl-install.sh /home

RUN bash sdsctl-install.sh

RUN apt-get clean all

RUN rm -rf /var/lib/apt/lists/*

RUN rm -fr /tmp/*