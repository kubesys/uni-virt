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
	"strings"
)

func NewCreateDiskFromImageCommand() *cli.Command {
	return &cli.Command{
		Name:      "create-disk-from-image",
		Usage:     "create disk from image for kubestack",
		UsageText: "sdsctl [global options] create-disk-from-image [options]",
		Action:    backcreateDiskFromImage,
		Flags: []cli.Flag{
			&cli.StringFlag{
				Name:  "type",
				Usage: "storage vol type",
				Value: "dir",
			},
			&cli.StringFlag{
				Name:  "targetPool",
				Usage: "storage pool name",
			},
			&cli.StringFlag{
				Name:  "name",
				Usage: "new storage disk name",
			},
			&cli.StringFlag{
				Name:  "source",
				Usage: "source storage vol path",
			},
			&cli.BoolFlag{
				Name:  "full-copy",
				Usage: "if full-copy, new disk will be created by snapshot",
			},
		},
	}
}

func backcreateDiskFromImage(ctx *cli.Context) error {
	err := createDiskFromImage(ctx)
	ksgvr := k8s.NewKsGvr(constant.VMDS_Kind)
	if err != nil && !strings.Contains(err.Error(), "already exists") {
		ksgvr.UpdateWithStatus(ctx.Context, constant.DefaultNamespace, ctx.String("vol"), constant.CRD_Volume_Key, nil, err.Error(), "400")
	}
	return err
}

func createDiskFromImage(ctx *cli.Context) error {
	logger := utils.GetLogger()
	pool := ctx.String("targetPool")
	parseBool := ctx.Bool("full-copy")
	//if err != nil {
	//	logger.Errorf("ParseBool full-copy err:%+v", err)
	//	return err
	//}
	active, err := virsh.IsPoolActive(pool)
	if err != nil {
		logger.Errorf("IsPoolActive err:%+v", err)
		return err
	} else if !active {
		return fmt.Errorf("pool %+v is inactive", pool)
	}
	exist := virsh.IsDiskExist(pool, ctx.String("source"))
	if exist {
		return errors.New(fmt.Sprintf("the volume %+v is already exist", ctx.String("source")))
	}

	// source
	image, _ := virsh.OpenImage(ctx.String("source"))
	// fix: iso not support
	if image.Format != "qcow2" {
		return errors.New(fmt.Sprintf("the volume %+v is not qcow2 format", ctx.String("source")))
	}

	sourceFormat := image.Format

	// target
	targetDiskDir, _ := virsh.ParseDiskDir(pool, ctx.String("name"))
	targetDiskPath := filepath.Join(targetDiskDir, ctx.String("name"))
	targetDiskConfig := filepath.Join(targetDiskDir, "config.json")
	if !utils.Exists(targetDiskDir) {
		os.MkdirAll(targetDiskDir, os.ModePerm)
	}
	if utils.Exists(targetDiskConfig) {
		return errors.New(fmt.Sprintf("target disk %s config already exists", targetDiskConfig))
	}

	if parseBool {
		if err := virsh.CreateFullCopyDisk(ctx.String("source"), sourceFormat, targetDiskPath); err != nil {
			logger.Errorf("CreateFullCopyDisk err:%+v", err)
			return err
		}
	} else {
		if err := virsh.CreateDiskWithBacking("qcow2", ctx.String("source"), sourceFormat, targetDiskPath); err != nil {
			logger.Errorf("CreateDiskWithBacking err:%+v", err)
			return err
		}
	}
	cfg := map[string]string{
		"name":    ctx.String("name"),
		"dir":     targetDiskDir,
		"current": targetDiskPath,
		"pool":    pool,
		// fix add vm
		"vm": "",
	}
	if err = virsh.CreateConfig(targetDiskDir, cfg); err != nil {
		logger.Errorf("virsh.CreateConfig err:%+v", err)
		return err
	}

	// update vmd
	ksgvr := k8s.NewKsGvr(constant.VMDS_Kind)
	flags := utils.ParseFlagMap(ctx)
	delete(flags, "name")
	extra := map[string]interface{}{
		"current":  targetDiskPath,
		"format":   "qcow2",
		"capacity": virsh.UniformBytes(image.Size),
	}
	flags = utils.MergeFlags(flags, extra)
	if err = ksgvr.Update(ctx.Context, constant.DefaultNamespace, ctx.String("name"), constant.CRD_Volume_Key, flags); err != nil {
		return err
	}
	return err
}
