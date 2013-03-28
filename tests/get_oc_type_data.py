import urllib2
import json
import base64

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

def extract_oc_object_type(json_data, object_type):
    if json_data is None:
        return None
    
    status = int(json_data['status'])
    
    try:
        if status == 200:
            extract = json_data[object_type]
            return extract
    except Exception,e:
        print str(e)
        return None
    

url = "https://166.78.253.120:8443"
oc_type = "tasks"
path = "/%s/" % oc_type
user = "admin"
password = "3lnNUktF6FzA"

json = oc_api(url + path, user, password)
extracted_oc_type_data = extract_oc_object_type(tasks_json, oc_type)

for entry in extracted_oc_type_data:
    print entry
