ifconfig ens3 up
ifconfig ens4 up
ifconfig ens3 0
ifconfig ens4 0
ifconfig smore 192.168.1.35
#ifconfig smore:1 10.0.1.19

for i in ens3 ens4 smore smore:1; do
	ifconfig $i mtu 1450
done
ip r add default via 192.168.1.1
echo "nameserver 192.168.1.1" >> /etc/resolv.conf
