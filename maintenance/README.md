# Zabbix maintenance script

- Create and remove maintenance modes for hosts in minutes
- Can be used as frontend scripts
- use yes or no for data collection or not

## Create a frontend script in Zabbix

### To put a host in maintenance
/usr/bin/python3 /usr/bin/zabbixMaintenance.py create {HOST.HOST} 60 yes | no 

### To remove a host from maintenance
/usr/bin/python3 /usr/bin/zabbixMaintenance.py delete {HOST.HOST}
