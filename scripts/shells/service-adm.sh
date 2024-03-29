#!/usr/bin/env bash

##############################init###############################################
if [[ ! -n "$1" ]] ;then
    echo "error: wrong parameter!"
    echo "Usage $0 <start|stop|restart|status|update>"
    exit 1
fi
    
if [[ "$1" != "start" ]] && [[ "$1" != "stop" ]] && [[ "$1" != "restart" ]] && [[ "$1" != "status" ]] && [[ "$1" != "update" ]];then
	echo "error: wrong parameter!"
    echo "Usage $0 <start|stop|restart|status|update>"
    exit 1
fi

##############################patch stuff#########################################
SHELL_FOLDER=$(dirname $(readlink -f "$0"))
cd ${SHELL_FOLDER}/../../

if [[ "$1" == "update" ]] ;then
	echo -e "\033[3;30;47m*** Pull latest version from Github.\033[0m"
	git pull
	if [ $? -ne 0 ]; then
	    echo "    Failed to pull latest version from Github!"
	    exit 1
	else
	    echo "    Success pull latest version."
	fi
	
	if [ ! -d "./dist" ]; then
		mkdir ./dist
	fi
	#wget -c https://raw.githubusercontent.com/kubesys/kubeext-SDN/master/src/kubeovn-adm
	cd ovnctl/src/
	chmod +x kubeovn-adm
	gzexe ./kubeovn-adm
	cp -f kubeovn-adm /usr/bin/
	gzexe -d ./kubeovn-adm
	rm -f ./kubeovn-adm~
	cd ../../
	#cp -f ./core/plugins/ovn-ovsdb.service /usr/lib/systemd/system/

  if [ ! -d "/etc/uniVirt/" ]; then
	  mkdir /etc/uniVirt/
  fi
	cp -f ./core/utils/arraylist.cfg /etc/uniVirt/
	cp -rf ./scripts/yamls /etc/uniVirt/

	cd ./sdsctl/cmd/sdsctl
  go build -o sdsctl main.go
  cp -f sdsctl /usr/bin/
  cd ../../../

	#pyinstaller -F kubevmm_adm.py -n kubevmm-adm
	#if [ $? -ne 0 ]; then
	#    echo "    Failed to compile <kubevmm-adm>!"
	#    exit 1
	#else
	#    echo "    Success compile <kubevmm-adm>."
	#fi
	#cp -f ./dist/kubevmm-adm /usr/bin/
	#rm -rf ./dist
	cp -rf ./client_python/kubesys ./core/
	cd ./core/plugins
	cp -f virshplus.py ../
	cd ../..
	pyinstaller --distpath ./dist/centos7/ -F virshplus.py --hidden-import urllib3 --hidden-import requests --hidden-import kubernetes --hidden-import tenacity  --add-data ../utils/*:utils --add-data ../utils/*:. --add-data ../kubesys/*:kubesys --clean
	if [ $? -ne 0 ]; then
	    echo "    Failed to compile <virshplus>!"
	    exit 1
	else
	    echo "    Success compile <virshplus>."
	fi
	cp -f ./dist/virshplus /usr/bin/
	rm -rf ./dist
	cd ..
	#git clone -b uit https://github.com/uit-plus/kubeext-SDS.git
	#cd ./kubeext-SDS
	
	#pyinstaller2.7 -F kubesds-adm.py
	#if [ $? -ne 0 ]; then
	#    echo "    Failed to compile <kubesds-adm>!"
	#    exit 1
	#else
	#    echo "    Success compile <kubesds-adm>."
	#fi
	#pyinstaller2.7 -F kubesds-rpc.py
	#if [ $? -ne 0 ]; then
	#    echo "    Failed to compile <kubesds-rpc>!"
	#    exit 1
	#else
	#    echo "    Success compile <kubesds-rpc>."
	#fi
	#cp -f ./dist/kubesds-adm /usr/bin/
	#cp -f ./dist/kubesds-rpc /usr/bin/
	#cd ..
	#rm -rf ./kubeext-SDS
	echo "restart services..."
	cd core/virtlet
	python3 virtlet.py restart
	
	cd ${SHELL_FOLDER}/../../
	cd core/virtctl
	python3 virtctl.py restart

	cd ${SHELL_FOLDER}/../../
	cd core/virtmonitor
	python3 virt_monitor.py restart

	cd ${SHELL_FOLDER}/../../
	cd core/libvirtwatcher
	python3 libvirt_watcher.py restart
else
	cd core/virtlet
	python3 virtlet.py $1
	
	cd ${SHELL_FOLDER}/../../
	cd core/virtctl
	python3 virtctl.py $1

	cd ${SHELL_FOLDER}/../../
	cd core/virtmonitor
	python3 virt_monitor.py $1

	cd ${SHELL_FOLDER}/../../
	cd core/libvirtwatcher
	python3 libvirt_watcher.py $1
fi