import subprocess
import sys
import re
import fileinput
import sys

keyword = "GRUB_CMDLINE_LINUX_DEFAULT"
set_iommu = "intel_iommu=on iommu=pt vfio-pci.ids="
flag = True
cmd = "lspci -nn | grep -i nvidia"
result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

pattern = r"\[[0-9a-fA-F]{4}:[0-9a-fA-F]{4}\]"

device_id = re.findall(pattern, result.stdout, re.MULTILINE)
dev_dict = {}
for dev_id in device_id :
    dev_dict[dev_id]=1
dev_str = ','.join(key for key in dev_dict)
dev_str = dev_str.replace("[", "").replace("]", "")
set_iommu = set_iommu + dev_str
with fileinput.FileInput("/etc/default/grub", inplace=True, backup=".bak") as file:
    for line in file:
        if keyword in line:
            if "iommu=on" in line:
                flag = False
                print(line, end='')
            end_index = line.rfind('"')
            if end_index != -1 and flag != False:
                new_line = line[:end_index] + " " + set_iommu + line[end_index:]
                print(new_line, end='')
        else:
            print(line, end='')
if flag:
    cmd = "update-grub"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print(result)
else:
    print("检查/etc/default/grub是否已经设置iommu")

flag = True
# 要写入的内容
content = """\
blacklist amdgpu
blacklist nouveau
blacklist snd_hda_intel
options nouveau modeset=0
"""

with open('/etc/modprobe.d/blacklist.conf', 'r') as file:
    for line in file:
        if "blacklist nouveau" in line:
            flag = False

if flag:
    with open('/etc/modprobe.d/blacklist.conf', 'a') as file:
        file.write(content)
    cmd = "update-initramfs -u"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print(result)
else:
    print("检查/etc/modprobe.d/blacklist.conf是否已经禁用nouveau驱动")
