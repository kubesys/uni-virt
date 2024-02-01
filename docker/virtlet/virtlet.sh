#!/usr/bin/env bash
##############################################################
##
##      Copyright (2024, ) Institute of Software
##          Chinese Academy of Sciences
##             Author: wuyuewen@otcaix.iscas.ac.cn
##
################################################################

echo "Now starting virtlet service..."
SHELL_FOLDER=$(dirname $(readlink -f "$0"))
cd ${SHELL_FOLDER}
cd ./virtlet
python3_path="/usr/local/python3/bin/python3"
script_path="virtlet_in_docker.py"

if [ -e "$python3_path" ]; then
  "$python3_path" "$script_path"
else
  /usr/bin/python3 "$script_path"
fi