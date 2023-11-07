package image

import (
	"fmt"
	"github.com/kube-stack/sdsctl/pkg/constant"
	"github.com/kube-stack/sdsctl/pkg/k8s"
	"github.com/kube-stack/sdsctl/pkg/rook"
	"github.com/kube-stack/sdsctl/pkg/utils"
	"github.com/kube-stack/sdsctl/pkg/virsh"
	"github.com/urfave/cli/v2"
	"path/filepath"
)

func NewUploadDiskImageCommand() *cli.Command {
	return &cli.Command{
		Name:      "upload-disk-image",
		Usage:     "upload disk image for kubestack",
		UsageText: "sdsctl [global options] upload-disk-image [options]",
		Action:    backuploadDiskImage,
		Flags: []cli.Flag{
			&cli.StringFlag{
				Name:  "type",
				Usage: "image hub type, support nfs & cephrgw now",
			},
			&cli.StringFlag{
				Name:  "pool",
				Usage: "source vmdi storage pool name",
			},
			&cli.StringFlag{
				Name:  "name",
				Usage: "source storage volume disk image name",
			},
			&cli.StringFlag{
				Name:  "target-path",
				Usage: "target nfs share path or bucket key",
			},
		},
	}
}

func backuploadDiskImage(ctx *cli.Context) error {
	err := uploadDiskImage(ctx)
	ksgvr := k8s.NewKsGvr(constant.VMDIS_KINDS)
	if err != nil {
		ksgvr.UpdateWithStatus(ctx.Context, constant.DefaultNamespace, ctx.String("name"), constant.CRD_Volume_Key, nil, err.Error(), "400")
	}
	return err
}

func uploadDiskImage(ctx *cli.Context) error {
	logger := utils.GetLogger()
	pool := ctx.String("pool")
	targetPath := ctx.String("target-path")
	active, err := virsh.IsPoolActive(pool)
	if err != nil {
		return err
	} else if !active {
		return fmt.Errorf("pool %+v is inactive", pool)
	}
	if !virsh.CheckPoolType(pool, "vmdi") {
		return fmt.Errorf("pool type error")
	}
	uploadPath, err := virsh.ParseDiskPath(pool, ctx.String("name"))

	// judge type nfs or cephrgw
	hubType := ctx.String("type")
	if hubType == constant.NfsImageHub {
		ip, err := k8s.GetNfsServiceIp()
		if err != nil {
			logger.Errorf("fail to get nfs service ip")
			return err
		}
		if !k8s.CheckNfsMount(ip, targetPath) {
			return fmt.Errorf("plz mount nfs path first")
		}

		targetImagePath := filepath.Join(targetPath, ctx.String("name"))
		return utils.CopyFile(uploadPath, targetImagePath)
	} else if hubType == constant.CephrwgImageHub {
		bucket, err := rook.NewDefaultAwsS3Bucket()
		if err != nil {
			logger.Errorf("rook.NewDefaultAwsS3Bucket err:%+v", err)
			return err
		}
		if err := bucket.InitS3Session(); err != nil {
			logger.Errorf("bucket.InitS3Session err:%+v", err)
			return err
		}
		if err := bucket.UploadS3(uploadPath, targetPath); err != nil {
			return err
		}
	} else {
		return fmt.Errorf("plz specify correct type：nfs or cephrgw")
	}
	return nil
}
