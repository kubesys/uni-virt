package pool

import (
	"fmt"
	"github.com/kube-stack/sdsctl/pkg/constant"
	"github.com/kube-stack/sdsctl/pkg/grpc/grpc_client"
	"github.com/kube-stack/sdsctl/pkg/grpc/pb_gen"
	"github.com/kube-stack/sdsctl/pkg/k8s"
	"github.com/kube-stack/sdsctl/pkg/rook"
	"github.com/kube-stack/sdsctl/pkg/utils"
	"github.com/kube-stack/sdsctl/pkg/virsh"
	"github.com/urfave/cli/v2"
	"os"
	"path/filepath"
	"strings"
)

func NewCreatePoolCommand() *cli.Command {
	return &cli.Command{
		Name:      "create-pool",
		Usage:     "create kvm pool for kubestack",
		UsageText: "sdsctl [global options] create-pool [options]",
		Action:    backcreatePool,
		Flags: []cli.Flag{
			&cli.StringFlag{
				Name:  "pool",
				Usage: "name of pool",
			},
			&cli.StringFlag{
				Name:  "type",
				Usage: "storage pool type",
				Value: "dir",
			},
			&cli.StringFlag{
				Name:  "url",
				Usage: "url of pool",
			},
			&cli.StringFlag{
				Name:  "content",
				Usage: "storage pool type",
				Value: "vmd",
			},
			&cli.BoolFlag{
				Name:  "auto-start",
				Usage: "if auto-start pool",
				//Value: true,
			},
			&cli.StringFlag{
				Name:  "source-host",
				Usage: "remote storage server ip",
			},
			&cli.StringFlag{
				Name:  "source-path",
				Usage: "mount path of remote storage server",
			},
			&cli.StringFlag{
				Name:  "source-name",
				Usage: "source rbd name of remote storage server",
			},
		},
	}
}

var poolTypeTrans = map[string]string{
	constant.PoolCephfsType:  constant.PoolDirType,
	constant.PoolNFSType:     constant.PoolNetfsType,
	constant.PoolDirType:     constant.PoolDirType,
	constant.PoolLocalFsType: constant.PoolDirType,
	constant.PoolCephRbdType: constant.PoolRbdType,
}

func backcreatePool(ctx *cli.Context) error {
	err := createPool(ctx)
	ksgvr := k8s.NewKsGvr(constant.VMPS_Kind)
	//logger := utils.GetLogger()

	if err != nil && !strings.Contains(err.Error(), "already exists") {
		//logger.Errorf("err here2: %+v", err)
		virsh.DeletePool(ctx.String("pool"))
		ksgvr.UpdateWithStatus(ctx.Context, constant.DefaultNamespace, ctx.String("pool"), constant.CRD_Pool_Key, nil, err.Error(), "400")
	}
	return err
}

// sdsctl create-pool --auto-start --content vmd --type dir --url /var/lib/libvirt/poolhub111 --pool poolhub111
func createPool(ctx *cli.Context) error {
	logger := utils.GetLogger()
	ptype := ctx.String("type")
	ksgvr := k8s.NewKsGvr(constant.VMPS_Kind)
	if _, ok := poolTypeTrans[ptype]; !ok {
		return fmt.Errorf("invalid pool type: %+v", ptype)
	}
	//autoStart, err := strconv.ParseBool(ctx.String("auto-start"))
	//if err != nil {
	//	logger.Errorf("strconv.ParseBool auto-start err:%+v", err)
	//	return err
	//}
	autoStart := ctx.Bool("auto-start")

	if !utils.Exists(ctx.String("url")) {
		utils.CreateDir(ctx.String("url"))
	}
	//fmt.Println("111")
	sourceHost, sourceName, sourcePath := ctx.String("source-host"), ctx.String("source-name"), ctx.String("source-path")
	if ptype == constant.PoolCephfsType {

		secret, err := rook.GetSecret()
		if err != nil {
			logger.Errorf("fail to get ceph secret: %+v", err)
			return err
		}

		subvol := filepath.Base(sourcePath)
		comm2 := &utils.Command{
			Cmd: fmt.Sprintf("ceph fs subvolumegroup create myfs %s", subvol),
		}
		if _, err := comm2.Execute(); err != nil {
			return err
		}

		scmd := fmt.Sprintf("mount -t ceph -o mds_namespace=%s,name=%s,secret=%s %s:%s %s", constant.DefaultMdsNamespace, constant.DefaultName, secret, sourceHost, sourcePath, ctx.String("url"))
		//fmt.Println(scmd)
		comm := utils.Command{Cmd: scmd}
		if _, err := comm.Execute(); err != nil {
			return err
		}
		client, err := grpc_client.NewGrpcClientUnixSocket(constant.SocketPath)
		if err != nil {
			logger.Errorf("fail to connect grpc server err: %+v", err)
			return err
		}

		req := &pb_gen.RPCRequest{
			Cmd: scmd,
		}
		resp, err := client.C.Call(ctx.Context, req)
		if err != nil || resp.Code != constant.STATUS_OK {
			return fmt.Errorf("grpc call msg: %+v, err: %+v", resp, err)
		}

		// 持久化
		// /etc/fstab内容
		// 方法一：source-host:source-path url ceph name=%s,secret=%s,rw,noatime,_netdev 0 0
		// 10.254.129.113:6789:/volumes/test /var/lib/libvirt/cephfspooltest ceph name=admin,secret=AQCVrkxlkDRbLxAA3fPUnAOrCr95hLoEmszGHw==,rw,noatime,_netdev 0 0
		// 方法二：ceph-fuse，略
		//scmd2 := fmt.Sprintf("echo \"%s:%s %s ceph name=%s,secret=%s,rw,noatime,_netdev 0 0\" >> /etc/fstab", sourceHost, sourcePath, ctx.String("url"), constant.DefaultName, secret)
		//req2 := &pb_gen.RPCRequest{
		//	Cmd: scmd2,
		//}
		//resp, err = client.C.Call(ctx.Context, req2)
		//if err != nil || resp.Code != constant.STATUS_OK {
		//	return fmt.Errorf("grpc call err: %+v", resp.Message)
		//}
	} else if ptype == constant.PoolCephRbdType {
		// create rook ceph rbd pool
		if err := rook.CreateRbdPool(sourceName); err != nil && !strings.Contains(err.Error(), "already exist") {
			return err
		}
		if err := rook.WaitRbdPoolReady(sourceName); err != nil {
			return err
		}
	}
	//fmt.Println("222")
	pool, err := virsh.CreatePool(ctx.String("pool"), poolTypeTrans[ptype], ctx.String("url"), sourceHost, sourceName, sourcePath)
	if err != nil {
		fmt.Println(err)
		if strings.Contains(err.Error(), "already exists") {
			return nil
		}
		virsh.DeletePool(ctx.String("pool"))
		return err
	}
	//fmt.Println("333")
	//logger.Infof("autostart:%+v", autoStart)
	if err := virsh.AutoStartPool(ctx.String("pool"), autoStart); err != nil {
		return err
	}
	//fmt.Println("444")
	//logger.Infof("write content")
	// write content file
	contentPath := filepath.Join(ctx.String("url"), "content")
	contentVar := strings.Trim(ctx.String("content"), " \n")
	var content = []byte(contentVar)
	os.WriteFile(contentPath, content, 0666)
	// update vmp

	flags := utils.ParseFlagMap(ctx)
	delete(flags, "auto-start")
	delete(flags, "source-host")
	delete(flags, "source-path")
	info, err := pool.GetInfo()
	if err != nil {
		logger.Errorf("GetInfo err:%+v", err)
		return err
	}
	extra := map[string]interface{}{
		"state":      constant.CRD_Pool_Active,
		"autostart":  autoStart,
		"capacity":   virsh.UniformBytes(info.Capacity),
		"sourceHost": sourceHost,
		"sourcePath": sourcePath,
	}
	flags = utils.MergeFlags(flags, extra)
	if err := ksgvr.Update(ctx.Context, constant.DefaultNamespace, ctx.String("pool"), constant.CRD_Pool_Key, flags); err != nil {
		logger.Errorf("err: %+v", err)
		return err
	}
	return nil
}
