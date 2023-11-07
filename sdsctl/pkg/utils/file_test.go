package utils

import (
	"fmt"
	"testing"
)

func TestGetDir(t *testing.T) {
	dir := GetDir("/var/lib/libvirt/pooltest2/disktest2/disktest2.qcow2")
	fmt.Println(dir)
}

func TestGetFilesUnderDir(t *testing.T) {
	files := GetFilesUnderDir("/var/lib/libvirt/pooltest2")
	fmt.Println(files)
}

func TestCopyRemoteFile(t *testing.T) {
	err := CopyFromRemoteFile("192.168.100.102", "/var/lib/libvirt/pooltest2/disktest2", "/root/cptest")
	fmt.Printf("err:%+v\n", err)
}

func TestGetFiles(t *testing.T) {
	files := GetFiles("/home/ftpuser")
	fmt.Println(files)
}
