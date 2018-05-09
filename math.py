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
        for i in disklist:
            print i.split()

machine = Machine()

machine.getDiskStatus()
# print machine.data

