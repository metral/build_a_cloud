import os
tests_dirpath = os.path.dirname(os.path.realpath(__file__))
source_dirpath = os.path.dirname(tests_dirpath)

import sys
sys.path.insert(0, source_dirpath)

import oc

url = "https://166.78.252.140:8443"
user = "admin"
password = "qU0HXgucv9Oo"

node = {'id':'6'}
    
controller = oc.Adventure.provision_nova_node("Infrastructure", node, url, user, password)
print controller['name']
