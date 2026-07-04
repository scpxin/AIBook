#!/bin/bash
set -e
HOST="ubuntu@140.143.210.177"
PASS="Tencent123c"
SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
SCP="sshpass -p '$PASS' scp $SSH_OPTS"
SSH="sshpass -p '$PASS' ssh $SSH_OPTS $HOST"

case "$1" in
  frontend)
    echo "=== Deploying frontend ==="
    $SCP /workspace/deploy/index-v2.html $HOST:/home/ubuntu/fanqie-docker/index-v2.html
    $SSH "cd /home/ubuntu/fanqie-docker && docker compose restart web"
    echo "Frontend deployed."
    ;;
  backend)
    echo "=== Deploying backend modules ==="
    $SSH "mkdir -p /tmp/novel_creator"
    $SCP /workspace/deploy/novel_creator/generator.py \
         /workspace/deploy/novel_creator/prompts.py \
         /workspace/deploy/novel_creator/craft_prompts.py \
         /workspace/deploy/novel_creator/ai_client.py \
         $HOST:/tmp/novel_creator/
    $SSH "docker cp /tmp/novel_creator/generator.py fanqie-backend:/app/novel_creator/generator.py && \
          docker cp /tmp/novel_creator/prompts.py fanqie-backend:/app/novel_creator/prompts.py && \
          docker cp /tmp/novel_creator/craft_prompts.py fanqie-backend:/app/novel_creator/craft_prompts.py && \
          docker cp /tmp/novel_creator/ai_client.py fanqie-backend:/app/novel_creator/ai_client.py"
    $SSH "cd /home/ubuntu/fanqie-docker && docker compose restart backend"
    echo "Backend modules deployed."
    ;;
  server)
    echo "=== Deploying server script ==="
    $SCP /workspace/deploy/server-v2.py $HOST:/tmp/server-v2.py
    $SSH "docker cp /tmp/server-v2.py fanqie-backend:/app/server-v2.py"
    $SSH "cd /home/ubuntu/fanqie-docker && docker compose restart backend"
    echo "Server script deployed."
    ;;
  all)
    $0 frontend
    $0 backend
    $0 server
    ;;
  *)
    echo "Usage: $0 {frontend|backend|server|all}"
    exit 1
    ;;
esac
