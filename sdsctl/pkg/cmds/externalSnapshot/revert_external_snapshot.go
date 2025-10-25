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

func NewRevertExternalSnapshotCommand() *cli.Command {
	return &cli.Command{
		Name:      "revert-external-snapshot",
		Usage:     "revert kvm snapshot for kubestack",
		UsageText: "sdsctl [global options] revert-external-snapshot [options]",
		Action:    backrevertExternalSnapshot,
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

func backrevertExternalSnapshot(ctx *cli.Context) error {
	err := revertExternalSnapshot(ctx)
	ksgvr := k8s.NewKsGvr(constant.VMDSNS_Kinds)
	if err != nil {
		ksgvr.UpdateWithStatus(ctx.Context, constant.DefaultNamespace, ctx.String("name"), constant.CRD_Volume_Key, nil, err.Error(), "400")
	}
	return err
}

func revertBackup(path string) {
	os.Remove(path)
}

// revert snapshot {name} 到上一个版本（back file）
func revertExternalSnapshot(ctx *cli.Context) error {
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

	exist := virsh.IsDiskSnapshotExist(pool, ctx.String("source"), ctx.String("snapshot"))
	if !exist {
		return errors.New(fmt.Sprintf("the snapshot %+v is not exist", ctx.String("source")))
	}
	diskDir, _ := virsh.ParseDiskDir(pool, ctx.String("source"))
	config, err := virsh.ParseConfig(diskDir)
	if err != nil {
		logger.Errorf("ParseConfig err:%+v", err)
		return err
	}
	if virsh.CheckDiskInUse(config["current"]) {
		return errors.New("current disk in use, plz check or set real domain field")
	}

	if domain != "" {
		vmActive, err := virsh.IsVMActive(domain)
		if err != nil {
			logger.Errorf("IsVMActive err:%+v", err)
			return err
		}
		if vmActive {
			return fmt.Errorf("domain %s is still active, plz stop it first", domain)
		}
	}
	backFile, err := virsh.GetBackFile(config["current"])
	if err != nil {
		return fmt.Errorf("get backing file failed: %v", err)
	}

	newFile := utils.GetUUID()
	newFilePath := filepath.Join(utils.GetDir(backFile), newFile)
	if !strings.Contains(newFilePath, "snapshots") {
		newFilePath = filepath.Join(utils.GetDir(backFile), "snapshots", newFile)
	}
	if err := virsh.CreateDiskWithBacking(ctx.String("format"), backFile, ctx.String("format"), newFilePath); err != nil {
		logger.Errorf("CreateDiskWithBacking err:%+v", err)
		return err
	}
	// change vm disk
	if domain != "" {
		if err := virsh.ChangeVMDisk(domain, config["current"], backFile); err != nil {
			revertBackup(newFilePath)
			logger.Errorf("ChangeVMDisk err:%+v", err)
			return err
		}
	}

	// update vmd
	ksgvr := k8s.NewKsGvr(constant.VMDS_Kind)
	vmd, err := ksgvr.Get(ctx.Context, constant.DefaultNamespace, ctx.String("source"))
	if err != nil {
		revertBackup(newFilePath)
		logger.Errorf("ksgvr.Get err:%+v", err)
		return err
	}
	res, _ := k8s.GetCRDSpec(vmd.Spec.Raw, constant.CRD_Volume_Key)
	res["disk"] = ctx.String("source")
	res["current"] = newFilePath
	res["full_backing_filename"] = backFile
	if err = ksgvr.Update(ctx.Context, constant.DefaultNamespace, ctx.String("source"), constant.CRD_Volume_Key, res); err != nil {
		revertBackup(newFilePath)
		return err
	}

	// create new disk snapshot
	logger.Infof("create vmdsn %s", newFile)
	ksgvr2 := k8s.NewKsGvr(constant.VMDSNS_Kinds)
	vmdsn, err := ksgvr2.Get(ctx.Context, constant.DefaultNamespace, ctx.String("name"))
	if err != nil {
		revertBackup(newFilePath)
		logger.Errorf("ksgvr2.Get err:%+v", err)
		return err
	}
	res2, _ := k8s.GetCRDSpec(vmdsn.Spec.Raw, constant.CRD_Volume_Key)
	res2["snapshot"] = newFile
	res2["current"] = newFilePath
	res2["format"] = ctx.String("format")
	if err = ksgvr2.Create(ctx.Context, constant.DefaultNamespace, newFile, constant.CRD_Volume_Key, res2); err != nil {
		revertBackup(newFilePath)
		logger.Errorf("ksgvr2.Create err:%+v", err)
		return err
	}

	// write config: current point to snapshot
	revertBackup(config["current"])
	config["current"] = backFile
	virsh.CreateConfig(diskDir, config)

	return nil
}
