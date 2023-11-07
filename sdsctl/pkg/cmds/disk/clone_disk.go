package disk

import (
	"errors"
	"fmt"
	"github.com/kube-stack/sdsctl/pkg/constant"
	"github.com/kube-stack/sdsctl/pkg/k8s"
	"github.com/kube-stack/sdsctl/pkg/utils"
	"github.com/kube-stack/sdsctl/pkg/virsh"
	"github.com/urfave/cli/v2"
	"os"
	"path/filepath"
)

func NewCloneDiskCommand() *cli.Command {
	return &cli.Command{
		Name:      "clone-disk",
		Usage:     "clone kvm disk for kubestack",
		UsageText: "sdsctl [global options] clone-disk [options]",
		Action:    backcloneDisk,
		Flags: []cli.Flag{
			&cli.StringFlag{
				Name:  "type",
				Usage: "storage vol type",
				Value: "dir",
			},
			&cli.StringFlag{
				Name:  "pool",
				Usage: "storage pool name for newvol",
				Value: "dir",
			},
			&cli.StringFlag{
				Name:  "vol",
				Usage: "storage vol name",
			},
			&cli.StringFlag{
				Name:  "newvol",
				Usage: "new vol name",
			},
			&cli.StringFlag{
				Name:  "format",
				Usage: "new vol format",
			},
		},
	}
}

func backcloneDisk(ctx *cli.Context) error {
	err := cloneDisk(ctx)
	ksgvr := k8s.NewKsGvr(constant.VMDS_Kind)
	if err != nil {
		ksgvr.UpdateWithStatus(ctx.Context, constant.DefaultNamespace, ctx.String("vol"), constant.CRD_Volume_Key, nil, err.Error(), "400")
	}
	return err
}

func cloneDisk(ctx *cli.Context) error {
	logger := utils.GetLogger()
	pool := ctx.String("pool")
	// new pool info & check
	poolGvr := k8s.NewKsGvr(constant.VMPS_Kind)
	vmp, err := poolGvr.Get(ctx.Context, constant.DefaultNamespace, pool)
	if err != nil {
		logger.Errorf("fail to get vmp %s err:%+v", pool, err)
		return err
	}
	poolInfo, _ := k8s.GetCRDSpec(vmp.Spec.Raw, constant.CRD_Pool_Key)
	if poolInfo["state"] != constant.CRD_Pool_Active {
		return fmt.Errorf("pool %+v is inactive", pool)
	}

	// old disk info & check
	diskGvr := k8s.NewKsGvr(constant.VMDS_Kind)
	sourceVmd, err := diskGvr.Get(ctx.Context, constant.DefaultNamespace, ctx.String("vol"))
	if err != nil {
		logger.Errorf("fail to get vmd %s err:%+v", ctx.String("vol"), err)
		return err
	}
	sourceVolInfo, _ := k8s.GetCRDSpec(sourceVmd.Spec.Raw, constant.CRD_Volume_Key)
	active, err := virsh.IsPoolActive(sourceVolInfo["pool"])
	if err != nil {
		logger.Errorf("IsPoolActive err:%+v", err)
		return err
	} else if !active {
		return fmt.Errorf("pool %+v is inactive", sourceVolInfo["pool"])
	}
	exist := virsh.IsVolExist(sourceVolInfo["pool"], ctx.String("vol"))
	if exist {
		return errors.New(fmt.Sprintf("the volume %+v is not exist", ctx.String("vol")))
	}

	// path
	uuid := utils.GetUUID()
	middleDir := filepath.Join(poolInfo["url"], uuid)
	middlePath := filepath.Join(middleDir, ctx.String("newvol"))
	sourceDiskPath := filepath.Join(sourceVolInfo["current"])
	targetDiskDir := filepath.Join(poolInfo["url"], ctx.String("newvol"))
	targetDiskPath := filepath.Join(targetDiskDir, ctx.String("newvol"))

	// build middle disk with config file for mv or scp
	os.MkdirAll(middleDir, os.ModePerm)
	defer os.RemoveAll(middleDir)
	//if !utils.Exists(targetDiskDir) {
	//	os.MkdirAll(targetDiskDir, os.ModePerm)
	//}
	utils.CopyFile(sourceDiskPath, middlePath)
	file, _ := virsh.GetBackFile(middlePath)
	if file != "" {
		if err = virsh.RebaseDiskSnapshot("", middlePath, ctx.String("format")); err != nil {
			logger.Errorf("RebaseDiskSnapshot err:%+v", err)
			return err
		}
	}
	cfg := map[string]string{
		"name":    ctx.String("newvol"),
		"dir":     targetDiskDir,
		"current": targetDiskPath,
		"pool":    pool,
		// fix add vm
		"vm": "",
	}
	if err = virsh.CreateConfig(middleDir, cfg); err != nil {
		logger.Errorf("CreateConfig err:%+v", err)
		return err
	}

	// judge node name
	sourceNode := k8s.GetNodeName(sourceVmd.Spec.Raw)
	targetNode := k8s.GetNodeName(vmp.Spec.Raw)
	if sourceNode == targetNode {
		// in same node
		if err := os.Rename(middleDir, targetDiskDir); err != nil {
			logger.Errorf("Rename err:%+v", err)
			return err
		}
	} else {
		// in different node
		targetIP, _ := k8s.GetIPByNodeName(targetNode)
		if err = utils.CopyToRemoteFile(targetIP, middleDir, targetDiskDir); err != nil {
			logger.Errorf("CopyToRemoteFile err:%+v", err)
			return err
		}
		// todo remote register?
	}

	// create vmd
	res := make(map[string]string)
	res["disk"] = ctx.String("vol")
	res["vol"] = ctx.String("vol")
	res["current"] = targetDiskPath
	res["pool"] = pool
	res["capacity"] = sourceVolInfo["capacity"]
	res["format"] = ctx.String("format")
	res["type"] = ctx.String("type")
	if err = diskGvr.Create(ctx.Context, constant.DefaultNamespace, ctx.String("newvol"), constant.CRD_Volume_Key, res); err != nil {
		logger.Errorf("diskGvr.Create err:%+v", err)
		return err
	}
	return nil
}
