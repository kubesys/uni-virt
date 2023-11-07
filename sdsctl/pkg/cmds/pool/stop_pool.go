package pool

import (
	"fmt"
	"github.com/kube-stack/sdsctl/pkg/constant"
	"github.com/kube-stack/sdsctl/pkg/k8s"
	"github.com/kube-stack/sdsctl/pkg/virsh"
	"github.com/urfave/cli/v2"
)

func NewStopPoolCommand() *cli.Command {
	return &cli.Command{
		Name:      "stop-pool",
		Usage:     "stop kvm pool for kubestack",
		UsageText: "sdsctl [global options] stop-pool [options]",
		Action:    backstopPool,
		Flags: []cli.Flag{
			&cli.StringFlag{
				Name:  "pool",
				Usage: "name of storage pool",
			},
			&cli.StringFlag{
				Name:  "type",
				Usage: "storage pool type ",
				Value: "dir",
			},
		},
	}
}

// sdsctl stop-pool --pool poolhub111
func backstopPool(ctx *cli.Context) error {
	err := stopPool(ctx)
	ksgvr := k8s.NewKsGvr(constant.VMPS_Kind)
	if err != nil {
		ksgvr.UpdateWithStatus(ctx.Context, constant.DefaultNamespace, ctx.String("pool"), constant.CRD_Pool_Key, nil, err.Error(), "400")
	}
	return err
}

func stopPool(ctx *cli.Context) error {
	if err := virsh.StopPool(ctx.String("pool")); err != nil {
		return err
	}
	// update vmp
	ksgvr := k8s.NewKsGvr(constant.VMPS_Kind)
	updateKey := fmt.Sprintf("%s.state", constant.CRD_Pool_Key)
	if err := ksgvr.Update(ctx.Context, constant.DefaultNamespace, ctx.String("pool"), updateKey, constant.CRD_Pool_Inactive); err != nil {
		return err
	}
	return nil
}
