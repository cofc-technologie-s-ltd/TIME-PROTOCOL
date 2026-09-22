import time
from time_ledger import SecureTimeLedger

def run_benchmark(iterations: int = 1000):
    ledger = SecureTimeLedger()
    wallet = "bc1q3cmhzwxa35egpqhr5eddrqqfmdd8jyeqqkky6h"
    
    print(f"Starting TIME Protocol Performance Benchmark ({iterations} transactions)...")
    start_time = time.time()
    
    success_count = 0
    for i in range(1, iterations + 1):
        success = ledger.update_account(wallet, balance=1000 + i, nonce=i, staked=500)
        if success:
            success_count += 1

    duration = time.time() - start_time
    tps = iterations / duration if duration > 0 else 0
    
    print(f"Benchmark Completed!")
    print(f"Processed: {success_count}/{iterations} transactions")
    print(f"Duration: {duration:.4f} seconds")
    print(f"Throughput: {tps:.2f} TX/sec")

if __name__ == "__main__":
    run_benchmark()
