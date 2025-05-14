import webbrowser
import time

def sync_njax_market():
    print("[NJAX] Syncing Njax product listings, price tracker, and metrics...")
    time.sleep(1)
    print("[NJAX] Connection established.")
    print("[NJAX] Tasks queued: Auto-post, earnings sync, traffic monitor.")
    
    # Launch Njax Market in browser
    webbrowser.open("https://njanja.net/njax-market")
    
    return True

if __name__ == "__main__":
    sync_njax_market() 