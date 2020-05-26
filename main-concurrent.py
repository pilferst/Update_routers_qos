"The script download an 'ip adresses data base' checks it and uploads it to routers"

import requests
import yaml
import time
import paramiko
import datetime
from concurrent.futures import ThreadPoolExecutor
from itertools import repeat
from typing import Dict
from typing import Any
from typing import List
from typing import Tuple


url_update = "https://endpoints.office.com/endpoints/worldwide?clientrequestid=1j5enre3-4533-374r-fnr4-b913446df9aw"
url_check = "https://endpoints.office.com/version?clientrequestid=11114411-2222-3333-4444-255555555555"
def check_database_version() -> Tuple[bool,str]:


    "Output is Tuple(bool, version)"
    new_version : int
    current_version : int

    global url_check

    try:
        answer=requests.get(url_check)
        if answer.status_code==200:
            new_version = int(answer.json()[0]["latest"])
            with open("version.yml","r") as file_read:
                current_version=yaml.safe_load(file_read)["version"]
            if new_version > current_version:
                with open("version.yml", "w") as file_write:
                    yaml.dump({"version" : new_version },file_write)
                return (True, str(new_version))
            else:
                return (False, str(new_version))
    except:
        return (False,"error")

def get_ip_url(numbers : List[int]) -> Tuple[bool,Tuple[str],Tuple[str]]:
    """Output is Tuple (Bool, List(IPs), List(Urls)"""
    global url_update

    result_list: List[Any]
    local_output_lict_ip : List[str]
    local_output_lict_url: List[str]

    local_output_lict_ip=[]
    local_output_lict_url=[]

    try:
        result = requests.get(url_update)
        if result.status_code==200:
            print("Done")
            for step in numbers:
                result_list=result.json()[step].get("ips")
                if result_list!=None:
                    for id in result_list:
                        if "::" not in id and "*" not in id and id not in local_output_lict_ip:
                            local_output_lict_ip.append(id)
                result_list = result.json()[step].get("urls")
                if result_list !=None:
                    for id in result_list:
                        if "*" == id[0]:
                            local_output_lict_url.append(".".join(id.split(".")[1:]))
                        else:
                            local_output_lict_url.append(id)
    except:
        return(False,tuple(),tuple())

    return(True,tuple(local_output_lict_ip),tuple(local_output_lict_url))



def download_database(office365_numbers : List [int],
                      onedrive_numbers : List [int],
                      teams_numbers : List [int]) -> Tuple[Tuple[Any],Tuple[Any],Tuple[Any]]:
    office365_ip_url_tuple : Tuple[bool,List[str],List[str]]
    onedrive_ip_url_tuple: Tuple[bool,List[str],List[str]]
    teams_ip_url_tuple: Tuple[bool,List[str],List[str]]

    office365_ip_url_tuple=get_ip_url(office365_numbers)
    onedrive_ip_url_tuple=get_ip_url(onedrive_numbers)
    teams_ip_url_tuple=get_ip_url(teams_numbers)

    return (office365_ip_url_tuple,onedrive_ip_url_tuple,teams_ip_url_tuple)

def get_credentials(file_name : str) -> Dict[str,str]:
    local_url : str
    local_dict : Dict[str,str]

    local_dict={}

    local_url = "/home/python/scripts/qos/" + file_name
    with open (local_url,"r") as file_read:
        for id in yaml.safe_load(file_read):
            local_dict.update(id)
    return local_dict

def get_routers(file_name : str) -> List[Tuple[str,str]]:
    local_url: str
    local_list: List[Tuple[str, str]]

    local_url = "/home/python/scripts/qos/" + file_name
    with open(file_name, "r") as f:
        local_list=list(yaml.safe_load(f).items())
    return local_list

def config_router(router : Tuple[str,str],
                  credentials : Dict[str,str],
                  ip_url : List[Tuple[Any]]):
    "ip_url list(Tuple(bool (name list), Tuple(IPs), Tuple(URLs))) "
    #command_office : str
    #command_onedrive : str
    #command_teams : str
    #command_remove_office : str
    #command_remove_onedrive : str
    #command_remove_teams : str
    #command_remove : str

    #command_remove_office='/ip firewall address-list remove [/ip firewall address-list find list="o365"]'
    #command_remove_onedrive='/ip firewall address-list remove [/ip firewall address-list find list="OneDrive"]'
    #command_remove_teams='/ip firewall address-list remove [/ip firewall address-list find list="Teams"]'


    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=router[1],port=credentials["port"], username=credentials["username"],password=credentials["password"],look_for_keys=False,allow_agent=False, timeout=10)
        #stdin, stdout, stderr = client.exec_command(command_remove_office)
        #stdin, stdout, stderr = client.exec_command(command_remove_onedrive)
        #stdin, stdout, stderr = client.exec_command(command_remove_teams)
        time.sleep(1)
        for id in ip_url:
            stdin, stdout, stderr = client.exec_command(f'/ip firewall address-list remove [/ip firewall address-list find list="{id[0]}"]')
            for id_1 in range(1,len(id)):
                for id_3 in id[id_1]:
                    command_office = f"/ip firewall address-list add address={id_3} list={id[0]}"
                    print(command_office)
                    stdin,stdout,stderr=client.exec_command(f"/ip firewall address-list add address={id_3} list={id[0]}")
                    time.sleep(0.3)
                    output = stdout.read().decode("utf-8")

        client.close()
    except:
        pass

def concurrent_config_router(routers : List[Tuple[Any]],
                             credentials : Dict[str,str],
                             ip_url : List[Tuple[Any]],
                             limit : int) -> None:
    with ThreadPoolExecutor(max_workers=limit) as executor:
        executor.map(config_router, routers, repeat(credentials), repeat(ip_url))
    return None

if __name__=="__main__":
    global_result : Tuple[List[str],List[str],List[str]]
    list_routers : List[Tuple[str,str]]
    dict_credentials = Tuple[Any]
    list_update : List[Any]
    limit_concurrent : int

    office365_numbers = [0, 1, 2, 3, 4, 5, 6, 7, ]
    onedrive_numbers = [21, 22, 23, 24, 25, 26, 27, 28]
    teams_numbers = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
    list_update=[]
    limit_concurrent=2

    check_result=check_database_version()
    if check_result[0]:
        with open("success.log","a") as f:
            f.write(f"new version is {check_result[1]}. Updating\n")
        global_result=download_database(office365_numbers,onedrive_numbers,teams_numbers)
        print("Global",global_result)
        dict_credentials=get_credentials("credentials.yml")
        list_routers=get_routers("routers.yml")
        if global_result[0][0] and not(global_result[0][1]==tuple()) and not(global_result[0][2]==tuple()):
            list_update.append(("o365",global_result[0][1],global_result[0][2]))
        if global_result[1][0] and not(global_result[1][1]==tuple()) and not(global_result[1][2]==tuple()):
            list_update.append(("OneDrive", global_result[0][1], global_result[0][2]))
        if global_result[2][0] and not(global_result[2][1]==tuple()) and not (global_result[2][2]==tuple()):
            list_update.append(("Teams", global_result[0][1], global_result[0][2]))

        print("list_update",list_update)
        if list_update:
            concurrent_config_router(list_routers,dict_credentials,list_update,limit_concurrent)
    else:
        with open("success.log","a") as f:
            f.write(f"new version is {check_result[1]}. It`s the same version\n")
