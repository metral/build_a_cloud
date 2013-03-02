#!/bin/bash

curl -L "https://bcd46edb6e5fd45555c0-409026321750f2e680f86e05ff37dd6d.ssl.cf1.rackcdn.com/install.sh" | bash -s server
curl -L "https://bcd46edb6e5fd45555c0-409026321750f2e680f86e05ff37dd6d.ssl.cf1.rackcdn.com/install.sh" | bash -s dashboard

# cleanup
rm /etc/prep.sh
 > /etc/rc.local
rm -rf /root/*
#rm -rf /root/.ssh
