package rook

import (
	"context"
	"fmt"
	"github.com/kube-stack/sdsctl/pkg/constant"
	"github.com/kube-stack/sdsctl/pkg/grpc/grpc_client"
	"github.com/kube-stack/sdsctl/pkg/grpc/pb_gen"
	"github.com/kube-stack/sdsctl/pkg/k8s"
	"github.com/kube-stack/sdsctl/pkg/utils"
	"github.com/tidwall/gjson"
	"path/filepath"
	"time"
)

func CreateNfsPool(poolName string) error {
	ksgvr := k8s.NewExternalGvr(constant.DefaultRookGroup, constant.DefaultRookVersion, constant.CephNFSPoolS_Kinds)
	res := make(map[string]interface{})
	res["server"] = map[string]interface{}{
		"active":   1,
		"logLevel": "NIV_INFO",
	}
	return ksgvr.CreateExternalCrd(context.TODO(), constant.RookNamespace, poolName, "spec", res)
}

func WaitNFSPoolReady(poolName string) error {
	ksgvr := k8s.NewExternalGvr(constant.DefaultRookGroup, constant.DefaultRookVersion, constant.CephNFSPoolS_Kinds)
	for i := 0; i < 60; i++ {
		rbdPool, err := ksgvr.Get(context.TODO(), constant.RookNamespace, poolName)
		if err != nil {
			return err
		}
		parse := gjson.ParseBytes(rbdPool.Status.Raw)
		status := parse.Get("phase")
		if status.Str == "Ready" || status.Str == "Progressing" {
			return nil
		}
		time.Sleep(500 * time.Millisecond)
	}
	return fmt.Errorf("rbd %s pool is not ready after 30s", poolName)
}

func ExportNFSPath(poolName, nfsPath string) error {
	//ceph fs subvolumegroup create myfs share
	//ceph nfs export create cephfs my-nfs /share myfs /volumes/share
	comm := &utils.Command{
		Cmd: fmt.Sprintf("ceph fs subvolumegroup create myfs %s", nfsPath),
	}
	if _, err := comm.Execute(); err != nil {
		return err
	}
	comm2 := &utils.Command{
		Cmd: fmt.Sprintf("ceph nfs export create cephfs %s /%s myfs %s", poolName, nfsPath, filepath.Join("/volumes", nfsPath)),
	}
	if _, err := comm2.Execute(); err != nil {
		return err
	}
	return nil
}

func ExportDeleteNFSPath(poolName, nfsPath string) error {
	//ceph nfs export rm my-nfs /share2
	//ceph fs subvolumegroup rm myfs share2
	comm := &utils.Command{
		Cmd: fmt.Sprintf("ceph nfs export rm %s /%s", poolName, nfsPath),
	}
	if _, err := comm.Execute(); err != nil {
		return err
	}
	// retain cephfs
	//comm2 := &utils.Command{
	//	Cmd: fmt.Sprintf("ceph fs subvolumegroup rm myfs %s", nfsPath),
	//}
	//if _, err := comm2.Execute(); err != nil {
	//	return err
	//}
	return nil
}

func GetNfsServiceIp(poolName string) string {
	comm := &utils.Command{
		Cmd: fmt.Sprintf("kubectl get svc -A | grep %s | awk '{print $4}'", poolName),
	}
	res, err := comm.Execute()
	if err != nil {
		return ""
	}
	return res
}

func MountNfs(nfsServerIp, nfsPath, localPath string) error {
	scmd := fmt.Sprintf("mount -t nfs4 %s:/%s %s", nfsServerIp, nfsPath, localPath)
	comm := &utils.Command{
		Cmd: scmd,
	}
	_, err := comm.Execute()
	if err != nil {
		return err
	}
	req := &pb_gen.RPCRequest{
		Cmd: scmd,
	}
	client, err := grpc_client.NewGrpcClientUnixSocket(constant.SocketPath)
	if err != nil {
		return err
	}
	resp, err := client.C.Call(context.TODO(), req)
	if err != nil || resp.Code != constant.STATUS_OK {
		return fmt.Errorf("grpc call err: %+v", resp.Message)
	}
	return nil
}

func UmountNfs(path string) error {
	scmd := fmt.Sprintf("umount %s", path)
	comm := &utils.Command{
		Cmd: scmd,
	}
	_, err := comm.Execute()
	if err != nil {
		return err
	}

	req := &pb_gen.RPCRequest{
		Cmd: scmd,
	}
	client, err := grpc_client.NewGrpcClientUnixSocket(constant.SocketPath)
	if err != nil {
		return err
	}
	resp, err := client.C.Call(context.TODO(), req)
	if err != nil || resp.Code != constant.STATUS_OK {
		return fmt.Errorf("grpc call err: %+v", resp.Message)
	}
	return nil
}

func QueryNfsCapacity(path string) (string, error) {
	scmd := fmt.Sprintf("df -h | grep %s | awk '{print $2}'", path)
	comm := &utils.Command{
		Cmd: scmd,
	}
	res, err := comm.Execute()
	if err != nil {
		return "", err
	}
	return res, nil
}
