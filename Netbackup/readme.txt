This script will monitor the errors in netbackup jobs over the last 7 days.


- Install on a server that has access to the Netbackup API a Zabbix agent and copy the file  "Userparameter-netbackup.conf" to the correct location.
- Copy the python script to /etc/zabbix/netbackup-failed-jobs-zabbix.py
- Make sure it has the proper rights to be executed by the Zabbix user.
- Upload the template "Template_Netbackup.yaml" in your Zabbix server templates
- Link the Template with you host where you have installed the scripts
