@echo off
cd /d D:\LAAP\aris_brain

REM 从 Hermes config 读 key
for /f "tokens=*" %%a in ('python -c "import yaml; c=yaml.safe_load(open(r'C:\Users\user\AppData\Local\hermes\profiles\aris\config.yaml')); print(c['providers']['deepseek']['api_key'])"') do set DEEPSEEK_API_KEY=%%a

set ARIS_MODE=llm
set DEEPSEEK_MODEL=deepseek-chat

python aris_feishu_bridge.py
