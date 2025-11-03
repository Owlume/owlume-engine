import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.feedback_bridge import FeedbackBridge

b = FeedbackBridge()
print(f"[BRIDGE] applied={b.run_once()}")


