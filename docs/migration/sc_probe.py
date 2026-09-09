import sqlite3, json, urllib.request, urllib.error, sys, time

PID = "581eb237-6e95-4a48-b577-efc81724038a"
DB = r"C:/Users/paren/AppData/Roaming/CherryStudio/Data/cherrystudio.sqlite"

con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
row = con.execute("SELECT endpoint_configs, api_keys FROM user_provider WHERE provider_id=?", (PID,)).fetchone()
con.close()
ep = json.loads(row[0]); ks = json.loads(row[1])
key = next(it["key"] for it in ks if it.get("isEnabled") and it.get("key"))
base = ep["openai-chat-completions"]["baseUrl"].rstrip("/")
url = base + "/chat/completions"

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36"}

def call(tag, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}", **UA}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            body = r.read(3000).decode("utf-8", "replace")
            print(f"[{tag}] HTTP {r.status}  head={body[:120]!r}")
    except urllib.error.HTTPError as e:
        body = e.read(1200).decode("utf-8", "replace")
        print(f"[{tag}] HTTP {e.code}  body={body!r}")
    except Exception as e:
        print(f"[{tag}] EXC {e}")

tools = [{"type": "function", "function": {"name": "get_weather", "description": "Get weather", "parameters": {"type": "object", "properties": {"location": {"type": "string"}}, "required": ["location"]}}}]
msgs = [{"role": "user", "content": "Weather in Paris? Use get_weather."}]
basep = {"model": "StandardCompute", "messages": msgs}

call("stream+tools", {**basep, "tools": tools, "tool_choice": "auto", "stream": True, "max_tokens": 100})
call("parallel_tool_calls", {**basep, "tools": tools, "tool_choice": "auto", "parallel_tool_calls": True, "max_tokens": 100})
call("stream_options", {**basep, "tools": tools, "tool_choice": "auto", "stream": True, "stream_options": {"include_usage": True}, "max_tokens": 100})
call("sampling_parms", {**basep, "tools": tools, "tool_choice": "auto", "temperature": 0.7, "top_p": 0.9, "presence_penalty": 0, "frequency_penalty": 0, "max_tokens": 100})
call("logprobs_n_user", {**basep, "tools": tools, "tool_choice": "auto", "logprobs": False, "n": 1, "max_tokens": 100})
call("max_completion_tokens", {**basep, "tools": tools, "tool_choice": "auto", "max_completion_tokens": 100})
call("minimal_plain", {**basep, "max_tokens": 20})
call("tool_choice_required", {**basep, "tools": tools, "tool_choice": {"type": "function", "function": {"name": "get_weather"}}, "max_tokens": 100})
