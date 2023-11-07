package internalSnapshot

import (
	"fmt"
	"github.com/kube-stack/sdsctl/pkg/constant"
	"github.com/kube-stack/sdsctl/pkg/k8s"
	"github.com/kube-stack/sdsctl/pkg/utils"
	"github.com/kube-stack/sdsctl/pkg/virsh"
	"github.com/urfave/cli/v2"
)

func NewDeleteInternalSnapshotCommand() *cli.Command {
	return &cli.Command{
		Name:      "delete-internal-snapshot",
		Usage:     "delete internal snapshot for kubestack",
		UsageText: "sdsctl [global options] delete-internal-snapshot [options]",
		Action:    backdeleteInternalSnapshot,
		Flags: []cli.Flag{
			&cli.StringFlag{
				Name:  "type",
				Usage: "storage vol type",
				Value: "dir",
			},
			&cli.StringFlag{
				Name:  "domain",
				Usage: "domain name",
			},
			&cli.StringFlag{
				Name:  "name",
				Usage: "storage disk name",
			},
			&cli.StringFlag{
				Name:  "snapshot",
				Usage: "storage vol format",
			},
		},
	}
}

func backdeleteInternalSnapshot(ctx *cli.Context) error {
	err := deleteInternalSnapshot(ctx)
	ksgvr := k8s.NewKsGvr(constant.VMDS_Kind)
	updateKey := fmt.Sprintf("%s.snapshots", constant.CRD_Volume_Key)
	if err != nil {
		ksgvr.UpdateWithStatus(ctx.Context, constant.DefaultNamespace, ctx.String("name"), updateKey, nil, err.Error(), "400")
	}
	return err
}

func deleteInternalSnapshot(ctx *cli.Context) error {
	logger := utils.GetLogger()
	domainName := ctx.String("domain")
	if domainName == "" {
		return fmt.Errorf("domain can't be empty")
	}
	if !virsh.IsVMExist(domainName) {
		return fmt.Errorf("no domain named %s", domainName)
	}
	if err := checkDomainDisk(ctx, domainName); err != nil {
		logger.Errorf("checkDomainDisk err:%+v", err)
		return err
	}
	if err := virsh.DeleteInternalSnapshot(domainName, ctx.String("snapshot")); err != nil {
		logger.Errorf("DeleteInternalSnapshot err:%+v", err)
		return err
	}
	return updateVMDSnapshot(ctx, domainName)
}
