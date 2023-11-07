package k8s

import (
	"context"
	"fmt"
	"github.com/kube-stack/sdsctl/pkg/constant"
	"testing"
)

func TestGetCRDSpec(t *testing.T) {
	ksgvr := NewKsGvr(constant.VMDS_Kind)
	vmd, _ := ksgvr.Get(context.TODO(), constant.DefaultNamespace, "diskhub111")
	spec, err := GetCRDSpec(vmd.Spec.Raw, constant.CRD_Volume_Key)
	fmt.Printf("err:%+v", err)
	fmt.Printf("spec:%+v", spec)
}
