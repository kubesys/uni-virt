package virsh

import (
	"encoding/xml"
	"github.com/kube-stack/sdsctl/pkg/constant"
	"github.com/kube-stack/sdsctl/pkg/utils"
	libvirtxml "github.com/libvirt/libvirt-go-xml"
	"libvirt.org/go/libvirt"
	"os"
	"path/filepath"
)

func GetPoolInfo(name string) (*libvirt.StoragePool, error) {
	conn, err := GetConn()
	defer conn.Close()
	if err != nil {
		return nil, err
	}
	pool, err := conn.LookupStoragePoolByName(name)
	if err != nil {
		return nil, err
	}
	return pool, nil
}

func GetPoolState(state libvirt.StoragePoolState) string {
	if state == libvirt.STORAGE_POOL_RUNNING {
		return "active"
	}
	return "inactive"
}

func CreatePool(name, ptype, target, sourceHost, sourceName, sourcePath string) (*libvirt.StoragePool, error) {
	pool, err := DefinePool(name, ptype, target, sourceHost, sourceName, sourcePath)
	if err != nil {
		return nil, err
	}
	// start pool
	err = StartPool(name)
	if err != nil {
		return nil, err
	}
	return pool, nil
}

func DefinePool(name, ptype, target, sourceHost, sourceName, sourcePath string) (*libvirt.StoragePool, error) {
	conn, err := GetConn()
	defer conn.Close()
	if err != nil {
		return nil, err
	}

	if !utils.Exists(target) {
		utils.CreateDir(target)
	}

	poolXML := libvirtxml.StoragePool{
		Type: ptype,
		Name: name,
		//Source:
		Target: &libvirtxml.StoragePoolTarget{
			Path: target,
		},
	}
	// fix
	if sourceName != "" {
		poolXML.Source = &libvirtxml.StoragePoolSource{
			Name: sourceName,
			Dir: &libvirtxml.StoragePoolSourceDir{
				Path: sourcePath,
			},
			Host: []libvirtxml.StoragePoolSourceHost{
				{
					Name: sourceHost,
				},
			},
			//Auth: &libvirtxml.StoragePoolSourceAuth{},
		}
	}
	if ptype == constant.PoolRbdType {
		poolXML.Source.Auth = &libvirtxml.StoragePoolSourceAuth{}
		secret, err := GetOrCreateCephTypeSecret("client.admin")
		if err != nil {
			return nil, err
		}
		poolXML.Source.Auth.Type = "ceph"
		poolXML.Source.Auth.Username = "admin"
		poolXML.Source.Auth.Secret = &libvirtxml.StoragePoolSourceAuthSecret{
			UUID: secret,
		}
	}
	poolDoc, err := poolXML.Marshal()
	if err != nil {
		return nil, err
	}
	// use define instead of create in order to create xml in /etc/libvirt/storage
	return conn.StoragePoolDefineXML(poolDoc, 0)
}

func AutoStartPool(name string, autoStart bool) error {
	conn, err := GetConn()
	defer conn.Close()
	if err != nil {
		return err
	}
	pool, err := conn.LookupStoragePoolByName(name)
	return pool.SetAutostart(autoStart)
}

func DeletePool(name string) error {
	conn, err := GetConn()
	defer conn.Close()
	if err != nil {
		return err
	}
	pool, err := conn.LookupStoragePoolByName(name)
	if err != nil {
		return err
	}
	//path, err := GetPoolTargetPath(name)
	//if utils.Exists(path) {
	//	os.RemoveAll(path)
	//}
	pool.Destroy()
	pool.Undefine()
	return nil
}

func StartPool(name string) error {
	conn, err := GetConn()
	defer conn.Close()
	if err != nil {
		return err
	}
	pool, err := conn.LookupStoragePoolByName(name)
	if err != nil {
		return err
	}
	return pool.Create(0)
}

func StopPool(name string) error {
	conn, err := GetConn()
	defer conn.Close()
	if err != nil {
		return err
	}
	pool, err := conn.LookupStoragePoolByName(name)
	if err != nil {
		return err
	}
	return pool.Destroy()
}

func IsPoolActive(name string) (bool, error) {
	conn, err := GetConn()
	defer conn.Close()
	if err != nil {
		return false, err
	}
	pool, err := conn.LookupStoragePoolByName(name)
	if err != nil {
		return false, err
	}
	return pool.IsActive()
}

func CheckPoolType(pool, content string) bool {
	poolDir, err := GetPoolTargetPath(pool)
	if err != nil {
		return false
	}
	contentPath := filepath.Join(poolDir, "content")
	file, err := os.ReadFile(contentPath)
	if err != nil {
		return false
	}
	return string(file) == content
}

func GetPoolTargetPath(name string) (string, error) {
	conn, err := GetConn()
	defer conn.Close()
	if err != nil {
		return "", err
	}
	pool, err := GetPoolInfo(name)
	if err != nil {
		return "", err
	}
	pxml, err := pool.GetXMLDesc(0)
	if err != nil {
		return "", err
	}
	poolObj := &libvirtxml.StoragePool{}
	err = xml.Unmarshal([]byte(pxml), poolObj)
	if err != nil {
		return "", err
	}
	return poolObj.Target.Path, nil
}
