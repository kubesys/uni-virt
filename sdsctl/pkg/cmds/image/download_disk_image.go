package image

import (
	"fmt"
	"github.com/kube-stack/sdsctl/pkg/constant"
	"github.com/kube-stack/sdsctl/pkg/k8s"
	"github.com/kube-stack/sdsctl/pkg/rook"
	"github.com/kube-stack/sdsctl/pkg/utils"
	"github.com/kube-stack/sdsctl/pkg/virsh"
	"github.com/urfave/cli/v2"
	"os"
	"path/filepath"
)

func NewDownloadDiskImageCommand() *cli.Command {
	return &cli.Command{
		Name:      "download-disk-image",
		Usage:     "download disk image for kubestack",
		UsageText: "sdsctl [global options] download-disk-image [options]",
		Action:    backdownloadDiskImage,
		Flags: []cli.Flag{
			&cli.StringFlag{
				Name:  "type",
				Usage: "image hub type, support nfs & cephrgw now",
			},
			&cli.StringFlag{
				Name:  "pool",
				Usage: "target vmdi storage pool name",
			},
			&cli.StringFlag{
				Name:  "name",
				Usage: "target storage volume disk image name",
			},
			&cli.StringFlag{
				Name:  "source-path",
				Usage: "source nfs share path or bucket key",
			},
		},
	}
}

func backdownloadDiskImage(ctx *cli.Context) error {
	err := downloadDiskImage(ctx)
	ksgvr := k8s.NewKsGvr(constant.VMDIS_KINDS)
	if err != nil {
		ksgvr.UpdateWithStatus(ctx.Context, constant.DefaultNamespace, ctx.String("name"), constant.CRD_Volume_Key, nil, err.Error(), "400")
	}
	return err
}

func downloadDiskImage(ctx *cli.Context) error {
	logger := utils.GetLogger()
	pool := ctx.String("pool")
	downloadPath := ctx.String("source-path")
	active, err := virsh.IsPoolActive(pool)
	if err != nil {
		return err
	} else if !active {
		return fmt.Errorf("pool %+v is inactive", pool)
	}
	if !virsh.CheckPoolType(pool, "vmdi") {
		return fmt.Errorf("pool type error")
	}
	sourceDir, err := virsh.ParseDiskDir(pool, ctx.String("name"))
	if !utils.Exists(sourceDir) {
		os.MkdirAll(sourceDir, os.ModePerm)
	}
	sourcePath := filepath.Join(sourceDir, ctx.String("name"))

	// judge type nfs or cephrgw
	hubType := ctx.String("type")
	if hubType == constant.NfsImageHub {
		ip, err := k8s.GetNfsServiceIp()
		if err != nil {
			logger.Errorf("fail to get nfs service ip")
			return err
		}
		if !k8s.CheckNfsMount(ip, downloadPath) {
			return fmt.Errorf("plz mount nfs path first")
		}
		if err := utils.CopyFile(downloadPath, sourcePath); err != nil {
			return fmt.Errorf("fail to download image from nfs share directory")
		}
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
		if err := bucket.DownloadS3(sourcePath, downloadPath); err != nil {
			logger.Errorf("bucket.DownloadS3 err:%+v", err)
			return err
		}
	} else {
		return fmt.Errorf("plz specify correct type：nfs or cephrgw")
	}

	// create vmdi
	image, err := virsh.OpenImage(sourcePath)
	if err != nil {
		logger.Errorf("fail to get image %s info: %+v", sourcePath, err)
		return err
	}
	res := make(map[string]string)
	res["current"] = sourcePath
	res["pool"] = pool
	res["format"] = image.Format
	res["type"] = "localfs"
	res["source-path"] = fmt.Sprintf("%s:%s", hubType, downloadPath)
	vmdiGvr := k8s.NewKsGvr(constant.VMDIS_KINDS)
	if err = vmdiGvr.Update(ctx.Context, constant.DefaultNamespace, ctx.String("name"), constant.CRD_Volume_Key, res); err != nil {
		logger.Errorf("vmdiGvr.Create err:%+v", err)
		return err
	}
	return nil
}
