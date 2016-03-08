'''
Documentation, License etc.

@package prepare_master_jenkins
'''
import json
import urllib2
import base64
from os.path import expanduser
from pprint import pprint

home = expanduser("~")

class PreemptiveBasicAuthHandler(urllib2.HTTPBasicAuthHandler):
    '''Preemptive basic auth.

    Instead of waiting for a 403 to then retry with the credentials,
    send the credentials if the url is handled by the password manager.
    Note: please use realm=None when calling add_password.'''
    def http_request(self, req):
        url = req.get_full_url()
        realm = None
        # this is very similar to the code from retry_http_basic_auth()
        # but returns a request object.
        user, pw = self.passwd.find_user_password(realm, url)
        if pw:
            raw = "%s:%s" % (user, pw)
            auth = 'Basic %s' % base64.b64encode(raw).strip()
            req.add_unredirected_header(self.auth_header, auth)
        return req

    https_request = http_request

with open(home + '/manager_auth.txt') as f:
  credentials = [x.strip().split(':') for x in f.readlines()]

for username,password in credentials:
    jenkins_url = "192.168.1.118:8081"
    username = username
    api_token = password

auth_handler = PreemptiveBasicAuthHandler()
auth_handler.add_password(
    realm=None, # default realm.
    uri=jenkins_url,
    user=username,
    passwd=api_token)
opener = urllib2.build_opener(auth_handler)
urllib2.install_opener(opener)
     
data_file = json.loads(open(home + 'tools/master_plugins.json').read())   

for x in data_file:
  all_plugins = (x['plugins'])
  for plugin in all_plugins:
    data = '<jenkins><install plugin="' + plugin + '@latest" /></jenkins>'
    url = 'https://build-sandbox.kde.org/pluginManager/installNecessaryPlugins'
    req = urllib2.Request(url, data, {'Content-Type': 'text/xml'})
    f = urllib2.urlopen(req)
    for y in f:
      pprint("Now installing " + plugin)
    f.close()