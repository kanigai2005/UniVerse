import asyncio
import subprocess

async def run_fastapi_app(module: str, port: int):
    command = ["uvicorn", f"{module}:app", "--host", "127.0.0.1", "--port", str(port), "--reload"]
    process = await asyncio.create_subprocess_exec(*command)
    return process

async def main():
    main_process = await run_fastapi_app("main", 8000)
    exp_process = await run_fastapi_app("exp", 8001)

    await asyncio.gather(
        main_process.wait(),
        exp_process.wait(),
    )

if __name__ == "__main__":
    asyncio.run(main())