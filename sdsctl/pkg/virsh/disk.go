package virsh

import (
	"encoding/json"
	"fmt"
	"github.com/kube-stack/sdsctl/pkg/utils"
	"os"
	"path/filepath"
	"strconv"
)

func ParseDiskDir(poolName, volName string) (string, error) {
	path, err := GetPoolTargetPath(poolName)
	if err != nil {
		return "", err
	}
	diskPath := filepath.Join(path, volName)
	return diskPath, err
}

func ParseSnapshotDir(poolName, volName, snapshotName string) (string, error) {
	path, err := GetPoolTargetPath(poolName)
	if err != nil {
		return "", err
	}
	snapshotNamePath := filepath.Join(path, volName, "snapshots", snapshotName)
	return snapshotNamePath, err
}

// func ParseDiskPath(poolName, volName, format string) (string, error) {
func ParseDiskPath(poolName, volName string) (string, error) {
	diskPath, err := ParseDiskDir(poolName, volName)
	if err != nil {
		return "", err
	}
	volPath := filepath.Join(diskPath, volName)
	return volPath, nil
}

func CheckDiskInUse(path string) bool {
	cmd := &utils.Command{
		Cmd: fmt.Sprintf("lsof %s | wc -l", path),
	}
	output, err := cmd.Execute()
	if err != nil || output != "0" {
		return true
	}
	return false
}

func GetDisk(poolName, volName string) (*Image, error) {
	volPath, err := ParseDiskPath(poolName, volName)
	if err != nil {
		return nil, err
	}
	image, err := OpenImage(volPath)
	return &image, err
}

func GetDiskConfig(pool, volName string) (map[string]string, error) {
	diskDir, _ := ParseDiskDir(pool, volName)
	return ParseConfig(diskDir)
}

func IsDiskExist(poolName, volName string) bool {
	diskPath, err := ParseDiskDir(poolName, volName)
	if err != nil {
		return false
	}
	return utils.IsDir(diskPath)
}

func IsDiskSnapshotExist(poolName, volName, snapshot string) bool {
	snapshotPath, err := ParseSnapshotDir(poolName, volName, snapshot)
	if err != nil {
		return false
	}
	return utils.Exists(snapshotPath)
}

func CreateConfig(diskDir string, info map[string]string) error {
	// write content file
	configPath := filepath.Join(diskDir, "config.json")
	content, err := json.Marshal(info)
	if err != nil {
		return err
	}
	return os.WriteFile(configPath, content, 0666)
}

func ParseConfig(diskDir string) (map[string]string, error) {
	configPath := filepath.Join(diskDir, "config.json")
	f, err := os.Open(configPath)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	res := make(map[string]string)
	decoder := json.NewDecoder(f)
	if err = decoder.Decode(&res); err != nil {
		return nil, err
	}
	return res, nil
}

func CreateDisk(poolName, volName, capacity, format string) error {
	diskPath, err := ParseDiskDir(poolName, volName)
	if err != nil {
		return err
	}
	if !utils.Exists(diskPath) {
		os.MkdirAll(diskPath, os.ModePerm)
	}
	// create image
	volPath, err := ParseDiskPath(poolName, volName)
	if err != nil {
		return err
	}
	num, _ := ParseCapacity(capacity)
	image := NewImage(volPath, format, num)
	return image.Create()
}

//func CreateDiskBack(poolName, volName, capacity, format string) error {
//
//	path, err := GetPoolTargetPath(poolName)
//	if err != nil {
//		return err
//	}
//	diskPath := filepath.Join(path, volName)
//	volFile := fmt.Sprintf("%s.%s", volName, format)
//	volPath := filepath.Join(diskPath, volFile)
//	cmd1 := &utils.Command{
//		Cmd: "mkdir -p " + volPath,
//	}
//	cmd2 := &utils.Command{
//		Cmd: "qemu-img create ",
//		Params: map[string]string{
//			"-f": "qcow2",
//			"":   fmt.Sprintf("%s %s", volPath, capacity),
//		},
//	}
//	cmds := utils.CommandList{
//		Comms: []*utils.Command{cmd1, cmd2},
//	}
//	return cmds.Execute()
//}

func DeleteDisk(poolName, volName string) error {
	path, err := GetPoolTargetPath(poolName)
	if err != nil {
		return err
	}
	diskPath := filepath.Join(path, volName)
	cmd := &utils.Command{
		Cmd: "rm -rf " + diskPath,
	}
	if _, err := cmd.Execute(); err != nil {
		return err
	}
	return nil
}

func ResizeDisk(poolName, volName, capacity string) error {
	diskDir, err := ParseDiskDir(poolName, volName)
	if err != nil {
		return err
	}
	config, err := ParseConfig(diskDir)
	if err != nil {
		return err
	}
	diskPath := config["current"]
	image, err := OpenImage(diskPath)
	if err != nil {
		return err
	}

	curr, _ := ParseCapacity(capacity)
	delta := int64(curr - image.Size)
	deltaStr := fmt.Sprintf("%sb", strconv.FormatInt(delta, 10))
	if delta == 0 {
		return fmt.Errorf("no change for disk size!")
	}
	if delta > 0 {
		deltaStr = "+" + deltaStr
	}
	return image.ResizeImage(deltaStr)
}

func CloneDisk(poolName, volName, newVolName string) error {
	return nil
}

func CreateFullCopyDisk(source, sourceFormat, targetDiskPath string) error {
	if sourceFormat != ImageFormatQCOW2 {
		// 将image转为qcow2格式，只有qcow2才支持rebase
		// convert a vmdk image file to a qcow2 image file:
		// qemu-img convert -f vmdk image.vmdk -O qcow2 image.qcow2
		cmd := &utils.Command{
			Cmd: "qemu-img convert ",
			Params: map[string]string{
				"-f": fmt.Sprintf("%s %s", sourceFormat, source),
				"-O": fmt.Sprintf("qcow2 %s", targetDiskPath),
			},
		}
		if _, err := cmd.Execute(); err != nil {
			return err
		}
	} else {
		if err := utils.CopyFile(source, targetDiskPath); err != nil {
			return err
		}
	}
	// rebase target with no backing file
	if err := RebaseDiskSnapshot("", targetDiskPath, "qcow2"); err != nil {
		return err
	}
	return nil
}

func CreateDiskWithBacking(sourceFormat, source, targetFormat, targetDiskPath string) error {
	// 指定qcow2 image创建cow overlay
	cmd := &utils.Command{
		Cmd: fmt.Sprintf("qemu-img create -f %s -b %s -F %s %s", sourceFormat, source, targetFormat, targetDiskPath),
	}
	_, err := cmd.Execute()
	return err
}
