package disk

import (
	"errors"
	"fmt"
	"github.com/kube-stack/sdsctl/pkg/constant"
	"github.com/kube-stack/sdsctl/pkg/k8s"
	"github.com/kube-stack/sdsctl/pkg/utils"
	"github.com/kube-stack/sdsctl/pkg/virsh"
	"github.com/urfave/cli/v2"
	"strings"
)

func NewCreateDiskCommand() *cli.Command {
	return &cli.Command{
		Name:      "create-disk",
		Usage:     "create kvm disk for kubestack",
		UsageText: "sdsctl [global options] create-disk [options]",
		Action:    backcreateDisk,
		Flags: []cli.Flag{
			&cli.StringFlag{
				Name:  "type",
				Usage: "storage vol type",
				Value: "dir",
			},
			&cli.StringFlag{
				Name:  "pool",
				Usage: "storage pool name",
				Value: "localfs",
			},
			&cli.StringFlag{
				Name:  "vol",
				Usage: "storage vol name",
			},
			&cli.StringFlag{
				Name:  "capacity",
				Usage: "storage vol name",
			},
			&cli.StringFlag{
				Name:  "format",
				Usage: "storage vol format",
			},
		},
	}
}

func backcreateDisk(ctx *cli.Context) error {
	err := createDisk(ctx)
	ksgvr := k8s.NewKsGvr(constant.VMDS_Kind)
	//logger := utils.GetLogger()
	if err != nil && !strings.Contains(err.Error(), "already exist") {
		//logger.Errorf("err here1:%+v", err)
		ksgvr.UpdateWithStatus(ctx.Context, constant.DefaultNamespace, ctx.String("vol"), constant.CRD_Volume_Key, nil, err.Error(), "400")
	}
	return err
}

// sdsctl create-disk --capacity 10G --format qcow2 --pool poolhub111 --type localfs --vol diskhub111
func createDisk(ctx *cli.Context) error {
	logger := utils.GetLogger()
	pool := ctx.String("pool")
	active, err := virsh.IsPoolActive(pool)
	if err != nil {
		logger.Errorf("IsPoolActive err:%+v", err)
		return err
	} else if !active {
		return fmt.Errorf("pool %+v is inactive", pool)
	}
	exist := virsh.IsDiskExist(pool, ctx.String("vol"))
	if exist {
		return errors.New(fmt.Sprintf("the volume %+v is already exist", ctx.String("vol")))
	}

	bytes, _ := virsh.ParseCapacity(ctx.String("capacity"))

	if err = virsh.CreateDisk(pool, ctx.String("vol"), ctx.String("capacity"), ctx.String("format")); err != nil {
		return err
	}
	// craete config.json
	diskPath, _ := virsh.ParseDiskDir(pool, ctx.String("vol"))
	volPath, _ := virsh.ParseDiskPath(pool, ctx.String("vol"))
	cfg := map[string]string{
		"name":    ctx.String("vol"),
		"dir":     diskPath,
		"current": volPath,
		"pool":    pool,
	}
	if err := virsh.CreateConfig(diskPath, cfg); err != nil {
		logger.Errorf("CreateConfig err:%+v", err)
		return err
	}
	// update vmd
	ksgvr := k8s.NewKsGvr(constant.VMDS_Kind)
	flags := utils.ParseFlagMap(ctx)
	delete(flags, "capacity")
	extra := map[string]interface{}{
		"current":  volPath,
		"capacity": virsh.UniformBytes(bytes),
		// fix add vm
		"vm": "",
	}
	flags = utils.MergeFlags(flags, extra)
	if err = ksgvr.Update(ctx.Context, constant.DefaultNamespace, ctx.String("vol"), constant.CRD_Volume_Key, flags); err != nil {
		logger.Errorf("ksgvr.Update err:%+v", err)
		return err
	}

	return err
}
