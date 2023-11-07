package pool

import (
	"fmt"
	"github.com/kube-stack/sdsctl/pkg/constant"
	"github.com/kube-stack/sdsctl/pkg/k8s"
	"github.com/kube-stack/sdsctl/pkg/virsh"
	"github.com/urfave/cli/v2"
)

func NewStartPoolCommand() *cli.Command {
	return &cli.Command{
		Name:      "start-pool",
		Usage:     "start kvm pool for kubestack",
		UsageText: "sdsctl [global options] start-pool [options]",
		Action:    backstartPool,
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

// sdsctl start-pool --pool poolhub111
func backstartPool(ctx *cli.Context) error {
	err := startPool(ctx)
	ksgvr := k8s.NewKsGvr(constant.VMPS_Kind)
	if err != nil {
		ksgvr.UpdateWithStatus(ctx.Context, constant.DefaultNamespace, ctx.String("pool"), constant.CRD_Pool_Key, nil, err.Error(), "400")
	}
	return err
}

func startPool(ctx *cli.Context) error {
	if err := virsh.StartPool(ctx.String("pool")); err != nil {
		return err
	}
	// update vmp
	ksgvr := k8s.NewKsGvr(constant.VMPS_Kind)
	updateKey := fmt.Sprintf("%s.state", constant.CRD_Pool_Key)
	if err := ksgvr.Update(ctx.Context, constant.DefaultNamespace, ctx.String("pool"), updateKey, constant.CRD_Pool_Active); err != nil {
		return err
	}
	return nil
}
