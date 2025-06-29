# core/bot_core/bot_manager.py

import os
import json
import subprocess
from datetime import datetime
from typing import Dict
from utils import docker_utils

class BotManager:
    def __init__(self, bots_data_path: str = "data/bots/", container_map_file: str = "core/bot_core/bot_containers.json"):
        self.bots_data_path = os.path.abspath(bots_data_path)
        self.container_map_file = os.path.abspath(container_map_file)
        self.container_map: Dict[str, str] = {}

        self._load_container_map()

    def _load_container_map(self):
        if os.path.exists(self.container_map_file):
            with open(self.container_map_file, "r") as f:
                self.container_map = json.load(f)

    def _save_container_map(self):
        with open(self.container_map_file, "w") as f:
            json.dump(self.container_map, f, indent=4)

    def _generate_bot_id(self, bot_type: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{bot_type}_{timestamp}"
    
    def create_bot(self, bot_type: str, config: dict) -> str:
        bot_id = self._generate_bot_id(bot_type)
        print(f"[DEBUG] Creating bot without launch: {bot_id}")

        bot_folder = os.path.join(self.bots_data_path, bot_id)
        os.makedirs(os.path.join(bot_folder, "extra_data"), exist_ok=True)
        open(os.path.join(bot_folder, "logs.txt"), "a").close()

        config_path = os.path.join(bot_folder, "config.json")
        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)

        return bot_id   

    def start_bot(self, bot_type: str, config: dict) -> str:
        bot_id = self._generate_bot_id(bot_type)
        print(f"[DEBUG] Generated bot_id: {bot_id}")

        bot_folder = os.path.join(self.bots_data_path, bot_id)
        print(f"[DEBUG] Creating folder: {bot_folder}")
        os.makedirs(os.path.join(bot_folder, "extra_data"), exist_ok=True)
        open(os.path.join(bot_folder, "logs.txt"), "a").close()

        config_path = os.path.join(bot_folder, "config.json")
        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)

        abs_path = os.path.abspath(bot_folder)
        image_name = f"{bot_type}"

        docker_cmd = [
            "docker", "run", "-d",
            "--name", bot_id,
            "-v", f"{abs_path}/config.json:/app/config.json",
            "-v", f"{abs_path}/logs.txt:/app/logs.txt",
            "-v", f"{abs_path}/extra_data:/app/extra_data",
            "-v", f"{abs_path}:/app",
            image_name
        ]

        try:
            result = subprocess.run(docker_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            if result.returncode != 0:
                print(f"[ERROR] Failed to start bot container: {result.stderr}")
                return ""

            container_id = result.stdout.strip()

            self.container_map[bot_id] = container_id
            self._save_container_map()

            print(f"[INFO] Bot {bot_id} started. Container ID: {container_id}")
            return bot_id

        except Exception as e:
            print(f"[EXCEPTION] Error launching bot: {e}")
            return ""

    def stop_bot(self, bot_id: str):
        """
        Останавливает запущенный Docker-контейнер по bot_id
        """
        container_name = bot_id
        docker_utils.stop_container(container_name)

    def start_existing_bot(self, bot_id: str, bot_type: str, config: dict) -> None:
        print(f"[DEBUG] Starting existing bot: {bot_id}")
        bot_folder = os.path.join(self.bots_data_path, bot_id)

        if not os.path.exists(bot_folder):
            print(f"[ERROR] Bot folder not found: {bot_folder}")
            return

        config_path = os.path.join(bot_folder, "config.json")
        logs_path = os.path.join(bot_folder, "logs.txt")
        extra_path = os.path.join(bot_folder, "extra_data")

        os.makedirs(extra_path, exist_ok=True)
        open(logs_path, "a").close()

        if not os.path.exists(config_path):
            print(f"[ERROR] Config not found: {config_path}")
            return

        abs_path = os.path.abspath(bot_folder)

        # 🔁 Правильный выбор имени образа по типу
        if bot_type == "crawler-bot":
            image_name = "crawler_bot-image"
        elif bot_type == "xss-bot":
            image_name = "xss-bot-image"
        else:
            print(f"[ERROR] Unknown bot type: {bot_type}")
            return

        # Проверка: уже запущен или нет
        check_cmd = ["docker", "ps", "-a", "--filter", f"name=^{bot_id}$", "--format", "{{.Status}}"]
        result = subprocess.run(check_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0 and result.stdout:
            status = result.stdout.strip()
            if "Up" in status:
                print(f"[INFO] Bot '{bot_id}' is already running.")
                return
            else:
                print(f"[INFO] Removing old container for bot '{bot_id}' (status: {status})")
                subprocess.run(["docker", "rm", bot_id], check=True)

        # 🔧 Docker запуск с монтированием
        docker_cmd = [
            "docker", "run", "-d",
            "--name", bot_id,
            "-v", f"{abs_path}/config.json:/app/config.json",
            "-v", f"{abs_path}/logs.txt:/app/logs.txt",
            "-v", f"{abs_path}/extra_data:/app/extra_data",
            "-v", f"{abs_path}:/app",
            image_name
        ]

        try:
            subprocess.run(docker_cmd, check=True)
            print(f"[INFO] Bot '{bot_id}' started using image '{image_name}'")
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to start bot '{bot_id}': {e}")

