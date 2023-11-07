package rook

import (
	"fmt"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/credentials"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/s3"
	"github.com/aws/aws-sdk-go/service/s3/s3manager"
	_ "github.com/aws/aws-sdk-go/service/s3/s3manager"
	"github.com/kube-stack/sdsctl/pkg/k8s"
	"os"
)

type AwsS3Bucket struct {
	IP        string
	Port      string
	Bucket    string
	AccessKey string
	SecretKey string
	Session   *session.Session
}

func NewDefaultAwsS3Bucket() (*AwsS3Bucket, error) {
	accessKey, secretKey, err := k8s.GetAwsS3AccessInfo()
	if err != nil {
		return nil, err
	}
	ip, port, name, err := k8s.GetAwsS3BucketInfo()
	if err != nil {
		return nil, err
	}
	return &AwsS3Bucket{
		IP:        ip,
		Port:      port,
		Bucket:    name,
		AccessKey: accessKey,
		SecretKey: secretKey,
	}, nil
}

func (s3Bucket *AwsS3Bucket) InitS3Session() error {
	session, err := session.NewSession(&aws.Config{
		Credentials:      credentials.NewStaticCredentials(s3Bucket.AccessKey, s3Bucket.SecretKey, ""),
		Endpoint:         aws.String(fmt.Sprintf("http://%s:%s", s3Bucket.IP, s3Bucket.Port)),
		Region:           aws.String("us-east-1"),
		DisableSSL:       aws.Bool(true),
		S3ForcePathStyle: aws.Bool(true), // !!! fix bug
	})
	if err != nil {
		return err
	}
	s3Bucket.Session = session
	return nil
}

func (s3Bucket *AwsS3Bucket) UploadS3(filePath, key string) error {
	s3Session := s3Bucket.Session
	uploader := s3manager.NewUploader(s3Session)
	file, err := os.Open(filePath)
	if err != nil {
		return err
	}
	defer file.Close()

	_, err = uploader.Upload(&s3manager.UploadInput{
		Bucket: aws.String(s3Bucket.Bucket),
		Key:    aws.String(key),
		Body:   file,
	})
	return err
}

func (s3Bucket *AwsS3Bucket) DownloadS3(filePath, key string) error {
	s3Session := s3Bucket.Session
	file, err := os.Create(filePath)
	if err != nil {
		return err
	}
	defer file.Close()

	downloader := s3manager.NewDownloader(s3Session)
	_, err = downloader.Download(file,
		&s3.GetObjectInput{
			Bucket: aws.String(s3Bucket.Bucket),
			Key:    aws.String(key),
		})
	return err
}

func (s3Bucket *AwsS3Bucket) ListBucketObject() error {
	svc := s3.New(s3Bucket.Session)
	params := &s3.ListObjectsInput{
		Bucket: aws.String(s3Bucket.Bucket),
	}
	resp, err := svc.ListObjects(params)
	if err != nil {
		return err
	}
	for _, item := range resp.Contents {
		fmt.Println("Name:         ", *item.Key)
		fmt.Println("Last modified:", *item.LastModified)
		fmt.Println("Size:         ", *item.Size)
		fmt.Println("Storage class:", *item.StorageClass)
		fmt.Println("")
	}
	return nil
}
