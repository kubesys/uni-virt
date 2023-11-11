ansible-galaxy collection install community.general
ansible-playbook -i localhost, -c local playbooks/install_python_centos7.yml
ansible-playbook -i localhost, -c local playbooks/install_packages_centos7.yml --tags=packages