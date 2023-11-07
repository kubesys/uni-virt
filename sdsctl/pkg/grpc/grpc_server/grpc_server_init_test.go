package grpc_server

import (
	"context"
	"github.com/kube-stack/sdsctl/pkg/constant"
	"testing"
)

func TestNewGrpcServer(t *testing.T) {
	stopCh := make(chan struct{})
	server := NewGrpcServer(9999, "", context.TODO(), stopCh)
	server.StartGrpcServerTcp()
}

func TestNewGrpcServer2(t *testing.T) {
	stopCh := make(chan struct{})
	server := NewGrpcServer(9999, constant.SocketPath, context.TODO(), stopCh)
	server.StartGrpcServerUnixSocket()
}
