package pool

import (
	"fmt"
	"github.com/kube-stack/sdsctl/pkg/constant"
	"github.com/kube-stack/sdsctl/pkg/k8s"
	"github.com/kube-stack/sdsctl/pkg/rook"
	"github.com/kube-stack/sdsctl/pkg/utils"
	"github.com/urfave/cli/v2"
	"os"
	"strings"
)

func NewCreateNFSPoolCommand() *cli.Command {
	return &cli.Command{
		Name:      "create-nfs-pool",
		Usage:     "create nfs image pool for kubestack",
		UsageText: "sdsctl [global options] create-nfs-pool [options]",
		Action:    backcreateNFSPool,
		Flags: []cli.Flag{
			&cli.StringFlag{
				Name:  "name",
				Usage: "name of pool",
			},
			&cli.StringFlag{
				Name:  "local-path",
				Usage: "local mount path",
			},
		},
	}
}

func backcreateNFSPool(ctx *cli.Context) error {
	err := createNFSPool(ctx)
	ksgvr := k8s.NewKsGvr(constant.VMPS_Kind)
	if err != nil && !strings.Contains(err.Error(), "already exists") {
		ksgvr.UpdateWithStatus(ctx.Context, constant.DefaultNamespace, ctx.String("pool"), constant.CRD_Pool_Key, nil, err.Error(), "400")
	}
	return err
}

func createNFSPool(ctx *cli.Context) error {
	logger := utils.GetLogger()
	name := ctx.String("name")
	//if err := rook.CreateNfsPool(name); err != nil {
	//	return err
	//}
	//logger.Infof("create here111")
	if err := rook.WaitNFSPoolReady(constant.DefaultNFSClusterName); err != nil {
		//logger.Infof("er: %+v", err)
		return err
	}
	nfsPath := name
	//logger.Infof("create here11111")
	if err := rook.ExportNFSPath(constant.DefaultNFSClusterName, nfsPath); err != nil && !strings.Contains(err.Error(), "already exists") {
		return err
	}
	logger.Infof("create here222")
	ip := rook.GetNfsServiceIp(constant.DefaultNFSClusterName)
	if len(ip) == 0 {
		return fmt.Errorf("fail to get nfs server ip")
	}
	logger.Infof("create here333")
	if !utils.Exists(ctx.String("local-path")) {
		os.MkdirAll(ctx.String("local-path"), os.ModePerm)
	}
	if err := rook.MountNfs(ip, nfsPath, ctx.String("local-path")); err != nil {
		//logger.Infof("er: %+v", err)
		return err
	}
	//logger.Infof("create here444")
	//ksgvr := k8s.NewExternalGvr(constant.DefaultRookGroup, constant.DefaultRookVersion, constant.CephNFSPoolS_Kinds)
	capacity, err := rook.QueryNfsCapacity(ctx.String("local-path"))
	if err != nil {
		return err
	}
	ksgvr := k8s.NewKsGvr(constant.VMPS_Kind)
	flags := map[string]string{
		"pool":        name,
		"content":     "vmdi",
		"type":        constant.PoolCephNFSType,
		"server-path": fmt.Sprintf("%s:/%s", ip, nfsPath),
		"local-path":  ctx.String("local-path"),
		"url":         ctx.String("local-path"),
		"state":       constant.CRD_Pool_Active,
		"autostart":   "false",
		"capacity":    capacity,
	}
	if err := ksgvr.Update(ctx.Context, constant.DefaultNamespace, name, constant.CRD_Pool_Key, flags); err != nil {
		return err
	}
	return nil
}
