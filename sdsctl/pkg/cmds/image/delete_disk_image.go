package image

import (
	"fmt"
	"github.com/kube-stack/sdsctl/pkg/constant"
	"github.com/kube-stack/sdsctl/pkg/k8s"
	"github.com/kube-stack/sdsctl/pkg/utils"
	"github.com/kube-stack/sdsctl/pkg/virsh"
	"github.com/urfave/cli/v2"
	"os"
)

func NewDeleteDiskImageCommand() *cli.Command {
	return &cli.Command{
		Name:      "delete-disk-image",
		Usage:     "delete disk image for kubestack",
		UsageText: "sdsctl [global options] delete-disk-image [options]",
		Action:    backdeleteDiskImage,
		Flags: []cli.Flag{
			&cli.StringFlag{
				Name:  "type",
				Usage: "storage vol type",
				Value: "dir",
			},
			&cli.StringFlag{
				Name:  "sourcePool",
				Usage: "vmdi storage pool name",
			},
			&cli.StringFlag{
				Name:  "name",
				Usage: "storage disk image name",
			},
		},
	}
}

func backdeleteDiskImage(ctx *cli.Context) error {
	err := deleteDiskImage(ctx)
	ksgvr := k8s.NewKsGvr(constant.VMDIS_KINDS)
	if err != nil {
		ksgvr.UpdateWithStatus(ctx.Context, constant.DefaultNamespace, ctx.String("name"), constant.CRD_Volume_Key, nil, err.Error(), "400")
	}
	return err
}

func deleteDiskImage(ctx *cli.Context) error {
	logger := utils.GetLogger()
	pool := ctx.String("sourcePool")
	active, err := virsh.IsPoolActive(pool)
	if err != nil {
		return err
	} else if !active {
		return fmt.Errorf("pool %+v is inactive", pool)
	}
	if !virsh.CheckPoolType(pool, "vmdi") {
		return fmt.Errorf("pool %s type error", pool)
	}
	if !virsh.IsDiskExist(pool, ctx.String("name")) {
		return fmt.Errorf("disk image %s is not exist", ctx.String("name"))
	}

	targetImageDir, _ := virsh.ParseDiskDir(pool, ctx.String("name"))
	if err = os.RemoveAll(targetImageDir); err != nil {
		logger.Errorf("os.RemoveAll err:%+v", err)
		return err
	}

	// delete vmdi
	ksgvr := k8s.NewKsGvr(constant.VMDIS_KINDS)
	if err = ksgvr.Delete(ctx.Context, constant.DefaultNamespace, ctx.String("name")); err != nil {
		return err
	}

	return nil
}
