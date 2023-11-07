package virsh

import (
	"fmt"
	libvirtxml "github.com/libvirt/libvirt-go-xml"
	"libvirt.org/go/libvirt"
	"strconv"
	"time"
)

type InternalSnapshot struct {
	Name    string
	Date    time.Time
	State   string
	Current bool
}

func IsCurrentInternalSnapshotExist(domainName string) (bool, error) {
	conn, err := GetConn()
	if err != nil {
		return false, err
	}
	domain, err := conn.LookupDomainByName(domainName)
	if err != nil {
		return false, err
	}
	return domain.HasCurrentSnapshot(0)
}

func GetCurrentInternalSnapshot(domainName string) (*libvirt.DomainSnapshot, error) {
	conn, err := GetConn()
	if err != nil {
		return nil, err
	}
	domain, err := conn.LookupDomainByName(domainName)
	if err != nil {
		return nil, err
	}
	exist, _ := domain.HasCurrentSnapshot(0)
	if !exist {
		return nil, fmt.Errorf("domain %s has no current internal snapshot", domainName)
	}
	return domain.SnapshotCurrent(0)
}

func ListAllCurrentInternalSnapshots(domainName string) ([]*InternalSnapshot, error) {
	conn, err := GetConn()
	if err != nil {
		return nil, err
	}
	domain, err := conn.LookupDomainByName(domainName)
	if err != nil {
		return nil, err
	}
	snapshots, err := domain.ListAllSnapshots(0)
	if err != nil {
		return nil, err
	}
	currentSnapshot, _ := GetCurrentInternalSnapshot(domainName)
	currentName, _ := currentSnapshot.GetName()
	internalSnapshots := make([]*InternalSnapshot, 0)
	for _, item := range snapshots {
		desc, _ := item.GetXMLDesc(0)
		xml := &libvirtxml.DomainSnapshot{}
		err := xml.Unmarshal(desc)
		if err != nil {
			return nil, err
		}
		i, _ := strconv.ParseInt(xml.CreationTime, 10, 64)
		formatTime := time.Unix(i, 0)
		current := false
		if xml.Name == currentName {
			current = true
		}
		internalSnapshots = append(internalSnapshots, &InternalSnapshot{
			Name:    xml.Name,
			Date:    formatTime,
			State:   xml.State,
			Current: current,
		})
	}
	return internalSnapshots, nil
}

func CreateInternalSnapshot(domainName, snapshotName string) error {
	conn, err := GetConn()
	if err != nil {
		return err
	}
	domain, err := conn.LookupDomainByName(domainName)
	if err != nil {
		return err
	}
	xml := &libvirtxml.DomainSnapshot{
		Name: snapshotName,
	}
	marshal, _ := xml.Marshal()
	_, err = domain.CreateSnapshotXML(marshal, 0)
	return err
}

func RevertInternalSnapshot(domainName, snapshotName string) error {
	conn, err := GetConn()
	if err != nil {
		return err
	}
	domain, err := conn.LookupDomainByName(domainName)
	if err != nil {
		return err
	}
	snapshot, err := domain.SnapshotLookupByName(snapshotName, 0)
	if err != nil {
		return err
	}
	return snapshot.RevertToSnapshot(0)
}

func DeleteInternalSnapshot(domainName, snapshotName string) error {
	conn, err := GetConn()
	if err != nil {
		return err
	}
	domain, err := conn.LookupDomainByName(domainName)
	if err != nil {
		return err
	}
	snapshot, err := domain.SnapshotLookupByName(snapshotName, 0)
	if err != nil {
		return err
	}
	return snapshot.Delete(0)
}
