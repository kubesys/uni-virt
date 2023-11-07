package pool

import (
	"fmt"
	"github.com/kube-stack/sdsctl/pkg/constant"
	"github.com/kube-stack/sdsctl/pkg/k8s"
	"github.com/kube-stack/sdsctl/pkg/rook"
	"github.com/kube-stack/sdsctl/pkg/utils"
	"github.com/urfave/cli/v2"
	"strings"
)

func NewCreateRgwPoolCommand() *cli.Command {
	return &cli.Command{
		Name:      "create-rgw-pool",
		Usage:     "create rgw image pool for kubestack",
		UsageText: "sdsctl [global options] create-rgw-pool [options]",
		Action:    backcreateRgwPool,
		Flags: []cli.Flag{
			&cli.StringFlag{
				Name:  "name",
				Usage: "name of pool",
			},
		},
	}
}

func backcreateRgwPool(ctx *cli.Context) error {
	err := createRgwPool(ctx)
	ksgvr := k8s.NewKsGvr(constant.VMPS_Kind)
	if err != nil && !strings.Contains(err.Error(), "already exists") {
		ksgvr.UpdateWithStatus(ctx.Context, constant.DefaultNamespace, ctx.String("pool"), constant.CRD_Pool_Key, nil, err.Error(), "400")
	}
	return err
}

func createRgwPool(ctx *cli.Context) error {
	logger := utils.GetLogger()
	name := ctx.String("name")
	// create storageclass & obc
	if err := rook.CreateBucketStorageClass(); err != nil && !strings.Contains(err.Error(), "already exists") {
		return err
	}
	if err := rook.CreateOBC(constant.DefaultCephRwgName); err != nil && !strings.Contains(err.Error(), "already exists") {
		return err
	}

	// update vmp crd
	info, err := rook.GetBucketInfo(constant.DefaultCephRwgName)
	if err != nil {
		return err
	}
	secret, err := rook.GetBucketSecret(constant.DefaultCephRwgName)
	if err != nil {
		return err
	}
	logger.Infof("bucket secret: %+v", secret)
	ksgvr := k8s.NewKsGvr(constant.VMPS_Kind)
	flags := map[string]string{
		"pool":       name,
		"content":    "vmdi",
		"type":       constant.PoolCephRgwType,
		"host":       info["host"],
		"bucket":     info["name"],
		"access-id":  secret["access-id"],
		"access-key": secret["access-key"],
		"url":        fmt.Sprintf("%s:%s", info["ip"], info["port"]),
		"state":      constant.CRD_Pool_Active,
		"autostart":  "false",
	}
	if err := ksgvr.Update(ctx.Context, constant.DefaultNamespace, name, constant.CRD_Pool_Key, flags); err != nil {
		return err
	}
	return nil
}
