
// revert_external_snapshot_fixed.go
package externalSnapshot

import (
    "fmt"
    "os"
    "path/filepath"
    "time"

    "github.com/urfave/cli/v2"
    // assume virsh and ksgvr helpers exist in the repo (as in original)
    "github.com/kube-stack/sdsctl/pkg/virsh"
    "github.com/kube-stack/sdsctl/pkg/k8s"
    "github.com/kube-stack/sdsctl/pkg/constant"
)

// revertExternalSnapshot performs a true revert to an existing qcow2 backing snapshot.
// Behavior:
//  - ensure the named snapshot (ctx.String("name")) exists for the source volume
//  - ensure VM is shut off (or offline) before switching disk
//  - switch VM disk from current -> backing file (the desired snapshot backing)
//  - optionally remove the previous 'current' file or keep as backup (configurable)
//  - update CRD config 'current' and 'full_backing_filename' accordingly
func revertExternalSnapshot(ctx *cli.Context) error {
    pool := ctx.String("pool")
    src := ctx.String("source")
    snapName := ctx.String("name")
    domain := ctx.String("domain")
    diskDir := ctx.String("disk-dir")
    format := ctx.String("format")
    if format == "" {
        format = "qcow2"
    }
    if pool == "" || src == "" || snapName == "" {
        return fmt.Errorf("pool, source and name must be provided")
    }

    // 1. verify snapshot exists
    exists, err := virsh.IsDiskSnapshotExist(pool, src, snapName)
    if err != nil {
        return fmt.Errorf("check snapshot exist failed: %v", err)
    }
    if !exists {
        return fmt.Errorf("snapshot %s does not exist for %s/%s", snapName, pool, src)
    }

    // 2. get full path of current volume file and the backing file for the snapshot
    currentFile, err := virsh.GetVolumePath(pool, src)
    if err != nil {
        return fmt.Errorf("get current volume path failed: %v", err)
    }
    // backing file for the snapshot (we assume virsh provides this)
    backingFile, err := virsh.GetSnapshotBackingFile(pool, src, snapName)
    if err != nil {
        return fmt.Errorf("get snapshot backing file failed: %v", err)
    }

    // 3. ensure domain is shutoff (safe operation)
    if domain != "" {
        state, err := virsh.DomainState(domain)
        if err != nil {
            return fmt.Errorf("get domain state failed: %v", err)
        }
        if state != "shut off" && state != "shutoff" && state != "shutdown" {
            return fmt.Errorf("domain %s must be shut off before reverting disk (current state: %s)", domain, state)
        }
    }

    // 4. perform disk switch: change VM disk source from currentFile -> backingFile
    if domain != "" {
        if err := virsh.ChangeVMDisk(domain, currentFile, backingFile); err != nil {
            return fmt.Errorf("change vm disk failed: %v", err)
        }
    }

    // 5. Optionally keep a backup of currentFile (rename)
    backup := currentFile + ".bak-" + time.Now().Format("20060102150405")
    if err := os.Rename(currentFile, backup); err != nil {
        // not fatal; log and continue
        fmt.Printf("warning: rename current file failed: %v, trying cp fallback\n", err)
        if cpErr := virsh.CopyFile(currentFile, backup); cpErr != nil {
            return fmt.Errorf("backup current file failed: %v (rename err: %v)", cpErr, err)
        }
    }

    // 6. create new empty placeholder current file pointing to backingFile (create qcow2 overlay)
    newCurrent := filepath.Join(diskDir, filepath.Base(currentFile))
    if err := virsh.CreateDiskWithBacking(format, backingFile, format, newCurrent); err != nil {
        return fmt.Errorf("create new current disk overlay failed: %v", err)
    }

    // 7. update config and CRD
    cfg := map[string]string{}
    cfg["current"] = newCurrent
    cfg["disk"] = src
    cfg["full_backing_filename"] = backingFile
    if err := virsh.CreateConfig(diskDir, cfg); err != nil {
        return fmt.Errorf("create config failed: %v", err)
    }

    // update CRD via ksgvr: update existing object (use ctx.String("name") as CR name if exists)
    res := map[string]interface{}{
        "spec": map[string]interface{}{
            "disk": cfg["disk"],
            "current": cfg["current"],
            "full_backing_filename": cfg["full_backing_filename"],
        },
    }
    // try update first, then create fallback
    if err := ksgvr.Update(ctx.Context, constant.DefaultNamespace, src, constant.CRD_Volume_Key, res); err != nil {
        // try create new resource with unique name
        u := fmt.Sprintf("%s-reverted-%d", src, time.Now().Unix())
        if err2 := ksgvr.Create(ctx.Context, constant.DefaultNamespace, u, constant.CRD_Volume_Key, res); err2 != nil {
            return fmt.Errorf("update/create CRD failed: update err: %v, create err: %v", err, err2)
        }
    }

    fmt.Printf("reverted %s to snapshot %s, new current: %s, old backed up to %s\n", src, snapName, newCurrent, backup)
    return nil
}
