package virsh

import (
	"encoding/xml"
	"fmt"
	libvirtxml "github.com/libvirt/libvirt-go-xml"
	"testing"
)

func TestGetPoolInfo(t *testing.T) {
	pool, _ := GetPoolInfo("pooltest2")
	info, _ := pool.GetInfo()
	fmt.Printf("info: %+v\n", info)
	pxml, _ := pool.GetXMLDesc(0)
	fmt.Printf("xml:%+v\n", pxml)
	now := &libvirtxml.StoragePool{}
	xml.Unmarshal([]byte(pxml), now)
	fmt.Printf("path:%+v", now.Target.Path)
}

func TestCreateLocalPool(t *testing.T) {
	pool, err := CreatePool("pooltest456", "dir", "/var/lib/libvirt/pooltest456", "", "", "")
	fmt.Printf("err: %+v\n", err)
	info, _ := pool.GetInfo()
	fmt.Printf("info: %+v\n", info)
}

func TestCreateNfsPool(t *testing.T) {
	pool, err := CreatePool("nfspool", "netfs", "/var/lib/libvirt/nfspool", "192.168.100.102", "", "/root/nfs/nfspool2")
	fmt.Printf("err: %+v\n", err)
	info, _ := pool.GetInfo()
	fmt.Printf("info: %+v\n", info)
}

func TestAutoStartPool(t *testing.T) {
	err := AutoStartPool("pooltest2", true)
	fmt.Printf("err: %+v\n", err)
}

func TestDeletePool(t *testing.T) {
	err := DeletePool("pooltest2")
	fmt.Printf("err: %+v\n", err)
}

func TestStartPool(t *testing.T) {
	err := StartPool("pooltest2")
	fmt.Printf("err: %+v\n", err)
}

func TestStopPool(t *testing.T) {
	err := StopPool("pooltest2")
	fmt.Printf("err: %+v\n", err)
}

func TestStopPool2(t *testing.T) {
	raw := "10G"
	var num uint64 = 0
	var unit string
	for idx := range raw {
		if raw[idx] >= '0' && raw[idx] <= '9' {
			num = 10*num + uint64(raw[idx]-'0')
		} else {
			unit = raw[idx:]
			break
		}
	}
	fmt.Println(num)
	fmt.Println(unit)
}

func TestCheckVMDiskSpec(t *testing.T) {
	poolType := CheckPoolType("poolhub111-image", "vmdi")
	fmt.Println(poolType)
}
