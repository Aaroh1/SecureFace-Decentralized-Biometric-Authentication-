from web3 import Web3
import json
import os
import sys  # Added for better error handling
from dotenv import load_dotenv
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    contract_path = os.path.join(script_dir, "../build/contracts/BiometricStorage.json")
    with open(contract_path, "r") as contract_file:
        contract_build = json.load(contract_file)
except FileNotFoundError:
    sys.exit("Error: BiometricStorage.json file not found. Ensure the file exists at the specified path.")

load_dotenv()
url = os.getenv("WEB3_URL")
web3 = Web3(Web3.HTTPProvider(url))

if not web3.is_connected():
    sys.exit("Error: Failed to connect to Ethereum. Ensure the Sepolia testnet endpoint and credentials are correct.")

abi = contract_build['abi']
contract_address = contract_build['networks']['11155111']['address']
contract = web3.eth.contract(address=contract_address, abi=abi)

def store_ipfs_hash(uid, ipfs_hash, account, private_key):
    tx = contract.functions.storeIPFSHash(uid, ipfs_hash).build_transaction({
        'from': account,
        'nonce': web3.eth.get_transaction_count(account),
        'gas': 2000000,
        'gasPrice': web3.to_wei('20', 'gwei')
    })
    signed_tx = web3.eth.account.sign_transaction(tx, private_key)
    web3.eth.send_raw_transaction(signed_tx.raw_transaction)

def update_ipfs_hash(uid, new_ipfs_hash, account, private_key):
    tx = contract.functions.updateIPFSHash(uid, new_ipfs_hash).build_transaction({
        'from': account,
        'nonce': web3.eth.get_transaction_count(account),
        'gas': 2000000,
        'gasPrice': web3.to_wei('20', 'gwei')
    })
    signed_tx = web3.eth.account.sign_transaction(tx, private_key)
    web3.eth.send_raw_transaction(signed_tx.raw_transaction)

def revoke_ipfs_hash(uid, account, private_key):
    tx = contract.functions.revokeIPFSHash(uid).build_transaction({
        'from': account,
        'nonce': web3.eth.get_transaction_count(account),
        'gas': 2000000,
        'gasPrice': web3.to_wei('20', 'gwei')
    })
    signed_tx = web3.eth.account.sign_transaction(tx, private_key)
    web3.eth.send_raw_transaction(signed_tx.raw_transaction)

def get_ipfs_hash(uid):
    return contract.functions.getIPFSHash(uid).call()