package rook

import (
	"context"
	"fmt"
	"github.com/kube-stack/sdsctl/pkg/constant"
	"github.com/kube-stack/sdsctl/pkg/k8s"
	"github.com/tidwall/gjson"
	"time"
)

func CreateRbdPool(poolName string) error {
	ksgvr := k8s.NewExternalGvr(constant.DefaultRookGroup, constant.DefaultRookVersion, constant.CephBlockPoolS_Kinds)
	res := make(map[string]interface{})
	res["failureDomain"] = "host"
	res["replicated"] = map[string]interface{}{
		"size":                   3,
		"requireSafeReplicaSize": true,
	}
	return ksgvr.CreateExternalCrd(context.TODO(), constant.RookNamespace, poolName, "spec", res)
}

func WaitRbdPoolReady(poolName string) error {
	ksgvr := k8s.NewExternalGvr(constant.DefaultRookGroup, constant.DefaultRookVersion, constant.CephBlockPoolS_Kinds)
	for i := 0; i < 30; i++ {
		rbdPool, err := ksgvr.Get(context.TODO(), constant.RookNamespace, poolName)
		if err != nil {
			return err
		}
		parse := gjson.ParseBytes(rbdPool.Status.Raw)
		status := parse.Get("phase")
		if status.Str == "Ready" {
			return nil
		}
		time.Sleep(500 * time.Millisecond)
	}
	return fmt.Errorf("rbd %s pool is not ready after 15s", poolName)
}
