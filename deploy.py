import requests
import sys
import json

if len(sys.argv) < 5:
    print("Usage: python deploy.py <URL> <API_KEY> <STACK_ID> <PROJECT_VERSION>")
    sys.exit(1)

url = sys.argv[1]
api_key = sys.argv[2]
stack_id = sys.argv[3]
project_version = sys.argv[4]

stacks_url = url + 'stacks/' + stack_id
headers = {'Content-Type': 'application/json', 'X-API-Key': api_key}

file_request = requests.get(stacks_url + '/file', headers=headers)
file_json = file_request.json()

get_request = requests.get(stacks_url, headers=headers)
get_json = get_request.json()

body = {'id': stack_id, 'StackFileContent': file_json['StackFileContent'], 'Env': [{
    'Name': 'PROJECT_VERSION',
    'Value': project_version
}], 'PullImage': True, 'Prune': False}

print("Request body", json.dumps(body, indent=4))

response = requests.put(stacks_url + '?endpointId=' + str(get_json['EndpointId']),
                        headers={'Content-Type': 'application/json', 'X-API-Key': api_key},
                        json=body
                        )
if response.status_code != 200:
    print("Error: Invalid response code", response.status_code)
    print(response.text)
    exit(1)

print('Deployed', project_version)
