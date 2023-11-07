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

func NewDeleteExternalSnapshotCommand() *cli.Command {
	return &cli.Command{
		Name:      "delete-external-snapshot",
		Usage:     "delete kvm snapshot for kubestack",
		UsageText: "sdsctl [global options] delete-external-snapshot [options]",
		Action:    backdeleteExternalSnapshot,
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

func backdeleteExternalSnapshot(ctx *cli.Context) error {
	err := deleteExternalSnapshot(ctx)
	ksgvr := k8s.NewKsGvr(constant.VMDSNS_Kinds)
	if err != nil {
		ksgvr.UpdateWithStatus(ctx.Context, constant.DefaultNamespace, ctx.String("name"), constant.CRD_Volume_Key, nil, err.Error(), "400")
	}
	return err
}

func deleteExternalSnapshot(ctx *cli.Context) error {
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
	targetSSDir := filepath.Join(diskDir, "snapshots")
	targetSSPath := filepath.Join(targetSSDir, ctx.String("name"))
	backFile, _ := virsh.GetBackFile(targetSSPath)
	logger.Infof("back file of %s: %s", targetSSPath, backFile)
	snapshotFiles := utils.GetFilesUnderDir(targetSSDir)
	files, err := virsh.GetBackChainFiles(snapshotFiles, targetSSPath)
	logger.Infof("delete files:%+v", files)
	if err != nil {
		logger.Errorf("GetBackChainFiles err:%+v", err)
		return err
	}
	// add snapshot
	files[filepath.Join(targetSSDir, ctx.String("name"))] = true

	// 删除的是current的祖先
	//vol := ctx.String("source")
	ksgvr := k8s.NewKsGvr(constant.VMDSNS_Kinds)
	if _, ok := files[config["current"]]; ok {
		vmActive := false
		if domain != "" {
			vmActive, err = virsh.IsVMActive(domain)
			if err != nil {
				logger.Errorf("IsVMActive err:%+v", err)
				return err
			}
		}
		// todo check?
		if domain != "" && vmActive {
			// live chain
			logger.Infof("domain LiveBlockForVMDisk")
			if err := virsh.LiveBlockForVMDisk(domain, config["current"], backFile); err != nil {
				logger.Errorf("LiveBlocksForVMDisk err:%+v", err)
				return err
			}
		} else {
			logger.Infof("no domain, RebaseDiskSnapshot")
			if err := virsh.RebaseDiskSnapshot(backFile, config["current"], ""); err != nil {
				logger.Errorf("RebaseDiskSnapshot err:%+v", err)
				return err
			}
		}
		// update current
		// 若是plain disk，则无需更新
		if strings.Contains(config["current"], "snapshots") {
			currentSnapShot := filepath.Base(config["current"])
			vms, err := ksgvr.Get(ctx.Context, constant.DefaultNamespace, currentSnapShot)
			if err != nil {
				logger.Errorf("fail to get vmdsn:%+v", err)
				return err
			}
			res, _ := k8s.GetCRDSpec(vms.Spec.Raw, constant.CRD_Volume_Key)
			res["full_backing_filename"] = backFile
			logger.Infof("res:%+v", res)
			if err = ksgvr.Update(ctx.Context, constant.DefaultNamespace, currentSnapShot, constant.CRD_Volume_Key, res); err != nil {
				logger.Errorf("fail to update vmdsn:%+v", err)
				return err
			}
			//delete(files, filepath.Base(config["current"]))
			delete(files, config["current"])
		}
	}

	logger.Infof("delete files:%+v", files)
	// delete files
	for k, _ := range files {
		//fullPath := filepath.Join(config["dir"], "snapshots", k)
		logger.Infof("delete file:%+v", k)
		os.Remove(k)
	}

	// delete vmdsn
	for k, _ := range files {
		vmdsnName := filepath.Base(k)
		if err := ksgvr.Delete(ctx.Context, constant.DefaultNamespace, vmdsnName); err != nil {
			logger.Errorf("ksgvr.Delete err:%+v", err)
			return err
		}
	}
	return nil
}
