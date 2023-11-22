package constant

import (
	"net/http"
)

// grpc status & msg
const (
	SocketPath      = "/var/lib/libvirt/ks.sock"
	CephfsMountPath = "/var/lib/libvirt/mount"
)

const (
	STATUS_OK         = http.StatusOK
	STATUS_BADREQUEST = http.StatusBadRequest
	STATUS_ERR        = http.StatusInternalServerError
)

const (
	MESSAGE_OK = "ok"
)

// log
const (
	DefualtLogPath = "/var/log/sdsctl.log"
)

// pool type
const (
	// yaml spec
	PoolCephfsType  = "cephfs"
	PoolNetfsType   = "netfs"
	PoolCephRbdType = "cephrbd"
	PoolCephNFSType = "cephnfs"
	PoolCephRgwType = "cephrgw"

	// virsh spec
	PoolDirType     = "dir"
	PoolLocalFsType = "localfs"
	PoolNFSType     = "nfs"
	PoolRbdType     = "rbd"
)

// rook
const (
	DefaultMdsNamespace   = "myfs"
	DefaultName           = "admin"
	DefaultNFSClusterName = "my-nfs"
	DefaultCephRwgName    = "ceph-delete-bucket"
)

const (
	// rook related
	RookNamespace = "rook-ceph"

	// aws rgw s3 default info
	S3ConfigMapName = "ceph-delete-bucket"
	S3SecretName    = "ceph-delete-bucket"

	// image hub type
	NfsImageHub     = "nfs"
	CephrwgImageHub = "cephrgw"

	// rbd pool
	DefaultRookGroup     = "ceph.rook.io"
	DefaultRookVersion   = "v1"
	CephBlockPool_Kind   = "CephBlockPool"
	CephBlockPoolS_Kinds = "cephblockpools"
	CephNFSPool_Kind     = "CephNFS"
	CephNFSPoolS_Kinds   = "cephnfses"
)

// k8s CRD
const (
	// crd group & version
	DefaultGroup     = "doslab.io"
	DefaultVersion   = "v1"
	DefaultNamespace = "default"

	// crd kind
	VMD_Kind     = "VirtualMachineDisk"
	VMDS_Kind    = "virtualmachinedisks"
	VMP_Kind     = "VirtualMachinePool"
	VMPS_Kind    = "virtualmachinepools"
	VMDSN_Kind   = "VirtualMachineDiskSnapshot"
	VMDSNS_Kinds = "virtualmachinedisksnapshots"
	VMDI_KIND    = "VirtualMachineDiskImage"
	VMDIS_KINDS  = "virtualmachinediskimages"

	// spec key
	CRD_Pool_Key     = "pool"
	CRD_Volume_Key   = "volume"
	CRD_NodeName_Keu = "nodeName"

	// vm pool status
	CRD_Pool_Active   = "active"
	CRD_Pool_Inactive = "inactive"

	CRD_Ready_Msg    = "The resource is ready."
	CRD_Ready_Reason = "Ready"
)
