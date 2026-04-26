import os
import sys
from epsimo import EpsimoClient

sys.path.append(os.getcwd())

def purge():
    client = EpsimoClient()
    PROJECT_ID = "1bea3f7c-1436-4b1a-a27a-4d460b064b60"
    
    resp = client.threads.list(PROJECT_ID)
    threads = resp.get('threads', [])
    count = 0
    for t in threads:
        try:
            client.threads.delete(PROJECT_ID, t['thread_id'])
            print(f"Deleted thread: {t['thread_id']}")
            count += 1
        except Exception as e:
            print(f"Failed to delete {t['thread_id']}: {e}")
            
    print(f"Purged {count} threads.")

if __name__ == "__main__":
    purge()
