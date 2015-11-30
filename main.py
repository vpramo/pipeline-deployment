import json
import sys
import httplib
import requests
import time
import yaml
import gnupg
import re
from tempfile import NamedTemporaryFile

authtoken=sys.argv[1]
#Example  https://aasemble.com
pkgbuilder_url=sys.argv[2]
search_tag=sys.argv[3]

gpg=gnupg.GPG(gnupghome='/tmp/')

def make_requests(api_path):
    Headers2 = {'Authorization':'Token '+ authtoken}
    r = requests.get(api_path, headers=Headers2)
    values = json.loads(r.content)
    return values

def get_mirrors():
    api_path=pkgbuilder_url+'/api/v2/mirrors/'
    mirrors=make_requests(api_path)
    return mirrors["results"]

def get_mirror_sets():
    api_path=pkgbuilder_url+'/api/v2/mirror_sets/'
    mirror_sets=make_requests(api_path)
    return mirror_sets["results"]

def get_snapshots():
    api_path=pkgbuilder_url+'/api/v2/snapshots/'
    snapshots=make_requests(api_path)
    return snapshots["results"]

def get_keys(key_url):
    r = requests.get(key_url)
    if r.status_code == requests.codes.ok:
        f = NamedTemporaryFile()
        f.write(r.content)
        f.seek(0)
        key_val=gpg.scan_keys(f.name)
        f.close()
        keyid=key_val[0]["keyid"]
        return keyid
    else:
        return "no keys"

def get_repo_properties(repo_url,series):
    r = requests.get(repo_url +"/dists/"+series+"/Release")
    if r.status_code == requests.codes.ok:
        origin=re.search("Origin: (\w+)",r.content).group(1)
        label=re.search("Label: (\w+)",r.content).group(1)
        return [origin,label]
    else:
       raise "Invalid URL"

def output_yaml():
    snapshot_list=get_snapshots()
    required_snapshots=[]
    repo_list={}
    for snapshot in snapshot_list:
        tags=snapshot["tags"]
        for tag in tags:
            if tag == search_tag:
                required_snapshots.append(snapshot)
    for snapshot in required_snapshots:
        ms = make_requests(snapshot["mirrorset"])
        for mirror in ms["mirrors"]:
            m = make_requests(mirror)
            name = str(m["url"].replace("http://","").replace("/","_"))
            repo_list[name]={}
            repo_list[name]["location"]=str(snapshot['self']).replace("/api/v2","")+str(m["url"]).replace("http://","").replace("https://","")
            repo_list[name]["release"]=str(" ".join(m["series"]))
            repo_list[name]["repos"]=str(" ".join(m["components"]))
            repo_list[name]["pin"]={}
            for series in m["series"]:
                repo_prop=get_repo_properties(str(m["url"]),str(series))
                repo_list[name]["pin"][str(series)+repo_prop[1]]={}
                repo_list[name]["pin"][str(series)+repo_prop[1]]["originator"]=repo_prop[0]
                repo_list[name]["pin"][str(series)+repo_prop[1]]["label"]=repo_prop[1]
                repo_list[name]["pin"][str(series)+repo_prop[1]]["priority"]='1001'
            keyid=get_keys(str(m["url"])+'/repo.key')
            if keyid != "no keys":
                repo_list[name]["key"]={}
                repo_list[name]["key"]["id"]=keyid
                repo_list[name]["key"]["source"]=str(m["url"])+'/repo.key'

    print " " + str(yaml.dump(repo_list, default_flow_style=False)).rstrip("\n")

output_yaml()



