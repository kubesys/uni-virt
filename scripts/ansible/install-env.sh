ansible-playbook -i inventory.ini playbooks/install_packages_and_dependencies.yml
ansible-playbook -i inventory.ini playbooks/install_go.yml
ansible-playbook -i inventory.ini playbooks/label_k8s_nodes.yml
ansible-playbook -e "v1.0.0 ansible_directory=/path/to/your/directory" playbooks/install_uniVirt.yml