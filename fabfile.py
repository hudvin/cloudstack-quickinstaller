from fabric.api import *
from fabric.contrib import *
env.hosts = ['127.0.0.1']
env.warn_only = True

repo_body = """
[cloudstack]
name=cloudstack
baseurl=http://cloudstack.apt-get.eu/rhel/4.1/
enabled=1
gpgcheck=0"""

my_cnf_body = """[mysqld]
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
pid-file=/var/run/mysqld/mysqld.pid"""

eth0_body="""DEVICE=eth0
HWADDR=%s
ONBOOT=yes
BOOTPROTO=none
TYPE=Ethernet
BRIDGE=cloudbr0"""

cloudbr0_body="""DEVICE=cloudbr0
HWADDR=%s
TYPE=Bridge
ONBOOT=yes
BOOTPROTO=none
IPADDR=%s
NETMASK=%s
GATEWAY=%s
DNS1=%s
IPV6INIT=no
IPV6_AUTOCONF=no
DELAY=0
STP=yes"""

nfs_sysconfig = """LOCKD_TCPPORT=32803
LOCKD_UDPPORT=32769
MOUNTD_PORT=892
RQUOTAD_PORT=875
STATD_PORT=662
STATD_OUTGOING_PORT=2020"""

libvirtd_conf_body = """listen_tls = 0
listen_tcp = 1
tcp_port = "16509"
auth_tcp = "none"
mdns_adv = 0"""


repo_file = '/etc/yum.repos.d/cloudstack.repo'
my_cnf_file = '/etc/my.cnf'

ip_addr = ''
dns = ''
gateway = ''
netmask = ''
hw_addr = ''
 

def start_local_ssh():
    sudo('service sshd start')

def install_cs():
    sudo('yum install cloudstack-management')
    sudo('yum install cloudstack-agent')

def install_mysql():
    sudo('yum install mysql-server')

def install_other():
    sudo('yum install ntp')
    sudo("yum install nfs-utils")

def check_fqdn():
    run('hostname --fqdn')

def add_repo():
     files.append(repo_file, repo_body, use_sudo=True)

def configure_system():
    sudo('rm /etc/my.cnf')
    files.append(my_cnf_file, my_cnf_body, use_sudo=True)
    files.comment('/etc/selinux/config','SELINUX=enforcing',use_sudo=True)
    files.append('/etc/selinux/config','SELINUX=permissive', use_sudo=True)
    sudo("setenforce permissive")
    files.append('/etc/sudoers','Defaults:cloud !requiretty', use_sudo=True)
    files.append('/etc/libvirt/libvirtd.conf', libvirtd_conf_body, use_sudo=True)
    files.append('/etc/sysconfig/libvirtd','LIBVIRTD_ARGS="--listen"', use_sudo=True)


def configure_cs():
    sudo('service mysqld start')
    sudo('mysql_secure_installation')
    sudo("cloudstack-setup-databases cloud:qwerty@localhost \--deploy-as=root:qwerty -i %s"%ip_addr)
    sudo('cloudstack-setup-management')

def start_all():
    sudo('service mysqld start')
    sudo('service cloudstack-agent start')
    sudo('service cloudstack-management start')
    sudo('service rpcbind start')
    sudo('service nfs start')
    sudo('service libvirtd start')


def stop_all():
    sudo('service mysqld stop')
    sudo('service cloudstack-agent stop')
    sudo('service cloudstack-management stop')
    sudo('service rpcbind stop')
    sudo('service nfs stop')
    sudo('service libvirtd stop')

def restart_network():
    sudo('service network restart')
    run('ping 8.8.8.8 -c 5')
def configure_nfs():
    sudo('mkdir -p /export/primary')
    sudo('mkdir -p /export/secondary')
    files.append('/etc/exports','/export  *(rw,async,no_root_squash)', use_sudo=True)
    sudo('exportfs -a')
    files.append('/etc/sysconfig/nfs', nfs_sysconfig, use_sudo=True)
    files.append('/etc/idmapd.conf', 'Domain=localhost.localdomain', use_sudo=True)
    

def download_system_vm():
    sudo('/usr/share/cloudstack-common/scripts/storage/secondary/cloud-install-sys-tmplt -m /export/secondary -u http://download.cloud.com/templates/acton/acton-systemvm-02062012.qcow2.bz2 -h kvm  -F')

def remove_cs():
    sudo('yum remove cloudstack-management cloudstack-agent')

def clean_dirs():
    run('rm /export/ -rf')

def drop_dbs():
    mysql_username = 'root'
    mysql_password  = prompt("What is mysql password?")
    cs_dbs = ['cloud','cloud_usage','cloudbridge']
    for db in cs_dbs:
        run('mysqladmin -u%s -p%s drop %s'%(mysql_username, mysql_password, db))

def grub_network_params():
    global ip_addr, dns, gateway, netmask, hw_addr
    ip_addr = prompt('Enter IP address of eth0:', default = '192.168.0.115')
    dns = prompt('Enter DNS:',default = '8.8.8.8')
    gateway = prompt('Enter Gateway:', default = '192.168.0.1')
    netmask = prompt('Enter Netmask:', default = '255.255.255.0') 
    hw_addr = run('ifconfig eth0 | awk \'/HWaddr/ {print $5}\'')
 

def configure_eth():
    #for eth0 (for my network)
    #ip_addr = prompt('Enter IP address of eth0:', default = '192.168.0.115')
    #dns = prompt('Enter DNS:',default = '8.8.8.8')
    #gateway = prompt('Enter Gateway:', default = '192.168.0.1')
    #netmask = prompt('Enter Netmask:', default = '255.255.255.0') 
    #hw_addr = run('ifconfig eth0 | awk \'/HWaddr/ {print $5}\'')
    #path to configs
    eth0_path = '/etc/sysconfig/network-scripts/ifcfg-eth0'
    cloudbr0_path = '/etc/sysconfig/network-scripts/ifcfg-cloudbr0' 
    #make backup
    from time import gmtime, strftime
    now = strftime("%Y-%m-%d_%H:%M:%S", gmtime())
    print 'making backup'
    sudo('cp %s %s' %(eth0_path,eth0_path+'.'+now))
    sudo('cp %s %s' %(cloudbr0_path,cloudbr0_path+'.'+now))
    #remove and create new
    sudo('rm %s'%eth0_path)
    sudo('rm %s'%cloudbr0_path)
    files.append(eth0_path, eth0_body%hw_addr, use_sudo=True)
    files.append(cloudbr0_path, cloudbr0_body%(hw_addr,ip_addr, netmask, gateway, dns), use_sudo=True)
    
    #if not files.contains(eth0_path, eth0_body%hw_addr,escape=False):
    #    files.append(eth0_path, eth0_body%hw_addr, use_sudo=True, escape=False)
    #if not files.contains(cloudbr0_path, cloudbr0_body%hw_addr,escape=False): 
    #    files.append(cloudbr0_path, cloudbr0_body%hw_addr, use_sudo=True, escape=False)
    sudo('rm /etc/udev/rules.d/70-persistent-net.rules')
    confirm = prompt('Do you want to reboot right now(y/N)?')
    if confirm == 'y':
        sudo('reboot')
    else:
        print 'Please, reboot system to apply changes!'

def configure_iptables():
    pass


def remove_all():
    stop_all()
    remove_cs()
    clean_dirs() 


def install_all():
    grub_network_params()    
    add_repo()
    install_mysql()
    drop_dbs()
    install_other()
    install_cs()
    configure_eth()
    restart_network()
    configure_cs()
    configure_nfs()
    download_system_vm()
    start_all()
