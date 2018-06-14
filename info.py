#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import commands
import json
import datetime
import time
import requests

now = datetime.datetime.now() # 当前时间
nowStamp = int(time.mktime(now.timetuple())) # 当前时间的时间戳
sevenDayAgo = (datetime.datetime.now() - datetime.timedelta(days = 7)) # 7天前的时间
timeStamp = int(time.mktime(sevenDayAgo.timetuple())) # 7天前的时间戳


url = 'http://zbx-sdn.devops.vipstack.net:28107/api/switch/zabbix/get_ip_history_max'
headers = {'Content-type':'application/json'}
data = {"time_from": timeStamp, "time_till": nowStamp, "ip": ["0.0.0.0"]}
data = json.dumps(data)
res = requests.post(url, data=data, headers=headers)
Netresult = json.loads(res.text)




commands.getoutput("ansible gz-demo --private-key /root/.ssh/id_rsa_devops -t /opt/info-log \
                    -u devops -b --become-user=root -m script -a '/apps/sh/get_machine_info.py'")


datadir = '/opt/info-log'
filelist = os.listdir(datadir)

CephUsedPer = []
VmNum = []
ComputeNum = []
MemUsedPer = []
CpuUsedPer = []

infolist = ['CephUsedPer', 'VmNum', 'ComputeNum', 'MemUsedPer', 'CpuUsedPer'] 

def average(seq):
    return round(float(sum(seq)) / len(seq), 2)


for i in range(0, len(filelist)):
    path = os.path.join(datadir, filelist[i])
    if os.path.isfile(path):
        with open(path) as f:
            info = eval(json.loads(f.read())["stdout"].encode().strip())
     	if info.has_key('CephUsedPer'):
			CephUsedPer.append(info['CephUsedPer'])
     	if info.has_key('ComputeNum'):
		    ComputeNum.append(info['ComputeNum'])
        if 'compute' in info['hostname']:
            MemUsedPer.append(info['MemUsedPer'])
            VmNum.append(info['VmNum'])
            CpuUsedPer.append(info['CpuUsedPer'])


Ceph = str(CephUsedPer[0]) + '%'
VM = sum(VmNum)
Compute = ComputeNum[0]
Mem = str(average(MemUsedPer)) + '%'
Cpu = str(average(CpuUsedPer)) + '%'

print ("""
计算节点数量： %s
云主机数量： %s
计算节点的cpu/内存/存储(ceph)平均使用百分比：%s / %s / %s
机房进/出流量峰值：进：%s 出：%s
"""，%(Compute, VM, Cpu, Mem, Ceph, Netresult['data']['in'], Netresult['data']['out']))

def get_token(self):
    config_keystone_public_url = self.cloud_conf["CONFIG_KEYSTONE_PUBLIC_URL"]
    root_domain = self.cloud_conf["ROOT_DOMAIN"]
    config_keystone_public_url = config_keystone_public_url.replace("%{hiera('ROOT_DOMAIN')}", root_domain) + '/tokens'
    headers = {'Content-Type': 'application/json'}
    data = {"auth": {"tenantName": "services", "passwordCredentials": {"username": "gnocchi",
                                                                       "password": self.cloud_conf[
                                                                           "CONFIG_GNOCCHI_KS_PW"]}}}
    r = requests.post(config_keystone_public_url, headers=headers, data=json.dumps(data))
    reslt = json.loads(r.text)
    self.token = reslt["access"]["token"]["id"]


def gnocchi_init(self):
    self.get_token()
    url_delete_archive_policy = "http://gnocchi.qy.vipstack.net:8041/v1/archive_policy/high"
    headers = {'X-Auth-Token': self.token, 'Content-Type': 'application/json'}

    r = requests.delete(url_delete_archive_policy, headers=headers)
    print url_delete_archive_policy, "HTTP CODE: ", r.status_code

    url_create_archive_policy = "http://gnocchi.qy.vipstack.net:8041/v1/archive_policy"
    data = {"aggregation_methods": ["95pct", "mean"], "back_window": 0,
            "definition": [{"granularity": "0:00:15", "points": 1440, "timespan": "6:00:00"},
                           {"granularity": "0:01:00", "points": 1440, "timespan": "1 day, 0:00:00"},
                           {"granularity": "6:00:00", "points": 1460, "timespan": "365 days, 0:00:00"},
                           {"granularity": "0:07:00", "points": 1440, "timespan": "7 days, 0:00:00"},
                           {"granularity": "0:30:00", "points": 1440, "timespan": "30 days, 0:00:00"}], "name": "high"}
    r = requests.post(url_create_archive_policy, headers=headers, data=json.dumps(data))
    print url_create_archive_policy, "HTTP CODE: ", r.status_code