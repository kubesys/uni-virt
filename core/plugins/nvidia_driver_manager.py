import subprocess
import sys
import re
import os
import time

# 执行lspci命令，获取包含NVIDIA的设备列表
cmd = "lspci -nn | grep -i nvidia"
result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

# 正则表达式，用于提取PCI地址
pci_pattern = r"^([0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-9a-fA-F])"

# 查找所有匹配的PCI地址
pci_addresses = re.findall(pci_pattern, result.stdout, re.MULTILINE)

print("---------------------------------------------------------------------------------")
# 遍历所有找到的PCI地址
for pci_addr in pci_addresses:
    cmd_details = f"lspci -vs {pci_addr}"
    result_details = subprocess.run(cmd_details, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    driver_pattern = r"Kernel driver in use: (.*)"
    driver_match = re.search(driver_pattern, result_details.stdout)

    if driver_match:
        print(f"PCI address: {pci_addr}, {driver_match.group(0)}")
    else :
        print(f"PCI address: {pci_addr}, has not bind kernel module")
print("---------------------------------------------------------------------------------")
user_input = input("请输入(Usage:bind/unbind nvidia/vfio PCI_ADDRESS,空格分隔)\n:")
bindStatus, driverType, pci_address = user_input.split()
if bindStatus == "unbind":
    if driverType == "nvidia":
        rmMod = ["rmmod nvidia_drm", "rmmod nvidia_modeset", "rmmod nvidia_uvm", "rmmod nvidia"]
        for rmCmd in rmMod:
            result = subprocess.run(rmCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.stderr:
                match = re.search(r'Module (\S+) is in use by (\S+)', result.stderr)
                if match:
                    print(result.stderr,"remove nvidia module before unbind failed, please remove manually")
                    sys.exit(1)
        cmd = f"echo 0000:{pci_address} > /sys/bus/pci/drivers/nvidia/unbind"
    elif driverType == "vfio":
        cmd = f"echo 0000:{pci_address} > /sys/bus/pci/drivers/vfio-pci/unbind"
    else:
        print("Usage: script.py bind/unbind nvidia/vfio PCI_ADDRESS")
        sys.exit(1)
    #可以优化一下非阻塞调用，检查执行状态,万一unbind会卡住
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    cmd = "lspci -vs {} | grep Kernel".format(pci_address)
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print(result.stdout)
elif bindStatus == "bind":
    #绑定之前确认解绑
    cmd = f'lspci -vs {pci_address} | grep "Kernel driver in use"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if "Kernel driver in use" in result.stdout:
        print(f"error: device {pci_address} should be unbind driver first")
        sys.exit(1)
    if driverType == "nvidia":
        insMod = ["modprobe nvidia", "modprobe nvidia_uvm", "modprobe nvidia_modeset", "modprobe nvidia_drm"]
        for insCmd in insMod:
            result = subprocess.run(insCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.stderr:
                print(result.stderr)
        if not os.path.isdir("/sys/bus/pci/drivers/nvidia"):
            print("load nvidia kernel module error, please load manaully")
            sys.exit(1)
        cmd = f"echo 0000:{pci_address} > /sys/bus/pci/drivers/nvidia/bind"
    elif driverType == "vfio":
        cmd = "dmesg | grep -E 'DMAR|IOMMU'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if "IOMMU enabled" not in result.stdout:
            print("IOMMU is not enabled.Please set IOMMU on")
            sys.exit(1)
        else:
            cmd = "modprobe vfio && modprobe vfio-pci"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if not os.path.isdir("/sys/bus/pci/drivers/vfio-pci"):
                print("load vfio-pci kernel error")
                sys.exit(1)
            cmd = f"echo 0000:{pci_address} > /sys/bus/pci/drivers/vfio-pci/bind"
    else:
        print("Usage: script.py bind/unbind nvidia/vfio PCI_ADDRESS")
        sys.exit(1)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stderr:
        print(f"bind {driverType} failed", result.stderr)
else:
    print("Usage: script.py bind/unbind nvidia/vfio PCI_ADDRESS")
    sys.exit(1)