#!/bin/bash

#curl -L "https://bcd46edb6e5fd45555c0-409026321750f2e680f86e05ff37dd6d.ssl.cf1.rackcdn.com/install.sh" | bash -s server 0.0.0.0 PASSWORD
#curl -L "https://bcd46edb6e5fd45555c0-409026321750f2e680f86e05ff37dd6d.ssl.cf1.rackcdn.com/install.sh" | bash -s dashboard
curl -s -L http://sh.opencenter.rackspace.com/install.sh | \
       sudo bash -s - --role=server -p=PASSWORD
curl -s -L http://sh.opencenter.rackspace.com/install.sh | \
        sudo bash -s - --role=dashboard --ip=0.0.0.0

# cleanup
rm /etc/prep.sh
 > /etc/rc.local
rm -rf /root/*
#rm -rf /root/.ssh

echo "export OPENCENTER_ENDPOINT=https://admin:PASSWORD@0.0.0.0:8443" >> /root/.bashrc
