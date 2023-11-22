package k8s

import (
	"context"
	"encoding/json"
	"fmt"
	yamltrans "github.com/ghodss/yaml"
	"github.com/kube-stack/sdsctl/pkg/constant"
	"github.com/tidwall/sjson"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/apimachinery/pkg/runtime/serializer/yaml"
	"k8s.io/client-go/dynamic"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/tools/clientcmd"
	"os"
	"path/filepath"
)

type KsGvr struct {
	gvr schema.GroupVersionResource
}

type KsCrd struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`
	Spec              runtime.RawExtension `json:"spec,omitempty"`
	Status            runtime.RawExtension `json:"status,omitempty"`
}

type KsCrdWithoutStatus struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`
	Spec              runtime.RawExtension `json:"spec,omitempty"`
}

type KsCrdList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []KsCrd `json:"items"`
}

func NewKsGvr(crdName string) KsGvr {
	return KsGvr{
		gvr: schema.GroupVersionResource{
			Group:    constant.DefaultGroup,
			Version:  constant.DefaultVersion,
			Resource: crdName,
		},
	}
}

func NewExternalGvr(group, version, crdName string) KsGvr {
	return KsGvr{
		gvr: schema.GroupVersionResource{
			Group:    group,
			Version:  version,
			Resource: crdName,
		},
	}
}

var Client dynamic.Interface

func GetCRDClient() (dynamic.Interface, error) {
	var err error
	if Client == nil {
		Client, err = NewCRDClient()
		if err != nil {
			return nil, err
		}
	}
	return Client, nil
}

func GetKubeConfig() string {
	home := os.Getenv("HOME")
	if home == "" {
		home = "root"
	}
	kubeconfig := filepath.Join(home, ".kube", "config")
	return kubeconfig
}
func NewCRDClient() (dynamic.Interface, error) {
	kubeconfig := GetKubeConfig()
	config, err := clientcmd.BuildConfigFromFlags("", kubeconfig)
	if err != nil {
		return nil, err
	}

	return dynamic.NewForConfig(config)
}

func NewClient() (*kubernetes.Clientset, error) {
	kubeconfig := GetKubeConfig()
	config, err := clientcmd.BuildConfigFromFlags("", kubeconfig)
	if err != nil {
		return nil, err
	}
	return kubernetes.NewForConfig(config)
}

func (ks *KsGvr) List(ctx context.Context, namespace string) (*KsCrdList, error) {
	client, err := GetCRDClient()
	if err != nil {
		return nil, err
	}
	utd, err := client.Resource(ks.gvr).Namespace(namespace).List(ctx, metav1.ListOptions{})
	if err != nil {
		return nil, err
	}
	data, err := utd.MarshalJSON()
	if err != nil {
		return nil, err
	}
	var kscrd *KsCrdList
	if err := json.Unmarshal(data, &kscrd); err != nil {
		return nil, err
	}
	return kscrd, nil
}

func (ks *KsGvr) Get(ctx context.Context, namespace string, name string) (*KsCrd, error) {
	client, err := GetCRDClient()
	if err != nil {
		return nil, err
	}
	utd, err := client.Resource(ks.gvr).Namespace(namespace).Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return nil, err
	}
	data, err := utd.MarshalJSON()
	//fmt.Printf("json:%+v", string(data))
	if err != nil {
		return nil, err
	}
	var kscrd KsCrd
	if err := json.Unmarshal(data, &kscrd); err != nil {
		return nil, err
	}
	return &kscrd, nil
}

func (ks *KsGvr) Exist(ctx context.Context, namespace string, name string) (bool, error) {
	_, err := ks.Get(ctx, namespace, name)
	if err != nil {
		if errors.IsNotFound(err) {
			return false, nil
		} else {
			return false, err
		}
	}
	return true, nil
}

var plural2kindMaps = map[string]string{
	constant.VMDS_Kind:            constant.VMD_Kind,
	constant.VMPS_Kind:            constant.VMP_Kind,
	constant.VMDSNS_Kinds:         constant.VMDSN_Kind,
	constant.VMDIS_KINDS:          constant.VMDI_KIND,
	constant.CephBlockPoolS_Kinds: constant.CephBlockPool_Kind,
	"objectbucketclaims":          "ObjectBucketClaim",
}

func (ks *KsGvr) Create(ctx context.Context, namespace, name, key string, value interface{}) error {
	hostName := GetVMHostName()
	createData := fmt.Sprintf(`
apiVersion: "%s/%s"
kind: "%s"
metadata:
  name: "%s"
  labels:
    host: "%s"
spec:
  nodeName: "%s"
  status: ''
`, ks.gvr.Group, ks.gvr.Version, plural2kindMaps[ks.gvr.Resource], name, hostName, hostName)
	jsonBytes, _ := yamltrans.YAMLToJSON([]byte(createData))
	//fmt.Println(string(jsonBytes))
	bytes, _ := sjson.SetBytes(jsonBytes, fmt.Sprintf("spec.%s", key), value)
	bytes, _ = AddPowerStatusForInit(bytes, constant.CRD_Ready_Msg, constant.CRD_Ready_Reason)
	//fmt.Println(string(bytes))
	client, err := GetCRDClient()
	if err != nil {
		return err
	}
	decoder := yaml.NewDecodingSerializer(unstructured.UnstructuredJSONScheme)
	obj := &unstructured.Unstructured{}
	if _, _, err = decoder.Decode(bytes, nil, obj); err != nil {
		return err
	}
	_, err = client.Resource(ks.gvr).Namespace(namespace).Create(ctx, obj, metav1.CreateOptions{})
	return err
}

func (ks *KsGvr) CreateExternalCrd(ctx context.Context, namespace, name, key string, value interface{}) error {
	createData := fmt.Sprintf(`
apiVersion: "%s/%s"
kind: "%s"
metadata:
  name: "%s"
  namespace: "%s"
spec:
`, ks.gvr.Group, ks.gvr.Version, plural2kindMaps[ks.gvr.Resource], name, namespace)
	jsonBytes, _ := yamltrans.YAMLToJSON([]byte(createData))
	bytes, _ := sjson.SetBytes(jsonBytes, key, value)
	client, err := GetCRDClient()
	if err != nil {
		return err
	}
	decoder := yaml.NewDecodingSerializer(unstructured.UnstructuredJSONScheme)
	obj := &unstructured.Unstructured{}
	if _, _, err = decoder.Decode(bytes, nil, obj); err != nil {
		return err
	}
	_, err = client.Resource(ks.gvr).Namespace(namespace).Create(ctx, obj, metav1.CreateOptions{})
	return err
}

func (ks *KsGvr) CreatePlainExternalCrd(ctx context.Context, namespace, createData string) error {
	bytes, _ := yamltrans.YAMLToJSON([]byte(createData))
	client, err := GetCRDClient()
	if err != nil {
		return err
	}
	decoder := yaml.NewDecodingSerializer(unstructured.UnstructuredJSONScheme)
	obj := &unstructured.Unstructured{}
	if _, _, err = decoder.Decode(bytes, nil, obj); err != nil {
		return err
	}
	_, err = client.Resource(ks.gvr).Namespace(namespace).Create(ctx, obj, metav1.CreateOptions{})
	return err
}

func (ks *KsGvr) Update(ctx context.Context, namespace, name, key string, value interface{}) error {
	client, err := GetCRDClient()
	if err != nil {
		return err
	}

	// get old crd
	utd, err := client.Resource(ks.gvr).Namespace(namespace).Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return err
	}

	obj := &unstructured.Unstructured{}
	obj.SetResourceVersion(utd.GetResourceVersion())

	data, err := utd.MarshalJSON()
	if err != nil {
		return err
	}
	var kscrd KsCrdWithoutStatus
	err = json.Unmarshal(data, &kscrd)
	if err != nil {
		return err
	}

	// update spec
	//fmt.Printf("before:%s\n", string(kscrd.Spec.Raw))
	bytes, err := sjson.SetBytes(kscrd.Spec.Raw, key, value)
	if err != nil {
		return err
	}
	// update status
	bytes, err = AddPowerStatus(bytes, constant.CRD_Ready_Msg, constant.CRD_Ready_Reason)
	if err != nil {
		return err
	}
	kscrd.Spec.Raw = bytes
	//fmt.Printf("after:%s\n", string(kscrd.Spec.Raw))
	// docode for bytes
	marshal, err := json.Marshal(kscrd)
	decoder := yaml.NewDecodingSerializer(unstructured.UnstructuredJSONScheme)
	if _, _, err = decoder.Decode(marshal, nil, obj); err != nil {
		return err
	}
	// write back to k8s
	_, err = client.Resource(ks.gvr).Namespace(namespace).Update(ctx, obj, metav1.UpdateOptions{})
	if err != nil {
		return err
	}
	return nil
}

func (ks *KsGvr) UpdateWithStatus(ctx context.Context, namespace, name, key string, value interface{}, msg, reason string) error {
	client, err := GetCRDClient()
	if err != nil {
		return err
	}

	// get old crd
	utd, err := client.Resource(ks.gvr).Namespace(namespace).Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return err
	}

	obj := &unstructured.Unstructured{}
	obj.SetResourceVersion(utd.GetResourceVersion())

	data, err := utd.MarshalJSON()
	if err != nil {
		return err
	}
	var kscrd KsCrdWithoutStatus
	err = json.Unmarshal(data, &kscrd)
	if err != nil {
		return err
	}

	// update spec
	//fmt.Printf("before:%s\n", string(kscrd.Spec.Raw))
	bytes := kscrd.Spec.Raw
	if value != nil {
		bytes, err = sjson.SetBytes(kscrd.Spec.Raw, key, value)
		if err != nil {
			return err
		}
	}

	// update status
	bytes, err = AddPowerStatus(bytes, msg, reason)
	if err != nil {
		return err
	}

	kscrd.Spec.Raw = bytes
	//kscrd.Status.Raw = []byte{}
	//fmt.Printf("after:%s\n", string(kscrd.Spec.Raw))
	// docode for bytes
	marshal, err := json.Marshal(kscrd)
	decoder := yaml.NewDecodingSerializer(unstructured.UnstructuredJSONScheme)
	if _, _, err = decoder.Decode(marshal, nil, obj); err != nil {
		return err
	}
	// write back to k8s
	_, err = client.Resource(ks.gvr).Namespace(namespace).Update(ctx, obj, metav1.UpdateOptions{})
	if err != nil {
		return err
	}
	return nil
}

func (ks *KsGvr) Delete(ctx context.Context, namespace string, name string) error {
	client, err := GetCRDClient()
	if err != nil {
		return err
	}
	return client.Resource(ks.gvr).Namespace(namespace).Delete(ctx, name, metav1.DeleteOptions{})
}
