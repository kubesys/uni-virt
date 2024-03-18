package externalSnapshot

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
	"strings"
)

func NewCreateExternalSnapshotCommand() *cli.Command {
	return &cli.Command{
		Name:      "create-external-snapshot",
		Usage:     "create kvm snapshot for kubestack",
		UsageText: "sdsctl [global options] create-external-snapshot [options]",
		Action:    backcreateExternalSnapshot,
		Flags: []cli.Flag{
			&cli.StringFlag{
				Name:  "type",
				Usage: "storage vol type",
				Value: "dir",
			},
			&cli.StringFlag{
				Name:  "pool",
				Usage: "storage pool name",
			},
			&cli.StringFlag{
				Name:  "name",
				Usage: "storage volume snapshot name",
			},
			&cli.StringFlag{
				Name:  "format",
				Usage: "storage vol format",
			},
			&cli.StringFlag{
				Name:  "source",
				Usage: "source storage disk file",
			},
			&cli.StringFlag{
				Name:  "domain",
				Usage: "domain name",
			},
		},
	}
}

func backcreateExternalSnapshot(ctx *cli.Context) error {
	err := createExternalSnapshot(ctx)
	ksgvr := k8s.NewKsGvr(constant.VMDSNS_Kinds)
	if err != nil && !strings.Contains(err.Error(), "already exists") {
		ksgvr.UpdateWithStatus(ctx.Context, constant.DefaultNamespace, ctx.String("name"), constant.CRD_Volume_Key, nil, err.Error(), "400")
	}
	return err
}

func createBackup(path string) {
	os.Remove(path)
}

func createExternalSnapshot(ctx *cli.Context) error {
	logger := utils.GetLogger()
	domain := ctx.String("domain")
	pool := ctx.String("pool")
	active, err := virsh.IsPoolActive(pool)
	if err != nil {
		logger.Errorf("IsPoolActive err:%+v", err)
		return err
	} else if !active {
		return fmt.Errorf("pool %+v is inactive", pool)
	}
	exist := virsh.IsDiskSnapshotExist(pool, ctx.String("source"), ctx.String("name"))
	if exist {
		return errors.New(fmt.Sprintf("the snapshot %+v is already exist", ctx.String("name")))
	}

	diskDir, _ := virsh.ParseDiskDir(pool, ctx.String("source"))
	config, err := virsh.ParseConfig(diskDir)
	if err != nil {
		logger.Errorf("ParseConfig err:%+v", err)
		return err
	}
	if !utils.Exists(config["current"]) {
		return errors.New(fmt.Sprintf("current disk %s not exists", config["current"]))
	}

	targetSSDir := filepath.Join(diskDir, "snapshots")
	if !utils.Exists(targetSSDir) {
		os.MkdirAll(targetSSDir, os.ModePerm)
	}
	//targetSSPath := filepath.Join(targetSSDir, fmt.Sprintf("%s.%s", ctx.String("name"), ctx.String("format")))
	targetSSPath := filepath.Join(targetSSDir, ctx.String("name"))
	if domain == "" { // without domain
		// create snapshot
		if err := virsh.CreateDiskWithBacking(ctx.String("format"), config["current"], ctx.String("format"), targetSSPath); err != nil {
			logger.Errorf("CreateDiskWithBacking err:%+v", err)
			return err
		}
	} else { // with domain
		// todo
		//if virsh.CheckDiskInUse(config["current"]) {
		//	return fmt.Errorf("disk %s is in use", config["current"])
		//}
		res, err := virsh.CheckVMDiskSpec(domain, config["current"])
		if err != nil {
			logger.Errorf("CheckVMDiskSpec err:%+v", err)
			return err
		}
		noNeedSnapshotDisk := ""
		for k, v := range res {
			if k != config["current"] {
				noNeedSnapshotDisk = fmt.Sprintf("%s --diskspec %s,snapshot=no ", noNeedSnapshotDisk, v)
			}
		}
		if err = virsh.CreateExternalSnapshot(domain, ctx.String("name"), config["current"], targetSSPath, noNeedSnapshotDisk, ctx.String("format")); err != nil {
			logger.Errorf("CreateExternalSnapshot err:%+v", err)
			return err
		}
	}
	// update vmd
	ksgvr := k8s.NewKsGvr(constant.VMDS_Kind)
	vmd, err := ksgvr.Get(ctx.Context, constant.DefaultNamespace, ctx.String("source"))
	if err != nil {
		createBackup(targetSSPath)
		logger.Errorf("fail to get vmd:%+v", err)
		return err
	}
	res, _ := k8s.GetCRDSpec(vmd.Spec.Raw, constant.CRD_Volume_Key)
	res["disk"] = ctx.String("source")
	res["current"] = targetSSPath
	if err = ksgvr.Update(ctx.Context, constant.DefaultNamespace, ctx.String("source"), constant.CRD_Volume_Key, res); err != nil {
		createBackup(targetSSPath)
		logger.Errorf("fail to update vmd:%+v", err)
		return err
	}

	// update vmdsn
	ksgvr2 := k8s.NewKsGvr(constant.VMDSNS_Kinds)
	vms, err := ksgvr2.Get(ctx.Context, constant.DefaultNamespace, ctx.String("name"))
	if err != nil {
		createBackup(targetSSPath)
		logger.Errorf("fail to get vmdsn:%+v", err)
		return err
	}
	res, _ = k8s.GetCRDSpec(vms.Spec.Raw, constant.CRD_Volume_Key)
	res["disk"] = ctx.String("source")
	res["pool"] = pool
	res["snapshot"] = ctx.String("name")
	res["current"] = targetSSPath
	res["format"] = ctx.String("format")
	res["domain"] = ctx.String("domain")
	// fix add vm
	res["vm"] = ctx.String("domain")
	// todo ?
	res["full_backing_filename"] = config["current"]
	if err = ksgvr2.Update(ctx.Context, constant.DefaultNamespace, ctx.String("name"), constant.CRD_Volume_Key, res); err != nil {
		createBackup(targetSSPath)
		logger.Errorf("fail to update vmdsn:%+v", err)
		return err
	}

	// write config: current point to snapshot
	//backFile := config["current"]
	config["current"] = targetSSPath
	virsh.CreateConfig(diskDir, config)
	return nil
}
