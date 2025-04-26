import time
from nectar.hive import Hive
from nectar.account import Account
from nectar.transactionbuilder import TransactionBuilder
from nectarbase.operations import Custom_json

# Hive + Nectar Setup
HIVE_NODES = ["https://api.hive.blog", "https://anyx.io"]
hive = Hive(node=HIVE_NODES)

RECEIVING_ACCOUNT = "peakecoin.swap"  # Your Hive account receiving Ecency Points gifts
PEK_TOKEN = "PEK"                     # Token symbol
SWAP_RATE = 0.001                     # 1 Ecency Point = 0.001 PEK

def send_pek(to_account, points_amount):
    """Send PEK tokens based on Ecency Points received."""
    pek_amount = points_amount * SWAP_RATE

    payload = {
        "contractName": "tokens",
        "contractAction": "transfer",
        "contractPayload": {
            "symbol": PEK_TOKEN,
            "to": to_account,
            "quantity": str(round(pek_amount, 8)),
            "memo": "Ecency Points Swap"
        }
    }

    tx = TransactionBuilder(blockchain_instance=hive)
    op = Custom_json(
        required_auths=[RECEIVING_ACCOUNT],
        required_posting_auths=[],
        id="ssc-mainnet-hive",
        json=payload
    )
    tx.appendOps(op)
    tx.appendSigner(RECEIVING_ACCOUNT, "active")
    tx.sign()
    tx.broadcast()

    print(f"✅ Sent {pek_amount} PEK to {to_account}")

if __name__ == "__main__":
    username = input("👤 Enter Hive username: ").strip()
    points = int(input("🎯 How many Ecency Points were gifted?: ").strip())

    send_pek(username, points)
