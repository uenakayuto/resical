from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from itertools import combinations
import threading
import time
import queue
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

def find_combination_worker(numbers, target, result_queue):
    best_sum = float('inf')
    best_combination = None

    for r in range(1, len(numbers) + 1):
        for comb in combinations(numbers, r):
            total = sum(comb)
            if total == target:
                result_queue.put(CombinationResponse(exact=list(comb)))
                return
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

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番では適切に制限
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)