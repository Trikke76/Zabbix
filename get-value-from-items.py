#!/usr/bin/env python3

import requests
import json

class ZabbixAPI:
    def __init__(self, url, username, password):
        self.url = url
        self.auth_token = self.login(username, password)

    def login(self, username, password):
        data = {
            'jsonrpc': '2.0',
            'method': 'user.login',
            'params': {
                'username': username,
                'password': password
            },
            'id': 1,
            'auth': None
        }
        response = self.post_request(data)
        if 'result' in response:
            return response['result']
        else:
            raise Exception(f"Login failed: {response['error']['message']}")

    def post_request(self, data):
        headers = {'Content-Type': 'application/json-rpc'}
        response = requests.post(self.url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        return response.json()

    def hostgroup_get(self, group_name):
        data = {
            'jsonrpc': '2.0',
            'method': 'hostgroup.get',
            'params': {
                'output': 'extend',
                'filter': {
                    'name': [group_name]
                }
            },
            'auth': self.auth_token,
            'id': 1
        }
        response = self.post_request(data)
        return response['result'][0] if response['result'] else None

    def host_get(self, group_id):
        data = {
            'jsonrpc': '2.0',
            'method': 'host.get',
            'params': {
                'output': ['hostid', 'name'],
                'groupids': group_id
            },
            'auth': self.auth_token,
            'id': 1
        }
        response = self.post_request(data)
        return response['result']

    def item_get(self, host_id, search):
        data = {
            'jsonrpc': '2.0',
            'method': 'item.get',
            'params': {
                'hostids': host_id,
                'search': {'name': search},
                'searchWildcardsEnabled': True,
                'output': ['itemid', 'name', 'lastvalue']
            },
            'auth': self.auth_token,
            'id': 1
        }
        response = self.post_request(data)
        return response['result']

    def logout(self):
        data = {
            'jsonrpc': '2.0',
            'method': 'user.logout',
            'params': [],
            'auth': self.auth_token,
            'id': 1
        }
        self.post_request(data)


def main():
    zabbix_url = 'https://<Zabbix URL>/api_jsonrpc.php'
    zabbix_user = '<username>'
    zabbix_password = '<password>'
    group_name = 'PostgreSQL'
    item_search = 'PostgreSQL: Version'

    zabbix_api = ZabbixAPI(zabbix_url, zabbix_user, zabbix_password)

    try:
        group = zabbix_api.hostgroup_get(group_name)
        if not group:
            print(f'Host group {group_name} not found')
            return

        hosts = zabbix_api.host_get(group['groupid'])
        if not hosts:
            print(f'No hosts found in group {group_name}')
            return

        for host in hosts:
            items = zabbix_api.item_get(host['hostid'], item_search)
            if not items:
                print(f'No items found for host {host["name"]} with search term "{item_search}"')
                continue

            for item in items:
                print(f'Item for host {host["name"]}: {item["name"]}, Value: {item["lastvalue"]}')

    finally:
        zabbix_api.logout()


if __name__ == '__main__':
    main()
