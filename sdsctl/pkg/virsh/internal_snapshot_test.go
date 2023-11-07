package virsh

import (
	"fmt"
	"testing"
)

func TestIsCurrentInternalSnapshotExist(t *testing.T) {
	exist, err := IsCurrentInternalSnapshotExist("kvm3")
	fmt.Printf("err:%+v\n", err)
	fmt.Printf("exist:%+v\n", exist)
}

func TestGetCurrentInternalSnapshot(t *testing.T) {
	snapshot, err := GetCurrentInternalSnapshot("kvm3")
	fmt.Printf("err:%+v\n", err)
	name, _ := snapshot.GetName()
	fmt.Printf("snapshot:%+v\n", name)
}

func TestCreateInternalSnapshot(t *testing.T) {
	err := CreateInternalSnapshot("kvm3", "test-clone12.qcow2")
	fmt.Printf("err:%+v\n", err)
}

// exist internal snapshot
func TestCreateInternalSnapshot2(t *testing.T) {
	err := CreateInternalSnapshot("kvm3", "test-clone6.qcow2")
	fmt.Printf("err:%+v\n", err)
}

func TestDeleteInternalSnapshot(t *testing.T) {
	err := DeleteInternalSnapshot("kvm3", "test-clone11.qcow2")
	fmt.Printf("err:%+v\n", err)
}

func TestRevertInternalSnapshot(t *testing.T) {
	err := RevertInternalSnapshot("kvm3", "test-clone12.qcow2")
	fmt.Printf("err:%+v\n", err)
}

func TestListAllCurrentInternalSnapshots(t *testing.T) {
	snapshots, err := ListAllCurrentInternalSnapshots("kvm3")
	for _, snap := range snapshots {
		fmt.Printf("snap:%+v\n", snap)
	}
	fmt.Printf("err:%+v", err)
}
