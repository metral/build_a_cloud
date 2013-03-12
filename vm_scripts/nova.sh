#!/bin/bash

source /root/openrc

nova secgroup-add-rule default icmp 0 8 0.0.0.0/0
nova secgroup-add-rule default tcp 22 22 0.0.0.0/0

rm -rf /root/*.sh
