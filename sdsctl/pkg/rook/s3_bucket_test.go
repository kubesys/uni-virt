package rook

import (
	"fmt"
	"testing"
)

func TestAwsS3Bucket_UploadS3(t *testing.T) {
	bucket, _ := NewDefaultAwsS3Bucket()
	bucket.InitS3Session()
	err := bucket.UploadS3("/tmp/rookobj", "/tmp/rookobj")
	fmt.Printf("err:%+v\n", err)
}

func TestAwsS3Bucket_DownloadS3(t *testing.T) {
	bucket, _ := NewDefaultAwsS3Bucket()
	bucket.InitS3Session()
	err := bucket.DownloadS3("/tmp/rookobj", "/tmp/rookobj")
	fmt.Printf("err:%+v\n", err)
}

func TestAwsS3Bucket_ListBucketObject(t *testing.T) {
	bucket, _ := NewDefaultAwsS3Bucket()
	bucket.InitS3Session()
	err := bucket.ListBucketObject()
	fmt.Printf("err:%+v\n", err)
}
