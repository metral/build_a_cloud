################################################################################
import sys
import json
import subprocess
#-------------------------------------------------------------------------------
def get_env_json():
    command = "/opt/chef-server/bin/knife environment show NovaCluster -f json"
    p = subprocess.Popen(command, stdout = subprocess.PIPE, shell=True)
    output, error = p.communicate()
    
    return output
#-------------------------------------------------------------------------------
def create_new_env_json(f):
    data = json.loads(f)

    attrs = data["override_attributes"]
    nova = attrs["nova"]

    nova["libvirt"] = {"virt_type": "qemu"}
    #del nova["libvirt"]

    attrs["nova"] = nova
    data["override_attributes"] = attrs

    data_json = json.dumps(data)
    
    fp = "/tmp/new_env.json"
    new_file = open(fp, "w")
    new_file.write(data_json)
    new_file.close()

    return fp
#-------------------------------------------------------------------------------
def update_env(fp):
    command = "/opt/chef-server/bin/knife environment from file %s" %fp
    p = subprocess.Popen(command, stdout = subprocess.PIPE, shell=True)
    output, error = p.communicate()
    return output, error
#-------------------------------------------------------------------------------
def main():
    env_json = get_env_json()
    fp = create_new_env_json(env_json)
    output, error = update_env(fp)
    
    # cleanup
    command = "rm -rf /root/*.py"
    p = subprocess.Popen(command, stdout = subprocess.PIPE, shell=True)
    
    print output, error
#-------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
#-------------------------------------------------------------------------------
################################################################################
