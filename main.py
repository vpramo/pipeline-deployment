import json
import sys
import httplib
import requests
import time
import yaml

authtoken=sys.argv[1]
#Example  https://aasemble.com/
pkgbuilder_url=sys.argv[2]
search_tag=sys.argv[3]

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
            repo_list[name]["location"]=str(m["url"])
            repo_list[name]["release"]=str(" ".join(m["series"]))
            repo_list[name]["repos"]=str(" ".join(m["components"]))
            repo_list[name]["pin"]='1002'
            print yaml.dump(repo_list, default_flow_style=False)

output_yaml()




