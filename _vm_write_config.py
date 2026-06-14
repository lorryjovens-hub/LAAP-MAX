"""Create Feishu config on VM"""
content = """FEISHU_APP_ID=cli_aaa4a20527f9dbd6
FEISHU_APP_SECRET=***..."
with open("/opt/aris/feishu.conf", "w") as f:
    f.write(content)
print("Config written")
