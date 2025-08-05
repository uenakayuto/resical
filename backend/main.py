from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
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

def reorder_by_original_order(original, subset):
    order_map = {num: i for i, num in enumerate(original)}
    return sorted(subset, key=lambda x: order_map[x])

def find_combination_worker(numbers, target, result_queue):
    validate_inputs(numbers, target, result_queue)
    if not result_queue.empty():
        return

    sorted_numbers = sorted(numbers, reverse=True)
    max_number = sorted_numbers[0]
    threshold = math.ceil(target / max_number)
    if threshold > len(sorted_numbers):
        result_queue.put(CombinationResponse(message="全合計がtargetに届きません．"))
        return

    best_sum = float('inf')
    best_combination = None

    def dfs(index, path, total, depth):
        nonlocal best_sum, best_combination, threshold

        # 深さが threshold に満たない間は合計チェックしない
        if depth >= threshold:
            if total == target:
                reordered = reorder_by_original_order(numbers, path)
                result_queue.put(CombinationResponse(exact=reordered))
                return True  # 終了
            elif total > target:
                if total < best_sum:
                    best_sum = total
                    best_combination = list(path)
                return False  # 枝切り
            else:
                threshold = depth + 1  # 探索深さを増やす

        for i in range(index, len(sorted_numbers)):
            next_num = sorted_numbers[i]
            if dfs(i + 1, path + [next_num], total + next_num, depth + 1):
                return True  # 終了
        return False

    dfs(0, [], 0, 0)

    if not result_queue.empty():
        return

    if best_combination:
        reordered = reorder_by_original_order(numbers, best_combination)
        result_queue.put(CombinationResponse(closest=reordered, closest_sum=sum(best_combination)))
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

# 使用済みの数字を取り除くエンドポイント
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

# ルートパス（UptimeRobot用など）
@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}

# CORS ミドルウェア
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 必要に応じて制限
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 13001, 12001, 14001, 11001, 15001, 10001, 16001, 9001, 17001, 8001, 18001, 7001, 19001, 6001, 20001, 5001, 21001, 4001, 22001, 3001, 23001, 2001, 24001, 1001, 25001