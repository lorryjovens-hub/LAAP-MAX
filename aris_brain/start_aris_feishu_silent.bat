@echo off
title Aris 飞书桥 (静默)
chcp 65001 >nul

:: ─── 静默启动飞书桥 (LLM模式) ───
cd /d D:\LAAP\aris_brain
set ARIS_MODE=llm
python aris_feishu_bridge.py
