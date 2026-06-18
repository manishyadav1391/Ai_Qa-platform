import subprocess
import time


def execute_script(script_path):

    start = time.time()

    result = subprocess.run(
        ["python", script_path],
        capture_output=True,
        text=True
    )

    duration = time.time() - start

    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "duration": duration
    }