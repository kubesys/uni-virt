#!/usr/bin/env bash
##############################################################
##
##      Copyright (2024, ) Institute of Software
##          Chinese Academy of Sciences
##             Author: wuyuewen@otcaix.iscas.ac.cn
##
################################################################

echo "Now starting virtlet service..."
source /root/.bashrc >/dev/null 2>&1
SHELL_FOLDER=$(dirname $(readlink -f "$0"))
cd ${SHELL_FOLDER}
cd ./virtlet
python3 virtlet_in_docker.py