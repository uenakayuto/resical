from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from itertools import combinations
import threading
import time
import queue
import math
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

class CombinationRequest(BaseModel):
    numbers: List[int]
    target: int

class CombinationResponse(BaseModel):
    exact: Optional[List[int]] = None
    closest: Optional[List[int]] = None
    closest_sum: Optional[int] = None
    message: Optional[str] = None
    execution_time: Optional[float] = None

def validate_inputs(numbers: List[int], target: int, result_queue):
    if target < 1 or not isinstance(target, int):
        result_queue.put(CombinationResponse(message="targetは1以上の自然数である必要があります．"))
    elif any(n < 1 or not isinstance(n, int) for n in numbers):
        result_queue.put(CombinationResponse(message="numbersには1以上の自然数のみを含めてください．"))

def find_combination_worker(numbers, target, result_queue):
    validate_inputs(numbers, target, result_queue)
    if not result_queue.empty():
        return
    sorted_numbers = sorted(numbers, reverse=True)
    # print(f"Sorted numbers: {sorted_numbers}")
    max_sorted_numbers = sorted_numbers[0]
    # print(f"Max sorted number: {max_sorted_numbers}")
    threshold = math.ceil(target / max_sorted_numbers)
    if threshold > len(sorted_numbers):
        result_queue.put(CombinationResponse(message="全合計がtargetに届きません．"))
        return
    # print(f"Threshold for combinations: {threshold}")
    best_sum = float('inf')
    best_combination = None

    for r in range(threshold, len(sorted_numbers) + 1):
        for comb in combinations(sorted_numbers, r):
            # print(f"Checking combination: {comb}")
            total = sum(comb)
            if total == target:
                result_queue.put(CombinationResponse(exact=list(comb)))
                return
            if total < target:
                # print(f"break: {comb}")
                break
            if target < total < best_sum:
                best_sum = total
                best_combination = comb

    if best_sum != float('inf'):
        result_queue.put(CombinationResponse(closest=list(best_combination), closest_sum=int(best_sum)))
    else:
        result_queue.put(CombinationResponse(message="全合計がtargetに届きません．"))

@app.post("/find_combination", response_model=CombinationResponse)
async def find_combination(req: CombinationRequest):
    start = time.perf_counter()
    result_queue = queue.Queue()
    thread = threading.Thread(target=find_combination_worker, args=(req.numbers, req.target, result_queue))
    thread.start()
    thread.join(timeout=5.5)

    if thread.is_alive():
        return CombinationResponse(
            message="実行時間が長すぎるため，処理を中断しました．",
            execution_time=round(time.perf_counter() - start, 3)
        )
    result = result_queue.get()
    result.execution_time = round(time.perf_counter() - start, 3)
    return result

# 13001, 12001, 14001, 11001, 15001, 10001, 16001, 9001, 17001, 8001, 18001, 7001, 19001, 6001, 20001, 5001, 21001, 4001, 22001, 3001, 23001, 2001, 24001, 1001, 25001

class RemovalRequest(BaseModel):
    numbers: List[int]
    used: List[int]

class RemovalResponse(BaseModel):
    remaining: List[int]

@app.post("/remove_used_numbers", response_model=RemovalResponse)
def remove_used_numbers(req: RemovalRequest):
    remaining = req.numbers.copy()
    for u in req.used:
        if u in remaining:
            remaining.remove(u)
    return {"remaining": remaining}

@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番では適切に制限
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)