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
        echo -e "              Copyright (2021)\n"
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
if [ ! -d "./dist/centos7" ]; then
	mkdir -p ./dist/centos7
fi
cp -f ./ovnctl/src/kubeovn-adm ./
chmod +x kubeovn-adm
gzexe ./kubeovn-adm
cp -f kubeovn-adm ./dist/centos7
gzexe -d ./kubeovn-adm
rm -f ./kubeovn-adm~ ./kubeovn-adm
gzexe ./core/plugins/device-passthrough
cp -f ./core/plugins/device-passthrough ./dist/centos7
gzexe -d ./core/plugins/device-passthrough
rm -f ./core/plugins/device-passthrough~
# gzexe ../scripts/kubevirt-ctl
# cp -f ../scripts/kubevirt-ctl ./dist/centos7
# gzexe -d ../scripts/kubevirt-ctl
# rm -f ../scripts/kubevirt-ctl~
#cp -f ./core/plugins/ovn-ovsdb.service ./dist/centos7
cp -f ./core/utils/arraylist.cfg ./dist/centos7
cp -rf ./scripts/yamls ./dist/centos7
cp -rf ./scripts/plugins ./dist/centos7
echo ${VERSION} > ./VERSION
cd ./core/plugins
pyinstaller --distpath ./dist/centos7/ -F kubevmm_adm.py -n kubevmm-adm
if [ $? -ne 0 ]; then
    echo "    Failed to compile <kubevmm-adm>!"
    exit 1
else
    echo "    Success compile <kubevmm-adm>."
fi
cp -f ./dist/centos7/kubevmm-adm ../../dist/centos7
pyinstaller --distpath ./dist/centos7/ -F virshplus.py
if [ $? -ne 0 ]; then
    echo "    Failed to compile <virshplus>!"
    exit 1
else
    echo "    Success compile <virshplus>."
fi
cp -f ./dist/centos7/virshplus ../../dist/centos7
cd ../../
#cp -rf ../SDS ./
#cd ./SDS

#git clone https://gitlink.org.cn/kubestack/sdsctl.git
cd ./sdsctl/cmd/sdsctl
go build -o sdsctl main.go
cp -f sdsctl ../../../dist/centos7
cd ../commctl
go build -o commctl main.go
cp -f commctl ../../../dist/centos7
cd ../../grpcservice
bash create-comm-service.sh
cd ../../
#rm -rf sdsctl

#pyinstaller --distpath ./dist/centos7/ -F kubesds-adm.py
#if [ $? -ne 0 ]; then
    #    echo "    Failed to compile <kubesds-adm>!"
    #exit 1
#else
    #    echo "    Success compile <kubesds-adm>."
#fi
#pyinstaller --distpath ./dist/centos7/ -F kubesds-rpc-service.py
#if [ $? -ne 0 ]; then
    #    echo "    Failed to compile <kubesds-rpc>!"
    #exit 1
#else
    #    echo "    Success compile <kubesds-rpc>."
#fi
#cp -f ./kubesds-ctl.sh ../docker/virtctl
#cp -f ./kubesds-ctl.sh ../dist/centos7
#cp -f ./kubesds.service ../dist/centos7
#cp -f ./dist/centos7/kubesds-adm ../docker/virtctl
#cp -f ./dist/centos7/kubesds-adm ../dist/centos7
#cp -f ./dist/centos7/kubesds-rpc-service ../docker/virtctl
#cp -f ./dist/centos7/kubesds-rpc-service ../dist/centos7
#cd ..
#rm -rf ./SDS

rm -rf $HOME/rpmbuild/
mkdir -p -p $HOME/rpmbuild/SOURCES/
find ${SHELL_FOLDER}/dist/centos7 -maxdepth 1 -type f -exec ln -s {} $HOME/rpmbuild/SOURCES/ \;
find ${SHELL_FOLDER}/dist/centos7 -type d -exec ln -s {} $HOME/rpmbuild/SOURCES/ \;

cp -rf ./dist/centos7/sdsctl docker/virtctl/centos7
cp -rf ./dist/centos7/commctl docker/virtctl/centos7
#cp -rf ./dist/centos7/yamls/ ./VERSION ./dist/centos7/arraylist.cfg ./dist/centos7/virshplus ./dist/centos7/kubevmm-adm ./dist/centos7/kubeovn-adm ./dist/centos7/device-passthrough ./dist/centos7/virt-monitor ./dist/centos7/monitor docker/virtctl
cp -rf ./dist/centos7/yamls/ ./VERSION ./dist/centos7/kubeovn-adm ./dist/centos7/arraylist.cfg ./dist/centos7/virshplus ./dist/centos7/kubevmm-adm ./dist/centos7/device-passthrough ./dist/centos7/plugins docker/virtctl/centos7
cp -rf ./dist/centos7/arraylist.cfg docker/virtlet/centos7
cp -rf ./dist/centos7/arraylist.cfg docker/libvirtwatcher/centos7
if [ $? -ne 0 ]; then
    echo "    Failed to copy stuff to docker/virtctl!"
    exit 1
else
    echo "    Success copy stuff to docker/virtctl."
fi

##############################patch image#########################################

# step 1 copy file
cd ./core
if [ ! -d "../docker/virtctl/centos7/utils" ]; then
	mkdir -p ../docker/virtctl/centos7/utils
fi
if [ ! -d "../docker/virtlet/centos7/utils" ]; then
	mkdir -p ../docker/virtlet/centos7/utils
fi
if [ ! -d "../docker/libvirtwatcher/centos7/utils" ]; then
	mkdir -p ../docker/libvirtwatcher/centos7/utils
fi
if [ ! -d "../docker/virtmonitor/centos7/utils" ]; then
	mkdir -p ../docker/virtmonitor/centos7/utils
fi
cp -rf utils/*.py ../docker/virtctl/centos7/utils/
cp -rf utils/*.py ../docker/virtlet/centos7/utils/
cp -rf utils/*.py ../docker/libvirtwatcher/centos7/utils/
cp -rf utils/*.py ../docker/virtmonitor/centos7/utils/
cp -rf virtctl/ ../docker/virtctl/centos7
cp -rf virtlet/ ../docker/virtlet/centos7
cp -rf libvirtwatcher/ ../docker/libvirtwatcher/centos7
cp -rf virtmonitor/ ../docker/virtmonitor/centos7
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
docker login -u containers-1699600016699 -p efa319535a51fc67963959bde4065d8745ef6615 g-ubjg5602-docker.pkg.coding.net

if [ $? -ne 0 ]; then
    echo "    Failed to login coding repository!"
    exit 1
else
    echo "    Success login...Pushing images!"
fi

# use docker buildx
#docker buildx create --name mybuilder --driver docker-container
#docker buildx use mybuilder
#docker run --privileged --rm tonistiigi/binfmt --install all

docker build base/centos7 -t g-ubjg5602-docker.pkg.coding.net/iscas-system/containers/univirt-centos7-base:latest --platform linux/amd64
docker build virtlet/centos7 -t g-ubjg5602-docker.pkg.coding.net/iscas-system/containers/univirt-centos7-virtlet:${VERSION} --platform linux/amd64
docker build virtctl/centos7 -t g-ubjg5602-docker.pkg.coding.net/iscas-system/containers/univirt-centos7-virtctl:${VERSION} --platform linux/amd64
docker build libvirtwatcher/centos7 -t g-ubjg5602-docker.pkg.coding.net/iscas-system/containers/univirt-centos7-libvirtwatcher:${VERSION} --platform linux/amd64
docker build virtmonitor/centos7 -t g-ubjg5602-docker.pkg.coding.net/iscas-system/containers/univirt-centos7-virtmonitor:${VERSION} --platform linux/amd64

#step 3 docker push

docker push g-ubjg5602-docker.pkg.coding.net/iscas-system/containers/univirt-centos7-base:latest
docker push g-ubjg5602-docker.pkg.coding.net/iscas-system/containers/univirt-centos7-virtlet:${VERSION}
docker push g-ubjg5602-docker.pkg.coding.net/iscas-system/containers/univirt-centos7-virtctl:${VERSION}
docker push g-ubjg5602-docker.pkg.coding.net/iscas-system/containers/univirt-centos7-libvirtwatcher:${VERSION}
docker push g-ubjg5602-docker.pkg.coding.net/iscas-system/containers/univirt-centos7-virtmonitor:${VERSION}

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

