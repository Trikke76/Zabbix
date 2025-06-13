#!/usr/bin/env python3
"""
Usage:
  zabbixmaintenance.py create <host> <duration> <nodata_yesno> [--description=<desc>] [--url=<url>] [--token=<token>]
  zabbixmaintenance.py remove <host> [--url=<url>] [--token=<token>]
"""

import time
from docopt import docopt
from zabbix_utils import ZabbixAPI
from zabbix_utils.exceptions import APIRequestError

# Default values
DEFAULT_URL = "http://<server ip>"
DEFAULT_TOKEN = "<token>"

def main():
    args = docopt(__doc__)

    # Use command-line args if present, otherwise fallback to default
    url = args.get("--url") or DEFAULT_URL
    token = args.get("--token") or DEFAULT_TOKEN

    api = ZabbixAPI(url=url, token=token, skip_version_check=True)

    if args["create"]:
        host_name = args["<host>"]
        duration_min = int(args["<duration>"])
        nodata_flag = args["<nodata_yesno>"].lower() == "no"  # 'no' means no data collection
        maintenance_type = 1 if nodata_flag else 0
        description = args.get("--description") or ""

        duration = duration_min * 60
        now = int(time.time())

        hosts = api.host.get(filter={"host": host_name})
        if not hosts:
            print(f"Host '{host_name}' not found")
            return
        hostid = hosts[0]["hostid"]

        try:
            result = api.maintenance.create({
                "name": host_name,
                "active_since": now,
                "active_till": now + duration,
                "maintenance_type": maintenance_type,
                "description": description,
                "hosts": [{"hostid": hostid}],
                "groups": [],
                "timeperiods": [{
                    "timeperiod_type": 0,
                    "start_date": now,
                    "period": duration
                }]
            })
            print("Maintenance created:", result["maintenanceids"])
        except APIRequestError as e:
            print("API error:", e)

    elif args["remove"]:
        host_name = args["<host>"]
        m = api.maintenance.get(filter={"name": host_name}, output=["maintenanceid"])
        if not m:
            print(f"No maintenance found with name '{host_name}'")
            return
        ids = [item["maintenanceid"] for item in m]
        try:
            result = api.maintenance.delete(ids)
            print("Maintenance removed:", result["maintenanceids"])
        except APIRequestError as e:
            print("API error:", e)

if __name__ == "__main__":
    main()
