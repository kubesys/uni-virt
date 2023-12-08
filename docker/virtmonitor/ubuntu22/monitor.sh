#!/usr/bin/env bash
##############################################################
##
##      Copyright (2024, ) Institute of Software
##          Chinese Academy of Sciences
##             Author: wuyuewen@otcaix.iscas.ac.cn
##
################################################################

echo "Now starting virt monitor service..."
source /root/.bashrc >/dev/null 2>&1
SHELL_FOLDER=$(dirname $(readlink -f "$0"))
cd ${SHELL_FOLDER}
cd ./virtmonitor
python3 virt_monitor_in_docker.py