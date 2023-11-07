package rook

import "github.com/kube-stack/sdsctl/pkg/utils"

func GetSecret() (string, error) {
	scmd := &utils.Command{
		Cmd: "grep key /etc/ceph/keyring | awk '{print $3}'",
	}
	return scmd.Execute()
}
