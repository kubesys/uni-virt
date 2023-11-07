package grpc_server

import (
	"context"
	"fmt"
	"github.com/kube-stack/sdsctl/pkg/grpc/pb_gen"
	"github.com/kube-stack/sdsctl/pkg/internal"
	"github.com/kube-stack/sdsctl/pkg/utils"
	"google.golang.org/grpc"
	"google.golang.org/grpc/reflection"
	"net"
	"os"
	"os/signal"
	"syscall"
)

type GrpcServer struct {
	*pb_gen.UnimplementedSdsCtlServiceServer
	ctx     context.Context
	stopCh  chan struct{}
	port    int
	socket  string
	service *internal.NetworkControllerService
}

var logger = utils.GetLogger()
var gServer *GrpcServer

func GetGServer() *GrpcServer {
	return gServer
}

func NewGrpcServer(port int, socket string, ctx context.Context, stopCh chan struct{}) *GrpcServer {
	s := &GrpcServer{
		ctx:    ctx,
		stopCh: stopCh,
		port:   port,
		socket: socket,
	}

	s.service = internal.NewLiteNCService()
	return s
}

func (s *GrpcServer) StartGrpcServerUnixSocket() error {
	serverAddress, err := net.ResolveUnixAddr("unix", s.socket)
	if err != nil {
		logger.Errorf("failed to listen: %v", err)
		return err
	}
	lis, err := net.ListenUnix("unix", serverAddress)
	if err != nil {
		logger.Errorf("listenErr: %v", err)
		return err
	}
	defer lis.Close()
	go s.cleanUp()

	gopts := []grpc.ServerOption{}
	server := grpc.NewServer(gopts...)
	// register reflection for grpcurl service
	reflection.Register(server)
	// register service
	pb_gen.RegisterSdsCtlServiceServer(server, s)
	logger.Infof("grpc server ready to listen %s", s.socket)

	go func() {
		for {
			select {
			case <-s.stopCh:
				server.GracefulStop()
				return
			}
		}
	}()

	if err := server.Serve(lis); err != nil {
		logger.Errorf("grpc server failed to serve: %v", err)
		return err
	}
	return nil
}

func (s *GrpcServer) StartGrpcServerTcp() error {
	defer logger.Debug("StartGrpcServerTcp done")

	tcpAddr := fmt.Sprintf(":%d", s.port)
	lis, err := net.Listen("tcp", tcpAddr)
	defer lis.Close()
	if err != nil {
		logger.Errorf("tcp failed to listen: %v", err)
		return err
	}

	gopts := []grpc.ServerOption{}
	server := grpc.NewServer(gopts...)
	// register reflection for grpcurl service
	reflection.Register(server)
	// register service
	pb_gen.RegisterSdsCtlServiceServer(server, s)
	logger.Infof("grpc server ready to serve at %+v", tcpAddr)

	go func() {
		for {
			select {
			case <-s.stopCh:
				server.GracefulStop()
				return
			}
		}
	}()

	if err := server.Serve(lis); err != nil {
		logger.Errorf("grpc server failed to serve: %v", err)
		return err
	}
	return nil
}

// server exit gracefully
func (server *GrpcServer) cleanUp() {

	defer logger.Info("server cleanup done")

	c := make(chan os.Signal, 1)
	// watch ctrl+c or kill pid
	signal.Notify(c, syscall.SIGINT, syscall.SIGTERM)
	<-c
	logger.Info("clean up")

	select {
	case <-server.stopCh:
		break
	default:
		close(server.stopCh)
	}
	// code zero indicates success
	//os.Exit(0)
}
