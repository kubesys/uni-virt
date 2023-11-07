package rook

import (
	"fmt"
	"testing"
)

func TestGetBucketInfo(t *testing.T) {
	info, _ := GetBucketInfo("ceph-delete-bucket")
	fmt.Printf("%+v\n", info)
}

func TestGetBucketSecret(t *testing.T) {
	GetBucketSecret("ceph-delete-bucket")
}

func TestCreateOBC(t *testing.T) {
	err := CreateOBC("ceph-delete-bucket")
	fmt.Printf("err: %+v\n", err)
}

func TestCreateBucketStorageClass(t *testing.T) {
	err := CreateBucketStorageClass()
	fmt.Printf("err: %+v\n", err)
}

func TestDeleteOBC(t *testing.T) {
	err := DeleteOBC("ceph-delete-bucket")
	fmt.Printf("err: %+v\n", err)
}

func TestDeleteBucketStorageClass(t *testing.T) {
	err := DeleteBucketStorageClass()
	fmt.Printf("err: %+v\n", err)
}
