#!/usr/bin/python
#-*- coding:utf-8 -*-

import os
import re
import sys
import socket
import commands
import psutil

if os.geteuid() != 0 :
    print ("此脚本必须以root用户身份运行")
    sys.exit(-1)

class Machine():

    def __init__(self):

        self.data = {}
        self.data['hostname'] = socket.gethostname()

    def getCPUstatus(self):
        CPU_Use = commands.getoutput("top -bn 1 -i -c |sed -n '3p' |awk -F [:] '{print $2}' |sed 's/[[:space:]]//'|sed 's/[[:space:]]//'")
        self.data['CPU'] = CPU_Use

    def getMemStatus(self):
        MemTotal = commands.getoutput("grep MemTotal /proc/meminfo | awk '{print $2}'")
        MemFree = commands.getoutput("grep MemFree /proc/meminfo | awk '{print $2}'")
        MemUsed = int(MemTotal) - int(MemFree)
        self.data['Mem'] = {}
        self.data['Mem']['Total'] = str(int(MemTotal) / 1024) + 'MB'
        self.data['Mem']['Free'] = str(int(MemFree) / 1024) + 'MB'
        self.data['Mem']['Used'] = str(MemUsed / 1024) + 'MB'
        self.data['Mem']['UsedPercent'] = str(round(float(MemUsed) / float(MemTotal) * 100, 2)) + '%'

    def getDiskStatus(self):
        diskcmd = "df -hTP | sed '1d' | awk '$2!=\"tmpfs\"{print}'|awk '$2!=\"devtmpfs\"{print}'|awk '$7!=\"/boot\"{print}'"
        DiskStatus = commands.getoutput(diskcmd)
        disklist = DiskStatus.split('\n')
        self.data['Disk'] = {}
        for i in disklist:
            b = i.split()
            self.data['Disk'][b[0]] = {}
            self.data['Disk'][b[0]]['Size'] = b[2]
            self.data['Disk'][b[0]]['Used'] = b[3]
            self.data['Disk'][b[0]]['Avail'] = b[4]
            self.data['Disk'][b[0]]['Use%'] = b[5]
            self.data['Disk'][b[0]]['Mounted on'] = b[6]

    def getNetworkStatus(self):
        nic = commands.getoutput("/sbin/ip add show  | grep -E 'BROADCAST'|grep -v 'veth\|qg\|tap\|qv\|qb\|vir\|br\|docker\|em3\|em4\|ovs-system:\|vxlan_sys' |awk '{print $2$(NF-2)}'")
        niclist = nic.replace(':', ' ').split('\n')
        self.data['Nic'] = {}
        for i in niclist:
            b = i.split()
            self.data['Nic'][b[0]] = b[1]

    def getOpenstackServerStatus(self):
        self.data['OpenstackServer'] = {}
        OpenstackServer = commands.getoutput("ls -l /etc/systemd/system/multi-user.target.wants/ | egrep 'openstack|neutron' | awk '{print $9}' |grep -v 'ovs'")
        status, result = commands.getstatusoutput("ls -l  /etc/systemd/system/multi-user.target.wants/ |grep openstack")
        if status != 0:
            self.data['OpenstackServer']["Server"] = None
        else:
            httpstatus, httpresult = self.ServerCheck('http')
            if httpstatus == 'active':
                self.data['OpenstackServer'][httpresult] = 'up'

            for i in OpenstackServer.split():
                ServerStatus, ServerResult = self.ServerCheck(i)
                if ServerStatus == 'active':
                    self.data['OpenstackServer'][i] = 'up'
                else:
                    self.data['OpenstackServer'][i] = 'down'

    def getOtherServerStatus(self):
        self.data['OtherServer'] = {}
        otherserver = ['redis.service','redis-sentinel.service', 'mariadb', 'rabbitmq', 'mongod', 'memcache', 'haproxy', 'keepalived']
        for i in otherserver:
            status, result = self.ServerCheck(i)
            if status == 'active':
                self.data['OtherServer'][result] = 'up'
            elif status == 1:
                self.data['OtherServer'][result] = 'None'
            else:
                self.data['OtherServer'][result] = 'down'

    def getOpenstackSystem(self):
        novaserver = commands.getoutput("source /root/keystonerc_admin && nova service-list |grep nova |awk -F '\|' '{print $3\" \"$4\" \"$6\" \"$7}' 2>/dev/null")
        neutronserver = commands.getoutput("source /root/keystonerc_admin && neutron agent-list |grep gd1 |awk -F '\|' '{print $4\" \"$6\" \"$7\" \"$8}' 2>/dev/null")
        cinderserver = commands.getoutput("source /root/keystonerc_admin && cinder service-list | grep gd1 |awk -F '\|' '{print $2\" \"$3\" \"$5\" \"$6}' 2>/dev/null")
        user = commands.getoutput("source /root/keystonerc_admin && keystone user-list 2>/dev/null |grep 'nova\|swift\|neutron\|aodh\|ceilometer\|glance\|gnocchi\|heat\|manila\|cinder\|designate' |awk -F '\|' '{print $3" "$4}' 2>/dev/null")
        tenant = commands.getoutput("source /root/keystonerc_admin && keystone tenant-list 2>/dev/null|grep 'admin\|services' | awk -F '\|' '{print $3" "$4}' 2>/dev/null")


    def ServerCheck(self, server):
        serverstatus, serverresult = commands.getstatusoutput("ls -l /etc/systemd/system/multi-user.target.wants/ |grep -w %s |awk '{print $9}'" %server)
        if serverstatus == 0 and serverresult != '':
            status = commands.getoutput("systemctl status %s|grep Active |awk '{print $2}'" %serverresult)
            return status, serverresult
        else:
            return (1, server)

    def getCephClusterStatus(self):
        pass

    def getQiyunResinStatus(self):
        self.data['Qiyun'] = {}
        resindict = {}
        self.data['Qiyun']['resin'] = {}
        resinfile = commands.getoutput('ls -lh /apps/sh/resin |grep resin')

        for i in resinfile.split('\n'):
                resininfo = re.findall('.*resin_(.*)_(.*).sh', i)
                if resininfo:
                    resindict[resininfo[0][0]] = resininfo[0][1]

        for key, value in resindict.items():
            if self.ProcessCheck(value):
                self.data['Qiyun']['resin'][key] = 'up'
            else:
                self.data['Qiyun']['resin'][key] = 'down'


    def ProcessCheck(self, port):
        serverPID = commands.getoutput("netstat -anlp |grep -w %s |grep LISTEN |awk '{print $7}'|awk -F '/' '{print $1}'" %port)
        try:
            p = psutil.Process(int(serverPID))
            return True
        except Exception as e:
            return False


    def get(self):

        # self.getMemStatus()
        # self.getCPUstatus()
        # self.getDiskStatus()
        # self.getNetworkStatus()
        # self.getOpenstackServerStatus()
        # self.getOtherServerStatus()
        # if os.path.exists('/etc/ceph/ceph.client.admin.keyring')
        #     self.getCephClusterStatus()
        if os.path.exists('/apps/sh/resin'):
            self.getQiyunResinStatus()

        return self.data

if __name__ == '__main__':

    machine = Machine()

    # machine.getOpenstackSystem()
    # print Machine().hostname
    print machine.get()
