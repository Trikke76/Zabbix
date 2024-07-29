#!/usr/bin/env python3

import requests
import json
from datetime import datetime, timedelta
import urllib3
import sys

# Disable InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# NetBackup API configuration
BASE_URL = "https://<Netbackup URL>:1556/netbackup"
USERNAME = ""
PASSWORD = ""

# Set the time range for job retrieval (last 7 days)
end_time = datetime.utcnow()
start_time = end_time - timedelta(hours=168)


# Convert start and end_time to ISO 8601 format
end_time_iso = end_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
start_time_iso = start_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")

def get_token():
    login_url = f"{BASE_URL}/login"
    headers = {"Content-Type": "application/json"}
    payload = {"userName": USERNAME, "password": PASSWORD}
    response = requests.post(login_url, headers=headers, json=payload, verify=False)
    if response.status_code == 201:
        return response.json()['token']
    else:
        raise Exception(f"Login failed: {response.status_code} - {response.text}")

def get_failed_jobs(token):
    failed_jobs = []
    current_url = f"{BASE_URL}/admin/jobs"
    headers = {
        "Content-Type": "application/vnd.netbackup+json;version=3.0",
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "page[limit]": 100,  # Adjust as needed
        "filter": f"status gt 1 and endTime ge {start_time_iso} and endTime le {end_time_iso}"
    }
    while True:
        response = requests.get(current_url, headers=headers, params=payload, verify=False)
        if response.status_code == 200:
            data = response.json()
            failed_jobs.extend(data['data'])
            # Check for pagination
            if 'links' in data and 'next' in data['links']:
                next_link = data['links']['next']
                if isinstance(next_link, dict) and 'href' in next_link:
                    current_url = next_link['href']
                elif isinstance(next_link, str):
                    current_url = next_link
                else:
                    print("Unexpected 'next' link format. Stopping pagination.")
                    break
                # Clear payload for subsequent requests
                payload = {}
            else:
                break
        else:
            print(f"Error retrieving jobs: {response.status_code}")
            print(response.text)
            break
    return failed_jobs

try:
    # Get authentication token
    token = get_token()
    # Retrieve failed jobs
    failed_jobs = get_failed_jobs(token)

    # Prepare the JSON structure for Zabbix low-level discovery
    discovery_data = {
        "data": []
    }


    for job in failed_jobs:
        job_data = {
            "{#JOBID}": job['attributes'].get('jobId', 'N/A'),
            "{#JOBTYPE}": job['attributes'].get('jobType', 'N/A'),
            "{#STATUSCODE}": job['attributes'].get('status', 'N/A'),
            "{#STATE}": job['attributes'].get('state', 'N/A'),
            "{#POLICYNAME}": job['attributes'].get('policyName', 'N/A'),
            "{#CLIENTNAME}": job['attributes'].get('clientName', 'N/A'),
            "{#STARTTIME}": job['attributes'].get('startTime', 'N/A'),
            "{#ENDTIME}": job['attributes'].get('endTime', 'N/A'),
            "{#ELAPSEDTIME}": job['attributes'].get('elapsedTime', 'N/A'),
            "{#KILOBYTESTRANSFERRED}": job['attributes'].get('kilobytesTransferred', 'N/A')
        }


        discovery_data["data"].append(job_data)

    # Print the JSON output
    print(json.dumps(discovery_data, indent=2))

except Exception as e:
    error_output = {
        "error": str(e)
    }
    print(json.dumps(error_output))
