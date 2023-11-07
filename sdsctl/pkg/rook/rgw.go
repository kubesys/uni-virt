package rook

import (
	"context"
	"fmt"
	"github.com/kube-stack/sdsctl/pkg/constant"
	"github.com/kube-stack/sdsctl/pkg/k8s"
	"github.com/kube-stack/sdsctl/pkg/utils"
	v1 "k8s.io/api/core/v1"
	storagev1 "k8s.io/api/storage/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"strings"
	"time"
)

func CreateOBC(obcName string) error {
	ksgvr := k8s.NewExternalGvr("objectbucket.io", "v1alpha1", "objectbucketclaims")
	res := make(map[string]interface{})
	res["generateBucketName"] = "ceph-bkt"
	res["storageClassName"] = "rook-ceph-delete-bucket"
	return ksgvr.CreateExternalCrd(context.TODO(), constant.DefaultNamespace, obcName, "spec", res)
}

func DeleteOBC(obcName string) error {
	ksgvr := k8s.NewExternalGvr("objectbucket.io", "v1alpha1", "objectbucketclaims")
	return ksgvr.Delete(context.TODO(), constant.DefaultNamespace, obcName)
}

func CreateBucketStorageClass() error {
	client, err := k8s.NewClient()
	if err != nil {
		return err
	}
	policy := v1.PersistentVolumeReclaimDelete
	obj := &storagev1.StorageClass{
		TypeMeta: metav1.TypeMeta{
			Kind:       "StorageClass",
			APIVersion: "storage.k8s.io/v1",
		},
		ObjectMeta: metav1.ObjectMeta{
			Name: "rook-ceph-delete-bucket",
		},
		Provisioner:   "rook-ceph.ceph.rook.io/bucket",
		ReclaimPolicy: &policy,
		Parameters: map[string]string{
			"objectStoreName":      "my-store",
			"objectStoreNamespace": "rook-ceph",
		},
	}
	_, err = client.StorageV1().StorageClasses().Create(context.TODO(), obj, metav1.CreateOptions{})
	return err
}

func DeleteBucketStorageClass() error {
	client, err := k8s.NewClient()
	if err != nil {
		return err
	}
	ksgvr := k8s.NewExternalGvr("objectbucket.io", "v1alpha1", "objectbucketclaims")
	for i := 0; i < 60; i++ {
		obj, err := ksgvr.Get(context.TODO(), constant.DefaultNamespace, constant.DefaultCephRwgName)
		if obj != nil && err == nil {
			time.Sleep(3 * time.Second)
		} else {
			break
		}
	}
	if err != nil {
		return err
	}
	return client.StorageV1().StorageClasses().Delete(context.TODO(), "rook-ceph-delete-bucket", metav1.DeleteOptions{})
}

func GetBucketInfo(cmName string) (map[string]string, error) {
	//svcName=$(echo $AWS_HOST | awk -F. '{print $1}') && kubectl get svc -A | grep $svcName | awk '{print $4}'
	//export PORT=$(kubectl -n default get cm ceph-delete-bucket -o jsonpath='{.data.BUCKET_PORT}')
	//export BUCKET_NAME=$(kubectl -n default get cm ceph-delete-bucket -o jsonpath='{.data.BUCKET_NAME}')
	client, err := k8s.NewClient()
	if err != nil {
		return nil, err
	}
	var cm *v1.ConfigMap
	for i := 0; i < 30; i++ {
		cm, err = client.CoreV1().ConfigMaps(constant.DefaultNamespace).Get(context.TODO(), cmName, metav1.GetOptions{})
		if err == nil && cm != nil {
			break
		}
		time.Sleep(1 * time.Second)
	}
	if cm == nil {
		return nil, err
	}

	host := cm.Data["BUCKET_HOST"]
	name := cm.Data["BUCKET_NAME"]
	port := cm.Data["BUCKET_PORT"]
	svcName := strings.Split(host, ".")[0]
	scmd := fmt.Sprintf("kubectl get svc -A | grep %s | awk '{print $4}'", svcName)
	cmd := &utils.Command{
		Cmd: scmd,
	}
	ip, _ := cmd.Execute()
	return map[string]string{
		"host": host,
		"name": name,
		"ip":   ip,
		"port": port,
	}, nil
}

func GetBucketSecret(secretName string) (map[string]string, error) {
	//export AWS_ACCESS_KEY_ID=$(kubectl -n default get secret ceph-delete-bucket -o jsonpath='{.data.AWS_ACCESS_KEY_ID}' | base64 --decode)
	//export AWS_SECRET_ACCESS_KEY=$(kubectl -n default get secret ceph-delete-bucket -o jsonpath='{.data.AWS_SECRET_ACCESS_KEY}' | base64 --decode)
	client, err := k8s.NewClient()
	if err != nil {
		return nil, err
	}
	var cm *v1.Secret
	for i := 0; i < 30; i++ {
		cm, err = client.CoreV1().Secrets(constant.DefaultNamespace).Get(context.TODO(), secretName, metav1.GetOptions{})
		if err == nil && cm != nil {
			break
		}
		time.Sleep(1 * time.Second)
	}

	if cm == nil {
		return nil, err
	}
	accessId := string(cm.Data["AWS_ACCESS_KEY_ID"])
	accessKey := string(cm.Data["AWS_SECRET_ACCESS_KEY"])
	return map[string]string{
		"access-id":  accessId,
		"access-key": accessKey,
	}, nil
}
