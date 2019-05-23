import sys  
import base64   
import json 
from main import report_build_status_github_func


class Context: 
    def __init__(self):    
        self.properties = {}

jsonfile = open('tstmsg.json', 'r')
msg = {}
msg['data'] = base64.b64encode(json.dumps(json.load(jsonfile)).encode('utf-8'))

context = Context()	

report_build_status_github_func(msg, context)
