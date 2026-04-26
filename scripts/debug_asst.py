import os
import sys
import json
from epsimo import EpsimoClient

sys.path.append(os.getcwd())

def debug_asst():
    client = EpsimoClient()
    PROJECT_ID = "1bea3f7c-1436-4b1a-a27a-4d460b064b60"
    ASSISTANT_ID = "557958f2-d5d2-48fd-a3f5-cf28b6d087de"
    
    asst = client.assistants.get(PROJECT_ID, ASSISTANT_ID)
    print("Full Assistant Config Debug:")
    print(json.dumps(asst, indent=2))

if __name__ == "__main__":
    debug_asst()
