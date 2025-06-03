import os
import subprocess
import json


def analyze_with_retire(file_path):
    abs_path = os.path.abspath(file_path)
    print(f"[RETIRE] Checking file: {abs_path}")

    command = f'npx retire "{abs_path}" --outputformat json'
    print(f"[RETIRE] CMD: {command}")

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True
        )

        print(f"[RETIRE] Exit code: {result.returncode}")
        if result.stderr:
            print(f"[RETIRE] STDERR: {result.stderr.strip()}")

        # ✅ Ничего не отображаем в GUI — просто возвращаем данные
        if result.returncode == 13:
            try:
                data = json.loads(result.stdout)
                return {
                    "status": "ok",
                    "file_path": file_path,
                    "data": data.get("data", [])
                }
            except json.JSONDecodeError:
                return {
                    "status": "error",
                    "file_path": file_path,
                    "error": "JSON decode error"
                }

        elif result.returncode == 0:
            return {
                "status": "ok",
                "file_path": file_path,
                "data": []
            }

        else:
            return {
                "status": "error",
                "file_path": file_path,
                "error": f"Unexpected exit code: {result.returncode}"
            }

    except Exception as e:
        return {
            "status": "error",
            "file_path": file_path,
            "error": str(e)
        }
