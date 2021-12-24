"""
    专用于生成ping targets yaml 文件
"""

import math
import os
import yaml
import requests

curPath=os.path.dirname(os.path.realpath(__file__))

# 降list均分为N等分
def chunks(arr, m):
    arr = chunks_target_arr(arr)
    n = int(math.ceil(len(arr) / float(m)))
    return [arr[i:i + n] for i in range(0, len(arr), n)]

def chunks_target_arr(arr):
    result = []
    for t in arr:
        result.append(t["destination"])
    return result

def get_conf():
    yaml1=os.path.join(curPath,"config.yml")
    f1=open(yaml1,'r', encoding="utf-8") #打开yaml文件
    d1=yaml.load(f1, Loader=yaml.FullLoader) #使用load方法加载
    return d1

def get_num_chunks():
    d1 = get_conf()
    return int(d1["num_chunks"])

def get_num_chunks():
    d1 = get_conf()
    return int(d1["num_chunks"])

def get_targets():
    rest_prefix = get_conf()["cmdb_rest_prefix"]
    r = requests.get(rest_prefix+'v_pinger_config?count=99999&where pinger_name="'+get_conf()["pinger_name"]+'"')
    arr = r.json()

    if len(arr)>0:
        if arr[0][0]["refresh_flag"] == "0":
            pass ### NO NEED to refresh target files 
        else:
            return chunks(arr,get_num_chunks())
    else:
        return None


def create__yaml_file(file_path,arr):
    f=open(file_path,"w+",encoding="utf-8")
    arr_dict = {"targets":arr}
    yaml.dump(arr_dict,f)
    f.close

def target_files_generation():
    arrs = get_targets()
    if arrs:
        for i in range(get_num_chunks()):
            file_path=os.path.join(curPath,"targets_"+str(i)+".yml")
            create__yaml_file(file_path,arrs[i])
    else:
        ## 无监控目标，清空所有target files
        os.remove(curPath+"targets_*")
        

if __name__ == '__main__':
    target_files_generation()