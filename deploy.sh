#!/bin/bash
echo "🚀 Deploying JARVIS..."
rsync -avz --exclude='venv' --exclude='__pycache__' --exclude='*.pyc' --exclude='.env' --exclude='token.json' --exclude='credentials.json' ~/Desktop/jarvis-proj/jarvis-core/ root@140.82.58.192:/root/jarvis-core/
ssh root@140.82.58.192 "supervisorctl restart jarvis"
echo "✅ Done! JARVIS is live at http://140.82.58.192:8000"
