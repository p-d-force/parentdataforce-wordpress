# EAGLE3 Speculative Decoding Setup

## 1. Install prerequisites

```bash
# Create a Python virtual environment (recommended)
python -m venv venv
source venv/bin/activate   # Windows: .\venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

## 2. Verify local GPT‑OSS‑20B model

The script expects the model to be available under a directory named `gptoss20b` (or a path supplied through the `GPTOSS20B_PATH` environment variable). If the model is located elsewhere, set the variable:

```bash
export GPTOSS20B_PATH=/absolute/path/to/gptoss20b  # Unix
set GPTOSS20B_PATH=C:\Users\User\path\to\gptoss20b   # Windows CMD
```

## 3. Launch the vLLM server with EAGLE3 speculative decoding

```bash
# Run the helper script
python run_eagle3.py
```

The script starts `vllm serve` with the spec‑config provided in `eagle3_spec_config.json`. It will expose the model on the default port (8000). You can adjust the port with the `--port` flag if needed.

## 4. Connect UnsloTH Studio

1. Open UnsloTH Studio. In the *Connection* tab, point the **Endpoint** field to the server address, e.g. `http://localhost:8000`. Use the same authentication credentials you used for the local model.
2. In the *Model* tab, set the **Model ID** to `gptoss20b` (or the name you use locally). Ensure the **Specification** option is enabled—UnsloTH will automatically use the EAGLE3 configuration provided by the server.

## 5. Test inference

From UnsloTH Studio’s prompt window, run:

```text
Hello, world!
```

You should see the model respond quickly due to speculative decoding. If you want to profile latency, enable the *Metrics* overlay in UnsloTH or use `curl`:

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model": "gptoss20b", "messages": [{"role": "user", "content": "Hello"}]}'
```

## 6. Troubleshooting

- **Missing GPU support**: EAGLE3 requires GPU acceleration. Ensure `torch` was built with CUDA/CuDNN and that your GPU drivers are up to date.
- **Port already in use**: Add `--port 8001` to the `vllm serve` invocation.
- **UnsloTH Studio fails to connect**: Verify the firewall allows traffic on the chosen port.

---

**Note**: This setup uses the vLLM native spec‑config interface. If you prefer to run the model purely via UnsloTH’s internal inference engine, you’ll need to translate the spec‑config into the internal format UnsloTH accepts.
