package disk

import (
	"errors"
	"fmt"
	"github.com/kube-stack/sdsctl/pkg/constant"
	"github.com/kube-stack/sdsctl/pkg/k8s"
	"github.com/kube-stack/sdsctl/pkg/utils"
	"github.com/kube-stack/sdsctl/pkg/virsh"
	"github.com/urfave/cli/v2"
)

func NewDeleteDiskCommand() *cli.Command {
	return &cli.Command{
		Name:      "delete-disk",
		Usage:     "delete kvm disk for kubestack",
		UsageText: "sdsctl [global options] delete-disk [options]",
		Action:    backdeleteDisk,
		Flags: []cli.Flag{
			&cli.StringFlag{
				Name:  "type",
				Usage: "storage vol type",
				Value: "dir",
			},
			&cli.StringFlag{
				Name:  "pool",
				Usage: "storage pool name",
				Value: "dir",
			},
			&cli.StringFlag{
				Name:  "vol",
				Usage: "storage vol name",
			},
		},
	}
}

// sdsctl delete-disk --pool poolhub111 --vol diskhub111
func backdeleteDisk(ctx *cli.Context) error {
	err := deleteDisk(ctx)
	ksgvr := k8s.NewKsGvr(constant.VMDS_Kind)
	if err != nil {
		ksgvr.UpdateWithStatus(ctx.Context, constant.DefaultNamespace, ctx.String("vol"), constant.CRD_Volume_Key, nil, err.Error(), "400")
	}
	return err
}

func deleteDisk(ctx *cli.Context) error {
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
	if !exist {
		return errors.New(fmt.Sprintf("the volume %+v is not exist", ctx.String("vol")))
	}

	if err = virsh.DeleteDisk(pool, ctx.String("vol")); err != nil {
		logger.Errorf("DeleteDisk err:%+v", err)
		return err
	}

	// delete vmd
	ksgvr := k8s.NewKsGvr(constant.VMDS_Kind)
	if ksgvr.Delete(ctx.Context, constant.DefaultNamespace, ctx.String("vol")); err != nil {
		logger.Errorf("ksgvr.Delete err:%+v", err)
		return err
	}
	return nil
}
