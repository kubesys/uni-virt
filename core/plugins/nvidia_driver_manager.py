import subprocess
import sys
import re
import os
import argparse


def check_iommu_enabled():
    # 检查 dmesg 日志是否包含 IOMMU 信息
    dmesg_cmd = "dmesg | grep -E 'DMAR|IOMMU'"
    dmesg_result = subprocess.run(dmesg_cmd, shell=True, capture_output=True, text=True)

    # 检查 /proc/cmdline 文件中的内核启动参数
    cmdline_cmd = "cat /proc/cmdline"
    cmdline_result = subprocess.run(cmdline_cmd, shell=True, capture_output=True, text=True)

    if "iommu=on" in cmdline_result.stdout or "intel_iommu=on" in cmdline_result.stdout or "amd_iommu=on" in cmdline_result.stdout:
        if "IOMMU enabled" in dmesg_result.stdout:
            print("IOMMU is enabled.")
        else:
            print("IOMMU maybe is not properly initialized. Please check your system configuration.")
    else:
        print("IOMMU is not enabled. Please set IOMMU on.")
        sys.exit(1)


# --可选参数
parser = argparse.ArgumentParser(description='Script for binding and unbinding devices to drivers with PCI address.')

subparsers = parser.add_subparsers(dest='command', required=True)

# Subparser for --bind
bind_parser = subparsers.add_parser('bind', help='Bind the device to a driver')
bind_parser.add_argument('driver', choices=['nvidia', 'vfio'], help='Driver to bind')
bind_parser.add_argument('pci_address', help='PCI address of the device')

# Subparser for --unbind
unbind_parser = subparsers.add_parser('unbind', help='Unbind the device from a driver')
unbind_parser.add_argument('driver', choices=['nvidia', 'vfio'], help='Driver to unbind')
unbind_parser.add_argument('pci_address', help='PCI address of the device')

# Show command
show_parser = subparsers.add_parser('show', help='Show the current bindings')

args = parser.parse_args()

if args.command == 'bind':
    print(f'Binding driver {args.driver} to device at PCI address {args.pci_address}')
elif args.command == 'unbind':
    print(f'Unbinding driver {args.driver} from device at PCI address {args.pci_address}')
elif args.command == 'show':
    print('Showing current bindings...')
    # Add logic to show bindings if necessary
else:
    parser.print_help()

# 执行lspci命令，获取包含NVIDIA的设备列表
if args.command == 'show':

    cmd = "lspci -nn | grep -i nvidia"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # 正则表达式，用于提取PCI地址
    pci_pattern = r"^([0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-9a-fA-F])"

    # 查找所有匹配的PCI地址
    pci_addresses = re.findall(pci_pattern, result.stdout, re.MULTILINE)

    print("----------------------------------------------------------------------------")
    # 遍历所有找到的PCI地址
    for pci_addr in pci_addresses:
        cmd_details = f"lspci -vs {pci_addr}"
        result_details = subprocess.run(cmd_details, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        text=True)

        driver_pattern = r"Kernel driver in use: (.*)"
        driver_match = re.search(driver_pattern, result_details.stdout)

        if driver_match:
            print(f"PCI address: {pci_addr}, {driver_match.group(0)}")
        else:
            if os.path.isdir(f"/sys/bus/pci/devices/0000:{pci_addr}/driver"):
                if os.path.isdir(f"/sys/bus/pci/devices/0000:{pci_addr}/driver/module/drivers"):
                    folders = next(os.walk(f"/sys/bus/pci/devices/0000:{pci_addr}/driver/module/drivers"))[1]
                    matching_nvidia_folders = [folder for folder in folders if 'nvidia' in folder]
                    matching_vfio_folders = [folder for folder in folders if 'vfio' in folder]
                    if matching_nvidia_folders:
                        print(f"PCI address: {pci_addr}, Kernel driver in use: nvidia")
                    elif matching_vfio_folders:
                        print(f"PCI address: {pci_addr}, Kernel driver in use: vfio")
                    else:
                        cmd = f"echo 0000:{pci_addr} > /sys/bus/pci/devices/0000:{pci_addr}/driver/unbind"
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                        print(f"PCI address: {pci_addr}, has not bind kernel module")
            else:
                print(f"PCI address: {pci_addr}, has not bind kernel module")
    print("----------------------------------------------------------------------------")
elif args.command == "unbind":
    if args.driver == "nvidia":
        cmd = f"echo 0000:{args.pci_address} > /sys/bus/pci/drivers/nvidia/unbind"
    elif args.driver == "vfio":
        cmd = f"echo 0000:{args.pci_address} > /sys/bus/pci/drivers/vfio-pci/unbind"
    else:
        print("Usage: script.py bind/unbind nvidia/vfio PCI_ADDRESS")
        sys.exit(1)
    # 可以优化一下非阻塞调用，检查执行状态,万一unbind会卡住
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    cmd = "lspci -vs {} | grep Kernel".format(args.pci_address)
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print(result.stdout)
elif args.command == "bind":
    # 绑定之前确认解绑
    cmd = f'lspci -vs {args.pci_address} | grep "Kernel driver in use"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if "Kernel driver in use" in result.stdout:
        print(f"error: device {args.pci_address} should be unbind driver first")
        sys.exit(1)
    if args.driver == "nvidia":
        insMod = ["modprobe nvidia", "modprobe nvidia_uvm", "modprobe nvidia_modeset", "modprobe nvidia_drm"]
        for insCmd in insMod:
            result = subprocess.run(insCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.stderr:
                print(result.stderr)
        if not os.path.isdir("/sys/bus/pci/drivers/nvidia"):
            print("load nvidia kernel module error, please load manaully")
            sys.exit(1)
        cmd = f"echo 0000:{args.pci_address} > /sys/bus/pci/drivers/nvidia/bind"
    elif args.driver == "vfio":
        check_iommu_enabled()
        cmd = "modprobe vfio && modprobe vfio-pci"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if not os.path.isdir("/sys/bus/pci/drivers/vfio-pci"):
            print("load vfio-pci kernel error")
            sys.exit(1)
        cmd = f"echo 0000:{args.pci_address} > /sys/bus/pci/drivers/vfio-pci/bind"
    else:
        print("Usage: script.py bind/unbind nvidia/vfio PCI_ADDRESS")
        sys.exit(1)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stderr:
        print(f"bind {args.driver} failed", result.stderr)
else:
    parser.print_help()
    sys.exit(1)


