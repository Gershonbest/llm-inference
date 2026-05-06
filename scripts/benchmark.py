import argparse
import asyncio
import time
import aiohttp

async def fetch(session, url, payload):
    start = time.perf_counter()
    async with session.post(url, json=payload) as response:
        await response.text()
        return time.perf_counter() - start

async def main(args):
    url = f"http://{args.host}:{args.port}/v2/models/{args.model}/generate"
    payload = {
        "text_input": "Once upon a time",
        "parameters": {
            "max_tokens": 100,
            "temperature": 0.7
        }
    }
    
    print(f"Starting benchmark with concurrency {args.concurrency} and {args.requests} total requests...")
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for _ in range(args.requests):
            tasks.append(fetch(session, url, payload))
            
            if len(tasks) >= args.concurrency:
                latencies = await asyncio.gather(*tasks)
                tasks = []
                
        if tasks:
            latencies = await asyncio.gather(*tasks)
            
    print("Benchmark complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", default="8000")
    parser.add_argument("--model", default="llama3")
    parser.add_argument("--concurrency", type=int, default=50)
    parser.add_argument("--requests", type=int, default=500)
    args = parser.parse_args()
    
    asyncio.run(main(args))
