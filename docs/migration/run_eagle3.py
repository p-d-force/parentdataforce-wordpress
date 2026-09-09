import os
import subprocess

# Path to local GPT-OSS-20B model directory
MODEL_PATH = os.getenv("GPTOSS20B_PATH", "gptoss20b")

# Speculative decoding config file created earlier
SPEC_CONFIG_FILE = "eagle3_spec_config.json"

# Build the vllm serve command
cmd = [
    "vllm",
    "serve",
    MODEL_PATH,
    "--speculative-config",
    SPEC_CONFIG_FILE,
]

print("Running vLLM server with speculative decoding: ", " ".join(cmd))
subprocess.run(cmd, check=True)
