import tenseal as ts
import numpy as np
import pickle
import hashlib
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from dotenv import load_dotenv

load_dotenv()

SCALE_FACTOR = int(os.getenv("SCALE_FACTOR"))
POLY_DEGREE = int(os.getenv("POLY_DEGREE"))
PRIME_MODULUS = int(os.getenv("PRIME_MODULUS"))
EMBEDDING_SIZE = int(os.getenv("EMBEDDING_SIZE"))


def hash_seed(user_seed):
    return hashlib.sha256(user_seed.encode()).digest()

def aes_encrypt(key, data):
    iv = os.urandom(12)
    cipher = Cipher(algorithms.AES(key[:32]), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(data) + encryptor.finalize()
    return iv + encryptor.tag + ciphertext

def aes_decrypt(key, encrypted_data):
    iv = encrypted_data[:12]
    tag = encrypted_data[12:28]
    ciphertext = encrypted_data[28:]
    cipher = Cipher(algorithms.AES(key[:32]), modes.GCM(iv, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(ciphertext) + decryptor.finalize()

def create_initial_context():
    context = ts.context(ts.SCHEME_TYPE.BFV, POLY_DEGREE, PRIME_MODULUS)
    context.generate_galois_keys()
    return context

def serialize_context_with_secret(context):
    return context.serialize(save_secret_key=True)

def load_context(serialized_context):
    return ts.context_from(serialized_context)

def generate_projection_matrix(seed_hash):
    np.random.seed(int.from_bytes(seed_hash[:4], 'big'))
    proj_matrix = np.random.randn(EMBEDDING_SIZE, EMBEDDING_SIZE)
    
    norm_factor = np.linalg.norm(proj_matrix)
    proj_matrix /= norm_factor  

    return proj_matrix

def apply_user_specific_projection(embedding, user_seed):
    user_seed_hash = hash_seed(user_seed)
    user_projection_matrix = generate_projection_matrix(user_seed_hash)
    return embedding @ user_projection_matrix

def create_encrypted_bundle(embedding, user_seed, threshold):
    seed_hash = hash_seed(user_seed)

    context = create_initial_context()
    serialized_context = serialize_context_with_secret(context)
    encrypted_serialized_context = aes_encrypt(seed_hash, serialized_context)

    final_embedding = apply_user_specific_projection(embedding, user_seed)
    scaled_embedding = (final_embedding * SCALE_FACTOR).astype(np.int64)

    encrypted_embedding = ts.bfv_vector(context, scaled_embedding).serialize()

    bundled_data = pickle.dumps({
        "encrypted_embedding": encrypted_embedding,
        "encrypted_context": encrypted_serialized_context,
        "threshold": threshold  
    })

    return bundled_data


def compute_encrypted_distance(bundled_data, new_embedding, user_seed):
    seed_hash = hash_seed(user_seed)

    data = pickle.loads(bundled_data)
    encrypted_serialized_context = data["encrypted_context"]
    serialized_embedding = data["encrypted_embedding"]

    serialized_context = aes_decrypt(seed_hash, encrypted_serialized_context)
    context = load_context(serialized_context)

    stored_embedding = ts.bfv_vector_from(context, serialized_embedding)

    final_embedding = apply_user_specific_projection(new_embedding, user_seed)
    scaled_embedding = (final_embedding * SCALE_FACTOR).astype(np.int64)
    encrypted_new_embedding = ts.bfv_vector(context, scaled_embedding)

    diff = stored_embedding - encrypted_new_embedding
    squared_diff = diff * diff
    encrypted_distance = squared_diff.sum()
    return encrypted_distance, context

def decrypt_distance(encrypted_distance, context):
    raw_dist = encrypted_distance.decrypt(context.secret_key())
    if isinstance(raw_dist, list):
        raw_dist = raw_dist[0]
    if raw_dist < 0:
        raw_dist += PRIME_MODULUS    
    distance = np.sqrt(abs(raw_dist)) / SCALE_FACTOR
    return distance
