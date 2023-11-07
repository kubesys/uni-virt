package grpc_server

import (
	"context"
	"github.com/kube-stack/sdsctl/pkg/grpc/pb_gen"
)

func (s *GrpcServer) HelloWorld(ctx context.Context, req *pb_gen.HelloWorldRequest) (*pb_gen.HelloWorldResponse, error) {
	logger.Infof("get HelloWorld request: %+v", req)
	resp := &pb_gen.HelloWorldResponse{ThanksText: "hello,this wanna"}
	return resp, nil
}

func (s *GrpcServer) Call(ctx context.Context, req *pb_gen.RPCRequest) (*pb_gen.RPCResponse, error) {
	logger.Infof("get Call request: %+v", req)
	return s.service.Call(ctx, req.Cmd)
}

func (s *GrpcServer) CallWithResult(ctx context.Context, req *pb_gen.RPCRequest) (*pb_gen.RPCResponse, error) {
	logger.Infof("get CallWithResult request: %+v", req)
	return s.service.CallWithResult(ctx, req.Cmd)
}
