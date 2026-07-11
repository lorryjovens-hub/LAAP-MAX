REM === 小智ESP32-C3 固件编译 & 烧录 ===
REM 在 Windows CMD (不是PowerShell, 不是git-bash) 中运行此文件

REM 1. 激活 ESP-IDF 环境
call D:\user\Documents\ESPclaw-lorry\esp\esp-idf\export.bat

REM 2. 进入小智项目目录
cd /d "D:\xiaozhi-esp32-main (2)\xiaozhi-esp32-main"

REM 3. 设置目标芯片 (xmini-c3 = ESP32-C3)
idf.py set-target esp32c3

REM 4. 编译
idf.py build

REM 5. 烧录 (把 COM3 改成你的串口号)
REM idf.py -p COM3 flash

echo.
echo === 完成 ===
echo 烧录命令: idf.py -p COMx flash
echo (把COMx换成xmini-c3的串口号)
