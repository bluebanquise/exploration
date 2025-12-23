from pathlib import Path
from yaml import safe_load as yload , dump

BB_INVENTORY_NAME = "bluebanquise"
BB_INVENTORY_PATH = "bluebanquise" # str(Path.home()) + '/' + BB_INVENTORY_NAME
WORKDIR = BB_INVENTORY_PATH
BB_TMP_PATH = WORKDIR + "/.bbui"
BB_CLUSTER_DIR_NAME = "inventory/cluster"
BB_NODES_DIR_NAME = "nodes"
BB_GROUPS_DIR_NAME = "groups"

class Host():
    def __init__(self, hostname : str, v : dict[str,any] = {}):
        self.hostname = hostname
        self.vars = v
    
    def __str__(self) -> str:
        return dump(self.to_dict())

    def to_dict(self) -> dict:
        return self.vars 


class Group():
    def __init__(self, name : str, hosts : list = [], 
                 v : dict = {}, children : list = []):
        
        self.name = name
        self.hosts = hosts
        self.vars = v
        self.children = children

    def __str__(self) -> str:
        return dump(self.to_dict())

    def to_dict(self):
        return { 
                    'hosts' : self.hosts,
                    'group_vars' : self.vars,
                    'children' : self.children 
                }


class Inventory() : 
    
    def __init__(self, p = WORKDIR, crawl : bool = True) :
        self.hosts = {}
        self.groups = {}
        self.p = Path(p)
    
        if crawl:
            self.crawl_inventory()


    def crawl_inventory(self):
        p_inventory = self.p / BB_CLUSTER_DIR_NAME / BB_NODES_DIR_NAME
        print(p_inventory)
        for p in p_inventory.glob('*.y*ml'):
            print(p)
            with open(p) as f:
                inv = yload(f)
                for k, v in inv['all']['hosts'].items():
                    self.hosts[k] = Host(k, v)

        p_inventory = self.p / BB_CLUSTER_DIR_NAME / BB_GROUPS_DIR_NAME
        print(p_inventory)
        for p in p_inventory.glob('**/*'):
            groups = parse_ini(str(p))
            for k, v in groups.items():
                for h in v['hosts']:
                    if h not in self.hosts.keys():
                        self.hosts[h] = Host(h, {})
                self.groups[k] = Group(k, v['hosts'],v['groupvars'],v['children'])
        
    def __str__(self) -> str:
        return dump(self.to_dict())
    
    def to_dict(self) -> dict: 
        out = {}
        out['hosts'] = {}
        out['groups'] = {}

        for k, v in self.hosts.items():
            out['hosts'][k] = v.to_dict()
        
        for k, v in self.groups.items():
            out['groups'][k] = v.to_dict()
            
        return out

    def update_host(self, host, host_data, create_host = False) -> bool:
        """
        Input: a dict in format:
          {hostname: {}} with inside the {} host parameters.
          This function is smart, and only update what is necessary.
          If the function finds the hosts does not exists, it will return an error except if create_host is True.
        """

        host_empty = {
            "alias": None,
            "bmc": {
                "name": None,
                "ip4": None,
                "network": None,
                "mac": None
            },
            "network_interfaces": []
        }

        if not host in self.hosts:
            if create_host:
                self.hosts[host] = Host(host, host_empty)
            else:
                print("Error, host does not exist!")
                return False
        self.hosts[host].vars.update(host_data)

