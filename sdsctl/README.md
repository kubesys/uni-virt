# sdsctl
Software-defined storage controller for kube-stack.

# Installation
```shell
cd ./sdsctl/cmd/sdsctl

go build -o sdsctl main.go

cp sdsctl /usr/bin
```

# usage
```shell
# ref: https://github.com/kube-stack/sdsctl/blob/main/cmd/sdsctl/main.go
# ref: https://github.com/kube-stack/sdsctl/blob/main/pkg/cmds/root.go
sdsctl --help

# ref: https://github.com/kube-stack/sdsctl/blob/main/pkg/cmds/pool/create_pool.go
sdsctl create-pool --help
```

# log
```shell
cat /var/log/sdsctl.log
```