import sqlite3, json, urllib.request, urllib.error, sys

PID = "581eb237-6e95-4a48-b577-efc81724038a"
DB = r"C:/Users/paren/AppData/Roaming/CherryStudio/Data/cherrystudio.sqlite"

con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
row = con.execute(
    "SELECT endpoint_configs, api_keys FROM user_provider WHERE provider_id=?",
    (PID,),
).fetchone()
con.close()
if not row:
    print("RESULT=NO_PROVIDER"); sys.exit(1)
endpoint_configs = json.loads(row[0])
api_keys = json.loads(row[1])

def find_key(keys_obj):
    # api_keys is a list of {"id","key","isEnabled"} OR dict endpoint->key OR plain str
    if isinstance(keys_obj, list):
        for item in keys_obj:
            if isinstance(item, dict):
                if item.get("isEnabled") and isinstance(item.get("key"), str) and item["key"]:
                    return item["key"]
        for item in keys_obj:
            if isinstance(item, dict) and isinstance(item.get("key"), str) and item["key"]:
                return item["key"]
        return None
    if isinstance(keys_obj, dict):
        for k in ("openai-chat-completions", "chat", "apiKey", "key", "default"):
            if k in keys_obj and isinstance(keys_obj[k], str) and keys_obj[k]:
                return keys_obj[k]
        for v in keys_obj.values():
            if isinstance(v, str) and v.startswith(("sk", "sc-", "stdc", "Bearer")):
                return v
    return keys_obj if isinstance(keys_obj, str) else None

key = find_key(api_keys)
base = endpoint_configs["openai-chat-completions"]["baseUrl"].rstrip("/")
url = base + "/chat/completions"
if not key:
    print("RESULT=NO_KEY_FOUND"); sys.exit(1)

tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {"location": {"type": "string"}},
            "required": ["location"],
        },
    },
}]
payload = {
    "model": "StandardCompute",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the current weather in Paris? Use the get_weather tool."},
    ],
    "tools": tools,
    "tool_choice": "auto",
    "max_tokens": 300,
}
req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}",
             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"},
    method="POST",
)
try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read().decode("utf-8"))
        status = resp.status
except urllib.error.HTTPError as e:
    raw = e.read().decode("utf-8", "replace")
    print(f"HTTP {e.code}")
    print("BODY:", raw[:600])
    sys.exit(0)

msg = (body.get("choices") or [{}])[0].get("message") or {}
tc = msg.get("tool_calls")
print("HTTP", status)
print("finish_reason:", (body.get("choices") or [{}])[0].get("finish_reason"))
print("message.tool_calls present:", bool(tc))
if tc:
    for call in tc:
        fn = call.get("function", {})
        print("tool_call name:", fn.get("name"))
        print("tool_call args:", fn.get("arguments")[:300])
        print("RESULT=TOOL_CALLS_OK")
else:
    print("content:", (msg.get("content") or "")[:300])
    print("RESULT=NO_TOOL_CALLS")
