#!/usr/bin/env python3
"""
Usage:
  zabbix-maintenance.py [--url=<url>] [--token=<token>] (--host=<hostname> | --group=<groupname>) (--add=<name> | --remove=<name>) [--duration=<minutes>] [--description=<text>] [--type=<normal|nodata>]
  zabbix-maintenance.py (-h | --help)
"""

import time
from docopt import docopt
from zabbix_utils import ZabbixAPI
from zabbix_utils.exceptions import APIRequestError

# Set default URL and token here:
DEFAULT_URL = "http://zabbix url/"
DEFAULT_TOKEN = "<user token>"

def main():
    args = docopt(__doc__)

    # Use CLI args if provided, otherwise fall back to default variables
    url = args["--url"] if args["--url"] else DEFAULT_URL
    token = args["--token"] if args["--token"] else DEFAULT_TOKEN

    duration = int(args["--duration"] or 60) * 60
    now = int(time.time())

    api = ZabbixAPI(
        url=url,
        token=token,
        skip_version_check=True
    )

    hosts = []
    groups = []
    if args["--host"]:
        h = api.host.get(filter={"host": args["--host"]})
        if not h:
            raise RuntimeError(f"Host '{args['--host']}' not found")
        hosts = [{"hostid": h[0]["hostid"]}]
    else:
        g = api.hostgroup.get(filter={"name": args["--group"]})
        if not g:
            raise RuntimeError(f"Group '{args['--group']}' not found")
        groups = [{"groupid": g[0]["groupid"]}]

    if args["--add"]:
        try:
            params = {
                "name": args["--add"],
                "active_since": now,
                "active_till": now + duration,
                "maintenance_type": 0 if args.get("--type") != "nodata" else 1,
                "description": args["--description"] or "",
                "hosts": hosts,
                "groups": groups,
                "timeperiods": [{
                    "timeperiod_type": 0,
                    "start_date": now,
                    "period": duration
                }]
            }
            result = api.maintenance.create(**params)
            print("Maintenance created:", result["maintenanceids"])
        except APIRequestError as e:
            print("API error:", e)

    elif args["--remove"]:
        m = api.maintenance.get(filter={"name": args["--remove"]}, output=["maintenanceid"])
        if not m:
            print("No maintenance found with that name")
            return
        ids = [item["maintenanceid"] for item in m]
        result = api.maintenance.delete(ids)
        print("Maintenance removed:", result["maintenanceids"])

if __name__ == "__main__":
    main()
