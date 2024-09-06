import requests
import json
import sys
from datetime import datetime, timedelta

# Zabbix API configuration
ZABBIX_API_URL = "https://zabbix-url/api_jsonrpc.php"
ZABBIX_USER = "your_username"
ZABBIX_PASSWORD = "your_password"

def zabbix_auth():
    auth_data = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {
            "username": ZABBIX_USER,
            "password": ZABBIX_PASSWORD
        },
        "id": 1
    }
    headers = {
        "Content-Type": "application/json-rpc"
    }
    try:
        response = requests.post(ZABBIX_API_URL, json=auth_data, headers=headers)
        response.raise_for_status()
        json_response = response.json()
        if 'result' in json_response:
            return json_response['result']
        elif 'error' in json_response:
            print(f"Authentication error: {json_response['error'].get('data', json_response['error'].get('message', 'Unknown error'))}")
            return None
        else:
            print(f"Unexpected response structure: {json_response}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        if hasattr(e, 'response'):
            print(f"Response content: {e.response.text}")
        return None
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        print(f"Raw response: {response.text}")
        return None

def get_host_id(auth_token, hostname):
    host_data = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "filter": {
                "host": [hostname]
            }
        },
        "auth": auth_token,
        "id": 2
    }
    headers = {
        "Content-Type": "application/json-rpc"
    }
    response = requests.post(ZABBIX_API_URL, json=host_data, headers=headers)
    result = response.json()['result']
    if result:
        return result[0]['hostid']
    else:
        raise Exception(f"Host '{hostname}' not found")

def create_maintenance(auth_token, host_id, duration_minutes):
    start_time = int(datetime.now().timestamp())
    end_time = int((datetime.now() + timedelta(minutes=duration_minutes)).timestamp())
    
    maintenance_data = {
        "jsonrpc": "2.0",
        "method": "maintenance.create",
        "params": {
            "name": f"Maintenance for host ID {host_id}",
            "active_since": start_time,
            "active_till": end_time,
            "hostids": [host_id],
            "timeperiods": [
                {
                    "timeperiod_type": 0,
                    "start_date": start_time,
                    "period": duration_minutes * 60
                }
            ]
        },
        "auth": auth_token,
        "id": 3
    }
    headers = {
        "Content-Type": "application/json-rpc"
    }
    response = requests.post(ZABBIX_API_URL, json=maintenance_data, headers=headers)
    return response.json()['result']

def delete_maintenance(auth_token, hostname):
    # First, get all maintenances
    get_maintenance_data = {
        "jsonrpc": "2.0",
        "method": "maintenance.get",
        "params": {
            "output": "extend",
            "selectHosts": "extend"
        },
        "auth": auth_token,
        "id": 4
    }
    headers = {
        "Content-Type": "application/json-rpc"
    }
    response = requests.post(ZABBIX_API_URL, json=get_maintenance_data, headers=headers)
    maintenances = response.json()['result']
    
    # Find maintenances for the specified host
    host_id = get_host_id(auth_token, hostname)
    maintenance_ids = [m['maintenanceid'] for m in maintenances if any(h['hostid'] == host_id for h in m['hosts'])]
    
    if not maintenance_ids:
        print(f"No active maintenances found for host '{hostname}'")
        return
    
    # Delete found maintenances
    delete_maintenance_data = {
        "jsonrpc": "2.0",
        "method": "maintenance.delete",
        "params": maintenance_ids,
        "auth": auth_token,
        "id": 5
    }
    response = requests.post(ZABBIX_API_URL, json=delete_maintenance_data, headers=headers)
    result = response.json()['result']
    print(f"Deleted {len(result['maintenanceids'])} maintenance(s) for host '{hostname}'")

def main(action, hostname, duration_minutes=None):
    auth_token = zabbix_auth()
    if auth_token is None:
        print("Authentication failed. Please check your Zabbix API configuration.")
        return

    try:
        if action.lower() == "create":
            if duration_minutes is None:
                raise ValueError("Duration is required for create action")
            host_id = get_host_id(auth_token, hostname)
            result = create_maintenance(auth_token, host_id, duration_minutes)
            print(f"Maintenance created successfully. Maintenance ID: {result['maintenanceids'][0]}")
        elif action.lower() == "delete":
            delete_maintenance(auth_token, hostname)
        else:
            print("Invalid action. Use 'create' or 'delete'.")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage:")
        print("  For create: python script.py create <hostname> <duration_minutes>")
        print("  For delete: python script.py delete <hostname>")
    else:
        action = sys.argv[1]
        hostname = sys.argv[2]
        duration_minutes = int(sys.argv[3]) if len(sys.argv) == 4 else None
        main(action, hostname, duration_minutes)
