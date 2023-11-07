package virsh

import (
	"fmt"
	"testing"
)

func TestCreateDisk(t *testing.T) {
	err := CreateDisk("pooltest2", "disktest4", "2G", "qcow2")
	fmt.Printf("err: %+v", err)
}

func TestGetDisk(t *testing.T) {
	disk, err := GetDisk("pooltest2", "disktest2")
	fmt.Printf("disk: %+v", disk)
	fmt.Printf("err: %+v", err)
}

func TestIsDiskExist(t *testing.T) {
	exist := IsDiskExist("pooltest2", "disktest2")
	fmt.Printf("exist: %+v", exist)
}

func TestDeleteDisk(t *testing.T) {
	err := DeleteDisk("pooltest2", "disktest2")
	fmt.Printf("err: %+v", err)
}

func TestResizeDisk(t *testing.T) {
	err := ResizeDisk("poolhub111", "diskhub111", "3G")
	fmt.Printf("err: %+v\n", err)
}

func TestCheckDiskInUse(t *testing.T) {
	use := CheckDiskInUse("/var/lib/libvirt/pooltest2/disktest4/disktest4.qcow2")
	fmt.Printf("use:%+v\n", use)
}

func TestCheckDiskInUse2(t *testing.T) {
	use := CheckDiskInUse("/var/lib/libvirt/pooltest2/disktest2/disktest2.qcow2")
	fmt.Printf("use:%+v\n", use)
}
