package virsh

import (
	"encoding/xml"
	"errors"
	"fmt"
	libvirtxml "github.com/libvirt/libvirt-go-xml"
)

func GetVMDiskSpec(domainName string) ([]libvirtxml.DomainDisk, error) {
	conn, err := GetConn()
	defer conn.Close()
	domain, err := conn.LookupDomainByName(domainName)
	if err != nil {
		return nil, err
	}
	// parse old format
	vxml, err := domain.GetXMLDesc(0)
	if err != nil {
		return nil, err
	}
	vmObj := &libvirtxml.Domain{}
	err = xml.Unmarshal([]byte(vxml), vmObj)
	if err != nil {
		return nil, err
	}
	disks := vmObj.Devices.Disks
	return disks, nil
}

func IsVMExist(domainName string) bool {
	conn, _ := GetConn()
	defer conn.Close()
	_, err := conn.LookupDomainByName(domainName)
	if err != nil {
		return false
	}
	return true
}

func IsVMActive(domainName string) (bool, error) {
	conn, err := GetConn()
	defer conn.Close()
	domain, err := conn.LookupDomainByName(domainName)
	if err != nil {
		return false, err
	}
	return domain.IsActive()
}

func ParseVMDiskSpec(domainName string) (map[string]string, error) {
	disks, err := GetVMDiskSpec(domainName)
	if err != nil {
		return nil, err
	}
	res := make(map[string]string)
	for _, disk := range disks {
		if disk.Source != nil {
			res[disk.Source.File.File] = disk.Target.Dev
		}
	}
	return res, nil
}

func CheckVMDiskSpec(domainName, diskPath string) (map[string]string, error) {
	res, err := ParseVMDiskSpec(domainName)
	if err != nil {
		return res, err
	}
	_, ok := res[diskPath]
	if ok {
		return res, nil
	}
	return res, errors.New(fmt.Sprintf("domain %s has no disk %s", domainName, diskPath))
}

func UpdateVMDiskSpec(domainName, source, target string) (*libvirtxml.DomainDisk, error) {
	disks, err := GetVMDiskSpec(domainName)
	if err != nil {
		return nil, err
	}
	for _, disk := range disks {
		if disk.Source != nil && disk.Source.File.File == source {
			disk.Source.File.File = target
			return &disk, nil
		}
	}
	return nil, fmt.Errorf("no vm disk named %s", source)
}

func ChangeVMDisk(domainName, source, target string) error {
	conn, err := GetConn()
	defer conn.Close()
	domain, err := conn.LookupDomainByName(domainName)
	if err != nil {
		return err
	}

	// update vm disk
	disksSpec, err := UpdateVMDiskSpec(domainName, source, target)
	if err != nil {
		return err
	}
	xmlStr, err := disksSpec.Marshal()
	if err = domain.UpdateDeviceFlags(xmlStr, 0); err != nil {
		return err
	}
	return nil
}
