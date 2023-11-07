package main

import (
	"context"
	"flag"
	"github.com/kube-stack/sdsctl/pkg/constant"
	"github.com/kube-stack/sdsctl/pkg/grpc/grpc_server"
)

var socket string

func main() {
	flag.StringVar(&socket, "socket", constant.SocketPath, "unix socket file for grpc communication")
	flag.Parse()
	stopCh := make(chan struct{})
	server := grpc_server.NewGrpcServer(9999, socket, context.TODO(), stopCh)
	server.StartGrpcServerUnixSocket()
}
