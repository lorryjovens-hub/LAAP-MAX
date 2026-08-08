@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64
if errorlevel 1 exit /b %errorlevel%
cl.exe /nologo /EHsc /std:c++17 /W4 /O2 "D:\LAAP\hanako\desktop\native\HanaWindowsSandboxHelper\main.cpp" /link /OUT:"D:\LAAP\hanako\dist-sandbox\win-x64\hana-win-sandbox.exe" userenv.lib advapi32.lib user32.lib
exit /b %errorlevel%
