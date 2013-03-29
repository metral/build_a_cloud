<!---------------------------------------------------------------------------->

# Build A Cloud

<!---------------------------------------------------------------------------->

<h3>Description</h3>
Build A Cloud allows you to deploy Rackspace's Private Cloud v3 onto VM's
deployed in Rackspace's Public Cloud Servers. This allows you to test the
OpenStack Nova capabilities offered by Rackspace's Private Cloud without
needing to setup or use any dedicated infrastructure of your own.

There are a total of 5 servers instantiated in the following capacity:

*   1 - OpenCenter Server
*   1 - OpenCenter Chef Server
*   1 - Nova Controller
*   2 - Nova Compute Nodes.

</br>
Specifically, Build A Cloud does the following:

1. Launches 5 vanilla Ubuntu 12.04 VM's.
2. Upgrades each VM to the latest packages & kernel
3. Executes the OpenCenter bootstrapping process depending on which node it is.
   The OpenCenter roles are: server, dashboard and agent.
   The OpenCenter Server receives the server & dashboard roles, where as the 
   remaining VM's get the agent role.
4. Once all 5 VM's are stood up with the appropriate OpenCenter role, the
   agent VM's are provisioned into the following types of nodes in the
   following order: OpenCenter Chef Server, Nova Controller & Nova Computes
5. Once all servers are provisioned and Build A Cloud has finished, 
   you may log into the either node to
   examine its setup and then log into the node assigned as the Nova
   Controller to begin dispatching VM's via the usual OpenStack methods.

<!---------------------------------------------------------------------------->
<h3>Pre-Requisites</h3>
Note: This is written for usage on an Ubuntu 12.04 machine

1. A Rackspace Cloud Servers account: https://cart.rackspace.com/cloud/
2. Cloud Networks enabled on the Cloud Servers Account: https://www.iwantcloudnetworks.com/
3. Quota availability of at least 1 Cloud Network
4. Quota availability of at least 40GB of RAM
5. Have your Cloud Servers API Key ready: https://mycloud.rackspace.com/a/metral/account/api-keys
6. Appropriately set your Cloud Servers username in 'creds'
7. Appropriately set your Cloud Servers password (api key) in 'creds'
8. Run `$ ./install_deps.sh` to install the dependencies needed
8. Source the 'creds' file into your environment
9. Test that the sourced 'creds' work by issuing a `$ nova image-list`

<!---------------------------------------------------------------------------->

<h3>Usage</h3>
1. `$ python cloud.py &`
2. Track deployment progress in logs/\{timestamp\}.log
3. All node information with regards to server IP's, usernames & passwords are
displayed in the logs
4. To view the OpenCenter GUI, use the bac-opencenter-server-\* IP and the
corresponding OpenCenter user & password
