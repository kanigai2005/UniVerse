import asyncio
import subprocess
import sys
import os
import webbrowser

async def run_app(command: list, env=None):
    executable = command[0]
    args = command[1:]
    process = await asyncio.create_subprocess_exec(
        executable,
        *args,
        env=env
    )
    return await process.wait()

async def main():
    # Start the login backend and open the browser
    command_main = [sys.executable, "main.py"]
    executable_main = command_main[0]
    args_main = command_main[1:]
    print("[run_all] Starting main.py (login backend) on http://localhost:8000...")
    process_main = await asyncio.create_subprocess_exec(
        executable_main,
        *args_main,
    )
    # Don't wait for main.py to exit

    print("[run_all] Opening login page in the browser...")
    webbrowser.open("http://localhost:8000")

    # Start the main backend (exp.py) - it will get the user ID from the /home route
    command_exp = [sys.executable, "-m", "uvicorn", "exp:app", "--reload", "--port", "8001"]
    executable_exp = command_exp[0]
    args_exp = command_exp[1:]
    print("[run_all] Running exp.py on http://localhost:8001...")
    await run_app(command_exp)
    print("[run_all] exp.py execution completed.")

if __name__ == "__main__":
    asyncio.run(main())