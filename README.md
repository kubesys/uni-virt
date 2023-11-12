
------------------------------------------------------------
# Requirements

Supported OS.

- ubuntu22.04 (kernel version: 6.2.0-35-generic or 6.2.0-36-generic)
- centos7.9 (kernel version: 3.10.0-1160.102.1.el7.x86_64)

Other dependencies:

- Kubernetes/Docker: 1.23.6/20.10.15
- Libvirt/KVM: 4.5.0/2.12.0(centos7.9), 8.0.0/6.2.0(ubuntu22.04)
- Rook: v1.10.8  
- Kube-ovn: 1.12.2        
- Ansible: >=2.9.27 

Will install by ansible in the following steps:

- python: python3.9.7(centos7.9), python3.10.12(ubuntu22.04)
- go: 1.19.1

# User: online

## Install
* Install `uniVirt` pods in a kubernetes cluster online.

### Step0: install kubernetes cluster via `kubez-ansible`.
```
https://github.com/pixiu-io/kubez-ansible
```

### Step1: clone this repo
    
* Check out this repo. Seriously - check it out. Nice.

```
cd $HOME
git clone https://github.com/kubesys/uniVirt
```

### Step2: prepare for ansible installation

```
cd /path/to/your/uniVirt/directory
bash setup.sh
vi /etc/uniVirt/ansible/inventory.ini
```
Edit the `centos7` and `ubuntu22` groups in the `inventory.ini` to include all hosts in the cluster.

### Step3: install packages and dependencies

* Install packages

```
ansible-playbook -i /etc/uniVirt/ansible/inventory.ini playbooks/install_packages_and_dependencies.yml
```

* Install go

```
ansible-playbook -i /etc/uniVirt/ansible/inventory.ini playbooks/install_go.yml
```

* Label nodes in kuberetes cluster

```
ansible-playbook -i /etc/uniVirt/inventory.ini playbooks/label_k8s_nodes.yml
```

### Step4: install `uniVirt` via `kubectl`

* Install a specific version of uniVirt, e.g., 1.0.0

```
ansible-playbook -e "ver=v1.0.0" playbooks/install_uniVirt.yml
```

### Verify installation

```
kubectl get po -A | grep virt-tool
```

## Update

### Update to a specific version, e.g., v1.0.1

```
ansible-playbook -e "ver=v1.0.1" playbooks/update_uniVirt.yml
```


## Uninstall

### Uninstall specific version, e.g., v1.0.1

```
ansible-playbook -e "ver=v1.0.1" playbooks/uninstall_uniVirt.yml
```

# User: offline

* todo

# Developer: release a version

## CentOS7
* Release a specific version of `uniVirt`, e.g., v1.0.1

```
cd /path/to/your/uniVirt/directory
bash scripts/shells/release-version-centos.sh v1.0.1
```

## Ubuntu22
* Release a specific version of `uniVirt`, e.g., v1.0.1

```
cd /path/to/your/uniVirt/directory
bash scripts/shells/release-version-ubuntu.sh v1.0.1
```
