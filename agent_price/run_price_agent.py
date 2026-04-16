import os
from datetime import datetime
from subprocess import run

def main():
    print("[PRICE AGENT] Preparing training data...")
    run(["python", "/opt/project/agent_price/prepare_training_data.py"], check=True)

    print("[PRICE AGENT] Training model...")
    run(["python", "/opt/project/agent_price/train_price_model.py"], check=True)

    print("[PRICE AGENT] Done.")
    print(f"[PRICE AGENT] Finished at {datetime.utcnow().isoformat()}")

if __name__ == "__main__":
    main()