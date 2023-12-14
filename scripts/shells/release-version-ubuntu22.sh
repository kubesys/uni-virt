#!/usr/bin/env bash

##############################init###############################################
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

echo -e "\033[3;30;47m*** Pull latest version from Github.\033[0m"
git pull
if [ $? -ne 0 ]; then
    echo "    Failed to pull latest version from Github!"
    exit 1
else
    echo "    Success pull latest version."
fi

##############################patch stuff#########################################
SHELL_FOLDER=$(dirname $(readlink -f "$0"))
cd ${SHELL_FOLDER}/../../
if [ ! -d "./dist/ubuntu22" ]; then
	mkdir -p ./dist/ubuntu22
fi
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
# gzexe ../scripts/kubevirt-ctl
# cp -f ../scripts/kubevirt-ctl ./dist/ubuntu22
# gzexe -d ../scripts/kubevirt-ctl
# rm -f ../scripts/kubevirt-ctl~
#cp -f ./core/plugins/ovn-ovsdb.service ./dist/ubuntu22
cp -f ./core/utils/arraylist.cfg ./dist/ubuntu22
cp -rf ./scripts/yamls ./dist/ubuntu22
cp -rf ./scripts/plugins ./dist/ubuntu22
#if [ ! -d "./dist/ansible/playbooks" ]; then
#	mkdir -p ./dist/ansible/playbooks
#fi
#cp -rf ./scripts/ansible/playbooks/install_packages_and_dependencies.yml ./dist/ansible/playbooks
#inventory_file="./dist/ansible/inventory.ini"

#cat <<EOF > "$inventory_file"
#[centos]
#
#[ubuntu]
#localhost
#
#EOF

echo ${VERSION} > ./VERSION
cd ./core/plugins
pyinstaller --distpath ./dist/ubuntu22/ -F kubevmm_adm.py -n kubevmm-adm
if [ $? -ne 0 ]; then
    echo "    Failed to compile <kubevmm-adm>!"
    exit 1
else
    echo "    Success compile <kubevmm-adm>."
fi
cp -f ./dist/ubuntu22/kubevmm-adm ../../dist/ubuntu22
pyinstaller --distpath ./dist/ubuntu22/ -F virshplus.py
if [ $? -ne 0 ]; then
    echo "    Failed to compile <virshplus>!"
    exit 1
else
    echo "    Success compile <virshplus>."
fi
cp -f ./dist/ubuntu22/virshplus ../../dist/ubuntu22
cd ../../
#cp -rf ../SDS ./
#cd ./SDS

#git clone https://gitlink.org.cn/kubestack/sdsctl.git
cd ./sdsctl/cmd/sdsctl
go build -o sdsctl main.go
cp -f sdsctl ../../../dist/ubuntu22
cd ../commctl
go build -o commctl main.go
cp -f commctl ../../../dist/ubuntu22
cd ../../grpcservice
bash create-comm-service.sh
cd ../../
#rm -rf sdsctl

#pyinstaller --distpath ./dist/ubuntu22/ -F kubesds-adm.py
#if [ $? -ne 0 ]; then
    #    echo "    Failed to compile <kubesds-adm>!"
    #exit 1
#else
    #    echo "    Success compile <kubesds-adm>."
#fi
#pyinstaller --distpath ./dist/ubuntu22/ -F kubesds-rpc-service.py
#if [ $? -ne 0 ]; then
    #    echo "    Failed to compile <kubesds-rpc>!"
    #exit 1
#else
    #    echo "    Success compile <kubesds-rpc>."
#fi
#cp -f ./kubesds-ctl.sh ../docker/virtctl
#cp -f ./kubesds-ctl.sh ../dist/ubuntu22
#cp -f ./kubesds.service ../dist/ubuntu22
#cp -f ./dist/ubuntu22/kubesds-adm ../docker/virtctl
#cp -f ./dist/ubuntu22/kubesds-adm ../dist/ubuntu22
#cp -f ./dist/ubuntu22/kubesds-rpc-service ../docker/virtctl
#cp -f ./dist/ubuntu22/kubesds-rpc-service ../dist/ubuntu22
#cd ..
#rm -rf ./SDS

#rm -rf $HOME/rpmbuild/
#mkdir -p -p $HOME/rpmbuild/SOURCES/
#find ${SHELL_FOLDER}/dist/ubuntu22 -maxdepth 1 -type f -exec ln -s {} $HOME/rpmbuild/SOURCES/ \;
#find ${SHELL_FOLDER}/dist/ubuntu22 -type d -exec ln -s {} $HOME/rpmbuild/SOURCES/ \;

#cp -rf ./dist/ubuntu22/yamls/ ./VERSION ./dist/ubuntu22/arraylist.cfg ./dist/ubuntu22/virshplus ./dist/ubuntu22/kubevmm-adm ./dist/ubuntu22/kubeovn-adm ./dist/ubuntu22/device-passthrough ./dist/ubuntu22/virt-monitor ./dist/ubuntu22/monitor docker/virtctl
#cp -rf ./dist/ansible docker/base/ubuntu22
cp -rf ./dist/ubuntu22/sdsctl docker/virtctl/ubuntu22
cp -rf ./dist/ubuntu22/commctl docker/virtctl/ubuntu22
cp -rf ./dist/ubuntu22/yamls/ ./VERSION ./dist/ubuntu22/kubeovn-adm ./dist/ubuntu22/arraylist.cfg ./dist/ubuntu22/virshplus ./dist/ubuntu22/kubevmm-adm ./dist/ubuntu22/device-passthrough ./dist/ubuntu22/plugins docker/virtctl/ubuntu22
cp -rf ./dist/ubuntu22/arraylist.cfg docker/virtlet/ubuntu22
cp -rf ./dist/ubuntu22/arraylist.cfg docker/libvirtwatcher/ubuntu22
if [ $? -ne 0 ]; then
    echo "    Failed to copy stuff to docker/virtctl!"
    exit 1
else
    echo "    Success copy stuff to docker/virtctl."
fi

##############################patch image#########################################

# step 1 copy file
cd ./core
if [ ! -d "../docker/virtctl/ubuntu22/utils" ]; then
	mkdir -p ../docker/virtctl/ubuntu22/utils
fi
if [ ! -d "../docker/virtlet/ubuntu22/utils" ]; then
	mkdir -p ../docker/virtlet/ubuntu22/utils
fi
if [ ! -d "../docker/libvirtwatcher/ubuntu22/utils" ]; then
	mkdir -p ../docker/libvirtwatcher/ubuntu22/utils
fi
if [ ! -d "../docker/virtmonitor/ubuntu22/utils" ]; then
	mkdir -p ../docker/virtmonitor/ubuntu22/utils
fi
cp -rf utils/*.py ../docker/virtctl/ubuntu22/utils/
cp -rf utils/*.py ../docker/virtlet/ubuntu22/utils/
cp -rf utils/*.py ../docker/libvirtwatcher/ubuntu22/utils/
cp -rf utils/*.py ../docker/virtmonitor/ubuntu22/utils/
cp -rf virtctl/ ../docker/virtctl/ubuntu22
cp -rf virtlet/ ../docker/virtlet/ubuntu22
cp -rf libvirtwatcher/ ../docker/libvirtwatcher/ubuntu22
cp -rf virtmonitor/ ../docker/virtmonitor/ubuntu22
cd ..
#cd ./core
#if [ ! -d "./compile" ]; then
#	mkdir -p ./compile
#fi
#cp -rf utils/ virtctl/ virtlet/ ./compile
#cd ./compile
#find ./ -name *.py | xargs python3 -m py_compile
#find ./ -name *.py | xargs rm -f
#cp -f virtctl/__pycache__/virtctl.*.pyc virtctl/virtctl.pyc
#cp -f virtctl/__pycache__/virtctl_in_docker.*.pyc virtctl/virtctl_in_docker.pyc
#cp -f virtlet/__pycache__/virtlet.*.pyc virtlet/virtlet.pyc
#cp -f virtlet/__pycache__/virtlet_in_docker.*.pyc virtlet/virtlet_in_docker.pyc
#cp -rf virtctl/ utils/ ../../docker/virtctl
#cp -rf virtlet/ utils/ ../../docker/virtlet
#cd ..
#rm -rf ./compile
#cd ..

#step 2 docker build & push
cd docker
#DOCKER_HUB_URL=registry.cn-beijing.aliyuncs.com
#IMAGE_TAG_PREFIX=${DOCKER_HUB_URL}/dosproj

#DOCKER_USER=netgenius201

echo -e "\033[3;30;47m*** Login docker image repository in coding.\033[0m"
#echo "Username: $DOCKER_USER"
#docker login --username=bigtree0613@126.com registry.cn-hangzhou.aliyuncs.com
#docker login -u ${DOCKER_USER} ${DOCKER_HUB_URL}
docker login -u containers-1701096977881 -p 12dc49b311d6efd88014314e08eb6eda138b3816 g-ubjg5602-docker.pkg.coding.net

if [ $? -ne 0 ]; then
    echo "    Failed to login coding repository!"
    exit 1
else
    echo "    Success login...Pushing images!"
fi

# use docker buildx
#docker buildx create --use
docker buildx create --name mybuilder --driver docker-container
docker buildx use mybuilder
docker run --privileged --rm tonistiigi/binfmt --install all

docker buildx build base/ubuntu22 -t g-ubjg5602-docker.pkg.coding.net/iscas-system/containers/univirt-ubuntu22-base:latest --platform linux/amd64 --push

if [ $? -ne 0 ]; then
    echo "    Failed to build base/ubuntu22!"
    exit 1
else
    echo "    Success build base/ubuntu22."
fi

docker buildx build virtlet/ubuntu22 -t g-ubjg5602-docker.pkg.coding.net/iscas-system/containers/univirt-ubuntu22-virtlet:${VERSION} --platform linux/amd64 --push

docker buildx build virtctl/ubuntu22 -t g-ubjg5602-docker.pkg.coding.net/iscas-system/containers/univirt-ubuntu22-virtctl:${VERSION} --platform linux/amd64 --push

docker buildx build libvirtwatcher/ubuntu22 -t g-ubjg5602-docker.pkg.coding.net/iscas-system/containers/univirt-ubuntu22-libvirtwatcher:${VERSION} --platform linux/amd64 --push

docker buildx build virtmonitor/ubuntu22 -t g-ubjg5602-docker.pkg.coding.net/iscas-system/containers/univirt-ubuntu22-virtmonitor:${VERSION} --platform linux/amd64 --push


#docker build base/ubuntu22 -t g-ubjg5602-docker.pkg.coding.net/iscas-system/containers/univirt-ubuntu22-base:latest --platform linux/amd64
#docker build virtlet/ubuntu22 -t g-ubjg5602-docker.pkg.coding.net/iscas-system/containers/univirt-ubuntu22-virtlet:${VERSION} --platform linux/amd64
#docker build virtctl/ubuntu22 -t g-ubjg5602-docker.pkg.coding.net/iscas-system/containers/univirt-ubuntu22-virtctl:${VERSION} --platform linux/amd64
#docker build libvirtwatcher/ubuntu22 -t g-ubjg5602-docker.pkg.coding.net/iscas-system/containers/univirt-ubuntu22-libvirtwatcher:${VERSION} --platform linux/amd64
#docker build virtmonitor/ubuntu22 -t g-ubjg5602-docker.pkg.coding.net/iscas-system/containers/univirt-ubuntu22-virtmonitor:${VERSION} --platform linux/amd64

#step 3 docker push

#docker push g-ubjg5602-docker.pkg.coding.net/iscas-system/containers/univirt-ubuntu22-base:latest
#docker push g-ubjg5602-docker.pkg.coding.net/iscas-system/containers/univirt-ubuntu22-virtlet:${VERSION}
#docker push g-ubjg5602-docker.pkg.coding.net/iscas-system/containers/univirt-ubuntu22-virtctl:${VERSION}
#docker push g-ubjg5602-docker.pkg.coding.net/iscas-system/containers/univirt-ubuntu22-libvirtwatcher:${VERSION}
#docker push g-ubjg5602-docker.pkg.coding.net/iscas-system/containers/univirt-ubuntu22-virtmonitor:${VERSION}

###############################patch version to SPECS/kubevmm.spec######################################################
echo -e "\033[3;30;47m*** Patch release version number to SPECS/kubevmm.spec\033[0m"
cd ..
sed "4s/.*/%define         _verstr      ${VERSION}/" ./scripts/specs/kubevmm.spec > ./scripts/specs/kubevmm.spec.new
mv ./scripts/specs/kubevmm.spec.new ./scripts/specs/kubevmm.spec
if [ $? -ne 0 ]; then
    echo "    Failed to patch version number to SPECS/kubevmm.spec!"
    exit 1
else
    echo "    Success patch version number to SPECS/kubevmm.spec."
fi

#echo -e "\033[3;30;47m*** Push new SPECS/kubevmm.spec to Github.\033[0m"
#git add ./scripts/specs/kubevmm.spec
## git add ./kubeovn-adm
#git commit -m "new release version ${VERSION}"
#git push
#if [ $? -ne 0 ]; then
    #    echo "    Failed to push SPECS/kubevmm.spec to Github!"
    #exit 1
#else
    #    echo "    Success push SPECS/kubevmm.spec to Github."
#fi

