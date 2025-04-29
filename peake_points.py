import time
import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from nectar.hive import Hive
from nectar.account import Account
from nectar.transactionbuilder import TransactionBuilder
from nectarbase.operations import Custom_json

# ---- CONFIG ---- #

HIVE_NODES = ["https://api.hive.blog", "https://anyx.io"]
HIVE_ACCOUNT = "peakecoin.bnb"
ACTIVE_KEY = "your_active_key_here"  # <-- INSERT YOUR ACTIVE KEY HERE
PEK_TOKEN = "PEK"
SWAP_RATE = 0.001

ECENCY_POINTS_URL = "https://ecency.com/@peakecoin.bnb/points"
CHECK_INTERVAL = 60  # seconds between page checks

# ---- SETUP ---- #

# Setup Hive connection
hive = Hive(node=HIVE_NODES, keys=[ACTIVE_KEY])
account = Account(HIVE_ACCOUNT, blockchain_instance=hive)

# Setup Headless Chromium on Raspberry Pi
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--window-size=1920x1080")

chromedriver_path = "/usr/lib/chromium-browser/chromedriver"
driver = webdriver.Chrome(service=Service(chromedriver_path), options=chrome_options)

# Ensure swap log exists
LOG_FILE = "swap_log.csv"
try:
    with open(LOG_FILE, "x", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "username", "points", "pek_sent"])
except FileExistsError:
    pass  # File already exists

# Load processed usernames to avoid double swaps
processed = set()
with open(LOG_FILE, newline="") as f:
    reader = csv.reader(f)
    next(reader, None)  # skip header
    for row in reader:
        if len(row) > 1:
            processed.add(row[1])

# ---- FUNCTIONS ---- #

def send_pek(to_account, points_amount):
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
        required_auths=[HIVE_ACCOUNT],
        required_posting_auths=[],
        id="ssc-mainnet-hive",
        json=payload
    )
    tx.appendOps(op)
    tx.appendSigner(HIVE_ACCOUNT, "active")
    tx.sign()
    tx.broadcast()

    print(f"✅ Sent {pek_amount} {PEK_TOKEN} to {to_account}")
    return pek_amount

def monitor_swaps():
    print("🚀 Starting Ecency Points Swap Bot...")
    while True:
        try:
            driver.get(ECENCY_POINTS_URL)
            time.sleep(5)  # let the page load

            notifications = driver.find_elements(By.CLASS_NAME, "items-center")

            for note in notifications:
                text = note.text.lower()
                if "points" in text and "peakecoin transfer" in text:
                    # Extract username and points
                    try:
                        parts = text.split(" ")
                        from_index = parts.index("from")
                        username = parts[from_index + 1].lstrip("@").strip()
                        points = int([p for p in parts if p.isdigit()][0])

                        if username not in processed:
                            print(f"🔍 Swap found: {username} sent {points} Points")
                            pek_sent = send_pek(username, points)

                            with open(LOG_FILE, "a", newline="") as f:
                                writer = csv.writer(f)
                                writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), username, points, pek_sent])

                            processed.add(username)

                    except Exception as e:
                        print(f"⚠️ Error parsing notification: {e}")

        except Exception as e:
            print(f"❌ Error during page check: {e}")

        time.sleep(CHECK_INTERVAL)

# ---- RUN ---- #

if __name__ == "__main__":
    monitor_swaps()
