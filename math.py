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
        MemTotal = int(commands.getoutput("grep MemTotal /proc/meminfo | awk '{print $2}'"))
        MemFree = int(commands.getoutput("grep MemFree /proc/meminfo | awk '{print $2}'"))
        MemUsed = MemTotal - MemFree
        self.data['Mem'] = {}
        self.data['Mem']['Total'] = str(MemTotal / 1024) + 'MB'
        self.data['Mem']['Free'] = str(MemFree / 1024) + 'MB'
        self.data['Mem']['Used'] = str(MemUsed / 1024) + 'MB'
        self.data['Mem']['UsedPercent'] = str(MemUsed / 1024) + '%'
        #MemPercent =

machine = Machine()

print machine.data

