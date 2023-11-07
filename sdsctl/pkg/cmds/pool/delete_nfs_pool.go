package pool

import (
	"github.com/kube-stack/sdsctl/pkg/constant"
	"github.com/kube-stack/sdsctl/pkg/k8s"
	"github.com/kube-stack/sdsctl/pkg/rook"
	"github.com/urfave/cli/v2"
)

func NewDeleteNFSPoolCommand() *cli.Command {
	return &cli.Command{
		Name:      "delete-nfs-pool",
		Usage:     "delete nfs image pool for kubestack",
		UsageText: "sdsctl [global options] delete-nfs-pool [options]",
		Action:    backdeleteNFSPool,
		Flags: []cli.Flag{
			&cli.StringFlag{
				Name:  "name",
				Usage: "name of pool",
			},
		},
	}
}

func backdeleteNFSPool(ctx *cli.Context) error {
	err := deleteNFSPool(ctx)
	ksgvr := k8s.NewKsGvr(constant.VMPS_Kind)
	if err != nil {
		ksgvr.UpdateWithStatus(ctx.Context, constant.DefaultNamespace, ctx.String("pool"), constant.CRD_Pool_Key, nil, err.Error(), "400")
	}
	return err
}

func deleteNFSPool(ctx *cli.Context) error {
	name := ctx.String("name")
	//ksgvr := k8s.NewExternalGvr(constant.DefaultRookGroup, constant.DefaultRookVersion, constant.CephNFSPoolS_Kinds)
	ksgvr := k8s.NewKsGvr(constant.VMPS_Kind)
	vmp, err := ksgvr.Get(ctx.Context, constant.DefaultNamespace, name)
	if err != nil {
		return err
	}
	res, _ := k8s.GetCRDSpec(vmp.Spec.Raw, constant.CRD_Pool_Key)
	if err := rook.UmountNfs(res["local-path"]); err != nil {
		return err
	}
	if err := rook.ExportDeleteNFSPath(constant.DefaultNFSClusterName, name); err != nil {
		return err
	}

	// delete vmp
	return ksgvr.Delete(ctx.Context, constant.DefaultNamespace, name)
}
