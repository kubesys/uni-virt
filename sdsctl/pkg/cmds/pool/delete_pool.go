package pool

import (
	"fmt"
	"github.com/kube-stack/sdsctl/pkg/constant"
	"github.com/kube-stack/sdsctl/pkg/grpc/grpc_client"
	"github.com/kube-stack/sdsctl/pkg/grpc/pb_gen"
	"github.com/kube-stack/sdsctl/pkg/k8s"
	"github.com/kube-stack/sdsctl/pkg/utils"
	"github.com/kube-stack/sdsctl/pkg/virsh"
	"github.com/urfave/cli/v2"
	"time"
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
	ksgvr := k8s.NewKsGvr(constant.VMPS_Kind)
	vmp, err := ksgvr.Get(ctx.Context, constant.DefaultNamespace, ctx.String("pool"))
	if err != nil {
		return err
	}
	res, _ := k8s.GetCRDSpec(vmp.Spec.Raw, constant.CRD_Pool_Key)
	if res["type"] == constant.PoolCephfsType {
		path := res["url"]
		scmd := fmt.Sprintf("umount  %s", path)
		//fmt.Println(scmd)
		client, err := grpc_client.NewGrpcClientUnixSocket(constant.SocketPath)
		if err != nil {
			return err
		}

		req := &pb_gen.RPCRequest{
			Cmd: scmd,
		}
		resp, err := client.C.Call(ctx.Context, req)
		if err != nil || resp.Code != constant.STATUS_OK {
			return fmt.Errorf("grpc call err: %+v", resp.Message)
		}

		time.Sleep(2 * time.Second)
		comm := utils.Command{Cmd: scmd}
		if _, err := comm.Execute(); err != nil {
			return err
		}

		// 持久化
		// /etc/fstab内容
		// 方法一：source-host:source-path url ceph name=%s,secret=%s,rw,noatime,_netdev 0 0
		// 10.254.129.113:6789:/volumes/test /var/lib/libvirt/cephfspooltest ceph name=admin,secret=AQCVrkxlkDRbLxAA3fPUnAOrCr95hLoEmszGHw==,rw,noatime,_netdev 0 0
		// 方法二：ceph-fuse，略
		//secret, err := rook.GetSecret()
		//if err != nil {
		//	return err
		//}
		//item := fmt.Sprintf("%s:%s %s ceph name=%s,secret=%s,rw,noatime,_netdev 0 0", res["sourceHost"], res["sourcePath"], res["url"], constant.DefaultName, secret)
		//scmd2 := fmt.Sprintf("sed -i '/%s/d' /etc/fstab ", item)
		//req2 := &pb_gen.RPCRequest{
		//	Cmd: scmd2,
		//}
		//resp, err = client.C.Call(ctx.Context, req2)
		//if err != nil || resp.Code != constant.STATUS_OK {
		//	return fmt.Errorf("grpc call err: %+v", resp.Message)
		//}
	}

	err = deletePool(ctx)
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
