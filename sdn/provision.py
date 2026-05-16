import os
import sys
import yaml
import requests

SDN_CONTROLLER_URL = os.environ.get("SDN_CONTROLLER_URL")
SDN_CONTROLLER_TOKEN = os.environ.get("SDN_CONTROLLER_TOKEN")

if not SDN_CONTROLLER_URL:
    raise RuntimeError("SDN_CONTROLLER_URL is not set")

if not SDN_CONTROLLER_TOKEN:
    raise RuntimeError("SDN_CONTROLLER_TOKEN is not set")

with open("sdn/policies.yml", "r", encoding="utf-8") as file:
    config = yaml.safe_load(file)

headers = {
    "Authorization": f"Bearer {SDN_CONTROLLER_TOKEN}",
    "Content-Type": "application/json",
}

for policy in config["policies"]:
    response = requests.post(
        f"{SDN_CONTROLLER_URL}/api/policies",
        headers=headers,
        json=policy,
        timeout=10,
    )

    if response.status_code >= 400:
        print(f"Failed to provision policy: {policy['name']}", file=sys.stderr)
        print(response.text, file=sys.stderr)
        response.raise_for_status()

    print(f"Provisioned SDN policy: {policy['name']}")