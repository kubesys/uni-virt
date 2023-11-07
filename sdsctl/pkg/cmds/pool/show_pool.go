package pool

import (
	"fmt"
	"github.com/kube-stack/sdsctl/pkg/constant"
	"github.com/kube-stack/sdsctl/pkg/k8s"
	"github.com/kube-stack/sdsctl/pkg/utils"
	"github.com/kube-stack/sdsctl/pkg/virsh"
	"github.com/urfave/cli/v2"
)

func NewShowPoolCommand() *cli.Command {
	return &cli.Command{
		Name:      "show-pool",
		Usage:     "show kvm pool for kubestack",
		UsageText: "sdsctl [global options] show-pool [options]",
		Action:    backshowPool,
		Flags: []cli.Flag{
			&cli.StringFlag{
				Name:  "type",
				Usage: "storage pool type",
				Value: "dir",
			},
			&cli.StringFlag{
				Name:  "pool",
				Usage: "storage pool type",
			},
			//&cli.StringFlag{
			//	Name:  "auto-start",
			//	Usage: "if auto-start pool",
			//	Value: "true",
			//},
		},
	}
}

func backshowPool(ctx *cli.Context) error {
	err := showPool(ctx)
	ksgvr := k8s.NewKsGvr(constant.VMPS_Kind)
	if err != nil {
		ksgvr.UpdateWithStatus(ctx.Context, constant.DefaultNamespace, ctx.String("pool"), constant.CRD_Pool_Key, nil, err.Error(), "400")
	}
	return err
}

func showPool(ctx *cli.Context) error {

	name := ctx.String("pool")
	pool, err := virsh.GetPoolInfo(name)
	if err != nil {
		return err
	}
	info, _ := pool.GetInfo()
	ksgvr := k8s.NewKsGvr(constant.VMPS_Kind)
	vmp, err := ksgvr.Get(ctx.Context, "default", name)
	if err != nil {
		return err
	}

	flags := utils.ParseFlagMap(ctx)
	uuid, _ := pool.GetUUIDString()
	extra := map[string]interface{}{
		"state":      virsh.GetPoolState(info.State),
		"uuid":       uuid,
		"free":       virsh.UniformBytes(info.Available),
		"capacity":   virsh.UniformBytes(info.Capacity),
		"allocation": virsh.UniformBytes(info.Allocation),
		"msg":        vmp.Spec.String(),
	}
	flags = utils.MergeFlags(flags, extra)
	fmt.Println(flags)

	return nil
}
