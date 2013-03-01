#===============================================================================
from rackspace import CloudServers
import os
#-------------------------------------------------------------------------------

USERNAME = os.environ["OS_USERNAME"]
API_KEY = os.environ["OS_PASSWORD"]

TENANT_NAME = os.environ["OS_TENANT_NAME"]
REGION = os.environ["OS_REGION_NAME"]
AUTH_SYSTEM = os.environ["OS_AUTH_SYSTEM"]
AUTH_URL = os.environ["OS_AUTH_URL"]
#-------------------------------------------------------------------------------
def main():
    # Create CloudServers object to connect with Rackspace CloudServers
    cloudservers = CloudServers.create(USERNAME, API_KEY, TENANT_NAME,
            AUTH_URL, AUTH_SYSTEM, REGION)
    
    # Build A Cloud
    CloudServers.build_a_cloud(cloudservers.nova_client)
#-------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
#-------------------------------------------------------------------------------
#===============================================================================
