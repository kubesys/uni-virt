package pool

import (
	"github.com/kube-stack/sdsctl/pkg/constant"
	"github.com/kube-stack/sdsctl/pkg/k8s"
	"github.com/kube-stack/sdsctl/pkg/virsh"
	"github.com/urfave/cli/v2"
)

func NewDeletePoolCommand() *cli.Command {
	return &cli.Command{
		Name:      "delete-pool",
		Usage:     "delete kvm pool for kubestack",
		UsageText: "sdsctl [global options] delete-pool [options]",
		Action:    backdeletePool,
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

func backdeletePool(ctx *cli.Context) error {
	err := deletePool(ctx)
	ksgvr := k8s.NewKsGvr(constant.VMPS_Kind)
	if err != nil {
		ksgvr.UpdateWithStatus(ctx.Context, constant.DefaultNamespace, ctx.String("pool"), constant.CRD_Pool_Key, nil, err.Error(), "400")
	}
	return err
}

func deletePool(ctx *cli.Context) error {
	if err := virsh.DeletePool(ctx.String("pool")); err != nil {
		// backup
		virsh.StartPool(ctx.String("pool"))
		return err
	}
	// delete vmp
	ksgvr := k8s.NewKsGvr(constant.VMPS_Kind)
	if err := ksgvr.Delete(ctx.Context, constant.DefaultNamespace, ctx.String("pool")); err != nil {
		return err
	}
	return nil
}
