import sys, os
# Add the project root (one level up from /scripts) to Python's import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.empathy_learner import EmpathyLearner

if __name__ == "__main__":
    el = EmpathyLearner(weights_path="data/weights/empathy_weights.json")

    # pretend these are the available moves for this context
    candidates = ["E_VALIDATE", "E_REFRAME", "E_PACE"]

    picked = el.recommend_top_k(
        mode="Reflective",
        principle="Assumption",
        candidate_moves=candidates,
        k=2,
        strategy="softmax",
        temp=0.7
    )
    print("[recommend]", picked)

    # simulate a session with positive clarity gain
    upd = el.update(
        did="DID-TEST-0001",
        mode="Reflective",
        principle="Assumption",
        move_ids=picked,
        delta=0.32,
        intensity=0.8,
        resonance=0.8,
        helpfulness=0.6
    )
    print("[update]", upd)
    print("OK ✓")
