package k8s

import (
	"fmt"
	"testing"
)

func TestGetVMHostName(t *testing.T) {
	name := GetVMHostName()
	fmt.Println(name)
}

func TestGetIPByNodeName(t *testing.T) {
	ip, err := GetIPByNodeName("vm.node131")
	fmt.Printf("err:%+v\n", err)
	fmt.Printf("name:%+v\n", ip)
}

func TestCheckNfsMount(t *testing.T) {
	mount := CheckNfsMount("10.107.246.5", "/var/lib/libvirt/share/image")
	fmt.Printf("mount:%+v", mount)
}

func TestGetAwsS3BucketInfo(t *testing.T) {
	info, s, s2, err := GetAwsS3BucketInfo()
	fmt.Printf("%s\n", info)
	fmt.Printf("%s\n", s)
	fmt.Printf("%s\n", s2)
	fmt.Printf("%+v\n", err)
}

func TestGetAwsS3AccessInfo(t *testing.T) {
	info, s, err := GetAwsS3AccessInfo()
	fmt.Printf("%s\n", info)
	fmt.Printf("%s\n", s)
	fmt.Printf("%+v\n", err)
}
