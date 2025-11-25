from fastapi import FastAPI, Response, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from pydantic import BaseModel
from typing import List, Optional
import threading
import time
import queue
import math
from fastapi.middleware.cors import CORSMiddleware

limiter = Limiter(key_func=get_remote_address)

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

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
        result_queue.put(CombinationResponse(message="目標値は1以上の自然数である必要があります．"))
    elif any(n < 1 or not isinstance(n, int) for n in numbers):
        result_queue.put(CombinationResponse(message="数値欄には1以上の自然数のみを含めてください．"))

def reorder_by_original_order(original, subset):
    order_map = {num: i for i, num in enumerate(original)}
    return sorted(subset, key=lambda x: order_map[x])

def remove_subset_from_list(original, subset):
    remaining = original.copy()
    for num in subset:
        if num in remaining:
            remaining.remove(num)
    return remaining

def find_combination_worker(numbers, target, result_queue):
    validate_inputs(numbers, target, result_queue)
    if not result_queue.empty():
        return
    
    n = len(numbers)
    if n == 0:
        result_queue.put(CombinationResponse(message="数値欄が空です．"))
        return

    sorted_numbers = sorted(numbers, reverse=True)

    max_number = sorted_numbers[0]
    threshold = math.ceil(target / max_number)
    if threshold > n:
        result_queue.put(CombinationResponse(message="全合計が目標値に届きません．"))
        return

    suffix_sum = [0] * n
    suffix_sum[-1] = sorted_numbers[-1]
    for i in range(n - 2, -1, -1):
        suffix_sum[i] = suffix_sum[i + 1] + sorted_numbers[i]

    reverse_mode = target <= suffix_sum[0] < 2 * target

    if reverse_mode:
        target = suffix_sum[0] - target
        threshold = max(math.ceil(target / max_number) - 1, 0)
        best_sum = 0
    else:
        best_sum = float('inf')
    best_combination = None

    def dfs(index, path, total, depth):
        nonlocal best_sum, best_combination, threshold

        # 深さが threshold に満たない間は合計チェックしない
        if depth >= threshold:
            if total > target:
                if not reverse_mode:
                    if total < best_sum:
                        best_sum = total
                        best_combination = list(path)
                return False  # 枝切り
            elif total < target:
                if reverse_mode:
                    if total > best_sum:
                        best_sum = total
                        best_combination = list(path)
                threshold = depth + 1
            elif total == target:
                if reverse_mode:
                    reordered = remove_subset_from_list(numbers, path)
                else:
                    reordered = reorder_by_original_order(numbers, path)
                result_queue.put(CombinationResponse(exact=reordered))
                return True  # 終了              

        for i in range(index, n):
            if reverse_mode:
                if suffix_sum[i] < best_sum - total:
                    break
            else:
                if suffix_sum[i] < target - total:
                    break

            next_num = sorted_numbers[i]

            if dfs(i + 1, path + [next_num], total + next_num, depth + 1):
                return True
        return False

    dfs(0, [], 0, 0)

    if not result_queue.empty():
        return

    if best_combination:
        if reverse_mode:
            reordered = remove_subset_from_list(numbers, best_combination)
        else:
            reordered = reorder_by_original_order(numbers, best_combination)
        result_queue.put(CombinationResponse(closest=reordered, closest_sum=sum(reordered)))
    else:
        if reverse_mode:
            result_queue.put(CombinationResponse(closest=numbers, closest_sum=suffix_sum[0]))
        else:
            result_queue.put(CombinationResponse(message="全合計が目標値に届きません．"))

@app.post("/find_combination", response_model=CombinationResponse)
@limiter.limit("60/minute")
async def find_combination(request: Request, req: CombinationRequest):
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

class RemovalRequest(BaseModel):
    numbers: List[int]
    used: List[int]

class RemovalResponse(BaseModel):
    remaining: List[int]

@app.post("/remove_used_numbers", response_model=RemovalResponse)
@limiter.limit("60/minute")
def remove_used_numbers(request: Request, req: RemovalRequest):
    remaining = req.numbers.copy()
    for u in req.used:
        if u in remaining:
            remaining.remove(u)
    return {"remaining": remaining}

# ルートパス
@app.get("/", include_in_schema=False)
@app.head("/", include_in_schema=False)
@limiter.limit("60/minute")
async def root(request: Request):
    return Response(content='{"message": "Hello, World!"}', media_type="application/json")

# CORS ミドルウェア
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://resical.vercel.app",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 13001, 12001, 14001, 11001, 15001, 10001, 16001, 9001, 17001, 8001, 18001, 7001, 19001, 6001, 20001, 5001, 21001, 4001, 22001, 3001, 23001, 2001, 24001, 1001, 25001
