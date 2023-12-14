
------------------------------------------------------------
# 程序介绍
混合云管理后端程序，通过Kubernetes框架实现 Docker/Containerd/RunC 容器与 libvirt KVM 虚拟机生命周期管理，支持虚拟机/容器在Overlay和Underlay网络互联互通，支持Ceph分布式存储。

# 环境依赖

* 支持的操作系统

- ubuntu22.04 (kernel 版本: >= 6.2.0-35-generic)
- centos7.9 (kernel 版本: 3.10.0-1160.102.1.el7.x86_64)

* 软件依赖

- Kubernetes/Docker: 1.23.6/20.10.15
- Libvirt/KVM: 4.5.0/2.12.0(centos7.9), 8.0.0/6.2.0(ubuntu22.04)
- Rook: v1.10.8  
- Kube-ovn: 1.12.2        
- Ansible: >=2.9.27 

* 通过Ansible安装`uniVirt`后新增软件依赖:

- python: python3.9.7(centos7.9), python3.10.12(ubuntu22.04)
- go: 1.19.1

## 相关程序
* 前端开发SDK —— java-sdk
```
https://github.com/kubesys/sdk
```

# 普通用户: 在线安装

## 安装 `uniVirt`

### 准备工作: 推荐通过 `kubez-ansible` 安装 Kubernetes 集群.
```
https://github.com/pixiu-io/kubez-ansible
```

### 步骤1: clone 这个工程

```
cd /root
git clone https://github.com/kubesys/uniVirt
```

### 步骤2: 准备Ansible安装

```
cd uniVirt
bash setup.sh
cp scripts/ansible/inventory.ini ./
vi inventory.ini
```

修改 `inventory.ini` 中的 `[master]` 和 `[worker]` 两个组将 Kuberentes 集群的所有服务器包含进来。
修改 `[chrony]` 组设置 chrony 时间服务器节点。
请参考如下示例：

```
[master] # 主节点组
# 填节点hostname，即IP地址
192.168.100.10

[worker] # 计算节点组
# 填节点hostname，即IP地址
192.168.100.11
192.168.100.12
192.168.100.13

[chrony] # 时间服务器，只设置1台
# 填节点hostname，即IP地址
192.168.100.10
```

### 步骤3: 通过Ansible安装依赖

* 通过 `inventory.ini` 进行安装

```
ansible-playbook -i inventory.ini scripts/ansible/playbooks/install_packages_and_dependencies.yml
```

* 安装 golang 环境

```
ansible-playbook -i inventory.ini scripts/ansible/playbooks/install_go.yml
```

* 安装 chrony 时间服务器，并将时区设置成“Asia/Shanghai”
```
ansible-playbook -i inventory.ini scripts/ansible/playbooks/install_and_setup_chrony.yml
```

* 配置集群免秘钥登录

```
ansible-playbook -i inventory.ini scripts/ansible/playbooks/config_root_ssh.yml
```

* 为计算节点打标签

```
ansible-playbook -i inventory.ini scripts/ansible/playbooks/label_k8s_nodes.yml
```

### 步骤4：在 Kubernetes 集群中安装 `uniVirt` DaemonSet

* 安装指定版本的 `uniVirt`，例如：v1.0.0.lab，则修改 -e "ver=v1.0.0.lab" 参数

```
ansible-playbook -i localhost, -e "ver=v1.0.0.lab" scripts/ansible/playbooks/install_uniVirt.yml
```

* 配置、启动外部服务

```
ansible-playbook -i inventory.ini scripts/ansible/playbooks/create_comm_service_env.yml
```

### 验证安装，当 virt-tool 都处于 Ready 状态则安装成功

```
kubectl get po -A | grep virt-tool
```

## 更新 `uniVirt`

* 更新至指定版本，例如：v1.0.1.lab，则修改 -e "ver=v1.0.1.lab" 参数

```
ansible-playbook -i localhost, -e "ver=v1.0.1.lab" scripts/ansible/playbooks/update_uniVirt.yml
```


## 卸载 `uniVirt`

### 卸载，例如： v1.0.0.lab

```
ansible-playbook -i localhost, -e "ver=v1.0.0.lab" scripts/ansible/playbooks/uninstall_uniVirt.yml
```

### 步骤5：当集群部署了 rook ceph 后，配置安装 ceph 客户端

* 配置`inventory-ceph.ini`文件，

```
cp scripts/ansible/inventory-ceph.ini ./
vi inventory-ceph.ini
```

* 设置 rook ceph cluster 对应的 namespace，以及属于这个 ceph 集群的节点
```
[rook-ceph]  #namespace名称
#填节点hostname，即IP地址
133.133.135.134
133.133.135.139
133.133.135.192
133.133.135.138
133.133.135.73
```

* 配置集群中节点的 ceph 客户端
```
ansible-playbook -i inventory-ceph.ini scripts/ansible/playbooks/copy_ceph_config.yml
```

* 验证 ceph 客户端，在 ceph 集群中任意节点执行
```
ceph fs status
```

# 普通用户：离线安装

* （待支持）

# 开发人员: 简明手册
## python3 包依赖，开发环境通过 pip3 install 安装，运行环境通过上面的 Ansible 自动安装。
* Python>=3.9.7
* libvirt-python==5.9.0
* kubernetes==26.1.0
* others:
  altgraph==0.17.3
  cachetools==4.2.4
  certifi==2023.5.7
  charset-normalizer==2.0.12
  google-auth==2.21.0
  grpcio==1.48.2
  grpcio-tools==1.48.2
  idna==3.4
  importlib-metadata==4.8.3
  oauthlib==3.2.2
  prometheus-client==0.17.0
  protobuf==3.19.6
  psutil==5.9.5
  pyasn1==0.5.0
  pyasn1-modules==0.3.0
  pyinstaller==4.10
  pyinstaller-hooks-contrib==2022.0
  python-dateutil==2.8.2
  PyYAML==6.0
  requests==2.27.1
  requests-oauthlib==1.3.1
  rsa==4.9
  six==1.16.0
  tenacity==8.2.3
  threadpool==1.3.2
  typing_extensions==4.1.1
  urllib3==1.26.16
  watchdog==2.3.1
  websocket-client==1.3.1
  xmljson==0.2.1
  xmltodict==0.13.0
  zipp==3.6.0

## 目录结构
```
* ----core ## 核心模块，通过Kubernetes CRD方式实现了虚拟机生命周期管理
*  ┝--libvirtwatcher ## 这个服务是DaemonSet virt-tool的一部分，监听libivrt-python中汇报的KVM虚拟机事件，包括虚拟机创建、删除、添加网卡等等。
*  ┝--plugins ## 这个文件夹包含可编译的python3执行文件，实现了KVM虚拟机管理功能。
*  ┝--utils ## 这个文件夹包含这个工程用到的工具方法。
*   ┕-constants.py ##  核心参数配置文件。
*  ┝--virtctl ## 这个服务是DaemonSet virt-tool的一部分，实现了k8s监听器watcher.py，命令转换器convertor.py，异步调用器executor.py，以及常规命令调用和RPC调用两种调用策略defaultPolicy.py和rpcPolicy.py。
*  ┝--virtlet ## 这个服务是DaemonSet virt-tool的一部分，host_reporter.py负责统计当前KVM虚拟机占用资源情况，向K8s周期性推送KVM虚拟机资源用量；os_event_handler.py负责监听处理系统事件，包括存储文件状态变化。
*  ┕--virtmonitor ## 这个服务是DaemonSet virt-tool的一部分，负责监听虚拟机的实时资源用量，包括CPU、内存、磁盘IO、网络IO，并将结果汇报给Prometheus。
* ----docker ## 容器镜像的build目录
*  ┝--base ## `uniVirt`的基础运行环境Dockerfile。
*  ┝--libvirtwatcher ## libvirtwatcher服务的Dockerfile。
*  ┝--virtctl ## virtctl服务的Dockerfile。
*  ┝--virtlet ## virtlet服务的Dockerfile。
*  ┕--virtmonitor ## virtmonitor服务的Dockerfile。
* ----scripts ## 脚本。
*  ┝--ansible ## Ansible安装脚本。
*  ┝--examples ## Json示例，按照步骤在Kubernetes集群中创建一个虚拟机，用`kubectl apply -f`命令执行。
*  ┝--plugins ## Yaml示例，用于部署 Prometheus, node-exporter 和 grafana。
*  ┝--shells ## Shell脚本，用于发布版本。
*  ┝--specs ## SPEC文件，用于生成 RPM 包。
*  ┕--yamls ## Yaml示例，用于安装/卸载 DamonSet `virt-tool` 以及 CRD.
* ----docs ## 相关文档
* ----ovnctl ## 针对 KVM 虚拟机的 Open Virtial Network (OVN) 网络管理
*  ┝--configs
*  ┝--olds
*  ┝--spec
*  ┕--src
* ----sdsctl ## 通过 Rook 实现 KVM 虚拟机的磁盘、磁盘镜像、磁盘快照等管理。 
*  ┝--cmd
*  ┝--docs
*  ┝--ftp
*  ┝--grpcservice
*  ┝--pipe
*  ┝--pkg
*  ┝--rook
*  ┕--test
```

## 支持的虚拟机管理 Custom Resource Definition (CRD)

* CRD —— 资源类型 —— 所属模块
```
virtualmachines —— 虚拟机 —— core/plugins/virshplus.py
virtualmachinedisks —— 虚拟机磁盘 —— sdsctl/cmd/sdsctl/main.go
virtualmachinediskimages —— 虚拟机磁盘镜像 —— sdsctl/cmd/sdsctl/main.go
virtualmachinedisksnapshots —— 虚拟机磁盘快照 —— sdsctl/cmd/sdsctl/main.go
virtualmachinepools —— 虚拟机存储池 —— sdsctl/cmd/sdsctl/main.go
virtualmachinenetworks —— 虚拟机网络 —— ovnctl/src/kubeovn-adm
```

## 开发步骤
### core文件夹中的主要模块介绍
* virtctl —— 虚拟机命令执行服务，当 watcher.py 监测到目标 CRD 存在 lifecycle 结构时，通过 convertor.py 解析 lifecycle 的命令名称和参数并转换成可执行命令，通过设置命令执行策略 defaultPolicy.py 执行命令，并查询执行结果。
* 服务内部调用链如下
```
virtctl_in_docker.py -> watcher.py -> convertor.py -> defaultPolicy.py (or rpcPolicy.py) -> executor.py
```
* 服务日志：每个计算节点拥有独立日志，例如计算节点worker1上的虚拟机在worker1上查看
```
/var/log/virtctl.log
```
* virtlet —— 虚拟机状态同步服务，host_reporter.py负责统计当前KVM虚拟机占用资源情况，向K8s周期性推送KVM虚拟机资源用量；os_event_handler.py负责监听处理系统事件，向k8s同步状态变化。
* 服务内部调用链如下
```
virtlet_in_docker.py --> host_reporter.py
                      ┕> os_event_handler.py
```
* 服务日志
```
/var/log/virtlet.log
```
* virtmonitor —— 虚拟机资源监听器，监听虚拟机的实时资源用量，包括CPU、内存、磁盘IO、网络IO，并将结果汇报给Prometheus。
* 服务内部调用链如下
```
virt_monitor_in_docker.py
```
* 服务日志
```
/var/log/virtmonitor.log
```
* libvirtwatcher —— 虚拟机事件监听器，监听 libivrt-python 中汇报的 KVM 虚拟机事件，包括虚拟机创建、删除、添加网卡等等。
* 服务内部调用链如下
```
libvirt_watcher_in_docker.py -> libvirt_event_handler.py
```
* 服务日志
```
/var/log/virtlet.log
```

### 步骤1：注册新命令
* 新命令注册与配置在core/utils/constants.py文件中，以CREATE_AND_START_VM_FROM_ISO_CMD为例
```
'''Virtual Machine supported commands'''
# 命令名称 = “命令调用策略，对象名称，前序操作，执行命令，查询操作”
CREATE_AND_START_VM_FROM_ISO_CMD   = "default,name,none,virshplus create_and_start_vm_from_iso,virshplus dumpxml"
```
其中，default表示使用的是“常规命令调用策略”defaultPolicy.py，name表示java-sdk或者json中对象的名称在“name”字段中，none表示执行该命令前的准备操作，virshplus create_and_start_vm_from_iso是创建虚拟机的命令本体，virshplus dumpxml是命令执行完之后的查询命令

### 步骤2：开发新命令
* 修改 `core/plugins/virshplus.py` 程序，支持 `virshplus create_and_start_vm_from_iso` 以及 `virshplus dumpxml` 命令。

### 步骤3：修改版本发布脚本，并发布、更新`uniVirt`版本
* 如果`virshplus`命令是新支持的命令，则需要修改`scripts/shells/release-version-centos7.sh`和`scripts/shells/release-version-ubuntu22.sh`脚本，将新命令打包进去，还需要同步修改`docker/base/centos7/Dockerfile`和`docker/base/ubuntu22/Dockerfile`，以及`docker/virtctl/centos7/Dockerfile`和`docker/virtctl/ubuntu22/Dockerfile`来支持该命令在集群中的同步更新。
* 如果`virshplus`命令已经存在则不需要做上述操作。
* 版本发布见下方教程，版本更新见普通用户教程。

### 步骤4：测试新命令
* 参考`scripts/examples/`中的 Json 文件写带有 lifecycle 的测试脚本。
```
{
  "apiVersion": "doslab.io/v1", //不用修改
  "kind": "VirtualMachine", //CRD对应的Kind，参考constants.py中设置
  "metadata": {
    "name": "centos-1", //见“注册新命令”步骤，将会转化成constants.py中申明的字段，并作为参数传递到后续的命令中
    "labels": {
      "host": "133.133.135.134" //在哪个计算节点上执行
    }
  },
  "spec": {
    "nodeName": "133.133.135.134", //在哪个计算节点上执行
    "lifecycle": {
      "createAndStartVMFromISO": { //具体的命令名称、参数，参考java-sdk中的API文档说明
        "virt_type": "kvm",
        "memory": "4096",
        "vcpus": "4",
        "os_variant": "centos7.0",
        "cdrom": "/var/lib/libvirt/iso/CentOS-7-x86_64-Minimal-1810.iso",
        "disk": "/var/lib/libvirt/cephfspool/centos-1-disk1/centos-1-disk1,format=qcow2",
        "network": "type=bridge,source=virbr0",
        "graphics": "vnc,listen=0.0.0.0",
        "noautoconsole": true
      }
    }
  }
}
```
### 步骤5：验证结果
* 调用 `kubectl get <CRD> -n kube-system -o wide`命令查询结果，例如
```
kubectl get vm -n kube-system -o wide
```

## 版本发布
注意！发布版本区分 CentOS7 和 Ubuntu22，需要在各自操作系统机器上进行。

每个运行环境请尽量单独发布版本，版本命名规范是：v1.0.0.<环境名称>，例如，v1.0.0.lab 表示lab实验室测试环境，v1.0.0.air，等等。

### 发布一个 CentOS7 的 v1.0.1.lab 版本

```
cd /root/uniVirt
bash scripts/shells/release-version-centos7.sh v1.0.1.lab
```

### 发布一个 Ubuntu22 的 v1.0.1.lab 版本

```
cd /root/uniVirt
bash scripts/shells/release-version-ubuntu22.sh v1.0.1.lab
```

## 开发者调试模式
开发者调试模式允许uniVirt服务通过本地源码方式运行，要求：1）下载了本工程源码，2）按照前序ansible步骤安装过环境依赖，包括libvirt、python3等，并且启动了libvirt服务。

### 启用调试模式
* 禁用当前节点的virt-tool服务
* CentOS 7执行
```commandline
kubectl label node <hostname> doslab/virt.tool.centos-
```
* Ubuntu 22执行
```commandline
kubectl label node <hostname> doslab/virt.tool.ubuntu-
```
* 从本地启动uniVirt
```commandline
cd /root/uniVirt
bash scripts/shells/service-adm.sh restart
```

### 更新二进制可执行程序并启用调试模式
* 禁用当前节点的virt-tool服务
* CentOS 7执行
```commandline
kubectl label node <hostname> doslab/virt.tool.centos-
```
* Ubuntu 22执行
```commandline
kubectl label node <hostname> doslab/virt.tool.ubuntu-
```
* 从本地启动uniVirt
```commandline
cd /root/uniVirt
bash scripts/shells/service-adm.sh update
```

### 退出调试模式
* 停止本地服务
```commandline
cd /root/uniVirt
bash scripts/shells/service-adm.sh stop
```
* 重新启用当前节点的virt-tool服务
* CentOS 7执行
```commandline
kubectl label node <hostname> doslab/virt.tool.centos=
```
* Ubuntu 22执行
```commandline
kubectl label node <hostname> doslab/virt.tool.ubuntu=
```

### 其他支持的操作
* 查询支持的操作
```commandline
bash scripts/shells/service-adm.sh
```

------------------------------------------------------------
# 版本信息

## 开发版本
```
v1.0.0.lab    支持Ansible安装部署，支持CentOS7和Ubuntu22，支持kube-ovn和Rook
v1.0.1.air
v1.0.1.gfdx
```

## 发行版本
```
(plan)
```