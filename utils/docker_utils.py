# utils/docker_utils.py
import subprocess

def stop_container(container_name: str):
    """
    Выполняет docker stop <container>
    """
    cmd = ["docker", "stop", container_name]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Docker stop failed: {result.stderr.strip()}")
