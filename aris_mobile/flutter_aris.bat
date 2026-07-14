@echo off
REM Aris Flutter launcher — bypasses git detection issues
SET FLUTTER_ROOT=C:\Users\user\flutter
SET cache_dir=%FLUTTER_ROOT%\bin\cache
SET dart_sdk_path=%cache_dir%\dart-sdk
SET dart=%dart_sdk_path%\bin\dart.exe
SET snapshot_path=%cache_dir%\flutter_tools.snapshot
SET flutter_tools_dir=%FLUTTER_ROOT%\packages\flutter_tools

"%dart%" --packages="%flutter_tools_dir%\.dart_tool\package_config.json" "%snapshot_path%" %*
