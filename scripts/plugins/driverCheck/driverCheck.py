# -*- coding: utf-8 -*-
import subprocess
import sys
import re
import os
import json
import time

my_dict = {}
previous_status_dict = {}
file_path = "/usr/local/driverCheck/data.json"

def get_driver_status():
    global my_dict
    cmd = "lspci -nn | grep -i nvidia"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # 正则表达式，用于提取PCI地址
    pci_pattern = r"^([0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-9a-fA-F])"

    # 查找所有匹配的PCI地址
    pci_addresses = re.findall(pci_pattern, result.stdout, re.MULTILINE)

    # 遍历所有找到的PCI地址
    for pci_addr in pci_addresses:
        cmd_details = f"lspci -vs {pci_addr}"
        result_details = subprocess.run(cmd_details, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        driver_pattern = r"Kernel driver in use: (.*)"
        driver_match = re.search(driver_pattern, result_details.stdout)
        
        if driver_match:
            my_dict[pci_addr] = driver_match.group(1)
        else :
            if os.path.isdir(f"/sys/bus/pci/devices/0000:{pci_addr}/driver"):
                if os.path.isdir(f"/sys/bus/pci/devices/0000:{pci_addr}/driver/module/drivers"):
                    folders = next(os.walk(f"/sys/bus/pci/devices/0000:{pci_addr}/driver/module/drivers"))[1]
                    matching_nvidia_folders = [folder for folder in folders if 'nvidia' in folder]
                    matching_vfio_folders = [folder for folder in folders if 'vfio' in folder]
                    if matching_nvidia_folders:
                         my_dict[pci_addr] = 'nvidia'
                    elif matching_vfio_folders:
                         my_dict[pci_addr] = 'vfio'
                    else :
                        cmd = f"echo 0000:{pci_addr} > /sys/bus/pci/devices/0000:{pci_addr}/driver/unbind"
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                        my_dict[pci_addr] = 'none'
            else :
                my_dict[pci_addr] = 'none'

def read_previous_driver_status():
    global previous_status_dict
    if not os.path.exists(file_path):
        print(f"Error: The file '{file_path}' does not exist.Has not previous driver status.")
        return -1
    
    with open(file_path, "r") as file:
        json_data = file.read()

    previous_status_dict = json.loads(json_data)

    return 1


def save_driver_status():
    global my_dict
    json_str = json.dumps(my_dict)

    os.makedirs(os.path.dirname("/usr/local/driverCheck"), exist_ok=True)
    # 将 JSON 字符串写入文件
    with open(file_path, "w") as file:
        file.write(json_str)

def driver_unbind(pci_address, type):
    print(f"unbinding driver {type}:{pci_address}")
    if type == "nvidia":
        cmd = f"echo 0000:{pci_address} > /sys/bus/pci/drivers/nvidia/unbind"
    elif type == "vfio":
        cmd = f"echo 0000:{pci_address} > /sys/bus/pci/drivers/vfio-pci/unbind"
    else:
        print("获取显卡驱动类型错误,检查是否正确绑定驱动")
        sys.exit(1)
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    cmd = "lspci -vs {} | grep Kernel".format(pci_address)
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print(result.stdout)

def driver_bind(pci_address, type):
    print(f"binding driver {type}:{pci_address}")
    #绑定之前确认解绑
    cmd = f'lspci -vs {pci_address} | grep "Kernel driver in use"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if "Kernel driver in use" in result.stdout:
        print(f"error: device {pci_address} should be unbind driver first")
        sys.exit(1)
    #检查确认路径当前pci设备是否绑定绑定有驱动
    if os.path.isdir(f"/sys/bus/pci/devices/0000:{pci_address}/driver"):
        cmd = f"echo 0000:{pci_address} > /sys/bus/pci/devices/0000:{pci_address}/driver/unbind"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if type == "nvidia":
        insMod = ["modprobe nvidia", "modprobe nvidia_uvm", "modprobe nvidia_modeset", "modprobe nvidia_drm"]
        for insCmd in insMod:
            result = subprocess.run(insCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.stderr:
                print(result.stderr)
        if not os.path.isdir("/sys/bus/pci/drivers/nvidia"):
            print("load nvidia kernel module error, please load manaully")
            sys.exit(1)
        cmd = f"echo 0000:{pci_address} > /sys/bus/pci/drivers/nvidia/bind"
    elif type == "vfio":
        cmd = "dmesg | grep -E 'DMAR|IOMMU'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if "IOMMU enabled" not in result.stdout:
            print("ERROR.IOMMU is not enabled.Please set IOMMU on")
            sys.exit(1)
        else:
            cmd = "modprobe vfio && modprobe vfio-pci"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if not os.path.isdir("/sys/bus/pci/drivers/vfio-pci"):
                print("load vfio-pci kernel error")
                sys.exit(1)
            cmd = f"echo 0000:{pci_address} > /sys/bus/pci/drivers/vfio-pci/bind"
    else:
        print("获取显卡驱动类型错误,检查是否正确绑定驱动")
        sys.exit(1)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stderr:
        print(f"bind {type} failed,检查驱动是否正确绑定", result.stderr)
    
if __name__ == '__main__':
    get_driver_status()
    flag = read_previous_driver_status()
    if flag == 1 :
        for key, value in my_dict.items():
            if previous_status_dict[key] != value and previous_status_dict[key] != 'none':
                if value != 'none':
                    driver_unbind(key, value)
                    driver_bind(key, previous_status_dict[key])
                elif value == 'none':
                    driver_bind(key, previous_status_dict[key])
            get_driver_status()
    while True:  
        get_driver_status()          
        save_driver_status()
        time.sleep(60)
