cidr=$(kubectl get subnet | grep ovn-default | awk '{print$5}')

kubectl ko nbctl set logical_switch ovn-default other_config:subnet="$cidr"
kubectl ko nbctl dhcp-options-create $cidr
uuid=$(kubectl ko nbctl --bare --columns=_uuid find dhcp_options cidr="$cidr")

ip=$(echo $cidr | awk -F'.' '{print$1"."$2"."$3".1"}')
kubectl ko nbctl dhcp-options-set-options $uuid lease_time=3600 router=$ip server_id=$ip server_mac=c0:ff:ee:00:00:01