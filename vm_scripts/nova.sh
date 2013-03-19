#!/bin/bash

source /root/openrc

nova secgroup-add-rule default icmp -1 -1 0.0.0.0/0
nova secgroup-add-rule default tcp 22 22 0.0.0.0/0

function setup_iptables {
    CLOUD_NET_IP=`ifconfig eth2 | grep "inet addr" | awk '{print $2}' | cut -d ":" -f2`;

    # Enable forwarding
    sed -i '/net.ipv4.ip_forward/ s/^#//' /etc/sysctl.conf
    sysctl -p /etc/sysctl.conf 1

    # Add iptables rule...
    if ! iptables -t nat -nvL PREROUTING | grep -q 443; then
        iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 443 -j DNAT --to-destination $CLOUD_NET_IP
    fi

    if ! iptables -t nat -nvL PREROUTING | grep -q 80; then
        iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 -j DNAT --to-destination $CLOUD_NET_IP
    fi

    # ...and make persistent
    echo iptables-persistent iptables-persistent/autosave_v4 select true | debconf-set-selections
    echo iptables-persistent iptables-persistent/autosave_v6 select true | debconf-set-selections
    apt-get -y install iptables-persistent

    iptables-save > /etc/iptables/rules
}

setup_iptables

rm -rf /root/*.sh
