#===============================================================================
from time import time, sleep
import base64
import inspect
import json
import logging
import os
import random
import socket
import subprocess
import sys
import urllib2
import logging
#-------------------------------------------------------------------------------
logger = logging.getLogger('build_a_cloud')
#-------------------------------------------------------------------------------
class Utils:
#-------------------------------------------------------------------------------
    @classmethod
    def read_data(cls, filepath):
        data = ""

        with open(filepath, "rb") as f:
            data = f.read()

        return data
#-------------------------------------------------------------------------------
    @classmethod
    def timestamp_rand(cls):
        return str(int(time())) + "-" + str(random.randint(10000000,99999999))
#-------------------------------------------------------------------------------
    @classmethod
    def generate_password(cls):
        error = ""

        try:
            command = "pwgen -s 12"
            p = subprocess.Popen(command, stdout = subprocess.PIPE, shell=True)
            output, error = p.communicate()
            output = output.replace("\n", "")
            output = output.replace(" ", "")
        except Exception,e:
            logger.error(str(e))
            return none

        return output
#-------------------------------------------------------------------------------
    @classmethod
    def do_subprocess(cls, command):
        try:
            with open(os.devnull) as quiet:
                p = subprocess.Popen(\
                        command, stdout=quiet, stderr=quiet, shell=True)
        except Exception,e:
            logger.error(str(e))
#-------------------------------------------------------------------------------
    @classmethod
    def find_server(cls, nova_client, server_name):
        try:
            servers = nova_client.servers.list()
            for server in servers:
                if server.name == server_name:
                    return server
        except Exception,e:
            logger.error(str(e))
            return None
#-------------------------------------------------------------------------------
    @classmethod
    def print_server_status(cls, server):
        try:
            msg = "Server Name: %s" % server.name
            logger.debug(msg)
            msg = "Server Status: %s" % server.status
            logger.debug(msg)
            msg = "Server Progress: %s%%" % server.progress
            logger.debug(msg)
        except Exception,e:
            logger.error(str(e))
#-------------------------------------------------------------------------------
    @classmethod
    def print_server_info(cls, server):
        try:
            msg = "Server Status: %s" % server.status
            logger.info(msg)
            msg =  "Server Name: %s" % server.name
            logger.info(msg)
            msg =  "Server Public IP: %s" % \
                cls.get_ipv4(server.addresses["public"])
            logger.info(msg)
            msg = "Server Root Password: %s" % server.adminPass
            logger.info(msg)
            if server.oc_password:
                msg = "OpenCenter Username: admin"
                logger.info(msg)
                msg = "OpenCenter Password: %s" % server.oc_password
                logger.info(msg)
        except Exception,e:
            pass
#-------------------------------------------------------------------------------
    @classmethod
    def get_ipv4(cls, addresses):
        ipv4 = ""

        for ip in addresses:
            if ip["version"] == 4:
                ipv4 = ip["addr"]

        return ipv4
#-------------------------------------------------------------------------------
    @classmethod
    def generate_unique_name(cls, name):
        unique_name = "-".join([name, cls.timestamp_rand()])
        return unique_name
#-------------------------------------------------------------------------------
    @classmethod
    def get_limit(cls, nova_client, limit_name):
        total_used = 0
        limits = None

        while limits is None:
            try:
                limits = nova_client.limits.get()
            except Exception,e:
                logger.error(str(e))
                msg = "Retrying in 10 secs..."
                logger.error(msg)
                sleep(10)
                
        for limit in limits.absolute:
            if limit.name == limit_name:
                total_used = limit.value

        return total_used
#-------------------------------------------------------------------------------
    @classmethod
    def has_enough(cls, nova_client, limit_name, needed, max):
        used = cls.get_limit(nova_client, limit_name)

        tentative_total = used + needed

        if tentative_total <= max:
            return True, used
        return False, used
#-------------------------------------------------------------------------------
    @classmethod
    def port_is_open(cls, ip, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(30)

        try:
            s.connect((ip, int(port)))
            s.settimeout(None)
            return True
        except:
            return False
#-------------------------------------------------------------------------------
#    @classmethod
#    def log(cls, message):
#        timestamp = str(int(time()))
#        filename = "%s.log" % timestamp
#        filepath = "/".join(["logs", filename]) 
#        f = open(filepath, 'w')
#
#        frame,filename,line_number,function_name,lines,index=\
#                inspect.getouterframes(inspect.currentframe())[1]
#        msg ="file: %s | func: %s() | line # %s | message: \n\t%s\n"\
#                    % (filename, function_name, line_number, str(data))
#        f.write(msg)
#
#        f.close()
#-------------------------------------------------------------------------------
    @classmethod
    def oc_api(cls, url, username, password, **kwargs):
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
                logger.error(error_json)
            json_data = json.loads(error_json)
            return json_data
#-------------------------------------------------------------------------------
    @classmethod
    def extract_oc_object_type(cls, json_data, object_type):
        if json_data is None:
            return None
        
        status = int(json_data['status'])
        
        try:
            if status == 200:
                extract = json_data[object_type]
                return extract
        except Exception,e:
            logger.error(str(e))
            return None
#-------------------------------------------------------------------------------
    @classmethod
    def execute(cls, path, url, user, password, params = None):
        full_url = url + path

        result = None
        if params:
            result = Utils.oc_api(full_url, user, password,
                    kwargs={'json': params})
        else:
            result = Utils.oc_api(full_url, user, password)

        if result:
            return result
        return None
#-------------------------------------------------------------------------------
#===============================================================================
