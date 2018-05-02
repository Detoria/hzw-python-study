#!/bin/bash

[ $(id -u) -gt 0 ] && echo "请用root用户执行此脚本！" && exit 1
centosVersion=$(awk '{print $(NF-1)}' /etc/redhat-release)

#日志相关
PROGPATH=`echo $0 | sed -e 's,[\\/][^\\/][^\\/]*$,,'`
[ -f $PROGPATH ] && PROGPATH="."
LOGPATH="$PROGPATH/log"
[ -e $LOGPATH ] || mkdir $LOGPATH
RESULTFILE="$LOGPATH/HostDailyCheck-`hostname`-`date +%Y%m%d`.txt"

function getCpuStatus(){
    #echo ""
    #echo ""
    #echo -e "\033[31m############################ CPU检查 #############################\033[0m"
    Physical_CPUs=$(grep "physical id" /proc/cpuinfo| sort | uniq | wc -l)
    Virt_CPUs=$(grep "processor" /proc/cpuinfo | wc -l)
    CPU_Kernels=$(grep "cores" /proc/cpuinfo|uniq| awk -F ': ' '{print $2}')
    CPU_Type=$(grep "model name" /proc/cpuinfo | awk -F ': ' '{print $2}' | sort | uniq)
    CPU_Arch=$(uname -m)
    #CPU_Use=$(top -bn 1 -i -c |sed -n '3p')
    CPU_Use=$(top -bn 1 -i -c |sed -n '3p' |awk -F [:] '{print $2}' |sed 's/[[:space:]]//'|sed 's/[[:space:]]//')
    #echo "物理CPU个数:$Physical_CPUs  逻辑CPU个数:$Virt_CPUs 每CPU核心数:$CPU_Kernels CPU型号:$CPU_Type  CPU架构:$CPU_Arch"
    echo $CPU_Use 
}

function getMemStatus(){
    #echo ""
    #echo ""
    #echo -e "\033[31m############################ 内存检查 ############################\033[0m"
    #free -h
    MemTotal=$(grep MemTotal /proc/meminfo| awk '{print $2}')  #KB
    MemFree=$(grep MemFree /proc/meminfo| awk '{print $2}')    #KB
    let MemUsed=MemTotal-MemFree
    MemPercent=$(awk "BEGIN {if($MemTotal==0){printf 100}else{printf \"%.2f\",$MemUsed*100/$MemTotal}}")
    report_MemTotal="$((MemTotal/1024))""MB"        #内存总容量(MB)
    report_MemFree="$((MemFree/1024))""MB"          #内存剩余(MB)
    report_MemUsedPercent="$(awk "BEGIN {if($MemTotal==0){printf 100}else{printf \"%.2f\",$MemUsed*100/$MemTotal}}")"   #内存使用率%
    #echo "内存总容量(MB) $report_MemTotal 内存剩余(MB) $report_MemFree 内存使用率% $report_MemUsedPercent"
    echo "Total:$report_MemTotal Free:$report_MemFree UsedPer:$report_MemUsedPercent%"
    #MemCompare=$(echo  "$report_MemUsedPercent" > "70" | bc)
    
}

function getDiskStatus(){
    #echo ""
    #echo ""
    #echo -e "\033[31m############################ 磁盘检查 ############################\033[0m"
    #df -hiP | sed 's/Mounted on/Mounted/'> /tmp/inode
    #df -hTP | sed 's/Mounted on/Mounted/'> /tmp/disk 
    #join /tmp/disk /tmp/inode | awk '{print $1,$2,"|",$3,$4,$5,$6,"|",$8,$9,$10,$11,"|",$12}'| column -t
  # diskdata=$(df -TP | sed '1d' | awk '$2!="tmpfs"{print}') #KB
  # disktotal=$(echo "$diskdata" | awk '{total+=$3}END{print total}') #KB
  # diskused=$(echo "$diskdata" | awk '{total+=$4}END{print total}')  #KB
  # diskfree=$((disktotal-diskused)) #KB
  # diskusedpercent=$(echo $disktotal $diskused | awk '{if($1==0){printf 100}else{printf "%.2f",$2*100/$1}}') 
  # inodedata=$(df -iTP | sed '1d' | awk '$2!="tmpfs"{print}')
  # inodetotal=$(echo "$inodedata" | awk '{total+=$3}END{print total}')
  # inodeused=$(echo "$inodedata" | awk '{total+=$4}END{print total}')
  # inodefree=$((inodetotal-inodeused))
  # inodeusedpercent=$(echo $inodetotal $inodeused | awk '{if($1==0){printf 100}else{printf "%.2f",$2*100/$1}}')
  # report_DiskTotal=$((disktotal/1024/1024))"GB"   #硬盘总容量(GB)
  # report_DiskFree=$((diskfree/1024/1024))"GB"     #硬盘剩余(GB)
  # report_DiskUsedPercent="$diskusedpercent""%"    #硬盘使用率%
  # report_InodeTotal=$((inodetotal/1000))"K"       #Inode总量
  # report_InodeFree=$((inodefree/1000))"K"         #Inode剩余
  # report_InodeUsedPercent="$inodeusedpercent""%"  #Inode使用率%
    #echo "硬盘总容量(GB) $report_DiskTotal 硬盘剩余(GB) $report_DiskFree 硬盘使用率% $report_DiskUsedPercent"
    #df -hTP | sed '1d' | awk '$2!="tmpfs"{print}'|awk '$2!="devtmpfs"{print}'|awk '$7!="/boot"{print}'|awk '{print $1 " ["$4"/"$3"(Use:"$6")]"}'|tr '\n' ';'
    df -hTP | sed '1d' | awk '$2!="tmpfs"{print}'|awk '$2!="devtmpfs"{print}'|awk '$7!="/boot"{print}'|awk '{print $1 "["$4"/"$3"("$6")];"}'|tr '\n' '  '
}

function getSystemStatus(){
#    echo ""
#    echo ""
#    echo -e "\033[31m############################ 系统检查 ############################\033[0m"
    if [ -e /etc/sysconfig/i18n ];then
        default_LANG="$(grep "LANG=" /etc/sysconfig/i18n | grep -v "^#" | awk -F '"' '{print $2}')"
    else
        default_LANG=$LANG
    fi
    export LANG="en_US.UTF-8"
    Release=$(cat /etc/redhat-release 2>/dev/null)
    Kernel=$(uname -r)
    OS=$(uname -o)
    Hostname=$(uname -n)
    SELinux=$(/usr/sbin/sestatus | grep "SELinux status: " | awk '{print $3}')
    LastReboot=$(who -b | awk '{print $3,$4}')
    uptime=$(uptime | sed 's/.*up \([^,]*\), .*/\1/')
#   echo "     系统：$OS"
#   echo " 发行版本：$Release"
#   echo "     内核：$Kernel"
    echo $Hostname
#   echo "  SELinux：$SELinux"
#   echo "语言/编码：$default_LANG"
#   echo " 当前时间：$(date +'%F %T')"
#   echo " 最后启动：$LastReboot"
#   echo " 运行时间：$uptime"
}

function getServiceStatus(){
    echo ""
    echo ""
    echo -e "\033[31m############################ 服务检查 ############################\033[0m"
    echo ""
    if [[ $centosVersion > 7 ]];then
        conf=$(systemctl list-unit-files --type=service --state=enabled --no-pager | grep "enabled")
        process=$(systemctl list-units --type=service --state=running --no-pager |grep '.service')
    else
        conf=$(/sbin/chkconfig | grep -E ":on|:启用")
        process=$(/sbin/service --status-all 2>/dev/null | grep -E "is running|正在运行")
    fi
    echo "服务配置"
    echo "--------"
    echo "$conf"  | column -t
    echo ""
    echo "正在运行的服务"
    echo "--------------"
    echo "$process"

}

function getAutoStartStatus(){
    echo ""
    echo ""
    echo -e "\033[31m############################ 自启动检查 ##########################\033[0m"
    conf=$(grep -v "^#" /etc/rc.d/rc.local| sed '/^$/d')
    echo "$conf"
}



function getNetworkStatus(){
   # echo ""
   # echo ""
   # echo -e "\033[31m############################ 网络检查 ############################\033[0m"
    #for i in $(ip link | grep BROADCAST |grep -v 'qbr\|tap\|qvo\|ve\|ovs\|vx'| awk -F: '{print $2}');
    #do
    #ip add show  | grep -E "BROADCAST|global"|grep -v 'veth'|awk '{print $2}' | tr '\n' ' '
    echo ''
    /sbin/ip add show  | grep  "inet"|grep "global"|grep -v 'veth\|qg' |grep -v '192.168.122.1'|awk '{print $2}' |awk -F[/] '{print $1}'|tr '\n' ' '
    #done
    GATEWAY=$(/sbin/ip route | grep default | awk '{print $3}')
#    DNS=$(grep nameserver /etc/resolv.conf| grep -v "#" | awk '{print $2}' | tr '\n' ',' | sed 's/,$//')
    DNS=$(grep nameserver /etc/resolv.conf| grep -v "#" | awk '{print $2}'|sed -n '1p')
    echo "网关：$GATEWAY DNS：$DNS"
    #/sbin/ip add show  | grep -E "BROADCAST"|grep -v 'veth\|qg\|tap\|qv\|qb\|vir\|ovs-\|br\|docker' |awk '{print $2"  "$(NF-2)" "}' |tr '\n' ' '
    /sbin/ip add show  | grep -E "BROADCAST"|grep -v 'veth\|qg\|tap\|qv\|qb\|vir\|br\|docker\|em3\|em4\|ovs-system:\|vxlan_sys' |awk '{print $2"  "$(NF-2)" "}' |tr '\n' ' '
    echo ""
}

function getListenStatus(){
    echo ""
    echo ""
    echo -e "\033[31m############################ 监听检查 ############################\033[0m"
    TCPListen=$(netstat -nlutp)
    echo "$TCPListen"
}

function getCronStatus(){
    echo ""
    echo ""
    echo -e "\033[31m############################ 计划任务检查 ########################\033[0m"
    if [ -s /var/spool/cron/root ];then	
        cat /var/spool/cron/root
    else 
	echo -e "\n无计划任务"
    fi
}

function getProcessStatus(){
    echo ""
    echo ""
    echo -e "\033[31m############################ 进程检查 ############################\033[0m"
    if [ $(ps -ef | grep defunct | grep -v grep | wc -l) -ge 1 ];then
        echo ""
        echo "僵尸进程";
        echo "--------"
        ps -ef | head -n1
        ps -ef | grep defunct | grep -v grep
    fi
    echo ""
    echo "内存占用TOP10"
    echo "-------------"
    echo -e "PID %MEM RSS COMMAND
    $(ps aux | awk '{print $2, $4, $6, $11}' | sort -k3rn | head -n 10 )"| column -t 
    echo ""
    echo "CPU占用TOP10"
    echo "------------"
    top b -n1 | head -17 | tail -11
}

function getJDKStatus(){
    echo ""
    echo ""
    echo -e "\033[31m############################ JDK检查 #############################\033[0m"
    java -version 2>/dev/null
    if [ $? -eq 0 ];then
        java -version 2>&1
    fi
    echo "JAVA_HOME=\"$JAVA_HOME\""
}

function getFirewallStatus(){
    echo ""
    echo ""
    echo -e "\033[31m############################ 防火墙检查 ##########################\033[0m"
    for i in 'firewalld.service' 'iptables.service';
    do
    	s=$(systemctl status $i |grep Active |awk '{print $2" "$3}')
    echo -e "$i\t状态: $s\n"
    done
#    echo "/etc/sysconfig/iptables"
#    echo "-----------------------"
#    cat /etc/sysconfig/iptables 2>/dev/null
}

AuthFile='/root/keystonerc_admin'
function getOpenstackServerStatus() {
    #echo -e "\033[31m#######/##################### openstack服务检查 #############################\033[0m \n"
    OpenstackServer=$(ls -l  /etc/systemd/system/multi-user.target.wants/ |grep openstack |awk '{print $9}')
    NeutronServer=$(ls -l /etc/systemd/system/multi-user.target.wants/ |grep neutron|awk '{print $9}'|grep -v 'ovs')
    OpenstackOrNot=$(ls -l  /etc/systemd/system/multi-user.target.wants/ |grep openstack)
    if [ $? -eq 0 ];then
       for i in $OpenstackServer $NeutronServer;
       do
           Status=$(systemctl status $i|grep Active |awk '{print $2}')
           if [ "$Status" == "active" ];then
                echo -e "$i OK" >> /opt/OpenstackAllserver.log
           else
                echo -e "$i  $Status" >> /opt/OpenstackAllserver.log
           fi
       done
       OpenstackAllStatus=$(grep -v "OK" /opt/OpenstackAllserver.log)
       if [ $? -eq 0 ];then
           echo -e "Openstack服务"
           echo "Error"
	   echo  "$OpenstackAllStatus"
           echo "Openstack服务end"
       else
           echo "Openstack服务"
	   echo "OK"
       fi
       rm -rf /opt/OpenstackAllserver.log 
    fi
 
    HttpServer=$(ls -l  /etc/systemd/system/multi-user.target.wants/ |grep http)
    if [ $? -eq 0 ];then
       HttpStatus=$(systemctl status httpd|grep Active |awk '{print $2}') 
        if [ "$HttpStatus" == "active" ];then
            echo -e "Http服务"
            echo "OK" 
            
            if [ -f $AuthFile ];then
               source $AuthFile
               #echo -e "\033[31m############################ 云环境nova服务状态 #############################\033[0m"
               nova service-list 2>/dev/null|grep down >> /opt/nova.log
               if [ $? -eq 0 ];then
                   #NovaError=$(cat /opt/nova.log|awk -F[\|] '{print"服务 "$3"   ""主机名 "$4"   ""Zone "$5"   ""Status "$6"   ""State "$7}')
                   NovaError=$(cat /opt/nova.log|awk -F[\|] '{print $3"   "$4"   "$6"   "$7}')
                   echo  "Nova服务"
		   echo  "Error"
		   echo  "$NovaError"
               else
                   echo "Nova服务"
		   echo "OK"
               fi
               rm -rf /opt/nova.log
         
              # echo -e "\033[31m############################ 云环境neutron服务状态 #############################\033[0m"
               neutron agent-list 2>/dev/null|grep down >> /opt/neutron.log
               if [ $? -eq 0 ];then
                   NeutronError=$(cat /opt/neutron.log|awk -F[\|] '{print $3"   "$4"   ""alive "$6"   ""admin_state_up "$7"binary "$8}')
                   echo "Neutron服务"
		   echo "Error"
		   echo  "$NeutronError"
               else
                   echo "Neutron服务"
		   echo "OK"
               fi
               rm -rf /opt/neutron.log
         
              # echo -e "\033[31m############################ 云环境cinder服务状态 #############################\033[0m"
               cinder service-list 2>/dev/null |grep down >> /opt/cinder.log
               if [ $? -eq 0 ];then
                   CinderError=$(cat /opt/cinder.log|awk -F[\|] '{print $2"   "$3"   ""Zone "$4"   ""Status "$5"   ""State "$6}')
                   echo "Cinder服务"
		   echo "Error"
		   echo "$CinderError"
               else
                   echo "Cinder服务"
		   echo "OK"
               fi
               rm -rf /opt/cinder.log
         
               #echo -e "\033[31m############################ OpenStack系统用户状态#############################\033[0m"
               keystone user-list 2>/dev/null |grep 'nova\|swift\|neutron\|aodh\|ceilometer\|glance\|gnocchi\|heat\|manila\|cinder' |grep False >> /opt/keystone-user.log
               if [ $? -eq 0 ];then
               	#  ErrorUser=$(cat /opt/keystone-user.log|awk -F[\|] '{print"用户名:"$3"   ""enable："$4}')
                   echo -e "Openstack系统用户"
		   echo "Error"
                   cat /opt/keystone-user.log|awk -F[\|] '{print"Username "$3"   ""enable "$4}'
               else
                   echo "Openstack系统用户"
		   echo "OK"
               fi
               rm -rf /opt/keystone-user.log
               
              # echo -e "\033[31m############################ OpenStack系统租户状态#############################\033[0m"
               keystone tenant-list 2>/dev/null|grep False >> /opt/keystone-tenant.log
               if [ $? -eq 0 ];then
                  # ErrorTenant=$(cat /opt/keystone-tenant.log|awk -F[\|] '{print"租户名:""             "$3"   ""enable："$4}')
                   echo -e "Openstack系统租户"
		   echo "Error"
                   cat /opt/keystone-tenant.log|awk -F[\|] '{print"TenantName ""             "$3"   ""enable "$4}'
               else
                   echo "Openstack系统租户"
		   echo "OK"
               fi
               echo "Openstack系统租户end"
               rm -rf /opt/keystone-tenant.log
            fi
        else
            echo "Httpd服务"
	        echo "$HttpStatus"
	        echo "控制节点httpd服务异常，无法进行Openstack各服务检查"
        fi
    fi
}

function getOtherServerStatus {

    OtherServer="redis mariadb rabbitmq mongod memcache haproxy keepalive"
    for o in $OtherServer;
    do  
        ls -l  /etc/systemd/system/multi-user.target.wants |grep $o >> /opt/Oservice.log
        if [ $? -eq 0 ];then
           Oservice=$(cat /opt/Oservice.log |awk '{print $9}')
	   for t in $Oservice;
	   do
               Ostatus=$(systemctl status $t|grep Active |awk '{print $2}')
               if [ "$Ostatus" == "active" ];then
                    echo "$t" #>> /opt/OtherServer.log
                    echo "OK" #>> /opt/OtherServer.log
               else
                    echo "$t" #>> /opt/OtherServer.log
                    echo "$OStatus" #>> /opt/OtherServer.log
               fi
           done
           rm -rf /opt/Oservice.log 
        fi
    done
#    if [ -f /opt/OtherServer.log ];then
#       OtherStatus=$(grep "OK" /opt/OtherServer.log)
#       OtherErrorStatus=$(grep -v "OK" /opt/OtherServer.log)
#       if [ $? -eq 0 ];then
#          echo "其他服务"
#          echo "Error"
#          echo $OtherErrorStatus
#          echo $OtherStatus
#      else
#          cat /opt/OtherServer.log
#      fi
#      rm -rf /opt/OtherServer.log
#   fi
}

function getCephClusterStatus { 
    if [ -f /etc/ceph/ceph.client.admin.keyring ];then
       #echo -e "\033[31m############################   ceph集群状态   #############################\033[0m"
       CephStatus=$(ceph -s 2>/dev/null|grep health|awk '{print $2}'|awk -F[_] '{print $2}')
       CephError=$(ceph -s 2>/dev/null |awk '/health/,/monmap/{print}'|grep -v "health\|monmap")
       if [ "$CephStatus" == "OK" ];then
           echo "Ceph健康状态"
	   echo "OK"
       else
	   echo "Ceph健康状态"
 	   echo "Error"
	   echo "$CephError"
       fi
 
       #CephClusterVolume=$(ceph osd df 2>/dev/null|grep TOTAL |awk '{print"SIZE:"$2"   ""USE:"$3"   ""AVAIL:"$4"   ""%USE:"$5}')
       CephClusterVolume=$(ceph osd df 2>/dev/null|grep TOTAL |awk '{print "["$3"/"$2":"" "$5"%""]"}')
       CephClusterUsePer=$(ceph osd df 2>/dev/null|grep TOTAL |awk '{print $5}')
       CephVolumeFullPer='80' ## ceph集群容量使用百分比阀值 
       ClusterCompare=$(echo  "$CephClusterUsePer > $CephVolumeFullPer" | bc) ##将当前的使用率与集群容量使用率阀值进行比较
       if [ $ClusterCompare -eq 1 ];then
	   echo -e "Ceph集群容量状态"
	   echo "Error"
           echo "$CephClusterVolume > $CephVolumeFullPer%" 
       else
	   echo  "Ceph集群容量状态"
           echo  "OK" 
           echo "$CephClusterVolume < $CephVolumeFullPer%"
       fi
   
       ceph osd tree 2>/dev/null |grep down >> /opt/osd-status.log
       if [ $? -eq 0 ];then
           DownOSD=$(cat /opt/osd-status.log  |awk '{print $3"   "$4}')
           echo "OSD服务状态"
           echo "Error"
	   echo "$DownOSD"
           rm -rf /opt/osd-status.log
       else
           echo "OSD服务状态"
           echo "OK"
       fi
         
       CephOSDVolume=$(ceph osd df 2>/dev/null |awk '/ID/,/TOTAL/{print}'|grep -v "ID\|TOTAL" |awk '{print"osd."$1"   ""SIZE:"$4"   ""USE:"$5"   ""AVAIL:"$6"   ""%USE:"$7"%"}')
       CephOSDUsePer=$(ceph osd df 2>/dev/null |awk '/ID/,/TOTAL/{print}'|grep -v "ID\|TOTAL"|awk '{print $7}'|uniq)
       CephOSDFullPer='80' ## ceph单个OSD容量使用百分比阀值
       for s in $CephOSDUsePer;
       do
	    OSDCompare=$(echo  "$s > $CephOSDFullPer" | bc) ##将当前每个OSD使用率与OSD容量使用率阀值进行比较
            if [ $OSDCompare -eq 1 ];then
	       #CephWarnOSD=$(ceph osd df 2>/dev/null |awk '/ID/,/TOTAL/{print}'|grep -v "ID\|TOTAL"|grep $s|awk '{print"osd."$1"   ""SIZE:"$4"   ""USE:"$5"   ""AVAIL:"$6"   ""%USE:"$7"%"}')
            CephWarnOSD=$(ceph osd df 2>/dev/null |awk '/ID/,/TOTAL/{print}'|grep -v "ID\|TOTAL"|grep $s|awk '{print"  osd."$1"("$5"/"$4":"$7"%"")"}')
                for i in $CephWarnOSD;
                do
                    echo "$CephWarnOSD > $CephOSDFullPer% " >> /opt/osd.log
                done
            else
                CephOKOSD=$(ceph osd df 2>/dev/null |awk '/ID/,/TOTAL/{print}'|grep -v "ID\|TOTAL"|grep $s|awk '{print"  osd."$1"("$5"/"$4":"$7"%"")"}')
                for i in $CephOKOSD;
                do
                    echo "$i < $CephOSDFullPer% " >> /opt/osd-ok.log
                done
            fi
       done

       if [ -f /opt/osd.log ];then
            OSDWarnStatus=$(cat /opt/osd.log)
	        echo -e "OSD容量状态"
            echo "Error"
	        #echo $OSDWarnStatus
            cat /opt/osd.log
            rm -rf /opt/osd.log
       else
            echo "OSD容量状态"
            #echo "OK"
            cat /opt/osd-ok.log
            rm -rf /opt/osd-ok.log
       
       fi
            echo "OSD容量状态end"
          
       CephOSDNum=$(ceph osd ls 2>/dev/null |wc -l)
       echo "OSD数量"
       echo $CephOSDNum

       CephPoolNum=$(ceph osd pool ls|wc -l)
       echo "Pool数量"
       echo $CephPoolNum
    
       CephPgNum=$(ceph pg stat 2>/dev/null |awk '{print $2}')
       echo "PG数量"
       echo $CephPgNum
    fi
}

ResinSh="/apps/sh/resin/"
function getQiyunResinStatus(){
    if [ -d $ResinSh ];then
     #   echo -e "\033[31m############################ 麒云平台服务检查 #############################\033[0m"
        ############################# 麒云 Resin 模块状态 #############################
        ResinPort=$(ls -l $ResinSh |grep resin |awk '{print $9}'|awk -F[_] '{print $4}'|awk -F[.] '{print $1}')
        ResinName=$(ls -l $ResinSh |grep resin |awk '{print $9}'|awk -F[.] '{print $1}'|awk -F[_] '{print $2"_"$3"_"$4}')
        for i in $ResinPort;
        do
            ResinPID=$(netstat -nltp|grep "$i" |awk '{print $7}'|awk -F[/] '{print $1}')
            if [ -n "$ResinPID" ];then
                    for j in $ResinName;
                    do
                            k=$(echo $j |awk -F[_] '{print $3}')
                            if [ $i = $k ];then
                                    ps -aux |grep -w "$ResinPID"|grep $j >> /dev/null 2>&1
                                    if [ $? -eq 0 ];then
                                            echo  "OK" >> /opt/resin.log
                                    else
                                          #  echo -e "resin模块\t$j:\033[31m \t\t错误 \033[0m \n"  >> /opt/resin.log
                                            echo -e "$j:Down"  >> /opt/resin.log
                                    fi
                            fi
                    done
            else
                 Name=$(ls -l /apps/sh/resin/ |grep $i |awk '{print $9}'|awk -F[.] '{print $1}'|awk -F[_] '{print $2"_"$3"_"$4}')
                 #echo -e "resin模块\t$Name：\033[31m \t\t错误 \033[0m \n"   >> /opt/resin.log
	         echo -e "$Name:Down"  >> /opt/resin.log
		 
            fi
        done
        
        ResinError=$(cat /opt/resin.log|grep Down)
        if [ $? -eq 0 ];then
             echo "麒云模块"
             echo "Error"
             cat /opt/resin.log|grep Down |column -t
        else
             echo "麒云模块"
	     echo "OK"
        fi
        rm -rf /opt/resin.log

    fi
}

############################## 麒云 Nginx 状态 #############################
function getQiyunNginxStatus(){
#	NginxPID=$(netstat -nltp |grep "80" |grep -i "nginx"|awk '{print $7}'|awk -F[/] '{print $1}')
#	ps -ef | grep "$NginxPID" |grep nginx >> /dev/null 2>&1
	netstat -nltp |grep "80"|grep nginx >> /dev/null 2>&1
	if [ $? -eq 0 ];then
		echo -e "Nginx"
		echo "OK"
	else
		echo -e "Nginx"
		echo "Error"
        fi
}

############################## 麒云 Mysql 状态 #############################
function getQiyunMysqlStatus(){
     #  MysqlPID=$(netstat -nltp |grep "3306" |awk '{print $7}'|awk -F[/] '{print $1}')	
#	ps -ef |grep "$MysqlPID" |grep mysql >> /dev/null 2>&1
	netstat -nltp |grep "3306"|grep mysqld >> /dev/null 2>&1
	if [ $? -eq 0 ];then
                echo -e "Mysql"
		echo "OK"
        else
                echo -e "Mysql"
		echo "Error"
        fi
}

############################## 麒云 redis 状态 #############################
function getQiyunRedisStatus(){
     #  RedisPID=$(netstat -nltp |grep "6363" |awk '{print $7}'|awk -F[/] '{print $1}')	
#	ps -ef |grep "$RedisPID" |grep redis >> /dev/null 2>&1
	netstat -nltp |grep "6363"|grep redis >> /dev/null 2>&1
	if [ $? -eq 0 ];then
                echo -e "Redis"
		echo "OK"
        else
                echo -e "Redis"
		echo "Error"
        fi
}

############################## 麒云 qy_agent 状态 #############################
function getQiyunQyAgentStatus(){
	#QyAgentPID=$(netstat -nltp |grep "10086" |awk '{print $7}'|awk -F[/] '{print $1}')	
#	ps -ef |grep "$QyAgentPID" |grep qy_agent >> /dev/null 2>&1
	netstat -nltp |grep "10086" >> /dev/null 2>&1
        if [ $? -eq 0 ];then
                echo -e "qy_agent"
		echo "OK"
        else
                echo -e "qy_agent"
		echo "Error"
        fi
}

function Containers {
    Containers=$(docker ps -qa)
    for i in $Containers;
    do
        ContainerName=$(/bin/docker inspect $i |grep  "Name"|awk -F[/] '{print $2}' |awk -F[\"] '{print $1}'|sed 'N;$d;P;D')
        ContainerStatus=$(/bin/docker inspect $i |grep  "Status"|awk '{print $2}'|awk -F[\"] '{print $2}')
        echo -e "$ContainerName  $ContainerStatus\n" >> /opt/docker.txt
    done

    AllStatus=$(cat /opt/docker.txt |grep  exited)
    if [ $? -eq 0 ];then
        echo "Container"
	echo "Error"
        echo "$AllStatus"
    else
        echo "Container"
	echo "OK"
        cat /opt/docker.txt
    fi
    rm -rf /opt/docker.txt
}

function DnsServer {
    DnsServerPID=$(netstat -nltp |grep named|awk '{print $7}'|awk -F[/] '{print $1}'|uniq)
    DnsStatus=$(ps -ef |grep $DnsServerPID|grep named)
    if [ $? -eq 0 ];then
        echo "DnsNameServer"
	echo "OK"
    else
        echo "DnsNameServer"
	echo "Error"
    fi

}

function ZabbixServer {
    /bin/docker ps -a |grep -w zabbix >> /dev/null
    if [ $? -eq 0 ];then
       #ZabbixServerPID=$(/bin/docker exec -it zabbix netstat -nltp |grep zabbix_server|awk '{print $7}'|awk -F[/] '{print $1}')
       #/bin/docker exec -it zabbix ps -ef |grep $ZabbixServerPID|grep zabbix_server |grep "\-c" >> /dev/null
       ZbxPID=$(netstat -nltp |grep '10051'|grep 'docker-prox'|awk '{print $7}'|awk -F[/] '{print $1}'|sed -n 1p)
       ZbxStatus=$(ps -ef |grep $ZbxPID|grep '10051')
       if [ $? -eq 0 ];then
           echo "ZabbixServer"
	   echo "OK"
       else
           echo "ZabbixServer"
	   echo "Error"
       fi
    else
       echo "ZabbixServer"
       echo "Error"
    fi
}

Docker=$(rpm -qa |grep docker)
DeployMachine=$(echo $?)
function DockerServer {
    DockerStatus=$(systemctl status docker|grep Active |awk '{print $2}')
    if [ "$DockerStatus" == "active" ];then
        Containers
        DnsServer
        ZabbixServer
    else
        echo "DockerServer"
	echo "Error"
    fi
}

function DiskHealth {
    Smart=$(yum list installed 2>/dev/null | grep smartmontools )
    if [ -z "$Smart" ];then
        yum -y install smartmontools >> /dev/null 2>&1
    fi
    echo "DiskStatus"
    for i in `seq 0 100`;
    do
        DiskResult=$(/sbin/smartctl -a -d megaraid,$i / |grep "self-assessment\|SMART Health Status" |awk '{print $NF}')
        DiskSize=$(/sbin/smartctl -a -d megaraid,$i / |grep -i 'User Capacity' |awk '{print $5$6}')
        DiskWear=$(/sbin/smartctl -a -d megaraid,$i / |grep "245" |awk '{print $4"/100"}')
        DiskModel=$(/sbin/smartctl -a -d megaraid,$i /|grep 'Device Model\|Transport protocol'|awk '{print $NF}'|cut -b 1,2)
        if [ "$DiskModel" = "SS" ];then
              DiskType="SSD"
        elif [ "$DiskModel" = "SA" ];then
              DiskType="SAS"
        elif [ "$DiskModel" = "ST" ];then
              DiskType="SATA"
        elif [ "$DiskModel" = "MZ" ];then
              DiskType="SSD"
        else
              DiskType="SSD"
        fi
        if [ -n "$DiskResult" ];then
            if [ -n "$DiskWear" ];then
                echo "第$[i+1]块硬盘$DiskType$DiskSize：$DiskResult;耐久性：$DiskWear" >> /opt/disk-health.log
            else
                echo "第$[i+1]块硬盘$DiskType$DiskSize：$DiskResult                                                                 " >> /opt/disk-health.log
            fi
        else
            break
        fi

    done
    cat /opt/disk-health.log
    rm -rf /opt/disk-health.log
    echo "DiskStatusEnd"

}


function check(){

############################## 系统状态 #############################
   getSystemStatus
   getCpuStatus
   getMemStatus
   getDiskStatus
   getNetworkStatus
   DiskHealth 
#  getListenStatus
#  getProcessStatus
#  getServiceStatus
#  getAutoStartStatus
#  getCronStatus
#  getJDKStatus
#  getFirewallStatus

############################## openstack服务状态 ############################
   getOpenstackServerStatus
   getOtherServerStatus
   getCephClusterStatus
   
############################## 麒云平台服务状态 #############################
   if [ -d /apps/sh/resin ];then

       getQiyunResinStatus
       getQiyunNginxStatus
       getQiyunMysqlStatus
       getQiyunRedisStatus
       getQiyunQyAgentStatus
   fi
  
  if [ $DeployMachine -eq 0 ];then
       DockerServer
  fi
}

###进行巡检检查###
check
