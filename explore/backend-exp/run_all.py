import asyncio
import subprocess
import sys
import os
import json  # To handle potential JSON output from main.py

async def run_app_get_output(command: list):
    """Runs a command and returns its standard output."""
    process = await asyncio.create_subprocess_exec(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        print(f"Error running command: {command}")
        print(stderr.decode())
        return None
    return stdout.decode().strip()

async def run_app(command: list, env=None):
    """Runs a command."""
    process = await asyncio.create_subprocess_exec(
        command,
        env=env
    )
    return await process.wait()

async def get_logged_in_user_id():
    """Runs main.py to simulate login and retrieve user ID."""
    command_main = [sys.executable, "main.py", "--get-user-id"]  # Assuming main.py has this argument
    output = await run_app_get_output(command_main)
    if output:
        try:
            # Assuming main.py prints the user ID directly or as JSON
            user_id = output.strip()
            # Or if main.py outputs JSON:
            # data = json.loads(output)
            # user_id = data.get("user_id")
            print(f"[run_all] Retrieved user ID from main.py: {user_id}")
            return user_id
        except json.JSONDecodeError:
            print("[run_all] Could not parse user ID from main.py output.")
            return None
        except Exception as e:
            print(f"[run_all] Error processing user ID: {e}")
            return None
    else:
        print("[run_all] Failed to get output from main.py.")
        return None

async def main():
    # Run main.py to get the user ID
    user_id = await get_logged_in_user_id()

    if user_id:
        # Run exp.py, passing the user ID as an environment variable
        command_exp = [sys.executable, "-m", "uvicorn", "exp:app", "--reload", "--port", "8001"]
        env_exp = os.environ.copy()
        env_exp["LOGGED_IN_USER_ID"] = user_id
        print(f"[run_all] Running exp.py with LOGGED_IN_USER_ID: {user_id}")
        await run_app(command_exp, env=env_exp)
        print("[run_all] exp.py execution completed (or started and detached).")
    else:
        print("[run_all] Could not retrieve user ID. Not running exp.py.")

if __name__ == "__main__":
    asyncio.run(main())