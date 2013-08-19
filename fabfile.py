from fabric.api import *
from fabric.contrib import *
print 'hello'
env.hosts = ['127.0.0.1']
repo_body = """
[cloudstack]
name=cloudstack
baseurl=http://cloudstack.apt-get.eu/rhel/4.1/
enabled=1
gpgcheck=0
"""

my_cnf_body = """
[mysqld]
innodb_rollback_on_timeout=1
innodb_lock_wait_timeout=600
max_connections=350
datadir=/var/lib/mysql
socket=/var/lib/mysql/mysql.sock
user=mysql
# Disabling symbolic-links is recommended to prevent assorted security risks
symbolic-links=0

[mysqld_safe]
log-error=/var/log/mysqld.log
pid-file=/var/run/mysqld/mysqld.pid
"""

repo_file = '/etc/yum.repos.d/cloudstack.repo'
my_cnf_file = '/etc/my.cnf'

def hello():
    files.append(repo_file, repo_body, use_sudo=True)
    run('hostname --fqdn')
    sudo('yum install ntp') 
    sudo('yum install cloudstack-management')
    sudo('yum install cloudstack-agent')
    sudo('yum install mysql-server')
    sudo('rm /etc/my.cnf')
    files.append(my_cnf_file, my_cnf_body, use_sudo=True)
    sudo('service mysqld restart')
    sudo('mysql_secure_installation')
    files.comment('/etc/selinux/config','SELINUX=enforcing',use_sudo=True)
    files.append('/etc/selinux/config','SELINUX=permissive', use_sudo=True)
    sudo("setenforce permissive")
    sudo("cloudstack-setup-databases cloud:qwerty@localhost \--deploy-as=root:qwerty ")
    files.append('/etc/sudoers','Defaults:cloud !requiretty', use_sudo=True)
    sudo('cloudstack-setup-management')


nfs_sysconfig = """
LOCKD_TCPPORT=32803
LOCKD_UDPPORT=32769
MOUNTD_PORT=892
RQUOTAD_PORT=875
STATD_PORT=662
STATD_OUTGOING_PORT=2020
"""

def setup_nfs():
    sudo("yum install nfs-utils")
    sudo('mkdir -p /export/primary')
    sudo('mkdir -p /export/secondary')
    files.append('/etc/exports','/export  *(rw,async,no_root_squash)', use_sudo=True)
    sudo('exportfs -a')
    files.append('/etc/sysconfig/nfs', nfs_sysconfig, use_sudo=True)
    #sudo('service iptables stop')
    files.append('/etc/idmapd.conf', 'Domain=localhost.localdomain', use_sudo=True)
    sudo('service rpcbind start')
    sudo('service nfs start')
#    sudo('mkdir -p /mnt/primary')
    #sudo('mkdir -p /mnt/secondary')
#   # sudo('mount -t nfs 127.0.0.1:/export/primary /mnt/primary')
#    sudo('mount -t nfs 127.0.0.1:/export/secondary /mnt/secondary') 

def download_system_vm():
    sudo('/usr/share/cloudstack-common/scripts/storage/secondary/cloud-install-sys-tmplt -m /export/secondary -u http://download.cloud.com/templates/acton/acton-systemvm-02062012.qcow2.bz2 -h kvm  -F')

libvirtd_conf_body = """
listen_tls = 0
listen_tcp = 1
tcp_port = "16509"
auth_tcp = "none"
mdns_adv = 0

"""

def setup_host():
    files.append('/etc/libvirt/libvirtd.conf', libvirtd_conf_body, use_sudo=True)
    files.append('/etc/sysconfig/libvirtd','LIBVIRTD_ARGS="--listen"', use_sudo=True)
    sudo('service libvirtd restart')



eth0_body="""
DEVICE=eth0
HWADDR=F0:DE:F1:A0:0E:D4 
ONBOOT=yes
HOTPLUG=no
BOOTPROTO=none
TYPE=Ethernet
"""
eth0_100_body="""
DEVICE=eth0.100
HWADDR=F0:DE:F1:A0:0E:D4
ONBOOT=yes
HOTPLUG=no
BOOTPROTO=none
TYPE=Ethernet
VLAN=yes
IPADDR=192.168.0.120
GATEWAY=192.168.0.1
NETMASK=255.255.255.0
"""
eth0_200_body="""
DEVICE=eth0.200
HWADDR=F0:DE:F1:A0:0E:D4
ONBOOT=yes
HOTPLUG=no
BOOTPROTO=none
TYPE=Ethernet
VLAN=yes
BRIDGE=cloudbr0
"""

eth0_300_body="""
DEVICE=eth0.300
HWADDR=F0:DE:F1:A0:0E:D4
ONBOOT=yes
HOTPLUG=no
BOOTPROTO=none
TYPE=Ethernet
VLAN=yes
BRIDGE=cloudbr1
"""

cloudbr0_body="""
DEVICE=cloudbr0
TYPE=Bridge
ONBOOT=yes
BOOTPROTO=none
IPV6INIT=no
IPV6_AUTOCONF=no
DELAY=5
STP=yes
"""

cloudbr1_body="""
DEVICE=cloudbr1
TYPE=Bridge
ONBOOT=yes
BOOTPROTO=none
IPV6INIT=no
IPV6_AUTOCONF=no
DELAY=5
STP=yes
"""


def setup_eth():
    eth0_path = '/etc/sysconfig/network-scripts/ifcfg-eth0'
    eth0_100_path = '/etc/sysconfig/network-scripts/ifcfg-eth0.100'
    eth0_200_path = '/etc/sysconfig/network-scripts/ifcfg-eth0.200'
    eth0_300_path = '/etc/sysconfig/network-scripts/ifcfg-eth0.300'
    cloudbr0_path = '/etc/sysconfig/network-scripts/ifcfg-cloudbr0' 
    cloudbr1_path = '/etc/sysconfig/network-scripts/ifcfg-cloudbr1'
    #append
    files.append(eth0_path, eth0_body, use_sudo=True)
    files.append(eth0_100_path, eth0_100_body, use_sudo=True)
    files.append(eth0_200_path, eth0_200_body, use_sudo=True)
    files.append(eth0_300_path, eth0_300_body, use_sudo=True)
    files.append(cloudbr0_path, cloudbr0_body, use_sudo=True)
    files.append(cloudbr1_path, cloudbr1_body, use_sudo=True)
    sudo('rm /etc/udev/rules.d/70-persistent-net.rules')
    sudo('reboot')
    


def setup_iptables():
    pass	
