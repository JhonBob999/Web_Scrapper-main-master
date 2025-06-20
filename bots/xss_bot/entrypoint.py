import json
import time

# Чтение конфига
with open("shared/config.json", "r") as f:
    config = json.load(f)

target = config.get("target")
param = config.get("param")
headless = config.get("headless")

print(f"[XSS-BOT] Target: {target}")
print(f"[XSS-BOT] Param: {param}")
print(f"[XSS-BOT] Headless mode: {headless}")

# Симуляция работы
status = {
    "status": "completed",
    "target": target,
    "success": True
}

# Пишем статус
with open("shared/status.json", "w") as f:
    json.dump(status, f, indent=4)

# Пишем лог
with open("shared/logs.txt", "w") as f:
    f.write("Payload test log...\n")
    f.write("All payloads executed successfully.\n")

print("[XSS-BOT] Done.")
time.sleep(2)
