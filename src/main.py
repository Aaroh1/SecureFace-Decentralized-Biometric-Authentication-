import getpass
import os
import pickle
import hashlib
import numpy as np
from dotenv import load_dotenv

from face_processing import get_face_embedding, capture_image
from encryption import (
    create_encrypted_bundle,
    compute_encrypted_distance,
    decrypt_distance,
    apply_user_specific_projection,
)
from ipfs_handler import IPFSHandler
from blockchain_interaction import (
    store_ipfs_hash,
    get_ipfs_hash,
    revoke_ipfs_hash,
)

load_dotenv()
SALT = os.getenv("GLOBAL_SALT")
ipfs = IPFSHandler()

def generate_uid(pin: str, salt: str) -> str:
    return hashlib.sha256((pin + salt).encode()).hexdigest()

print("Choose an option:")
print("1. Registration")
print("2. Authentication")
print("3. Revoke Biometric Data")
choice = input("Enter 1, 2, or 3: ")

user_pin = getpass.getpass("🔐 Enter your secret PIN: ")
uid = generate_uid(user_pin, SALT)

my_account = os.getenv("MY_ACCOUNT")
my_private_key = os.getenv("MY_PRIVATE_KEY")

if choice == "1":
    print("\n🔹 Starting Registration Process...")
    try:
        existing_hash = get_ipfs_hash(uid)
        if existing_hash:
            print(f"❌ Already registered. Stored hash: {existing_hash}")
            exit(1)
    except:
        print("✅ No prior registration found. Continuing...")

    embeddings = []
    print("\n📸 Capture 5 registration images:")
    for i in range(5):
        input(f"Press Enter to capture image #{i+1}: ")
        path = capture_image()
        emb = get_face_embedding(path)
        embeddings.append(emb)

    primary = embeddings[0]
    proj_primary = apply_user_specific_projection(primary, user_pin)

    dists = []
    for other in embeddings[1:]:
        proj = apply_user_specific_projection(other, user_pin)
        dists.append(np.linalg.norm(proj_primary - proj))

    threshold = np.mean(dists) + 2 * np.std(dists)
    print(f"🚩 Chosen Threshold: {threshold:.4f}")

    bundle = create_encrypted_bundle(primary, user_pin, threshold)
    ipfs_hash = ipfs.upload_encrypted_bundle(bundle)
    store_ipfs_hash(uid, ipfs_hash, my_account, my_private_key)
    print("✅ Registration successful.")

elif choice == "2":
    print("\n🔹 Starting Authentication...")
    try:
        ipfs_hash = get_ipfs_hash(uid)
    except:
        print("❌ No biometric data found for this UID.")
        exit(1)

    bundle = ipfs.retrieve_encrypted_bundle(ipfs_hash)
    data = pickle.loads(bundle)
    threshold = data["threshold"]

    input("Press Enter to capture your face: ")
    emb = get_face_embedding(capture_image())

    enc_dist, ctx = compute_encrypted_distance(bundle, emb, user_pin)
    dist = decrypt_distance(enc_dist, ctx)

    print(f"🔹 Distance = {dist:.4f}, Threshold = {threshold:.4f}")
    print("✅ Auth Result:", "GRANTED" if dist < threshold else "DENIED")

elif choice == "3":
    print("\n⚠️ Starting Biometric Revocation...")
    try:
        ipfs_hash = get_ipfs_hash(uid)
    except:
        print("❌ No biometric data found.")
        exit(1)

    bundle = ipfs.retrieve_encrypted_bundle(ipfs_hash)
    data = pickle.loads(bundle)
    threshold = data["threshold"]

    print("📸 Capture your face for revocation verification:")
    emb = get_face_embedding(capture_image())

    enc_dist, ctx = compute_encrypted_distance(bundle, emb, user_pin)
    dist = decrypt_distance(enc_dist, ctx)

    if dist < threshold:
        confirm = input("Type 'REVOKE' to delete your biometric data: ")
        if confirm == "REVOKE":
            revoke_ipfs_hash(uid, my_account, my_private_key)
            print("✅ Biometric data successfully revoked.")
        else:
            print("❌ Revocation canceled.")
    else:
        print("❌ Verification failed. Revocation denied.")
else:
    print("❌ Invalid option.")
