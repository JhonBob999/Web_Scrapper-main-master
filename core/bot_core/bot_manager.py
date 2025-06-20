# core/bot_core/bot_manager.py

import os
import json
import subprocess
from datetime import datetime
from typing import Optional, Dict, List

class BotManager:
    """
    Responsible for managing bot containers: starting, stopping, deleting, 
    tracking statuses and interacting with bot result folders.
    """

    def __init__(self, bots_data_path: str = "data/bots/", container_map_file: str = "core/bot_core/bot_containers.json"):
        """
        Initialize BotManager with paths to result storage and container mapping.
        """
        self.bots_data_path = os.path.abspath(bots_data_path)
        self.container_map_file = os.path.abspath(container_map_file)
        self.container_map: Dict[str, str] = {}  # bot_id -> container_id

        self._load_container_map()

    def _load_container_map(self):
        """
        Load the bot_id → container_id mapping from disk.
        """
        if os.path.exists(self.container_map_file):
            with open(self.container_map_file, "r") as f:
                self.container_map = json.load(f)

    def _save_container_map(self):
        """
        Save the bot_id → container_id mapping to disk.
        """
        with open(self.container_map_file, "w") as f:
            json.dump(self.container_map, f, indent=4)

    def _generate_bot_id(self, bot_type: str) -> str:
        """
        Generate a unique bot ID based on bot type and timestamp.
        Example: xss-bot_20250620_1950
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{bot_type}_{timestamp}"

    def start_bot(self, bot_type: str, config: dict) -> str:
        """
        Start a Docker container with the given bot type and config.
        Creates working directory, saves config, runs container.
        Returns bot_id.
        """
        # 1. Generate bot ID
        bot_id = self._generate_bot_id(bot_type)
        print(f"[DEBUG] Generated bot_id: {bot_id}")
        

        # 2. Create working directory: data/bots/<bot_id>/
        bot_folder = os.path.join(self.bots_data_path, bot_id)
        print(f"[DEBUG] Creating folder: {bot_folder}")
        os.makedirs(bot_folder, exist_ok=True)

        # 3. Save config.json inside the bot folder
        config_path = os.path.join(bot_folder, "config.json")
        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)

        # 4. Construct docker run command
        abs_volume_path = os.path.abspath(bot_folder)
        image_name = f"{bot_type}"  # Docker image should match bot_type (e.g. xss-bot)

        docker_cmd = [
            "docker", "run", "-d",  # -d = detached
            "--name", bot_id,
            "-v", f"{abs_volume_path}:/app/shared",
            image_name
        ]

        try:
            # 5. Run Docker container
            result = subprocess.run(docker_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            if result.returncode != 0:
                print(f"[ERROR] Failed to start bot container: {result.stderr}")
                return ""

            container_id = result.stdout.strip()

            # 6. Save container ID mapping
            self.container_map[bot_id] = container_id
            self._save_container_map()

            print(f"[INFO] Bot {bot_id} started. Container ID: {container_id}")
            return bot_id

        except Exception as e:
            print(f"[EXCEPTION] Error launching bot: {e}")
            return ""

    def stop_bot(self, bot_id: str) -> bool:
        """
        Stop the Docker container associated with the bot_id.
        Returns True if successfully stopped.
        """
        # Use 'docker stop <container_id>'
        pass

    def delete_bot(self, bot_id: str) -> bool:
        """
        Delete bot folder and stop/remove container if running.
        Returns True if deleted successfully.
        """
        # Stop container, remove folder, remove from container_map
        pass

    def get_status(self, bot_id: str) -> Optional[dict]:
        """
        Read and return status.json from bot's result folder.
        """
        # Read file: data/bots/<bot_id>/status.json
        pass

    def get_logs(self, bot_id: str) -> Optional[str]:
        """
        Read and return contents of logs.txt from bot folder.
        """
        # Read file: data/bots/<bot_id>/logs.txt
        pass

    def list_bots(self) -> List[str]:
        """
        List all existing bot launches by folder name (bot_id).
        """
        # Return list of folder names in data/bots/
        pass
