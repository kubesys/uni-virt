package main

import (
	"context"
	"flag"
	"fmt"
	"github.com/kube-stack/sdsctl/pkg/constant"
	"github.com/kube-stack/sdsctl/pkg/grpc/grpc_server"
	"github.com/kube-stack/sdsctl/pkg/k8s"
	"github.com/kube-stack/sdsctl/pkg/rook"
	"github.com/kube-stack/sdsctl/pkg/utils"
	"io"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/client-go/kubernetes/scheme"
	"k8s.io/client-go/tools/clientcmd"
	"k8s.io/client-go/tools/remotecommand"
	"os"
	"time"
)

var socket string

func main() {
	flag.StringVar(&socket, "socket", constant.SocketPath, "unix socket file for grpc communication")
	flag.Parse()
	stopCh := make(chan struct{})
	if utils.Exists(constant.SocketPath) {
		os.RemoveAll(constant.SocketPath)
	}
	server := grpc_server.NewGrpcServer(9999, socket, context.TODO(), stopCh)
	var logger = utils.GetLogger()
	go func() {
		ticker := time.NewTicker(1 * time.Minute)
		for range ticker.C {
			host := k8s.GetHostIp()
			logger.Infof("start check cephfs mount,host:%s", host)
			ksgvr := k8s.NewKsGvr(constant.VMPS_Kind)
			list, _ := ksgvr.List(context.TODO(), "default")
			//logger.Infof("start check cephfs mount test1:%+v", list)
			for _, item := range list.Items {
				nodeName, _ := k8s.GetCRDSpecNodeName(item.Spec.Raw)
				if nodeName != host {
					continue
				}
				logger.Infof("item nodeName:%s", nodeName)
				info, _ := k8s.GetCRDSpec(item.Spec.Raw, constant.CRD_Pool_Key)
				logger.Infof("check umount %s:%s %s", info["sourceHost"], info["sourcePath"], info["url"])
				if !k8s.CheckCephfsMount(info["sourceHost"], info["sourcePath"], info["url"]) {
					logger.Infof("start mount %s:%s %s", info["sourceHost"], info["sourcePath"], info["url"])
					secret, _ := rook.GetSecret()

					// mount host
					scmd := fmt.Sprintf("mount -t ceph -o mds_namespace=%s,name=%s,secret=%s %s:%s %s", constant.DefaultMdsNamespace, constant.DefaultName, secret, info["sourceHost"], info["sourcePath"], info["url"])
					comm := utils.Command{Cmd: scmd}
					comm.Execute()

					// mount pod
					podName := k8s.GetNodeVirtToolIp(nodeName)
					logger.Infof("mount virt-tool: %s", podName)
					//scmd2 := fmt.Sprintf("kubectl exec -it %s -n kube-system -c virtctl -- mount -t ceph -o mds_namespace=%s,name=%s,secret=%s %s:%s %s", podName, constant.DefaultMdsNamespace, constant.DefaultName, secret, info["sourceHost"], info["sourcePath"], info["url"])
					//comm2 := utils.Command{Cmd: scmd2}
					//comm2.Execute()
					client, _ := k8s.NewClient()
					req := client.CoreV1().RESTClient().Post().
						Resource("pods").
						Name(podName).
						Namespace("kube-system").
						SubResource("exec").
						VersionedParams(&corev1.PodExecOptions{
							Command:   []string{"/bin/bash", "-c", scmd},
							Container: "virtctl",
							Stdin:     true,
							Stdout:    true,
							Stderr:    true,
							TTY:       false,
						}, scheme.ParameterCodec)
					config, _ := clientcmd.BuildConfigFromFlags("", k8s.GetKubeConfig())
					exec, _ := remotecommand.NewSPDYExecutor(config, "POST", req.URL())
					screen := struct {
						io.Reader
						io.Writer
					}{os.Stdin, os.Stdout}
					exec.Stream(remotecommand.StreamOptions{
						Stdin:  screen,
						Stdout: screen,
						Stderr: screen,
						Tty:    false,
					})
				}
			}
		}
	}()
	server.StartGrpcServerUnixSocket()
}
