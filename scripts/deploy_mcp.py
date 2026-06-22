import requests, json

url = "https://n8n.grupoellev.com.br/mcp-server/http"
headers = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0N2MxNzUzYy04ZmUwLTQ4NGYtYjUxYi0yODllYTEwZjk2MGQiLCJpc3MiOiJuOG4iLCJhdWQiOiJtY3Atc2VydmVyLWFwaSIsImp0aSI6IjljOWE4NGQwLTNhZDEtNDZhNy05NmE5LTEzNzk5OGQ0Njk4NSIsImlhdCI6MTc3NzE1NjIwMH0.KG8vA58LC304mt4PlhzPC7xmlQ-hrjM2U0SeyRz7QKA",
    "Accept": "application/json, text/event-stream"
}

with open("/home/jessegoncalves/problm/workflow_terra_vista.json") as f:
    wf = json.load(f)

payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "n8n_update_full_workflow",
        "arguments": {
            "id": "GoReM1W65uebzAMu",
            "nodes": wf["nodes"],
            "connections": wf["connections"]
        }
    }
}

r = requests.post(url, headers=headers, json=payload)
print(r.text)
