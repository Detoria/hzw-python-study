#!/usr/bin/python
#-*- coding:utf-8 -*-
import json
import os
import re
import sys
import socket
import commands



if os.geteuid() != 0 :
    print ("此脚本必须以root用户身份运行")
    sys.exit(-1)

psutil_or_not = commands.getoutput("rpm -qa |grep psutil")
if not psutil_or_not:
    result, info = commands.getstatusoutput("yum -y install python2-psutil")
    if result == 0:
        import psutil
    else:
        print('错误:psutil模块(python2-psutil)安装失败')
        sys.exit(-1)
else:
    import psutil

smartcl_or_not = commands.getoutput("rpm -qa |grep smartmontools")
if not smartcl_or_not:
    result, info = commands.getstatusoutput("yum -y install smartmontools")
    if result != 0:
        print('错误:smartmontools工具安装失败')
        sys.exit(-1)



class Machine():

    def __init__(self):

        self.data = {}
        self.data['hostname'] = socket.gethostname()

    def getCPUstatus(self):
        self.data['CpuStatus'] = {}
        CPU_Status = commands.getoutput("top -bn 1 -i -c |sed -n '3p' | awk -F [:] '{print $2}'")
        for i in CPU_Status.split(','):
            self.data['CpuStatus'][i.split()[1]] = i.split()[0]

        CpuUsedPer = commands.getoutput("top -bn 1 -i -c |sed -n '3p'|awk '{print $8}'")
        self.data['CpuStatus']['CpuUsedPer'] = str(100 - float(CpuUsedPer)) + '%'

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


    def getPdStatus(self):
        self.data['Pdisk'] = {}

        for i in range(0, 100):
            j = i + 1
            pdiskHealth = commands.getoutput("/sbin/smartctl -a -d megaraid,%s / |grep 'self-assessment\|SMART Health Status' |awk '{print $NF}'" %i)
            if pdiskHealth:
                self.data['Pdisk'][str(j)] = {}
                pdiskSize = commands.getoutput("/sbin/smartctl -a -d megaraid,%s / |grep -i 'User Capacity' |awk -F '[' '{print $2}'|awk -F ']' '{print $1}'" %i)
                pdiskWear = str(int(commands.getoutput("/sbin/smartctl -a -d megaraid,%s / |grep '245' |awk '{print $4}'" %i))) + '%'

                pdiskModel = commands.getoutput("/sbin/smartctl -a -d megaraid,%s /|grep 'Device Model\|Transport protocol'|awk '{print $NF}'|cut -b 1,2" %i)
                if pdiskModel == 'SS':
                    pdiskType = 'SSD'
                elif pdiskModel == 'SA':
                    pdiskType = 'SAS'
                elif pdiskModel == 'ST':
                    pdiskType = 'SATA'
                else:
                    pdiskType = 'SSD'

                self.data['Pdisk'][str(j)] = {'Size': pdiskSize, 'Wear': pdiskWear, 'Model': pdiskType}
            else:
                break


    def getNetworkStatus(self):
        nic = commands.getoutput(
            "/sbin/ip add show  | grep -E 'BROADCAST'|grep -v 'veth\|qg\|tap\|qv\|qb\|vir\|br\|docker\|em3\|em4\|ovs-system:\|vxlan_sys' |awk '{print $2$(NF-2)}'")
        niclist = nic.replace(':', ' ').split('\n')
        self.data['Nic'] = {}
        for i in niclist:
            b = i.split()
            self.data['Nic'][b[0]] = b[1]


        ip = commands.getoutput(
            "/sbin/ip add show  | grep  'inet'|grep 'global'|grep -v 'veth\|qg' |grep 'bond\|br'|grep -v 'virbr' |awk '{print $2}' |awk -F[/] '{print $1}'|tr '\n' ' '")
        iplist = ip.strip().split()
        self.data['Net'] = {}
        self.data['Net']['ip'] = iplist

        dns = commands.getoutput(
            "/bin/grep nameserver /etc/resolv.conf| grep -v '#' | awk '{print $2}'|sed -n '1p'")
        self.data['Net']['dns'] = dns

        gateway = commands.getoutput("/sbin/ip route | grep default | awk '{print $3}'")
        self.data['Net']['gateway'] = gateway

    def getOpenstackSystemStatus(self):
        self.data['OpenstackSystem'] = {}
        OpenstackServer = commands.getoutput(
            "ls -l /etc/systemd/system/multi-user.target.wants/ | egrep 'openstack|neutron' | awk '{print $9}' |grep -v 'ovs'")

        status, result = commands.getstatusoutput("ls -l  /etc/systemd/system/multi-user.target.wants/ |grep openstack")
        if status != 0:
            self.data['OpenstackSystem']["System"] = None
        else:
            httpstatus, httpresult = self.ServerCheck('http')
            if httpstatus == 'active':
                self.data['OpenstackSystem'][httpresult] = 'up'

            for i in OpenstackServer.split():
                ServerStatus, ServerResult = self.ServerCheck(i)
                if ServerStatus == 'active':
                    self.data['OpenstackSystem'][i] = 'up'
                else:
                    self.data['OpenstackSystem'][i] = 'down'

    def getOtherServerStatus(self):
        self.data['OtherServer'] = {}
        otherserver = ['redis.service', 'redis-sentinel.service', 'mariadb', 'rabbitmq', 'mongod', 'memcache', 'haproxy', 'keepalived']
        for i in otherserver:
            status, result = self.ServerCheck(i)
            if status == 'active':
                self.data['OtherServer'][result] = 'up'
            elif status == 1:
                self.data['OtherServer'][result] = 'None'
            else:
                self.data['OtherServer'][result] = 'down'

    def getOpenstackServerStatus(self):
        self.data['OpenstackServer'] = {}
        novaserver = commands.getoutput(
            "source /root/keystonerc_admin && nova service-list |grep nova |awk -F '\|' '{print $3\" \"$4\" \"$7}' 2>/dev/null")
        self.OpenStackServerTra(novaserver, 'novaserver')

        neutronserver = commands.getoutput(
            "source /root/keystonerc_admin && neutron agent-list |grep neutron |awk -F '\|' '{print $8\" \"$4\" \"$7}' 2>/dev/null")
        self.OpenStackServerTra(neutronserver, 'neutronserver')

        cinderserver = commands.getoutput(
            "source /root/keystonerc_admin && cinder service-list | grep cinder |awk -F '\|' '{print $2\" \"$3\" \"$6}' 2>/dev/null")
        self.OpenStackServerTra(cinderserver, 'cinderserver')

        user = commands.getoutput(
            "source /root/keystonerc_admin && keystone user-list 2>/dev/null |grep 'nova\|swift\|neutron\|aodh\|ceilometer\|glance\|gnocchi\|heat\|manila\|cinder\|designate' |awk -F '\|' '{print $3\" \"$4}' 2>/dev/null")
        self.OpenStackServerTra(user, 'user')

        tenant = commands.getoutput(
            "source /root/keystonerc_admin && keystone tenant-list 2>/dev/null|grep 'admin\|services' | awk -F '\|' '{print $3\" \"$4}' 2>/dev/null")
        self.OpenStackServerTra(tenant, 'tenant')

    def OpenStackServerTra(self, server, servername):
        serverstatus = server.split('\n')
        self.data['OpenstackServer'][servername] = {}
        num = 1
        for i in serverstatus:
            a = i.split(' ')
            m = [x for x in a if x != '']
            if len(m) == 3:
                self.data['OpenstackServer'][servername][num] = {}
                self.data['OpenstackServer'][servername][num][m[0]] = {}
                self.data['OpenstackServer'][servername][num][m[0]] = {'host': m[1], 'status': m[2]}
                num += 1

            else:
                self.data['OpenstackServer'][servername][m[0]] = m[1]


    def ServerCheck(self, server):
        serverstatus, serverresult = commands.getstatusoutput("ls -l /etc/systemd/system/multi-user.target.wants/ |grep -w %s |awk '{print $9}'" %server)
        if serverstatus == 0 and serverresult != '':
            status = commands.getoutput("systemctl status %s|grep Active |awk '{print $2}'" %serverresult)
            return status, serverresult
        else:
            return (1, server)

    def getCephClusterStatus(self):
        self.data['CephClusterStatus'] = {}
        self.data['CephClusterStatus']['ClusterHealth'] = {}
        CephClusterHealth = commands.getoutput("ceph -s 2>/dev/null|grep health|awk '{print $2}'|awk -F[_] '{print $2}'")
        CephErrorInfo = commands.getoutput("ceph -s 2>/dev/null |awk '/health/,/monmap/{print}'|grep -v 'health\|monmap'")
        self.data['CephClusterStatus']['ClusterHealth']['status'] = CephClusterHealth
        if CephErrorInfo:
            self.data['CephClusterStatus']['ClusterHealth']['error'] = CephErrorInfo

        self.data['CephClusterStatus']['CephClusterVolume'] = {}
        CephClusterVolume = commands.getoutput("ceph osd df 2>/dev/null|grep TOTAL |awk '{print $3\" \"$2\" \"$5\"%\"}'").split()
        self.data['CephClusterStatus']['CephClusterVolume'] = {'Use': CephClusterVolume[0], 'Size': CephClusterVolume[1], 'UsePer': CephClusterVolume[2]}

        self.data['CephClusterStatus']['CephOsdStatus'] = {}
        self.data['CephClusterStatus']['CephOsdStatus']['OsdStatus'] = {}
        self.data['CephClusterStatus']['CephOsdStatus']['VolumeStatus'] = {}
        self.data['CephClusterStatus']['CephOsdStatus']['OsdHealth'] = {}

        CephOsdStatus = commands.getoutput("ceph osd tree 2>/dev/null |grep 'osd\.' |awk '{print $3\" \"$4}'|sort |uniq").split('\n')
        for i in CephOsdStatus:
            osdstatus = i.split()
            self.data['CephClusterStatus']['CephOsdStatus']['OsdStatus'][osdstatus[0]] = osdstatus[1]

        CephVolumeStatus = commands.getoutput("ceph osd df 2>/dev/null|grep -v 'TOTAL\|MIN\|ID' |awk '{print \"osd.\"$1\" \"$4\" \"$5\" \"$7\"%\"}' |sort|uniq").split('\n')
        for j in CephVolumeStatus:
            volumestatus= j.split()
            self.data['CephClusterStatus']['CephOsdStatus']['VolumeStatus'][volumestatus[0]] = {'Size': volumestatus[1], 'Use': volumestatus[2], 'UsePer': volumestatus[3]}

        osdDict = self.data['CephClusterStatus']['CephOsdStatus']['OsdStatus']
        osdcheck = [k for k, v in osdDict.items() if v == 'down']
        if osdcheck:
            self.data['CephClusterStatus']['CephOsdStatus']['OsdHealth'] = {'status': 'Error', 'osd': osdcheck}
        else:
            self.data['CephClusterStatus']['CephOsdStatus']['OsdHealth'] = {'status': 'OK'}

        osdnum = commands.getoutput("ceph osd ls 2>/dev/null |wc -l")
        self.data['CephClusterStatus']['OsdNum'] = osdnum

        poolnum = commands.getoutput("ceph osd pool ls|wc -l")
        self.data['CephClusterStatus']['PoolNum'] = poolnum

        pgnum = commands.getoutput("ceph pg stat 2>/dev/null |awk '{print $2}'")
        self.data['CephClusterStatus']['PgNum'] = pgnum


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


    def get_info(self):

        self.getMemStatus()
        self.getCPUstatus()
        self.getDiskStatus()
        self.getPdStatus()
        self.getNetworkStatus()
        self.getOpenstackSystemStatus()
        if 'control' in self.data['hostname']:
            self.getOpenstackServerStatus()
        self.getOtherServerStatus()
        if os.path.exists('/etc/ceph/ceph.client.admin.keyring'):
            self.getCephClusterStatus()
        if os.path.exists('/apps/sh/resin'):
            self.getQiyunResinStatus()

        return json.dumps(self.data)

if __name__ == '__main__':

    machine = Machine()

    # machine.getOpenstackSystem()
    # print Machine().hostname
    print machine.get_info()
