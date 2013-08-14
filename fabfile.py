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
    #sudo('mysql_secure_installation')
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
    sudo('service iptables stop')
    files.append('/etc/idmapd.conf', 'Domain=localhost.localdomain', use_sudo=True)
    sudo('service rpcbind start')
    sudo('service nfs start')
    sudo('mkdir -p /mnt/primary')
    sudo('mkdir -p /mnt/secondary')
    sudo('mount -t nfs 127.0.0.1:/export/primary /mnt/primary')
    sudo('mount -t nfs 127.0.0.1:/export/secondary /mnt/secondary') 

def download_system_vm():
    sudo('/usr/share/cloudstack-common/scripts/storage/secondary/cloud-install-sys-tmplt -m /mnt/secondary -u http://download.cloud.com/templates/acton/acton-systemvm-02062012.qcow2.bz2 -h kvm  -F')

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

