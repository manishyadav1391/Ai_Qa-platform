import subprocess
import time
import re
import os
from pathlib import Path


def execute_script(script_path: str):

    start_time = time.time()

    try:

        result = subprocess.run(
            [
                "pytest",
                script_path,
                "-v",
                "--tb=short"
            ],
            capture_output=True,
            text=True,
            timeout=300
        )

        duration = round(time.time() - start_time, 2)

        stdout = result.stdout or ""
        stderr = result.stderr or ""

        # -----------------------------
        # Parse pytest results
        # -----------------------------
        passed = 0
        failed = 0
        skipped = 0

        passed_match = re.search(r'(\d+)\s+passed', stdout)
        failed_match = re.search(r'(\d+)\s+failed', stdout)
        skipped_match = re.search(r'(\d+)\s+skipped', stdout)

        if passed_match:
            passed = int(passed_match.group(1))

        if failed_match:
            failed = int(failed_match.group(1))

        if skipped_match:
            skipped = int(skipped_match.group(1))

        total = passed + failed + skipped

        # -----------------------------
        # Detect no tests
        # -----------------------------
        if "collected 0 items" in stdout:
            status = "NO_TESTS_FOUND"

        elif failed > 0:
            status = "FAILED"

        elif passed > 0:
            status = "PASSED"

        else:
            status = "UNKNOWN"

        # -----------------------------
        # Save report
        # -----------------------------
        os.makedirs("execution_reports", exist_ok=True)

        report_name = (
            Path(script_path).stem
            + "_report.txt"
        )

        report_path = os.path.join(
            "execution_reports",
            report_name
        )

        with open(
            report_path,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(
                "===== STDOUT =====\n\n"
            )

            f.write(stdout)

            f.write(
                "\n\n===== STDERR =====\n\n"
            )

            f.write(stderr)

        return {

            "status": status,

            "returncode": result.returncode,

            "passed": passed,

            "failed": failed,

            "skipped": skipped,

            "total": total,

            "duration": duration,

            "report_path": report_path,

            "stdout": stdout,

            "stderr": stderr
        }

    except subprocess.TimeoutExpired:

        duration = round(
            time.time() - start_time,
            2
        )

        return {

            "status": "TIMEOUT",

            "returncode": -1,

            "duration": duration,

            "passed": 0,

            "failed": 0,

            "skipped": 0,

            "total": 0,

            "stdout": "",

            "stderr": "Execution timed out after 300 seconds."
        }

    except Exception as e:

        duration = round(
            time.time() - start_time,
            2
        )

        return {

            "status": "ERROR",

            "returncode": -1,

            "duration": duration,

            "passed": 0,

            "failed": 0,

            "skipped": 0,

            "total": 0,

            "stdout": "",

            "stderr": str(e)
        }