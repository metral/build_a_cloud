#!/bin/bash

curl -L "https://bcd46edb6e5fd45555c0-409026321750f2e680f86e05ff37dd6d.ssl.cf1.rackcdn.com/install.sh" | bash -s agent SERVER_IP PASSWORD

# cleanup
rm /etc/prep.sh
 > /etc/rc.local
rm -rf /root/*
#rm -rf /root/.ssh

echo "if [ -f /root/openrc ]; then source /root/openrc ; fi" >> /root/.bashrc
