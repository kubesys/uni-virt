package virsh

import (
	"fmt"
	"testing"
)

func TestGetOneBackChainFiles(t *testing.T) {
	files, err := GetOneBackChainFiles("/var/lib/libvirt/pooltest2/test3.qcow2")
	fmt.Printf("err:%+v\n", err)
	fmt.Printf("files:%+v\n", files)
}

func TestGetBackChainFiles(t *testing.T) {
	//files, err := GetBackChainFiles("/var/lib/libvirt/pooltest2")
	//fmt.Printf("err:%+v\n", err)
	//fmt.Printf("files:%+v\n", files)
}

func TestGetBackFile(t *testing.T) {
	file, err := GetBackFile("/var/lib/libvirt/pooltest2/test3.qcow2")
	fmt.Printf("err:%+v\n", err)
	fmt.Printf("files:%+v\n", file)
}
