#!/bin/bash
### Make sure yum-plugin-security package is installed ###
### Make sure zabbix-sender package is installed ###
### Add the script to the crontab and import template in Zabbix ###

HOSTNAME=$(egrep ^Hostname= /etc/zabbix/zabbix_agentd.conf | cut -d = -f 2)
zabbixserverip=$(egrep ^ServerActive /etc/zabbix/zabbix_agentd.conf | cut -d = -f 2)
release=$(cat "/etc/redhat-release")

Moderate=$(yum updateinfo list --sec-severity=Moderate | grep Moderate | wc -l)
Important=$(yum updateinfo list --sec-severity=Important | grep Important | wc -l)
Low=$(yum updateinfo list --sec-severity=Low | grep Low | wc -l)
Critical=$(yum updateinfo list --sec-severity=Critical | grep Critical | wc -l)

zabbix_sender -k yum.moderate -o $Moderate -z $zabbixserverip -s $HOSTNAME > /dev/null 2>&1
zabbix_sender -k yum.imporant -o $Important -z $zabbixserverip -s $HOSTNAME > /dev/null 2>&1
zabbix_sender -k yum.low -o $Low -z $zabbixserverip -s $HOSTNAME > /dev/null 2>&1
zabbix_sender -k yum.critical -o $Critical -z $zabbixserverip -s $HOSTNAME > /dev/null 2>&1
zabbix_sender -k yum.release -o "$(cat /etc/redhat-release)" -z $zabbixserverip -s $HOSTNAME > /dev/null 2>&1
