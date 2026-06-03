import json
import time
import random
from web3 import Web3

# ---------- CONFIG ----------
CONTRACT_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3"
HARDHAT_NODE_URL = "http://127.0.0.1:8545"

# Hardhat default account #2 (oracle) private key
ORACLE_PRIVATE_KEY = "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a"

# ---------- SETUP ----------
w3 = Web3(Web3.HTTPProvider(HARDHAT_NODE_URL))
assert w3.is_connected(), "Cannot connect to Hardhat node"

# Load ABI from compiled contract artifact
import os
artifact_path = os.path.join(
    os.path.dirname(__file__),
    "..",
    "artifacts",
    "contracts",
    "ColdChainEscrow.sol",
    "ColdChainEscrow.json"
)
with open(artifact_path) as f:
    contract_json = json.load(f)
abi = contract_json["abi"]

contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)

# Oracle account
oracle_account = w3.eth.account.from_key(ORACLE_PRIVATE_KEY)

# Hardhat default accounts (pre-funded)
buyer = w3.eth.accounts[0]
seller = w3.eth.accounts[1]

print("Oracle address:", oracle_account.address)
print("Buyer address:", buyer)
print("Seller address:", seller)

# ---------- START TRIP ----------
tx_hash = contract.functions.startTrip().transact({
    'from': buyer,
    'value': w3.to_wei(1, 'ether')
})
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print("Trip started. Tx hash:", receipt.transactionHash.hex())

# ---------- SIMULATE 10 TEMP READINGS ----------
print("\nSimulating temperature readings...")
for i in range(10):
    # Introduce a breach at reading 7 (index 6)
    if i == 6:
        temp = random.choice([0, 1, 9, 10])  # out of safe range 2-8
    else:
        temp = random.randint(2, 8)

    # Build and send transaction from oracle
    nonce = w3.eth.get_transaction_count(oracle_account.address)
    tx = contract.functions.recordTemperature(temp).build_transaction({
        'from': oracle_account.address,
        'nonce': nonce,
        'gas': 200000,
        'gasPrice': w3.to_wei('20', 'gwei')
    })
    signed = w3.eth.account.sign_transaction(tx, ORACLE_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"  Recorded temp: {temp}°C")
    time.sleep(3)   # simulate real-time intervals

# ---------- END TRIP ----------
print("\nEnding trip...")
nonce = w3.eth.get_transaction_count(oracle_account.address)
tx = contract.functions.endTrip().build_transaction({
    'from': oracle_account.address,
    'nonce': nonce,
    'gas': 200000,
    'gasPrice': w3.to_wei('20', 'gwei')
})
signed = w3.eth.account.sign_transaction(tx, ORACLE_PRIVATE_KEY)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
w3.eth.wait_for_transaction_receipt(tx_hash)

# Check final state
state = contract.functions.state().call()
if state == 2:  # Completed
    if contract.functions.tempBreached().call():
        print("Result: Temperature breach detected → Payment REFUNDED to buyer.")
    else:
        print("Result: All temps safe → Payment RELEASED to seller.")
print("Done.")