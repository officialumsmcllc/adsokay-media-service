import time
import datetime
import traceback
import sys
from olx_scraper import run_olx_cycle
from dubicars_scraper import run_dubicars_cycle

def log(msg):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] [WORKER-DAEMON] {msg}", flush=True)

def main():
    log("AdsOkay 24/7 Render Cloud Scraper Engine Started!")
    
    cycle_count = 1
    while True:
        try:
            log(f"========== Starting Sync Cycle #{cycle_count} ==========")
            
            # 1. Run OLX Pakistan Scraper
            log("--> Step 1: Running OLX Pakistan Multi-City Scraper...")
            olx_added = run_olx_cycle()
            log(f"--> Step 1 Completed. Total OLX ads added: {olx_added}")
            
            # Short rest between tasks
            time.sleep(15)
            
            # 2. Run DubiCars UAE Scraper
            log("--> Step 2: Running DubiCars UAE Motors Scraper...")
            dubi_added = run_dubicars_cycle()
            log(f"--> Step 2 Completed. Total DubiCars ads added: {dubi_added}")
            
            log(f"========== Cycle #{cycle_count} Completed Successfully ==========")
            cycle_count += 1
            
            # Sleep 15 minutes before the next full cycle
            log("Sleeping 15 minutes before next cycle...")
            time.sleep(900)
            
        except Exception as e:
            log(f"Unexpected error in worker loop: {e}")
            traceback.print_exc()
            time.sleep(60)

if __name__ == "__main__":
    main()
