#!/usr/bin/env bash
# Copyright (2024) Institute of Software, Chinese Academy of Sciences
# @author: liujiexin@otcaix.iscas.ac.cn
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

if [ ! -n "$1" ] ;then
    echo "error: please input a release version number!"
    echo "Usage $0 <version number>"
    exit 1
else
    if [[ "$1" =~ ^[A-Za-z0-9.]*$ ]] ;then
        echo -e "\033[3;30;47m*** Build a new release version: \033[5;36;47m($1)\033[0m)"
        echo -e "Institute of Software, Chinese Academy of Sciences"
        echo -e "        wuyuewen@otcaix.iscas.ac.cn"
        echo -e "              Copyright (2024)\n"
    else
        echo "error: wrong syntax in release version number, support chars=[A-Za-z0-9.]"
        exit 1
    fi
fi

VERSION=$1

##############################patch stuff#########################################
SHELL_FOLDER=$(dirname $(readlink -f "$0"))
WORKSPACE_ROOT=${SHELL_FOLDER}/../../../..

# 检查 others 目录是否存在
if [ ! -d "${WORKSPACE_ROOT}/others" ]; then
    echo "错误: others 目录不存在: ${WORKSPACE_ROOT}/others"
    exit 1
fi

# 自动检测项目目录名称
PROJECT_NAMES=("uni-virt" "univirt" "uniVirt")
PROJECT_ROOT=""

for name in "${PROJECT_NAMES[@]}"; do
    if [ -d "${WORKSPACE_ROOT}/others/${name}" ]; then
        PROJECT_ROOT="${WORKSPACE_ROOT}/others/${name}"
        echo "找到项目目录: ${name}"
        break
    fi
done

if [ -z "${PROJECT_ROOT}" ]; then
    echo "错误: 未找到项目目录。请确保项目目录(uni-virt/univirt/uniVirt)存在于 ${WORKSPACE_ROOT}/others/ 下"
    exit 1
fi

# 检查必要的目录是否存在
required_dirs=(
    "${PROJECT_ROOT}/dist/ubuntu22"
    "${PROJECT_ROOT}/docker/virtctl/ubuntu22"
    "${PROJECT_ROOT}/docker/virtlet/ubuntu22"
    "${PROJECT_ROOT}/docker/libvirtwatcher/ubuntu22"
    "${PROJECT_ROOT}/docker/virtmonitor/ubuntu22"
    "${PROJECT_ROOT}/ovnctl/src"
    "${PROJECT_ROOT}/core/plugins"
    "${PROJECT_ROOT}/core/utils"
    "${PROJECT_ROOT}/scripts/yamls"
    "${PROJECT_ROOT}/scripts/plugins"
)

for dir in "${required_dirs[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "错误: 目录不存在: $dir"
        exit 1
    fi
done

cd ${PROJECT_ROOT}

cp -f ./ovnctl/src/kubeovn-adm ./
chmod +x kubeovn-adm
gzexe ./kubeovn-adm
cp -f kubeovn-adm ./dist/ubuntu22
gzexe -d ./kubeovn-adm
rm -f ./kubeovn-adm~ ./kubeovn-adm
gzexe ./core/plugins/device-passthrough
cp -f ./core/plugins/device-passthrough ./dist/ubuntu22
gzexe -d ./core/plugins/device-passthrough
rm -f ./core/plugins/device-passthrough~

cp -f ./core/utils/arraylist.cfg ./dist/ubuntu22
cp -rf ./scripts/yamls ./dist/ubuntu22
cp -rf ./scripts/plugins ./dist/ubuntu22

echo ${VERSION} > ./VERSION
cd ./core/plugins
cp -f ./dist/ubuntu22/kubevmm-adm ../../dist/ubuntu22
cp -f ./dist/ubuntu22/virshplus ../../dist/ubuntu22
cp -f ./dist/ubuntu22/nvidia_driver_manager ../../dist/ubuntu22

# Go 环境设置
cd ${WORKSPACE_ROOT}/others
if [ ! -f "go1.19.1.linux-amd64.tar.gz" ]; then
    echo "错误: 未找到 Go 安装包 (go1.19.1.linux-amd64.tar.gz)"
    echo "请将 go1.19.1.linux-amd64.tar.gz 放置在 ${WORKSPACE_ROOT}/others 目录下"
    exit 1
fi

tar xzvf go1.19.1.linux-amd64.tar.gz
if [ ! -d "/usr/local" ]; then
    echo "错误: 目录不存在: /usr/local"
    exit 1
fi
cp -rf go /usr/local

# 设置 Go 环境变量
if ! grep -q "GOROOT=/usr/local/go" /root/.bashrc; then
    echo 'export GOROOT=/usr/local/go' >> /root/.bashrc
    echo 'export GOPATH=$HOME/go' >> /root/.bashrc
    echo 'export PATH=/usr/local/go/bin:$HOME/go/bin:$PATH' >> /root/.bashrc
fi
source /root/.bashrc

cd ${PROJECT_ROOT}

# 复制文件到 docker 目录
cp -rf ./dist/ubuntu22/sdsctl docker/virtctl/ubuntu22/ || true
cp -rf ./dist/ubuntu22/commctl docker/virtctl/ubuntu22/ || true
cp -rf ./dist/ubuntu22/nvidia_driver_manager docker/virtctl/ubuntu22/ || true

cp -rf ./dist/ubuntu22/yamls/ ./VERSION ./dist/ubuntu22/kubeovn-adm ./dist/ubuntu22/arraylist.cfg ./dist/ubuntu22/virshplus ./dist/ubuntu22/kubevmm-adm ./dist/ubuntu22/device-passthrough ./dist/ubuntu22/plugins docker/virtctl/ubuntu22/
cp -rf ./dist/ubuntu22/arraylist.cfg docker/virtlet/ubuntu22/
cp -rf ./dist/ubuntu22/arraylist.cfg docker/libvirtwatcher/ubuntu22/

# 检查核心目录
core_dirs=(
    "../docker/virtctl/ubuntu22/utils"
    "../docker/virtlet/ubuntu22/utils"
    "../docker/libvirtwatcher/ubuntu22/utils"
    "../docker/virtmonitor/ubuntu22/utils"
)

cd ./core
for dir in "${core_dirs[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "错误: 目录不存在: $dir"
        exit 1
    fi
done

cp -rf utils/*.py ../docker/virtctl/ubuntu22/utils/
cp -rf utils/*.py ../docker/virtlet/ubuntu22/utils/
cp -rf utils/*.py ../docker/libvirtwatcher/ubuntu22/utils/
cp -rf utils/*.py ../docker/virtmonitor/ubuntu22/utils/

cp -rf virtctl/ ../docker/virtctl/ubuntu22/
cp -rf virtlet/ ../docker/virtlet/ubuntu22/
cp -rf libvirtwatcher/ ../docker/libvirtwatcher/ubuntu22/
cp -rf virtmonitor/ ../docker/virtmonitor/ubuntu22/

cd ${PROJECT_ROOT}/docker

# Docker 构建
docker build virtlet/ubuntu22 -t g-ubjg5602-docker.pkg.coding.net/iscas-system/containers/univirt-ubuntu22-virtlet:${VERSION}
docker build virtctl/ubuntu22 -t g-ubjg5602-docker.pkg.coding.net/iscas-system/containers/univirt-ubuntu22-virtctl:${VERSION}
docker build libvirtwatcher/ubuntu22 -t g-ubjg5602-docker.pkg.coding.net/iscas-system/containers/univirt-ubuntu22-libvirtwatcher:${VERSION}
docker build virtmonitor/ubuntu22 -t g-ubjg5602-docker.pkg.coding.net/iscas-system/containers/univirt-ubuntu22-virtmonitor:${VERSION}

# 更新版本号
cd ${PROJECT_ROOT}
sed "4s/.*/%define         _verstr      ${VERSION}/" ./scripts/specs/kubevmm.spec > ./scripts/specs/kubevmm.spec.new
mv ./scripts/specs/kubevmm.spec.new ./scripts/specs/kubevmm.spec
if [ $? -ne 0 ]; then
    echo "    Failed to patch version number to SPECS/kubevmm.spec!"
    exit 1
else
    echo "    Success patch version number to SPECS/kubevmm.spec."
fi