package virsh

import (
	"fmt"
	"testing"
)

func TestGetVMDiskSpec(t *testing.T) {
	disks, err := GetVMDiskSpec("test")
	fmt.Printf("err:%+v\n", err)
	for _, disk := range disks {
		fmt.Printf("disk:%+v\n", disk)
	}
}

// todo with domain
func TestChangeVMDisk(t *testing.T) {
	err := ChangeVMDisk("test", "/var/lib/libvirt/pooltest2/disktest4/disktest4.qcow2", "/var/lib/libvirt/pooltest2/disktest4/disktest4.qcow2")
	fmt.Printf("err:%+v\n", err)
}

func TestChangeVMDisk2(t *testing.T) {
	err := ChangeVMDisk("test", "/var/lib/libvirt/pooltest2/test2.qcow2", "/var/lib/libvirt/pooltest2/test.qcow2")
	fmt.Printf("err:%+v\n", err)
}

func TestIsVMActive(t *testing.T) {
	active, err := IsVMActive("test111")
	fmt.Printf("err:%+v\n", err)
	fmt.Printf("active:%+v\n", active)
}
