package disk

import (
	"fmt"
	"github.com/kube-stack/sdsctl/pkg/constant"
	"github.com/kube-stack/sdsctl/pkg/k8s"
	"github.com/kube-stack/sdsctl/pkg/virsh"
	"github.com/urfave/cli/v2"
)

func NewShowDiskCommand() *cli.Command {
	return &cli.Command{
		Name:      "show-disk",
		Usage:     "show kvm disk for kubestack",
		UsageText: "sdsctl [global options] show-disk [options]",
		Action:    backshowDisk,
		Flags: []cli.Flag{
			&cli.StringFlag{
				Name:  "type",
				Usage: "storage vol type",
				Value: "dir",
			},
			&cli.StringFlag{
				Name:  "pool",
				Usage: "storage pool",
				Value: "dir",
			},
			&cli.StringFlag{
				Name:  "vol",
				Usage: "storage vol type",
			},
		},
	}
}

func backshowDisk(ctx *cli.Context) error {
	err := showDisk(ctx)
	ksgvr := k8s.NewKsGvr(constant.VMDS_Kind)
	if err != nil {
		ksgvr.UpdateWithStatus(ctx.Context, constant.DefaultNamespace, ctx.String("vol"), constant.CRD_Volume_Key, nil, err.Error(), "400")
	}
	return err
}

func showDisk(ctx *cli.Context) error {
	pool := ctx.String("pool")
	active, err := virsh.IsPoolActive(pool)
	if err != nil {
		return err
	} else if !active {
		return fmt.Errorf("pool %+v is inactive", pool)
	}

	return nil
}
