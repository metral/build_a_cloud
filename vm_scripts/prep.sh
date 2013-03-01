#!/bin/bash

chmod +x /root/upgrade.sh
/root/upgrade.sh > /root/upgrade_status.txt 2>&1 &
