import getpass
import pickle
import numpy as np
import os
from dotenv import load_dotenv
from face_processing import get_face_embedding, capture_image
from encryption import (
    create_encrypted_bundle,
    compute_encrypted_distance,
    decrypt_distance,
    apply_user_specific_projection
)
from ipfs_handler import IPFSHandler
from blockchain_interaction import store_ipfs_hash, get_ipfs_hash, revoke_ipfs_hash


ipfs = IPFSHandler()

print("Choose an option:")
print("1. Registration")
print("2. Authentication")
print("3. Revoke Biometric Data")
choice = input("Enter 1, 2, or 3: ")

email = input("Enter Email: ")



load_dotenv()

my_account = os.getenv("MY_ACCOUNT")
my_private_key = os.getenv("MY_PRIVATE_KEY")


if choice == "1":
    print("\n🔹 Starting Registration Process...")
    try:
        existing_ipfs_hash = get_ipfs_hash(email)
        if existing_ipfs_hash:
            print(f"❌ Registration already exists for {email}. Please try again with a different email.")
            print(f"🔹 Stored IPFS hash: {existing_ipfs_hash}")
            exit(1)
    except:
        print("🔹 No existing registration found. Proceeding...")

    image_path = capture_image()
    if image_path is None:
        print("❌ Image capture failed. Exiting...")
        exit(1)

    print(f"✅ Captured Image: {image_path}")
    user_seed = getpass.getpass("🔐 Set your secret PIN (for cancellable biometrics): ")

    num_samples = 5  # Number of samples clearly
    embeddings = []

    print("\n📸 Please capture multiple images for registration and threshold determination:")
    for i in range(num_samples):
        input(f"\nPress Enter to capture registration image #{i+1}: ")
        image_path = capture_image()
        embedding = get_face_embedding(image_path)
        embeddings.append(embedding)
        print(f"✅ Image #{i+1} captured and embedding extracted.")

    # Primary embedding is the first one
    primary_embedding = embeddings[0]

    # Apply user-specific projection before distance calculation (Corrected!)
    projected_primary_embedding = apply_user_specific_projection(primary_embedding, user_seed)

    distances = []
    for idx, calib_embedding in enumerate(embeddings[1:], start=2):
        projected_calib_embedding = apply_user_specific_projection(calib_embedding, user_seed)
        distance = np.linalg.norm(projected_primary_embedding - projected_calib_embedding)
        distances.append(distance)
        print(f"🔹 Distance (image 1 ↔ image {idx}): {distance:.4f}")

    # Robust threshold calculation clearly:
    mean_distance = np.mean(distances)
    std_distance = np.std(distances)
    optimal_threshold = mean_distance + (2 * std_distance)

    print("\n📊 Threshold Calculation clearly (after projection):")
    print(f"✅ Mean Distance: {mean_distance:.4f}")
    print(f"✅ Standard Deviation: {std_distance:.4f}")
    print(f"🚩 Chosen Threshold (mean + 2×std): {optimal_threshold:.4f}")

    # After threshold determination, create encrypted bundle
    encrypted_bundle = create_encrypted_bundle(primary_embedding, user_seed, optimal_threshold)

    # Upload to IPFS and store IPFS hash on blockchain
    ipfs_hash = ipfs.upload_encrypted_bundle(encrypted_bundle)
    store_ipfs_hash(email, ipfs_hash, my_account, my_private_key)

    print(f"✅ Registration Complete for {email}")

elif choice == "2":
    print("\n🔹 Starting Authentication Process...")
    user_seed = getpass.getpass("🔐 Enter your secret PIN: ")

    ipfs_hash = get_ipfs_hash(email)

    encrypted_bundle = ipfs.retrieve_encrypted_bundle(ipfs_hash)
    data = pickle.loads(encrypted_bundle)
    AUTH_THRESHOLD = data["threshold"]

    input("\nPress Enter to capture image for authentication: ")
    image_path = capture_image()
    embedding = get_face_embedding(image_path)

    encrypted_dist, context = compute_encrypted_distance(encrypted_bundle, embedding, user_seed)
    decrypted_dist = decrypt_distance(encrypted_dist, context)

    result = decrypted_dist < AUTH_THRESHOLD

    print(f"🔹 Computed Distance: {decrypted_dist:.4f}")
    print(f"🔹 Threshold: {AUTH_THRESHOLD:.4f}")
    print("✅ Authentication:", "GRANTED" if result else "DENIED")
elif choice == "3":
    print("\n⚠️ Biometric Data Revocation ⚠️")
    try:
        ipfs_hash = get_ipfs_hash(email)
    except:
        print("❌ No biometric data found for given email.")
        exit(1)
    # Ask for user PIN first clearly for verification
    user_seed = getpass.getpass("🔐 Enter your secret PIN for verification: ")

    # Fetch stored bundle and threshold
    

    encrypted_bundle = ipfs.retrieve_encrypted_bundle(ipfs_hash)
    data = pickle.loads(encrypted_bundle)
    threshold = data["threshold"]

    # Perform biometric verification
    print("📸 Please capture your image for verification clearly:")
    embedding = get_face_embedding(capture_image())
    encrypted_dist, context = compute_encrypted_distance(encrypted_bundle, embedding, user_seed)
    decrypted_dist = decrypt_distance(encrypted_dist, context)

    if decrypted_dist < threshold:
        confirm = input("Type 'REVOKE' to confirm deletion of biometric data: ")
        if confirm == "REVOKE":
            revoke_ipfs_hash(email, my_account, my_private_key)
            print(f"✅ Biometric data successfully revoked for {email}.")
        else:
            print("❌ Revocation canceled by user.")
    else:
        print("❌ Verification failed. Revocation denied.")

else:
    print("❌ Invalid choice. Please enter 1, 2, or 3.")