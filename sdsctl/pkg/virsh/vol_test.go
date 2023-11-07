package virsh

import (
	"fmt"
	"testing"
)

func TestShowVol(t *testing.T) {
	vol, err := GetVol("pooltest2", "disktest")
	fmt.Printf("vol:%+v\n", vol)
	fmt.Printf("err:%+v\n", err)
}

func TestCreateVol(t *testing.T) {
	vol, err := CreateVol("pooltest2", "disktest3", "dir", "1.5G", "qcow2")
	fmt.Printf("vol:%+v\n", vol)
	fmt.Printf("err:%+v\n", err)
}

func TestDeleteVol(t *testing.T) {
	err := DeleteVol("pooltest2", "disktest4")
	fmt.Printf("err:%+v\n", err)
}

func TestResizeVol(t *testing.T) {
	err := ResizeVol("pooltest2", "test3.qcow2", "5.5G")
	fmt.Printf("err:%+v\n", err)
}

func TestCloneVol(t *testing.T) {
	err := CloneVol("pooltest2", "test2.qcow2", "test3.qcow2")
	fmt.Printf("err:%+v\n", err)
}
