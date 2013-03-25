#!/bin/bash

ssh-keygen -t rsa

sudo apt-get update
sudo apt-get install python-setuptools -y

sudo easy_install pip
sudo pip install rackspace-novaclient

sudo apt-get install pwgen -y
