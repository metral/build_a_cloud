#!/bin/bash

ENVIRONMENT_FILE="/usr/share/pyshared/opencenter/backends/chef-client/environment.tmpl"

sed -i 's/"apply_patches": true,/"apply_patches": true,\n\t"libvirt": {\n\t\t"virt_type": "qemu"\n\t},/g' $ENVIRONMENT_FILE

/etc/init.d/opencenter-agent restart

rm -rf /root/*.sh
