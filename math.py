#!/usr/bin/python
#-*- coding:utf-8 -*-

import os
import sys
import socket
import commands

if os.geteuid() != 0 :
    print ("此脚本必须以root用户身份运行")
    sys.exit(-1)

class Machine():

    hostname = socket.gethostname()

    def __init__(self):

        self.data = {}
        self.data['hostname'] = self.__class__.hostname
        self.getMemStatus()
        self.getCPUstatus()
        self.getDiskStatus()
        self.getNetworkStatus()

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
        OpenstackServer = commands.getoutput("ls -l /etc/systemd/system/multi-user.target.wants/ | grep openstack | awk '{print $9}'")
        NeutronServer = commands.getoutput("ls -l /etc/systemd/system/multi-user.target.wants/ | grep neutron | awk '{print $9}' | grep -v 'ovs'")
        status, result = commands.getstatusoutput("ls -l  /etc/systemd/system/multi-user.target.wants/ |grep openstack")
        if status != 0:
            self.data['OpenstackServer']["Server"] = None
        else:
            for i in OpenstackServer, NeutronServer:
                ServerStatus = commands.getoutput("systemctl status %s|grep Active |awk '{print $2}'" %i)
                if ServerStatus == 'active':
                    print "OK"



machine = Machine()

machine.getOpenstackServerStatus()
# print machine.data

