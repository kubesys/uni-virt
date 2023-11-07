package internal

import (
	"context"
	"github.com/kube-stack/sdsctl/pkg/constant"
	"github.com/kube-stack/sdsctl/pkg/grpc/pb_gen"
	"github.com/kube-stack/sdsctl/pkg/utils"
	"github.com/op/go-logging"
)

type NetworkControllerService struct {
}

var logger *logging.Logger

func NewLiteNCService() *NetworkControllerService {
	return &NetworkControllerService{}
}

func (service *NetworkControllerService) Call(ctx context.Context, cmd string) (*pb_gen.RPCResponse, error) {
	comm := utils.Command{
		Cmd: cmd,
	}
	_, err := comm.Execute()
	resp := &pb_gen.RPCResponse{
		Code:    constant.STATUS_OK,
		Message: constant.MESSAGE_OK,
		Data:    "",
	}
	if err != nil {
		resp.Code = constant.STATUS_ERR
		resp.Message = err.Error()
	}
	return resp, nil
}

func (service *NetworkControllerService) CallWithResult(ctx context.Context, cmd string) (*pb_gen.RPCResponse, error) {
	comm := utils.Command{
		Cmd: cmd,
	}
	res, err := comm.Execute()
	resp := &pb_gen.RPCResponse{
		Code:    constant.STATUS_OK,
		Message: constant.MESSAGE_OK,
		Data:    "",
	}
	if err != nil {
		resp.Code = constant.STATUS_ERR
		resp.Message = err.Error()
		return resp, nil
	}
	resp.Data = res
	return resp, nil
}
