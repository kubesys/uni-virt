import json
import xml.etree.ElementTree as ET

# Your JSON data
json_data = '''
{
            "_id": 1,
            "_type": "kvm",
            "clock": {
                "_offset": "utc",
                "timer": [
                    {
                        "_name": "rtc",
                        "_tickpolicy": "catchup"
                    },
                    {
                        "_name": "pit",
                        "_tickpolicy": "delay"
                    },
                    {
                        "_name": "hpet",
                        "_present": "no"
                    }
                ]
            },
            "cpu": {
                "_check": "none",
                "_migratable": "on",
                "_mode": "host-passthrough"
            },
            "currentMemory": {
                "_unit": "KiB",
                "text": 33554432
            },
            "devices": {
                "_interface": [
                    {
                        "_type": "bridge",
                        "address": {
                            "_bus": "0x06",
                            "_domain": "0x0000",
                            "_function": "0x0",
                            "_slot": "0x00",
                            "_type": "pci"
                        },
                        "alias": {
                            "_name": "net0"
                        },
                        "mac": {
                            "_address": "52:54:00:6c:57:d9"
                        },
                        "model": {
                            "_type": "virtio"
                        },
                        "source": {
                            "_bridge": "br-bond1"
                        },
                        "target": {
                            "_dev": "fe54006c57d9"
                        },
                        "virtualport": {
                            "_type": "openvswitch",
                            "parameters": {
                                "__interfaceid": "175bac49-7d0b-406f-bd78-af2a362c6bca"
                            }
                        },
                        "vlan": {
                            "tag": {
                                "_id": 176
                            }
                        }
                    }
                ],
                "audio": {
                    "_id": 1,
                    "_type": "none"
                },
                "channel": [
                    {
                        "_type": "unix",
                        "address": {
                            "_bus": 0,
                            "_controller": 0,
                            "_port": 1,
                            "_type": "virtio-serial"
                        },
                        "alias": {
                            "_name": "channel0"
                        },
                        "source": {
                            "_mode": "bind",
                            "_path": "/var/lib/libvirt/qemu/channel/target/domain-1-backend-ai-1/org.qemu.guest_agent.0"
                        },
                        "target": {
                            "_name": "org.qemu.guest_agent.0",
                            "_state": "disconnected",
                            "_type": "virtio"
                        }
                    }
                ],
                "console": [
                    {
                        "_tty": "/dev/pts/1",
                        "_type": "pty",
                        "alias": {
                            "_name": "serial0"
                        },
                        "source": {
                            "_path": "/dev/pts/1"
                        },
                        "target": {
                            "_port": 0,
                            "_type": "serial"
                        }
                    }
                ],
                "controller": [
                    {
                        "_index": 0,
                        "_model": "qemu-xhci",
                        "_ports": 15,
                        "_type": "usb",
                        "address": {
                            "_bus": "0x01",
                            "_domain": "0x0000",
                            "_function": "0x0",
                            "_slot": "0x00",
                            "_type": "pci"
                        },
                        "alias": {
                            "_name": "usb"
                        }
                    },
                    {
                        "_index": 0,
                        "_model": "pcie-root",
                        "_type": "pci",
                        "alias": {
                            "_name": "pcie.0"
                        }
                    },
                    {
                        "_index": 1,
                        "_model": "pcie-root-port",
                        "_type": "pci",
                        "address": {
                            "_bus": "0x00",
                            "_domain": "0x0000",
                            "_function": "0x0",
                            "_multifunction": "on",
                            "_slot": "0x02",
                            "_type": "pci"
                        },
                        "alias": {
                            "_name": "pci.1"
                        },
                        "model": {
                            "_name": "pcie-root-port"
                        },
                        "target": {
                            "_chassis": 1,
                            "_port": "0x10"
                        }
                    },
                    {
                        "_index": 2,
                        "_model": "pcie-root-port",
                        "_type": "pci",
                        "address": {
                            "_bus": "0x00",
                            "_domain": "0x0000",
                            "_function": "0x1",
                            "_slot": "0x02",
                            "_type": "pci"
                        },
                        "alias": {
                            "_name": "pci.2"
                        },
                        "model": {
                            "_name": "pcie-root-port"
                        },
                        "target": {
                            "_chassis": 2,
                            "_port": "0x11"
                        }
                    },
                    {
                        "_index": 3,
                        "_model": "pcie-root-port",
                        "_type": "pci",
                        "address": {
                            "_bus": "0x00",
                            "_domain": "0x0000",
                            "_function": "0x2",
                            "_slot": "0x02",
                            "_type": "pci"
                        },
                        "alias": {
                            "_name": "pci.3"
                        },
                        "model": {
                            "_name": "pcie-root-port"
                        },
                        "target": {
                            "_chassis": 3,
                            "_port": "0x12"
                        }
                    },
                    {
                        "_index": 4,
                        "_model": "pcie-root-port",
                        "_type": "pci",
                        "address": {
                            "_bus": "0x00",
                            "_domain": "0x0000",
                            "_function": "0x3",
                            "_slot": "0x02",
                            "_type": "pci"
                        },
                        "alias": {
                            "_name": "pci.4"
                        },
                        "model": {
                            "_name": "pcie-root-port"
                        },
                        "target": {
                            "_chassis": 4,
                            "_port": "0x13"
                        }
                    },
                    {
                        "_index": 5,
                        "_model": "pcie-root-port",
                        "_type": "pci",
                        "address": {
                            "_bus": "0x00",
                            "_domain": "0x0000",
                            "_function": "0x4",
                            "_slot": "0x02",
                            "_type": "pci"
                        },
                        "alias": {
                            "_name": "pci.5"
                        },
                        "model": {
                            "_name": "pcie-root-port"
                        },
                        "target": {
                            "_chassis": 5,
                            "_port": "0x14"
                        }
                    },
                    {
                        "_index": 6,
                        "_model": "pcie-root-port",
                        "_type": "pci",
                        "address": {
                            "_bus": "0x00",
                            "_domain": "0x0000",
                            "_function": "0x5",
                            "_slot": "0x02",
                            "_type": "pci"
                        },
                        "alias": {
                            "_name": "pci.6"
                        },
                        "model": {
                            "_name": "pcie-root-port"
                        },
                        "target": {
                            "_chassis": 6,
                            "_port": "0x15"
                        }
                    },
                    {
                        "_index": 7,
                        "_model": "pcie-root-port",
                        "_type": "pci",
                        "address": {
                            "_bus": "0x00",
                            "_domain": "0x0000",
                            "_function": "0x6",
                            "_slot": "0x02",
                            "_type": "pci"
                        },
                        "alias": {
                            "_name": "pci.7"
                        },
                        "model": {
                            "_name": "pcie-root-port"
                        },
                        "target": {
                            "_chassis": 7,
                            "_port": "0x16"
                        }
                    },
                    {
                        "_index": 8,
                        "_model": "pcie-root-port",
                        "_type": "pci",
                        "address": {
                            "_bus": "0x00",
                            "_domain": "0x0000",
                            "_function": "0x7",
                            "_slot": "0x02",
                            "_type": "pci"
                        },
                        "alias": {
                            "_name": "pci.8"
                        },
                        "model": {
                            "_name": "pcie-root-port"
                        },
                        "target": {
                            "_chassis": 8,
                            "_port": "0x17"
                        }
                    },
                    {
                        "_index": 9,
                        "_model": "pcie-root-port",
                        "_type": "pci",
                        "address": {
                            "_bus": "0x00",
                            "_domain": "0x0000",
                            "_function": "0x0",
                            "_multifunction": "on",
                            "_slot": "0x03",
                            "_type": "pci"
                        },
                        "alias": {
                            "_name": "pci.9"
                        },
                        "model": {
                            "_name": "pcie-root-port"
                        },
                        "target": {
                            "_chassis": 9,
                            "_port": "0x18"
                        }
                    },
                    {
                        "_index": 10,
                        "_model": "pcie-root-port",
                        "_type": "pci",
                        "address": {
                            "_bus": "0x00",
                            "_domain": "0x0000",
                            "_function": "0x1",
                            "_slot": "0x03",
                            "_type": "pci"
                        },
                        "alias": {
                            "_name": "pci.10"
                        },
                        "model": {
                            "_name": "pcie-root-port"
                        },
                        "target": {
                            "_chassis": 10,
                            "_port": "0x19"
                        }
                    },
                    {
                        "_index": 11,
                        "_model": "pcie-root-port",
                        "_type": "pci",
                        "address": {
                            "_bus": "0x00",
                            "_domain": "0x0000",
                            "_function": "0x2",
                            "_slot": "0x03",
                            "_type": "pci"
                        },
                        "alias": {
                            "_name": "pci.11"
                        },
                        "model": {
                            "_name": "pcie-root-port"
                        },
                        "target": {
                            "_chassis": 11,
                            "_port": "0x1a"
                        }
                    },
                    {
                        "_index": 12,
                        "_model": "pcie-root-port",
                        "_type": "pci",
                        "address": {
                            "_bus": "0x00",
                            "_domain": "0x0000",
                            "_function": "0x3",
                            "_slot": "0x03",
                            "_type": "pci"
                        },
                        "alias": {
                            "_name": "pci.12"
                        },
                        "model": {
                            "_name": "pcie-root-port"
                        },
                        "target": {
                            "_chassis": 12,
                            "_port": "0x1b"
                        }
                    },
                    {
                        "_index": 13,
                        "_model": "pcie-root-port",
                        "_type": "pci",
                        "address": {
                            "_bus": "0x00",
                            "_domain": "0x0000",
                            "_function": "0x4",
                            "_slot": "0x03",
                            "_type": "pci"
                        },
                        "alias": {
                            "_name": "pci.13"
                        },
                        "model": {
                            "_name": "pcie-root-port"
                        },
                        "target": {
                            "_chassis": 13,
                            "_port": "0x1c"
                        }
                    },
                    {
                        "_index": 14,
                        "_model": "pcie-root-port",
                        "_type": "pci",
                        "address": {
                            "_bus": "0x00",
                            "_domain": "0x0000",
                            "_function": "0x5",
                            "_slot": "0x03",
                            "_type": "pci"
                        },
                        "alias": {
                            "_name": "pci.14"
                        },
                        "model": {
                            "_name": "pcie-root-port"
                        },
                        "target": {
                            "_chassis": 14,
                            "_port": "0x1d"
                        }
                    },
                    {
                        "_index": 0,
                        "_type": "sata",
                        "address": {
                            "_bus": "0x00",
                            "_domain": "0x0000",
                            "_function": "0x2",
                            "_slot": "0x1f",
                            "_type": "pci"
                        },
                        "alias": {
                            "_name": "ide"
                        }
                    },
                    {
                        "_index": 0,
                        "_type": "virtio-serial",
                        "address": {
                            "_bus": "0x02",
                            "_domain": "0x0000",
                            "_function": "0x0",
                            "_slot": "0x00",
                            "_type": "pci"
                        },
                        "alias": {
                            "_name": "virtio-serial0"
                        }
                    }
                ],
                "disk": [
                    {
                        "_device": "disk",
                        "_type": "file",
                        "address": {
                            "_bus": "0x03",
                            "_domain": "0x0000",
                            "_function": "0x0",
                            "_slot": "0x00",
                            "_type": "pci"
                        },
                        "alias": {
                            "_name": "virtio-disk0"
                        },
                        "backingStore": {},
                        "driver": {
                            "_name": "qemu",
                            "_type": "qcow2"
                        },
                        "source": {
                            "_file": "/var/lib/libvirt/myfs/backend-ai-1-disk1/backend-ai-1-disk1",
                            "_index": 2
                        },
                        "target": {
                            "_bus": "virtio",
                            "_dev": "vda"
                        }
                    },
                    {
                        "_device": "cdrom",
                        "_type": "file",
                        "address": {
                            "_bus": 0,
                            "_controller": 0,
                            "_target": 0,
                            "_type": "drive",
                            "_unit": 0
                        },
                        "alias": {
                            "_name": "sata0-0-0"
                        },
                        "driver": {
                            "_name": "qemu"
                        },
                        "readonly": {},
                        "target": {
                            "_bus": "sata",
                            "_dev": "sda"
                        }
                    }
                ],
                "emulator": {
                    "text": "/usr/bin/qemu-system-x86_64"
                },
                "graphics": [
                    {
                        "_autoport": "yes",
                        "_listen": "0.0.0.0",
                        "_port": 5900,
                        "_type": "vnc",
                        "listen": {
                            "_address": "0.0.0.0",
                            "_type": "address"
                        }
                    }
                ],
                "input": [
                    {
                        "_bus": "usb",
                        "_type": "tablet",
                        "address": {
                            "_bus": 0,
                            "_port": 1,
                            "_type": "usb"
                        },
                        "alias": {
                            "_name": "input0"
                        }
                    },
                    {
                        "_bus": "ps2",
                        "_type": "mouse",
                        "alias": {
                            "_name": "input1"
                        }
                    },
                    {
                        "_bus": "ps2",
                        "_type": "keyboard",
                        "alias": {
                            "_name": "input2"
                        }
                    }
                ],
                "memballoon": {
                    "_model": "virtio",
                    "address": {
                        "_bus": "0x04",
                        "_domain": "0x0000",
                        "_function": "0x0",
                        "_slot": "0x00",
                        "_type": "pci"
                    },
                    "alias": {
                        "_name": "balloon0"
                    },
                    "stats": {
                        "_period": 5
                    }
                },
                "rng": [
                    {
                        "_model": "virtio",
                        "address": {
                            "_bus": "0x05",
                            "_domain": "0x0000",
                            "_function": "0x0",
                            "_slot": "0x00",
                            "_type": "pci"
                        },
                        "alias": {
                            "_name": "rng0"
                        },
                        "backend": {
                            "_model": "random",
                            "text": "/dev/urandom"
                        }
                    }
                ],
                "serial": [
                    {
                        "_type": "pty",
                        "alias": {
                            "_name": "serial0"
                        },
                        "source": {
                            "_path": "/dev/pts/1"
                        },
                        "target": {
                            "_port": 0,
                            "_type": "isa-serial",
                            "model": {
                                "_name": "isa-serial"
                            }
                        }
                    }
                ],
                "video": [
                    {
                        "address": {
                            "_bus": "0x00",
                            "_domain": "0x0000",
                            "_function": "0x0",
                            "_slot": "0x01",
                            "_type": "pci"
                        },
                        "alias": {
                            "_name": "video0"
                        },
                        "model": {
                            "_heads": 1,
                            "_primary": "yes",
                            "_type": "vga",
                            "_vram": 16384
                        }
                    }
                ]
            },
            "features": {
                "acpi": {},
                "apic": {}
            },
            "memory": {
                "_unit": "KiB",
                "text": 33554432
            },
            "metadata": {
                "{http://libosinfo.org/xmlns/libvirt/domain/1.0}libosinfo": {
                    "{http://libosinfo.org/xmlns/libvirt/domain/1.0}os": {
                        "_id": "http://centos.org/centos/7.0"
                    }
                }
            },
            "name": {
                "text": "backend-ai-1"
            },
            "on_crash": {
                "text": "destroy"
            },
            "on_poweroff": {
                "text": "destroy"
            },
            "on_reboot": {
                "text": "restart"
            },
            "os": {
                "boot": [
                    {
                        "_dev": "hd"
                    }
                ],
                "type": {
                    "_arch": "x86_64",
                    "_machine": "pc-q35-6.2",
                    "text": "hvm"
                }
            },
            "pm": {
                "suspend_to_disk": {
                    "_enabled": "no"
                },
                "suspend_to_mem": {
                    "_enabled": "no"
                }
            },
            "resource": {
                "partition": {
                    "text": "/machine"
                }
            },
            "seclabel": [
                {
                    "_model": "apparmor",
                    "_relabel": "yes",
                    "_type": "dynamic",
                    "imagelabel": {
                        "text": "libvirt-8aeb211c-4862-4799-8fc7-490a7fab2ab5"
                    },
                    "label": {
                        "text": "libvirt-8aeb211c-4862-4799-8fc7-490a7fab2ab5"
                    }
                },
                {
                    "_model": "dac",
                    "_relabel": "yes",
                    "_type": "dynamic",
                    "imagelabel": {
                        "text": "+64055:+109"
                    },
                    "label": {
                        "text": "+64055:+109"
                    }
                }
            ],
            "uuid": {
                "text": "8aeb211c-4862-4799-8fc7-490a7fab2ab5"
            },
            "vcpu": {
                "_placement": "static",
                "text": 16
            }
        }
'''

def toKubeJson(json):
    return json.replace('_', '').replace('$', 'text').replace(
            'interface', '_interface').replace('transient', '_transient').replace(
                    'nested-hv', 'nested_hv').replace('suspend-to-mem', 'suspend_to_mem').replace('suspend-to-disk', 'suspend_to_disk')

json_data = toKubeJson(json_data)

# Parse the JSON data
data = json.loads(json_data)

# Convert JSON to XML
def dict_to_xml(element, data):
    for key, value in data.items():
        if isinstance(value, dict):
            sub_element = ET.SubElement(element, key)
            dict_to_xml(sub_element, value)
        elif isinstance(value, list):
            for item in value:
                sub_element = ET.SubElement(element, key)
                dict_to_xml(sub_element, item)
        else:
            element.set(key, str(value))

root = ET.Element("domain")
dict_to_xml(root, data)

# Create the XML string
xml_str = ET.tostring(root, encoding="utf-8").decode("utf-8")

# Print or save the XML string
print(xml_str)
