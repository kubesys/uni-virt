# 测试说明

>  存储池（VMP）

| 类型          | 测试demo                                                     | 说明                             |
| ------------- | ------------------------------------------------------------ | -------------------------------- |
| 本地存储池    | https://github.com/kube-stack/sdsctl/tree/main/test/local/pool | 创建、删除、自动启动、启动、停止 |
| cephfs存储池  | https://github.com/kube-stack/sdsctl/tree/main/test/cephfs/pool | 创建、删除、自动启动、启动、停止 |
| cephrbd存储池 | https://github.com/kube-stack/sdsctl/tree/main/test/cephrbd/pool | 创建、删除、自动启动、启动、停止 |

> 镜像存储池（VMP）

| 类型    | 测试demo                                                    | 说明                                  |
| ------- | ----------------------------------------------------------- | ------------------------------------- |
| nfs     | https://github.com/kube-stack/sdsctl/tree/main/test/nfs     | 创建、删除 |
| cephrgw | https://github.com/kube-stack/sdsctl/tree/main/test/cephrgw | 创建、删除 |

> 镜像（VMDI）

| 型       | 测试demo                                                     | 说明                                                  |
| -------- | ------------------------------------------------------------ | ----------------------------------------------------- |
| 本地镜像 | https://github.com/kube-stack/sdsctl/tree/main/test/image    | 创建本地镜像池、创建磁盘镜像（指定路径 or vmd）、删除 |
| cephrgw  | https://github.com/kube-stack/sdsctl/tree/main/test/cephrgw/image | 创建磁盘镜像（vmd）、删除、上传、下载                 |
| nfs      | https://github.com/kube-stack/sdsctl/tree/main/test/nfs/image | 创建磁盘镜像（vmd）、删除、上传、下载                 |

> 磁盘（VMD）

| 类型           | 测试demo                                                     | 说明                                   |
| -------------- | ------------------------------------------------------------ | -------------------------------------- |
| 本地磁盘       | https://github.com/kube-stack/sdsctl/tree/main/test/local/disk | 创建、删除、调整大小、克隆、从镜像创建 |
| cephfs存储磁盘 | https://github.com/kube-stack/sdsctl/tree/main/test/cephfs/disk | 创建、删除、调整大小、克隆、从镜像创建 |

> 外部快照（VMDS）

| 类型     | 测试demo                                                     | 说明                                 |
| -------- | ------------------------------------------------------------ | ------------------------------------ |
| 本地磁盘 | https://github.com/kube-stack/sdsctl/tree/main/test/externalSnapshot | 创建、恢复、删除  （是否存在domain） |

> 内部快照（VMD）

| 类型     | 测试demo                                                     | 说明             |
| -------- | ------------------------------------------------------------ | ---------------- |
| 本地磁盘 | https://github.com/kube-stack/sdsctl/tree/main/test/internalSnapshot | 创建、恢复、删除 |

