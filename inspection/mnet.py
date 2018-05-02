#!/usr/bin/env python
# coding: utf-8
'''
网络流量巡检脚本，输出：
1，网络（公网）总出口当前峰值、近一天最大峰值、最小值、平均峰值.
2，各线路当前峰值、近一天最大峰值、最小值、平均峰值.
3，输出格式如下：（单位bit/s）

    {
        "all_bandwidth_subnet": [{
            "subnet": "163.177.19.96/27",
            "rate": {
                "peak_value_max": "473472",
                "peak_value_min": "1384",
                "peak_value_average": "8125",
                "current_in": "3976",
                "current_out": "4888"
            }
        }, {
            "subnet": "125.88.153.64/26",
            "rate": {
                "peak_value_max": "8653632",
                "peak_value_min": "6536",
                "peak_value_average": "191212",
                "current_in": "10936",
                "current_out": "37072"
            }
        }, {
            "subnet": "14.18.236.192/26",
            "rate": {
                "peak_value_max": "2264040",
                "peak_value_min": "32856",
                "peak_value_average": "172885",
                "current_in": "320648",
                "current_out": "334272"
            }
        }, {
            "subnet": "183.232.73.0/26",
            "rate": {
                "peak_value_max": "2008",
                "peak_value_min": "416",
                "peak_value_average": "519",
                "current_in": "480",
                "current_out": "0"
            }
        }, {
            "subnet": "43.254.131.192/26",
            "rate": {
                "peak_value_max": "0",
                "peak_value_min": "0",
                "peak_value_average": "0",
                "current_in": "0",
                "current_out": "0"
            }
        }, {
            "subnet": "14.152.70.128/27",
            "rate": {
                "peak_value_max": "520",
                "peak_value_min": "0",
                "peak_value_average": "21",
                "current_in": "0",
                "current_out": "0"
            }
        }],
        "all_bandwidth_qy": {
            "peak_value_max": "8695144",
            "peak_value_min": "46552",
            "peak_value_average": "369890",
            "current_in": "130680",
            "current_out": "166632"
        }
    }

'''

import datetime
import json
import urllib2
import re
import time
import os
import commands

# #测试环境
# zabbix_sdn_url = "http://100.64.0.58/zabbix/api_jsonrpc.php"
# zabbix_sdn_user = "Admin"
# zabbix_sdn_password = "zabbix"

#demo环境
zabbix_sdn_url = "http://10.10.20.10:1080/zabbix/api_jsonrpc.php"
zabbix_sdn_user = "Admin"
zabbix_sdn_password = "vipstack"

zabbix_sdn_header = {"Content-Type": "application/json-rpc"}
zabbix_sdn_host_name = "zbx-sdn.devops.vipstack.net"

log_path = ""
log_name = "network_inspection.log"

#麒云总带宽
ip = "0.0.0.0"

#麒云各公网线路
subnet_list = ["163.177.19.96/27","125.88.153.64/26","14.18.236.192/26","183.232.73.0/26","43.254.131.192/26","14.152.70.128/27"]

#定义日志
class SdnLog:
    '''定义日志格式'''
    def __init__(self):
        self.path = log_path
        self.log_name = log_name

    def write_log(self, alarm_level, log_source, msg):
        """记录日志"""
        # if not os.path.isdir('%s' % self.path):
        #     commands.getoutput('rm -rf %s && mkdir %s' % (self.path, self.path))
        logs = "%s %s %s %s\n" % (datetime.datetime.now().isoformat(), alarm_level, log_source, msg)
        with open("%s%s" % (self.path, self.log_name), 'a') as f:
            f.write(logs)

sdn_log = SdnLog()

#定义zabbix的类
class SdnZabbixRequest:
    """定义sdn与zabbix相关操作的类"""

    def __init__(self, sdn_zabbix_url, sdn_zabbix_header, Num=10):

        self.id = Num
        self.authID = self.user_login()
        self.zabbix_url = sdn_zabbix_url
        self.zabbix_header = sdn_zabbix_header
        self.path = log_path
        self.log_error_name = log_name
        self.interval = 300  # 监控的时间间隔，默认5分钟

    def user_login(self):
        """获取zabbix的登录认证token"""
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "user.login",
                "params": {
                    "user": zabbix_sdn_user,
                    "password": zabbix_sdn_password
                },
                "id": self.id,
            })
        try:
            request = urllib2.Request(zabbix_sdn_url, data, zabbix_sdn_header)
            result = urllib2.urlopen(request)
            response = json.loads(result.read())
            authID = response['result']
        except KeyError as e:
            # self.write_log("user_login", "Auth Failed, Please Check Your Name And Password.%s" % e)
            # return "Auth Failed, Please Check Your Name And Password."
            return -1
        except urllib2.URLError as e:
            # self.write_log("user_login", "connect to server failed.%s" % e)
            # return "connect to server failed."
            return -1
        else:
            return authID

    def get_data(self, data):
        """获取zabbix数据的函数,供下面函数调用"""
        request = urllib2.Request(self.zabbix_url, data, self.zabbix_header)
        result = urllib2.urlopen(request)
        return json.loads(result.read())

    def get_hostid(self, HostNames=zabbix_sdn_host_name):
        """根据主机名,获取hostid,默认主机名"Zabbix server",部署的时候需要修改"""

        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "host.get",
                "params": {
                    "output": [
                        "hostid"
                    ],
                    "filter": {
                        "host": HostNames
                    }
                },
                "id": self.id,
                "auth": self.authID
            })

        response = self.get_data(data)

        if response["result"] == []:
            return []
        else:
            response = response['result'][0]["hostid"]
            return response

    def get_itemid(self, key, hostid):
        """根据key值获取对应的itemid"""

        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "item.get",
                "params": {
                    "output": ["itemids", "key_"],
                    "filter": {
                        "key_": key
                    },
                    "hostids": hostid,
                },
                "id": self.id,
                "auth": self.authID
            })
        try:
            itemids = self.get_data(data)['result']
            return itemids[0]["itemid"]
        except Exception, e:
            # self.write_log("get_itemid", "get itemid failed.%s" % e)
            return -1

    def get_trend(self, itemid, time_from, time_till):
        """根据itemid获取一定时间范围内的趋势数据"""
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "trend.get",
                "params": {
                    "output": ["itemid", "clock", "value_avg"],
                    "itemids": itemid,
                    "time_from": time_from,
                    "time_till": time_till
                },
                "auth": self.authID,
                "id": self.id
            })
        try:
            history = self.get_data(data)['result']
            history_new = {}
            for h in history:
                clock = h["clock"]
                new_clock = int(clock) - int(clock) % self.interval
                value = h["value_avg"]
                history_new[new_clock] = value
            return history_new
        except Exception as e:
            # self.write_log("get_trend", "get trend failed.%s" % e)
            return {}

    def get_history(self, itemid, time_from, time_till):
        """根据itemid获取一定时间范围内的历史数据"""
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "history.get",
                "params": {
                    "output": "extend",
                    "history": 3,
                    "itemids": itemid,
                    "time_from": time_from,
                    "time_till": time_till
                },
                "id": self.id,
                "auth": self.authID
            })
        try:
            history = self.get_data(data)['result']
            history_new = {}
            for h in history:
                clock = h["clock"]
                new_clock = int(clock) - int(clock) % self.interval
                value = h["value"]
                history_new[new_clock] = value
            return history_new
        except Exception, e:
            # self.write_log("get_history", "get history failed.%s" % e)
            return {}

    def result_trend_bits(self, ip, time_from, time_till):
        """根据IP地址,获取一定时间范围内的趋势数据(单位bps,zabbix监控项存储值为一个小时内的最大值)"""
        try:
            key_in = "switch.get.ip.bits[in,%s]" % ip
            key_out = "switch.get.ip.bits[out,%s]" % ip
            hostid = self.get_hostid(zabbix_sdn_host_name)
            iteam_in = self.get_itemid(key_in, hostid)
            iteam_out = self.get_itemid(key_out, hostid)

            if iteam_in == -1:
                trend_in = {}
            if iteam_out == -1:
                trend_out = {}
            if iteam_in != -1 and iteam_out != -1:
                trend_in = self.get_trend(iteam_in, time_from, time_till)
                trend_out = self.get_trend(iteam_out, time_from, time_till)

            # 点数对齐
            in_keys = trend_in.keys()
            out_keys = trend_out.keys()

            for h in in_keys:
                if h not in out_keys:
                    trend_out[h] = "0"
            for h in out_keys:
                if h not in in_keys:
                    trend_in[h] = "0"

            result_trend = {}
            result_trend[ip] = {"in": trend_in, "out": trend_out}
            return result_trend
        except Exception as e:
            # self.write_log("result_trend_bits", e)
            return {}

    def result_history_bits(self, ip, time_from, time_till):
        """根据IP地址,获取一定时间范围内的历史数据(单位bps,zabbix监控项存储值为每秒差量)"""
        try:
            key_in = "switch.get.ip.bits[in,%s]" % ip
            key_out = "switch.get.ip.bits[out,%s]" % ip
            hostid = self.get_hostid(zabbix_sdn_host_name)
            iteam_in = self.get_itemid(key_in, hostid)
            iteam_out = self.get_itemid(key_out, hostid)

            if iteam_in == -1:
                history_in = {}
            if iteam_out == -1:
                history_out = {}
            if iteam_in != -1 and iteam_out != -1:
                history_in = self.get_history(iteam_in, time_from, time_till)
                history_out = self.get_history(iteam_out, time_from, time_till)

            # 点数对齐,缺少的补0
            in_keys = history_in.keys()
            out_keys = history_out.keys()

            for h in in_keys:
                if h not in out_keys:
                    history_out[h] = "0"
            for h in out_keys:
                if h not in in_keys:
                    history_in[h] = "0"

            result_history = {}
            result_history[ip] = {"in": history_in, "out": history_out}
            return result_history
        except Exception as e:
            # self.write_log("result_history_bits", e)
            return {}

    def peak_value(self, key, dict1, peak=True):
        """ 计算出峰值"""

        if dict1.has_key(key) and dict1[key] == {'out': {}, 'in': {}}:
            dict1[key]["peak_value_max"] = "-1"
            dict1[key]["peak_value_4"] = "-1"
            dict1[key]["peak_value_95"] = "-1"
            dict1[key]["peak_value_average"] = "-1"
            return dict1
        elif dict1.has_key(key):

            if peak:
                peak_list = []
                dict_in_keys = dict1[key]["in"].keys()
                dict_out_keys = dict1[key]["out"].keys()
                dict_in_keys.sort()
                dict_out_keys.sort()
                for k in dict_in_keys:
                    value_in = dict1[key]["in"][k]
                    value_out = dict1[key]["out"][k]
                    if int(value_in) > int(value_out):
                        peak_list.append(value_in)
                    else:
                        peak_list.append(value_out)
                peak_list = list(map(int, peak_list))
                peak_list.sort(reverse=True)
                peak_value_max = peak_list[0]
                peak_value_min = peak_list[-1]
                peak_value_average = sum(peak_list) / len(peak_list)
                dict1[key]["peak_value_max"] = "%s" % peak_value_max
                dict1[key]["peak_value_min"] = "%s" % peak_value_min
                dict1[key]["peak_value_average"] = "%s" % peak_value_average
                return dict1
            else:
                return dict1

sdn_zabbix = SdnZabbixRequest(zabbix_sdn_url, zabbix_sdn_header)

def zabbix_get_history_qy(ip):
    api_name = "zabbix_get_history_qy"
    try:
        time_till = int(time.time())
        time_from = time_till - 1 * 24 * 60 * 60

        #dict1 = sdn_zabbix.result_trend_bits(ip, time_from, time_till)
        dict1 = sdn_zabbix.result_history_bits(ip, time_from, time_till)

        dict1 = sdn_zabbix.peak_value(ip, dict1)

        #当前in方向的流量值
        time_in = dict1[ip]["in"].keys()
        time_in.sort()
        rate_in = dict1[ip]["in"][time_in[-1]]

        #当前out方向的流量值
        time_out = dict1[ip]["out"].keys()
        time_out.sort()
        rate_out = dict1[ip]["out"][time_out[-1]]


        dict1[ip]["current_in"] = rate_in
        dict1[ip]["current_out"] = rate_out

        # 删除历史数据
        del dict1[ip]["in"]
        del dict1[ip]["out"]

        return dict1[ip]

    except Exception,e:
        sdn_log.write_log("ERROR", api_name, "%s" % e)
        return json.dumps({"code": -1, "data": "%s" % e})

def zabbix_get_history_subnet_bandwidth(subnet_list):
    api_name = "zabbix_get_history_subnet_bandwidth"
    try:
        time_till = int(time.time())
        time_from = time_till - 1 * 24 * 60 * 60

        response = []
        for subnet in subnet_list:

            key_item_out = "switch.get.network.bits[%s,%s]" % ("out", subnet)
            key_item_in = "switch.get.network.bits[%s,%s]" % ("in", subnet)

            # 获取itemid
            hostid = sdn_zabbix.get_hostid(zabbix_sdn_host_name)
            itemid_in = sdn_zabbix.get_itemid(key_item_in, hostid)
            itemid_out = sdn_zabbix.get_itemid(key_item_out, hostid)

            if itemid_in == -1 and itemid_out == -1:
                #无监控项返回空
                response.append({"subnet":subnet,"rate":{}})
            elif itemid_in != -1 and itemid_out != -1:

                # result_history_in = sdn_zabbix.get_trend(itemid_in, time_from, time_till)
                # result_history_out = sdn_zabbix.get_trend(itemid_out, time_from, time_till)

                result_history_in = sdn_zabbix.get_history(itemid_in, time_from, time_till)
                result_history_out = sdn_zabbix.get_history(itemid_out, time_from, time_till)

                # 点数对齐
                in_keys = result_history_in.keys()
                out_keys = result_history_out.keys()

                for h in in_keys:
                    if h not in out_keys:
                        result_history_out[h] = "0"
                for h in out_keys:
                    if h not in in_keys:
                        result_history_in[h] = "0"


                # 处理数据,计算峰值
                peak_dict = {subnet: {"in": result_history_in, "out": result_history_out}}
                peak_dict = sdn_zabbix.peak_value(subnet, peak_dict)

                # 当前in方向的流量值
                time_in = peak_dict[subnet]["in"].keys()
                time_in.sort()
                rate_in = peak_dict[subnet]["in"][time_in[-1]]

                # 当前out方向的流量值
                time_out = peak_dict[subnet]["out"].keys()
                time_out.sort()
                rate_out = peak_dict[subnet]["out"][time_out[-1]]

                peak_dict[subnet]["current_in"] = rate_in
                peak_dict[subnet]["current_out"] = rate_out

                # 删除历史数据
                del peak_dict[subnet]["in"]
                del peak_dict[subnet]["out"]

                response.append({"subnet": subnet, "rate": peak_dict[subnet]})

        return response
    except Exception as e:
        sdn_log.write_log("ERROR", api_name, "%s" % e)
        return json.dumps({"code": -1, "data": "%s" % e})

try:
    all_bandwidth_qy = zabbix_get_history_qy(ip)
    all_bandwidth_subnet = zabbix_get_history_subnet_bandwidth(subnet_list)
    response = {"all_bandwidth_qy":all_bandwidth_qy,"all_bandwidth_subnet":all_bandwidth_subnet}
    # print json.dumps(response)
    print response
except Exception, e:
    sdn_log.write_log("ERROR", "网络巡检脚本", "%s" % e)
