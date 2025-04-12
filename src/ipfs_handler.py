import requests

IPFS_API_URL = "http://127.0.0.1:5001/api/v0"

class IPFSHandler:
    def __init__(self):
        """Check if IPFS daemon is running."""
        try:
            res = requests.post(f"{IPFS_API_URL}/id")
            if res.status_code == 200:
                print("✅ Connected to IPFS")
            else:
                raise ConnectionError("❌ Failed to connect to IPFS")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"❌ IPFS daemon not running: {e}")

    def upload_encrypted_bundle(self, encrypted_data, filename="encrypted_embedding.enc"):
        """Uploads an encrypted file (embedding) to IPFS."""
        with open(filename, "wb") as f:
            f.write(encrypted_data)  # Save encrypted data
        with open(filename, "rb") as f:
            files = {"file": f}
            res = requests.post(f"{IPFS_API_URL}/add", files=files)
            if res.status_code == 200:
                ipfs_hash = res.json()["Hash"]
                print(f"✅ Encrypted embedding stored on IPFS: {ipfs_hash}")
                return ipfs_hash
            else:
                raise Exception("❌ Failed to upload embedding to IPFS")

    def retrieve_encrypted_bundle(self, ipfs_hash, output_path="retrieved_encrypted_embedding.enc"):
        """Retrieves an encrypted file from IPFS."""
        print(f"🔹 Fetching IPFS hash from local node: {ipfs_hash}")
        url = f"http://127.0.0.1:8080/ipfs/{ipfs_hash}"
        res = requests.get(url, stream=True)  
        
        if res.status_code == 200:
            with open(output_path, "wb") as f:
                for chunk in res.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"✅ File retrieved from Local IPFS and saved as: {output_path}")
            with open(output_path, "rb") as f:
                return f.read()  # Return serialized encrypted embedding
        else:
            print(f"❌ Failed to retrieve from Local IPFS: {res.status_code} - {res.text}")
            raise Exception("❌ Failed to retrieve encrypted embedding from IPFS")
