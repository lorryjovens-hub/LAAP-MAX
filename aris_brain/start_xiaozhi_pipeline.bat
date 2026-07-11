@echo off
cd /d D:\LAAP\aris_brain
echo ========================================
echo  Aris 小智 全链路启动
echo  DNS 重定向 + MQTT 透明代理
echo ========================================
echo.
echo 热点: Aris_P4 (192.168.137.1)
echo 小智: 192.168.137.200
echo.
echo 正在启动 DNS 重定向 (端口53) + MQTT 代理 (端口1883)...
echo.
python -u aris_pipeline_startup.py
pause
