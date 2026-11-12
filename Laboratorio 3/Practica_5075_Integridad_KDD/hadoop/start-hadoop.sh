#!/usr/bin/env bash
set -u

pids=()
names=(NameNode DataNode ResourceManager NodeManager)

hdfs namenode &
pids+=("$!")
hdfs datanode &
pids+=("$!")
yarn resourcemanager &
pids+=("$!")
yarn nodemanager &
pids+=("$!")

cleanup() {
  for pid in "${pids[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  for pid in "${pids[@]}"; do
    wait "$pid" 2>/dev/null || true
  done
}

trap cleanup EXIT
trap 'exit 0' INT TERM

while true; do
  for index in "${!pids[@]}"; do
    pid="${pids[$index]}"
    if ! kill -0 "$pid" 2>/dev/null; then
      wait "$pid"
      status=$?
      echo "${names[$index]} exited with status ${status}" >&2
      exit 1
    fi
  done
  sleep 2
done
