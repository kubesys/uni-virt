package pool

import (
	"fmt"
	"github.com/kube-stack/sdsctl/pkg/constant"
	"github.com/kube-stack/sdsctl/pkg/k8s"
	"github.com/kube-stack/sdsctl/pkg/virsh"
	"github.com/urfave/cli/v2"
)

func NewAutoStartPoolCommand() *cli.Command {
	return &cli.Command{
		Name:      "auto-start-pool",
		Usage:     "auto-start kvm pool for kubestack",
		UsageText: "sdsctl [global options] auto-start-pool [options]",
		Action:    backautostartPool,
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
			&cli.BoolFlag{
				Name:  "auto-start",
				Usage: "if auto-start pool",
				Value: true,
			},
		},
	}
}

func backautostartPool(ctx *cli.Context) error {
	err := autostartPool(ctx)
	ksgvr := k8s.NewKsGvr(constant.VMPS_Kind)
	if err != nil {
		ksgvr.UpdateWithStatus(ctx.Context, constant.DefaultNamespace, ctx.String("pool"), constant.CRD_Pool_Key, nil, err.Error(), "400")
	}
	return err
}

func autostartPool(ctx *cli.Context) error {
	//autoStart, err := strconv.ParseBool(ctx.String("auto-start"))
	//if err != nil {
	//	return err
	//}
	autoStart := ctx.Bool("auto-start")
	if err := virsh.AutoStartPool(ctx.String("pool"), autoStart); err != nil {
		return err
	}
	// update vmp
	ksgvr := k8s.NewKsGvr(constant.VMPS_Kind)
	updateKey := fmt.Sprintf("%s.autostart", constant.CRD_Pool_Key)
	if err := ksgvr.Update(ctx.Context, constant.DefaultNamespace, ctx.String("pool"), updateKey, autoStart); err != nil {
		return err
	}
	return nil
}
