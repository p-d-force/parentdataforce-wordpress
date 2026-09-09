#!/usr/bin/env python3
"""Benchmark harness for OMP models. Runs omp bench, prints METRIC lines.

Override via env:
  MODEL_ID  — model selector (default: unsloth/peculiar-ragdoll/Dirk-Qwen3.8-27B-GGUF)
  RUNS      — requests per profile (default: 3)
  PAR       — concurrent requests (default: 1)
  PREFILL_BYTES — synthetic input bytes for prefill profile (default: 32768)
"""
import json, os, subprocess, sys

OMP = r"C:\Users\paren\AppData\Local\omp\omp.exe"
MODEL = os.environ.get("MODEL_ID", "unsloth/peculiar-ragdoll/Dirk-Qwen3.8-27B-GGUF")
RUNS = int(os.environ.get("RUNS", "3"))
PAR = int(os.environ.get("PAR", "1"))
PREFILL_BYTES = int(os.environ.get("PREFILL_BYTES", "32768"))


def bench_profile(model, profile, extra=""):
    cmd = [OMP, "bench", model, "--profile", profile,
           "--runs", str(RUNS), "--par", str(PAR)]
    if extra:
        cmd.extend(extra.split())
    cmd.append("--json")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    if r.returncode != 0:
        print(f"METRIC error={profile}_bench_failed rc={r.returncode}", file=sys.stderr)
        return None
    return json.loads(r.stdout)


def extract_metrics(prefix, data):
    if data is None:
        return
    failures = data.get("failures", 0)
    total = data.get("runs", 0)
    rate = 1.0 - failures / max(total, 1)
    print(f"METRIC {prefix}_success_rate={rate}")
    for m in data.get("models", []):
        s = m.get("stats", {})
        print(f"METRIC {prefix}_tokens_per_sec={s['tokensPerSecond']['mean']}")
        print(f"METRIC {prefix}_gen_tps={s['generationTps']['mean']}")
        print(f"METRIC {prefix}_prefill_tps={s['prefillTps']['mean']}")
        print(f"METRIC {prefix}_ttft_ms={s['ttftMs']['mean']}")
        print(f"METRIC {prefix}_tokens_out={s['outputTokens']}")
        print(f"METRIC {prefix}_tokens_in={s['inputTokens']}")
        print(f"METRIC {prefix}_cost={s['cost']}")
        print(f"METRIC {prefix}_p50_tps={s['tokensPerSecond']['p50']}")
        print(f"METRIC {prefix}_p95_tps={s['tokensPerSecond']['p95']}")


def run_benchmarks(label, model, prefix):
    for profile in ("chat", "prefill", "generation"):
        extra = f"--prefill-bytes {PREFILL_BYTES}" if profile == "prefill" else ""
        print(f"[+] {label} {profile} benchmark ({RUNS} runs)...", file=sys.stderr)
        data = bench_profile(model, profile, extra)
        extract_metrics(f"{prefix}_{profile}", data)


# Detect vision model
vision_model = os.environ.get("VISION_MODEL_ID", "")
if not vision_model:
    import urllib.request
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:8888/v1/models",
            headers={"Authorization": "Bearer sk-unsloth-c46713195c40bf8f34bf18b8fb3e597a"}
        )
        resp = urllib.request.urlopen(req, timeout=5)
        models = json.loads(resp.read()).get("data", [])
        for m in models:
            mid = m.get("id", "")
            if m.get("loaded", False) and any(k in mid.lower() for k in ("vision", "vl", "visual")):
                vision_model = mid
                break
    except Exception:
        pass

print(f"[+] Running text benchmarks for: {MODEL}", file=sys.stderr)
run_benchmarks("text", MODEL, "text")

if vision_model:
    print(f"[+] Running vision benchmarks for: {vision_model}", file=sys.stderr)
    run_benchmarks("vision", vision_model, "vision")
else:
    print("[-] No vision model loaded, skipping", file=sys.stderr)

sys.exit(0)