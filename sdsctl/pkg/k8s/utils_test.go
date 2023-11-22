package k8s

import (
	"fmt"
	"github.com/kube-stack/sdsctl/pkg/constant"
	"github.com/kube-stack/sdsctl/pkg/rook"
	"io"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/client-go/kubernetes/scheme"
	"k8s.io/client-go/tools/clientcmd"
	"k8s.io/client-go/tools/remotecommand"
	"os"
	"testing"
)

func TestGetVMHostName(t *testing.T) {
	name := GetVMHostName()
	fmt.Println(name)
}

func TestGetIPByNodeName(t *testing.T) {
	ip, err := GetIPByNodeName("vm.node131")
	fmt.Printf("err:%+v\n", err)
	fmt.Printf("name:%+v\n", ip)
}

func TestCheckNfsMount(t *testing.T) {
	mount := CheckNfsMount("10.107.246.5", "/var/lib/libvirt/share/image")
	fmt.Printf("mount:%+v", mount)
}

func TestGetAwsS3BucketInfo(t *testing.T) {
	info, s, s2, err := GetAwsS3BucketInfo()
	fmt.Printf("%s\n", info)
	fmt.Printf("%s\n", s)
	fmt.Printf("%s\n", s2)
	fmt.Printf("%+v\n", err)
}

func TestGetAwsS3AccessInfo(t *testing.T) {
	info, s, err := GetAwsS3AccessInfo()
	fmt.Printf("%s\n", info)
	fmt.Printf("%s\n", s)
	fmt.Printf("%+v\n", err)
}

func TestGetNfsServiceIp(t *testing.T) {
	fmt.Println(GetHostIp())
	fmt.Println(GetNodeVirtToolIp("133.133.135.138"))
}

func TestGetNodeVirtToolIp(t *testing.T) {
	//fmt.Println(GetNodeVirtToolIp("133.133.135.138"))
	podName := GetNodeVirtToolIp("133.133.135.138")
	//comm2 := utils.Command{Cmd: scmd2}
	//comm2.Execute()
	secret, _ := rook.GetSecret()
	sourceHost := "10.254.129.113:6789"
	sourcePath := "/volumes/subvolume1"
	url := "/var/lib/libvirt/cephfspool"
	scmd2 := fmt.Sprintf("mount -t ceph -o mds_namespace=%s,name=%s,secret=%s %s:%s %s", constant.DefaultMdsNamespace, constant.DefaultName, secret, sourceHost, sourcePath, url)
	fmt.Println(scmd2)
	client, _ := NewClient()
	req := client.CoreV1().RESTClient().Post().
		Resource("pods").
		Name(podName).
		Namespace("kube-system").
		SubResource("exec").
		VersionedParams(&corev1.PodExecOptions{
			Command:   []string{"/bin/bash", "-c", scmd2},
			Container: "virtctl",
			Stdin:     true,
			Stdout:    true,
			Stderr:    true,
			TTY:       false,
		}, scheme.ParameterCodec)
	config, _ := clientcmd.BuildConfigFromFlags("", "/root/.kube/config")
	exec, err := remotecommand.NewSPDYExecutor(config, "POST", req.URL())
	screen := struct {
		io.Reader
		io.Writer
	}{os.Stdin, os.Stdout}
	err = exec.Stream(remotecommand.StreamOptions{
		Stdin:  screen,
		Stdout: screen,
		Stderr: screen,
		Tty:    false,
	})
	fmt.Println(err)
	//fmt.Printf("Output from pod: %v", stdout.String())
	//fmt.Printf("Error from pod: %v", stderr.String())
}
