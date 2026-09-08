#!/bin/bash
# B10: Swallow-8B(bf16) full probe / B11: 2行形の書式エラー率(8B INT8 + Swallow)。09-05と同構成(BATCH_INVARIANT・conc8・temp0)。
set -u
cd ~/bench/quality_probe_v0
export VLLM_BATCH_INVARIANT=1 VLLM_USE_FLASHINFER_SAMPLER=0 VLLM_LOGGING_LEVEL=INFO OMP_NUM_THREADS=4
VB=~/venvs/vllm-bench/bin
mkdir -p logs results_swallow results_2line
tmux kill-session -t b1011 2>/dev/null
tmux new-session -d -s b1011 -n q8b "CUDA_VISIBLE_DEVICES=4 $VB/vllm serve nytopop/Qwen3-8B.w8a8 --served-model-name Qwen3-8B-int8 --port 8000 --host 127.0.0.1 --gpu-memory-utilization 0.90 --max-model-len 4096 --max-num-batched-tokens 8192 --max-num-seqs 32 --enable-prefix-caching 2>&1 | tee logs/server-b1011-q8b.log"
tmux new-window -t b1011 -n swallow "CUDA_VISIBLE_DEVICES=5 $VB/vllm serve tokyotech-llm/Llama-3.1-Swallow-8B-Instruct-v0.3 --served-model-name Swallow-8B-bf16 --dtype bfloat16 --port 8001 --host 127.0.0.1 --gpu-memory-utilization 0.90 --max-model-len 4096 --max-num-batched-tokens 8192 --max-num-seqs 32 --enable-prefix-caching 2>&1 | tee logs/server-b1011-swallow.log"
cat > run_b1011_inner.sh <<'INNER'
#!/bin/bash
cd ~/bench/quality_probe_v0
for p in 8000 8001; do until curl -s http://127.0.0.1:$p/v1/models >/dev/null; do sleep 15; done; echo "port $p ready $(date +%T)"; done
echo "B10 start $(date +%T)"
python3 run_probe.py --endpoints http://127.0.0.1:8001 --quants bf16 --engine-ver 0.28.0 --conc 8 --out results_swallow/quality_ledger.csv --raw-dir results_swallow/raw
python3 scorer.py --ledger results_swallow/quality_ledger.csv --probes probes.jsonl --report results_swallow/report.md || true
echo "B11 start $(date +%T)"
python3 run_probe.py --probes probes_2line.jsonl --endpoints http://127.0.0.1:8000,http://127.0.0.1:8001 --quants int8,bf16 --engine-ver 0.28.0 --conc 8 --out results_2line/quality_ledger.csv --raw-dir results_2line/raw
echo "RUN_DONE $(date +%T)"; wc -l results_swallow/quality_ledger.csv results_2line/quality_ledger.csv
INNER
tmux new-window -t b1011 -n runner "bash run_b1011_inner.sh > logs/b1011_run.txt 2>&1"
echo "b1011 launched: $(sha256sum probes_2line.jsonl | cut -c1-16)"
