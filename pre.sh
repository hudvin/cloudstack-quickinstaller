!#/bin/bash
yum install mc
yum -y install python python-devel gcc 
curl http://python-distribute.org/distribute_setup.py | python
curl https://raw.github.com/pypa/pip/master/contrib/get-pip.py | python
pip install fabric fexpect

pip uninstall pycrypto
pip install PyCrypto==2.3

