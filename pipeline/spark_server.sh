#!/usr/bin/env bash
# Démarre la voix Spark de MALIBA-AI sur CPU (llama.cpp pour le modèle de langage + passerelle pour le vocodeur).
# Utilisé par GitHub Actions. En cas de succès, écrit MALIBA_SERVER dans $GITHUB_ENV.
set -euo pipefail
GGUF="${SPARK_GGUF:-bambara-tts-Q8_0.gguf}"
MB=/tmp/mb
[ -d $MB ] || git clone -q --depth 1 https://github.com/MALIBA-AI/bambara-tts $MB
pip install -q -r $MB/server/requirements.txt
pip install -q --no-deps -e $MB
cd $MB
python -m server.download_models --gguf "$GGUF"
mkdir -p /tmp/llama
if [ -z "$(find /tmp/llama -name llama-server -type f | head -1)" ]; then
  gh release download -R ggml-org/llama.cpp --pattern '*-bin-ubuntu-x64.zip' -D /tmp/llama --clobber
  unzip -q -o /tmp/llama/*.zip -d /tmp/llama
fi
BIN=$(dirname "$(find /tmp/llama -name llama-server -type f | head -1)")
export LD_LIBRARY_PATH="$BIN:${LD_LIBRARY_PATH:-}"
nohup "$BIN/llama-server" --model "models/$GGUF" --host 127.0.0.1 --port 8080 --ctx-size 4096 \
  --n-gpu-layers 0 --parallel 1 --threads "$(nproc)" --special --no-webui > /tmp/llama.log 2>&1 &
LLAMA_SERVER_URL=http://127.0.0.1:8080 TTS_DEVICE=cpu nohup uvicorn server.app:app --host 127.0.0.1 --port 8000 > /tmp/gateway.log 2>&1 &
for i in $(seq 1 120); do
  if curl -sf http://127.0.0.1:8000/health | grep -q '"ok"'; then
    echo "Voix Spark prête"; echo "MALIBA_SERVER=http://127.0.0.1:8000" >> "${GITHUB_ENV:-/dev/null}"; exit 0
  fi
  sleep 5
done
echo "La voix Spark n'a pas démarré"; tail -40 /tmp/llama.log /tmp/gateway.log; exit 1
