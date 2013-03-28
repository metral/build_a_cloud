import base64
import json
import urllib2

def oc_api(url, username, password, **kwargs):
    request = urllib2.Request(url)
    result = None

    if kwargs:
        data = kwargs['kwargs']['json']
        data = json.dumps(data)
        request.add_data(data)
        request.add_header("Content-Type", "application/json")   

    base64string = base64.encodestring('%s:%s' % (username,
        password)).replace('\n', '')
    request.add_header("Authorization", "Basic %s" % base64string)   

    try:
        result = urllib2.urlopen(request)
        json_data = json.loads(result.read())
        return json_data
    except Exception, e:
        error_json = e.read()
        if e.code != 409:
            print error_json
        json_data = json.loads(error_json)
        return json_data

def execute(path, url, user, password, params = None):
    full_url = url + path

    result = None
    if params:
        result = oc_api(full_url, user, password,
                kwargs={'json': params})
    else:
        result = oc_api(full_url, user, password)

    if result:
        return result
    return None

cidr = "192.168.3.0/24"
params = {
        "node": 1,
        "plan": [
            { "primitive": "node.add_backend",
                "ns": {
                    "backend": "nova"}},
                { "primitive": "nova.create_cluster",
                    "ns": {
                        "chef_server": 5,
                        "cluster_name": "NovaCluster",
                        "nova_public_if": "eth0",
                        "keystone_admin_pw": "qU0HXgucv9Oo",
                        "nova_dmz_cidr": "172.16.0.0/24",
                        "nova_vm_fixed_range": "172.28.48.0/24",
                        "nova_vm_fixed_if": "eth2",
                        "nova_vm_bridge": "br100",
                        "osops_mgmt": cidr,
                        "osops_nova": cidr,
                        "osops_public": cidr,
                        "libvirt_type": "qemu",
                        }
                    }
                ]
        }

path = "/plan/"
result = execute(path, "https://166.78.252.140:8443", "admin", "qU0HXgucv9Oo", params)

print result

task_id = int(result['task']['id'])
print task_id
