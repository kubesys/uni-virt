package k8s

import (
	"context"
	"errors"
	"fmt"
	"github.com/kube-stack/sdsctl/pkg/constant"
	"github.com/kube-stack/sdsctl/pkg/utils"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"net"
	"os"
	"strings"
)

func GetVMHostName() string {
	name, _ := os.Hostname()
	return fmt.Sprintf("vm.%s", strings.ToLower(name))
}

func GetIPByNodeName(nodeName string) (string, error) {
	client, err := NewClient()

	if err != nil {
		return "", err
	}
	nodeInfo, err := client.CoreV1().Nodes().Get(context.TODO(), nodeName, metav1.GetOptions{})
	if err != nil {
		return "", err
	}
	annotations := nodeInfo.GetObjectMeta().GetAnnotations()
	return annotations["THISIP"], nil
}

func GetHostIp() string {
	addrList, err := net.InterfaceAddrs()
	if err != nil {
		fmt.Println("get current host ip err: ", err)
		return ""
	}
	var ip string
	for _, address := range addrList {
		if ipNet, ok := address.(*net.IPNet); ok && !ipNet.IP.IsLoopback() {
			if ipNet.IP.To4() != nil {
				ip = ipNet.IP.String()
				break
			}
		}
	}
	return ip
}

func GetNodeVirtToolIp(nodeIp string) string {
	client, err := NewClient()
	if err != nil {
		return ""
	}
	podlist, err := client.CoreV1().Pods("kube-system").List(context.TODO(), metav1.ListOptions{})
	if err != nil {
		return ""
	}
	for _, pod := range podlist.Items {
		if pod.Spec.NodeName == nodeIp && strings.Contains(pod.Name, "virt-tool") {
			return pod.Name
		}
	}
	return ""
}

func GetNfsServiceIp() (string, error) {
	client, err := NewClient()
	if err != nil {
		return "", err
	}
	svclist, err := client.CoreV1().Services(constant.RookNamespace).List(context.TODO(), metav1.ListOptions{})
	if err != nil {
		return "", err
	}
	for _, svc := range svclist.Items {
		if strings.Contains(svc.Name, "nfs") {
			return svc.Spec.ClusterIP, nil
		}
	}
	return "", errors.New("no nfs service")
}

func CheckCephfsMount(sourceHost, sourcePath, path string) bool {
	scmd := fmt.Sprintf("df -h | grep '%s:%s' | grep %s | awk '{print $6}'", sourceHost, sourcePath, path)
	cmd := utils.Command{
		Cmd: scmd,
	}
	output, err := cmd.Execute()
	if err != nil || output != "" {
		return strings.Contains(path, output)
	}
	return false
}

func CheckNfsMount(nfsSvcIp, path string) bool {
	scmd := fmt.Sprintf("df -h | grep '%s' | awk '{print $6}'", nfsSvcIp)
	cmd := utils.Command{
		Cmd: scmd,
	}
	output, err := cmd.Execute()
	if err != nil || output != "" {
		return strings.Contains(path, output)
	}
	return false
}

func GetAwsS3BucketInfo() (string, string, string, error) {
	client, err := NewClient()
	if err != nil {
		return "", "", "", err
	}
	cm, err := client.CoreV1().ConfigMaps(constant.DefaultNamespace).Get(context.TODO(), constant.S3ConfigMapName, metav1.GetOptions{})
	if err != nil {
		return "", "", "", err
	}
	bucketHost := cm.Data["BUCKET_HOST"]
	bucketPort := cm.Data["BUCKET_PORT"]
	bucketName := cm.Data["BUCKET_NAME"]
	svcName := strings.Split(bucketHost, ".")[0]
	svc, err := client.CoreV1().Services(constant.RookNamespace).Get(context.TODO(), svcName, metav1.GetOptions{})
	if err != nil {
		return "", "", "", err
	}
	return svc.Spec.ClusterIP, bucketPort, bucketName, nil
}

func GetAwsS3AccessInfo() (string, string, error) {
	client, err := NewClient()
	if err != nil {
		return "", "", err
	}
	secret, err := client.CoreV1().Secrets(constant.DefaultNamespace).Get(context.TODO(), constant.S3SecretName, metav1.GetOptions{})
	if err != nil {
		return "", "", err
	}
	return string(secret.Data["AWS_ACCESS_KEY_ID"]), string(secret.Data["AWS_SECRET_ACCESS_KEY"]), nil
	//if _, err = base64.RawStdEncoding.Decode(secret.Data["AWS_ACCESS_KEY_ID"], accessKeyId); err != nil {
	//	return "", "", err
	//}
	//if _, err = base64.RawStdEncoding.Decode(secret.Data["AWS_SECRET_ACCESS_KEY"], accessKey); err != nil {
	//	return "", "", err
	//}
	//return string(accessKeyId), string(accessKey), nil
}
