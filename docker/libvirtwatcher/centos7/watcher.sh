#!/usr/bin/env bash
##############################################################
##
##      Copyright (2024, ) Institute of Software
##          Chinese Academy of Sciences
##             Author: wuyuewen@otcaix.iscas.ac.cn
##
################################################################

echo "Now starting libvirt watcher service..."
source /root/.bashrc >/dev/null 2>&1
SHELL_FOLDER=$(dirname $(readlink -f "$0"))
cd ${SHELL_FOLDER}
cd ./libvirtwatcher
python3_path="/usr/local/python3/bin/python3"
script_path="libvirt_watcher_in_docker.py"

if [ -e "$python3_path" ]; then
  "$python3_path" "$script_path"
else
  /usr/bin/python3 "$script_path"
fi