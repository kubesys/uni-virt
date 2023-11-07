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

func NewResizeDiskCommand() *cli.Command {
	return &cli.Command{
		Name:      "resize-disk",
		Usage:     "resize kvm disk for kubestack",
		UsageText: "sdsctl [global options] resize-disk [options]",
		Action:    backresizeDisk,
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
			&cli.StringFlag{
				Name:  "capacity",
				Usage: "new storage vol capacity",
			},
		},
	}
}

//sdsctl resize-disk --capacity 3G --pool poolhub111 --type localfs --vol diskhub111

func backresizeDisk(ctx *cli.Context) error {
	err := resizeDisk(ctx)
	ksgvr := k8s.NewKsGvr(constant.VMDS_Kind)
	if err != nil && !strings.Contains(err.Error(), "no change") {
		ksgvr.UpdateWithStatus(ctx.Context, constant.DefaultNamespace, ctx.String("vol"), constant.CRD_Volume_Key, nil, err.Error(), "400")
	}
	return err
}

func resizeDisk(ctx *cli.Context) error {
	logger := utils.GetLogger()
	pool := ctx.String("pool")
	bytes, _ := virsh.ParseCapacity(ctx.String("capacity"))
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

	if err := virsh.ResizeDisk(pool, ctx.String("vol"), ctx.String("capacity")); err != nil {
		logger.Errorf("resize disk err:%+v", err)
		return err
	}

	// update vmd
	capacity := virsh.UniformBytes(bytes)
	ksgvr := k8s.NewKsGvr(constant.VMDS_Kind)
	updateKey := fmt.Sprintf("%s.capacity", constant.CRD_Volume_Key)
	if err := ksgvr.Update(ctx.Context, constant.DefaultNamespace, ctx.String("vol"), updateKey, capacity); err != nil {
		logger.Errorf("ksgvr.Update err:%+v", err)
		return err
	}
	return nil
}
