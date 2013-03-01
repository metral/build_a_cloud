#!/bin/bash

# update & dist-upgrade
unset UCF_FORCE_CONFFOLD
export UCF_FORCE_CONFFNEW=YES
ucf --purge /boot/grub/menu.lst

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get -o Dpkg::Options::="--force-confnew" --force-yes -fuy dist-upgrade

(cat | sudo tee /etc/rc.local) << EOF
#!/bin/sh -e
#
# rc.local
#
#
# This script is executed at the end of each multiuser runlevel.
# Make sure that the script will "exit 0" on success or any other
# value on error.
#
# In order to enable or disable this script just change the execution
#
# bits.
#
# By default this script does nothing.

chmod +x /root/install_server.sh
/root/install_server.sh > /root/install_server_status.txt 2>&1 &
exit 0
EOF

reboot
