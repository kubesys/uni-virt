package pool

import (
	"github.com/kube-stack/sdsctl/pkg/constant"
	"github.com/kube-stack/sdsctl/pkg/k8s"
	"github.com/kube-stack/sdsctl/pkg/rook"
	"github.com/kube-stack/sdsctl/pkg/utils"
	"github.com/urfave/cli/v2"
)

func NewDeleteRgwPoolCommand() *cli.Command {
	return &cli.Command{
		Name:      "delete-rgw-pool",
		Usage:     "delete rgw image pool for kubestack",
		UsageText: "sdsctl [global options] delete-rgw-pool [options]",
		Action:    backdeleteRgwPool,
		Flags: []cli.Flag{
			&cli.StringFlag{
				Name:  "name",
				Usage: "name of pool",
			},
		},
	}
}

func backdeleteRgwPool(ctx *cli.Context) error {
	err := deleteRgwPool(ctx)
	ksgvr := k8s.NewKsGvr(constant.VMPS_Kind)
	if err != nil {
		ksgvr.UpdateWithStatus(ctx.Context, constant.DefaultNamespace, ctx.String("pool"), constant.CRD_Pool_Key, nil, err.Error(), "400")
	}
	return err
}

func deleteRgwPool(ctx *cli.Context) error {
	name := ctx.String("name")
	logger := utils.GetLogger()
	// delete storageclass & obc
	if err := rook.DeleteOBC(constant.DefaultCephRwgName); err != nil {
		return err
	}
	//if err := rook.DeleteBucketStorageClass(); err != nil {
	//	return err
	//}
	logger.Info("delete bucket storageclass")

	// delete vmp
	ksgvr2 := k8s.NewKsGvr(constant.VMPS_Kind)
	return ksgvr2.Delete(ctx.Context, constant.DefaultNamespace, name)
}
