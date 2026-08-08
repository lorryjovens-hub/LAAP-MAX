import sqlite3
conn = sqlite3.connect(r"D:\LAAP\laap\memory_vault\aris_lorry_vault.db")
try:
    cur = conn.execute("PRAGMA cipher_version")
    print("SQLCipher version:", cur.fetchone())
except Exception as e:
    print("NOT SQLCipher:", e)
try:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print("tables:", [r[0] for r in rows][:8])
    print("=> 明文可读，vault 未加密")
except Exception as e:
    print("read failed:", e)
conn.close()
