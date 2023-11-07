package grpc_client

import (
	"context"
	"fmt"
	"github.com/kube-stack/sdsctl/pkg/constant"
	"github.com/kube-stack/sdsctl/pkg/grpc/pb_gen"
	"testing"
)

func Test(t *testing.T) {
	client, _ := NewGrpcClient("localhost", "9999")
	request := &pb_gen.HelloWorldRequest{
		HelloText: "hello",
	}
	resp, _ := client.C.HelloWorld(context.TODO(), request)
	fmt.Println(resp)
}

func TestGrpcClient_InitGrpcClientUnixSocketConn(t *testing.T) {
	client, err := NewGrpcClientUnixSocket(constant.SocketPath)
	fmt.Println(err)
	request := &pb_gen.HelloWorldRequest{
		HelloText: "hello",
	}
	resp, _ := client.C.HelloWorld(context.TODO(), request)
	fmt.Println(resp)
}
