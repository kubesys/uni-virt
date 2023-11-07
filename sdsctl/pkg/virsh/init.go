package virsh

import (
	"libvirt.org/go/libvirt"
)

func GetConn() (*libvirt.Connect, error) {
	conn, err := libvirt.NewConnect("qemu:///system")
	if err != nil {
		return nil, err
	}
	return conn, nil
}
