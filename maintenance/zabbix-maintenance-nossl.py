#!/usr/bin/python
import requests
import json
import sys
from datetime import datetime, timedelta

requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

ZABBIX_API_URL = "https://<IP>/api_jsonrpc.php" # Replace with your IP or DNS
ZABBIX_API_TOKEN = "TOKEN"  # Replace with your provided auth token

def get_host_id(auth_token, hostname):
    payload = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "filter": {
                "host": [hostname]
            }
        },
        "id": 2
    }
    headers = {
        "Content-Type": "application/json-rpc",
        "Authorization": f"Bearer {auth_token}"
    }
    
    response = requests.post(ZABBIX_API_URL, json=payload, headers=headers, verify=False) 
    
    try:
        response_json = response.json()
        result = response_json.get('result', [])
        if result:
            return result[0]['hostid']
        else:
            raise Exception(f"Host '{hostname}' not found.")
    except Exception as e:
        raise Exception(f"Failed to retrieve host ID: {e}")

def create_maintenance(auth_token, host_id, duration_minutes, collect_data=True):
    start_time = int(datetime.now().timestamp())
    end_time = int((datetime.now() + timedelta(minutes=duration_minutes)).timestamp())

    payload = {
        "jsonrpc": "2.0",
        "method": "maintenance.create",
        "params": {
            "name": f"Maintenance for host ID {host_id}",
            "active_since": start_time,
            "active_till": end_time,
            "maintenance_type": 0 if collect_data else 1,
            "timeperiods": [{
                "timeperiod_type": 0,
                "start_date": start_time,
                "period": duration_minutes * 60
            }],
            "hosts": [{
                "hostid": host_id
            }]
        },
        "id": 3
    }

    headers = {
        "Content-Type": "application/json-rpc",
        "Authorization": f"Bearer {auth_token}"
    }

    response = requests.post(ZABBIX_API_URL, json=payload, headers=headers, verify=False) 
    
    try:
        response_json = response.json()
        if 'result' in response_json:
            return response_json['result']
        elif 'error' in response_json:
            raise Exception(f"Zabbix API error: {response_json['error']['data']}")
        else:
            raise Exception(f"Unexpected response: {response_json}")
    except json.JSONDecodeError:
        raise Exception(f"Invalid JSON response: {response.text}")

def delete_maintenance(auth_token, hostname):
    headers = {
        "Content-Type": "application/json-rpc",
        "Authorization": f"Bearer {auth_token}"
    }

    host_id = get_host_id(auth_token, hostname) 

    payload = {
        "jsonrpc": "2.0",
        "method": "maintenance.get",
        "params": {
            "output": "extend",
            "selectHosts": ["hostid"]
        },
        "id": 4
    }

    response = requests.post(ZABBIX_API_URL, json=payload, headers=headers, verify=False) 
    maintenances = response.json().get('result', [])

    maintenance_ids = [
        m['maintenanceid']
        for m in maintenances
        if any(h['hostid'] == host_id for h in m.get('hosts', []))
    ]

    if not maintenance_ids:
        print(f"No active maintenance found for host '{hostname}'")
        return

    delete_payload = {
        "jsonrpc": "2.0",
        "method": "maintenance.delete",
        "params": maintenance_ids,
        "id": 5
    }

    del_response = requests.post(ZABBIX_API_URL, json=delete_payload, headers=headers, verify=False)
    del_result = del_response.json()
    if 'result' in del_result:
        print(f"✅ Deleted {len(del_result['result']['maintenanceids'])} maintenance(s) for host '{hostname}'")
    elif 'error' in del_result:
        print(f"Error deleting maintenance: {del_result['error']['data']}")

def main(action, hostname, duration_minutes=None, collect_data=True):
    auth_token = ZABBIX_API_TOKEN
    try:
        if action.lower() == "create":
            if duration_minutes is None:
                raise ValueError("Missing duration for maintenance.")
            host_id = get_host_id(auth_token, hostname)
            result = create_maintenance(auth_token, host_id, duration_minutes, collect_data)
            print(f"✅ Maintenance created. ID: {result['maintenanceids'][0]}")
            print(f"Data collection during maintenance: {'Enabled' if collect_data else 'Disabled'}")
        elif action.lower() == "delete":
            delete_maintenance(auth_token, hostname)
        else:
            print("Invalid action. Use 'create' or 'delete'.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage:")
        print("  Create: script.py create <hostname> <duration_minutes> [yes|no]")
        print("  Delete: script.py delete <hostname>")
    else:
        action = sys.argv[1]
        hostname = sys.argv[2]

        
        duration_minutes = None
        collect_data = True 

        if action.lower() == "create":
            if len(sys.argv) > 3:
                try:
                    duration_minutes = int(sys.argv[3])
                except ValueError:
                    print("❌ Error: Duration must be an integer.")
                    sys.exit(1)

            if len(sys.argv) > 4:
                collect_data = sys.argv[4].lower() == "yes"
        
        main(action, hostname, duration_minutes, collect_data)
