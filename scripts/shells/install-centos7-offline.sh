#本机IP
LOCALIP="localhost"
printChangeIp() {
	if [ "$LOCALIP" = "localhost" ]; then
		echo "你的ip未修改,请修改成你部署机ip"
		exit 1
	fi
}

imageload() {
  echo "正在导入镜像"
  for i in $(ls *.tar)
  do
        docker load -i $i
  done
}
pushImage(){
  printChangeIp
  tar xzvf image.tar.gz
  imageload
  sh load_image.sh $LOCALIP
  cd ..
}

pushRpm(){
  printChangeIp
  tar xzvf rpm-package.tar.gz
  cd package || exit 1
  sh push_rpm.sh $LOCALIP
  cd ..
}

Push() {
	case $1 in
	"all")
		pushImage
		sleep 10
		pushRpm
		;;
	"image")
		pushImage
		;;
	"rpm")
		pushRpm
		;;
	esac
}


Sdsctl(){
  printChangeIp
  yum install cloud-utils usbutils libguestfs-tools-c virt-manager libvirt-devel gcc gcc-c++ glib-devel glibc-devel libvirt virt-install qemu-kvm -y
  tar xzvf command.tar.gz
  cp sdsctl /usr/bin
  cp commctl /usr/bin
  sdsctl
  commctl
}

case $1 in
"push")
	Push $2
	;;
"sdsctl")
  Sdsctl
  ;;
esac
#res=$(cat /etc/profile | grep GOROOT | wc -l)
#if [ $res == 0 ]; then
#    mkdir /root/go
#    echo "
## add go
#export GO111MODULE=on
#export GOROOT=/usr/local/go
#export GOPATH=/root/go
#PATH=\$GOROOT/bin:\$PATH" >> /etc/profile
#    source /etc/profile
#fi
#
#go env -w GOPROXY=https://goproxy.cn,direct

##SHELL_FOLDER=$(dirname $(readlink -f "$0"))
#cd ${SHELL_FOLDER}

#kubectl apply -f ./yamls/*.yaml