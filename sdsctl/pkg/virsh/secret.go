package virsh

import (
	"fmt"
	"github.com/kube-stack/sdsctl/pkg/utils"
	libvirtxml "github.com/libvirt/libvirt-go-xml"
	"libvirt.org/go/libvirt"
	"strings"
)

func GetCephAdminSecret(name string) ([]byte, error) {
	cmd := &utils.Command{
		Cmd: fmt.Sprintf("ceph auth get-key %s", name),
	}
	return cmd.ExecuteWithPlain()
}

func GetSecretValue(usageName string) (string, error) {
	conn, err := GetConn()
	if err != nil {
		return "", err
	}
	secret, err := conn.LookupSecretByUsage(libvirt.SECRET_USAGE_TYPE_CEPH, usageName)
	if err != nil {
		return "", err
	}
	value, err := secret.GetValue(0)
	return string(value), err
}

func SetSecretValue(usageName string) error {
	conn, err := GetConn()
	if err != nil {
		return err
	}
	secret, err := conn.LookupSecretByUsage(libvirt.SECRET_USAGE_TYPE_CEPH, usageName)
	if err != nil {
		return err
	}
	uuid, err := secret.GetUUIDString()
	cmd := &utils.Command{
		Cmd: fmt.Sprintf("virsh secret-set-value --secret %s --base64 $(ceph auth get-key %s)", uuid, usageName),
	}
	_, err = cmd.Execute()
	return err
}

func CreateCephTypeSecret(usageName string) (*libvirt.Secret, error) {
	conn, err := GetConn()
	if err != nil {
		return nil, err
	}
	secretXml := libvirtxml.Secret{
		Ephemeral: "no",
		Private:   "no",
		Usage: &libvirtxml.SecretUsage{
			Type: "ceph",
			Name: usageName,
		},
	}
	marshal, err := secretXml.Marshal()
	if err != nil {
		return nil, err
	}
	secret, err := conn.SecretDefineXML(marshal, 0)
	if err != nil {
		return nil, err
	}
	if err = SetSecretValue(usageName); err != nil {
		return nil, err
	}
	return secret, err
}

func GetOrCreateCephTypeSecret(usageName string) (string, error) {
	conn, err := GetConn()
	if err != nil {
		return "", err
	}
	secret, err := conn.LookupSecretByUsage(libvirt.SECRET_USAGE_TYPE_CEPH, usageName)
	if err != nil {
		// libvirt.ERR_NO_SECRET
		if !strings.Contains(err.Error(), "not found") {
			return "", err
		} else {
			secret, err = CreateCephTypeSecret(usageName)
			if err != nil {
				return "", err
			}
		}
	}
	return secret.GetUUIDString()
}
