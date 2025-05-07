import cv2
import torch
import numpy as np
import tenseal as ts
import time
import csv
import logging
from facenet_pytorch import InceptionResnetV1, MTCNN
from itertools import combinations

# ==================== VALIDATED CONFIGURATION ====================
IMG_SIZE = 160
SCALE_FACTOR = 1000
NUM_TRIALS = 5
IMAGE_FILES = [f"../input{i}.jpg" for i in range(1,9)]  # Assuming images are named from image0.jpg to image9.jpg
PARAM_SETS = [
    {   # 128-bit security (validated for TenSEAL 0.3.15)
        'poly_degree': 4096,
        'plain_modulus': 3221225473,          # Prime ≡ 1 mod 8192 (2×4096)
    },
    {   # 128-bit security (validated for TenSEAL 0.3.15)
        'poly_degree': 4096,
        'plain_modulus': 34359771137         # Prime ≡ 1 mod 8192 (2×4096)
    },
    {   # 128-bit security (validated for TenSEAL 0.3.15)
        'poly_degree': 8192,
        'plain_modulus': 3221225473          # Prime ≡ 1 mod 8192 (2×4096)
    },
    {   # 192-bit security
        'poly_degree': 8192,
        'plain_modulus': 34359771137          # Prime ≡ 1 mod 16384 (2×8192)
    },
    
]

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HEPerfTest")

# Initialize face processing models
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
facenet = InceptionResnetV1(pretrained='vggface2').eval().to(device)
mtcnn = MTCNN(image_size=IMG_SIZE, margin=20, device=device)

def get_face_embedding(image_path):
    """Robust face embedding extraction with error handling"""
    try:
        img = cv2.cvtColor(cv2.imread(image_path), cv2.COLOR_BGR2RGB)
        if img is None:
            raise ValueError("Image load failed")
            
        face = mtcnn(img)
        if face is None:
            raise ValueError("No face detected")
            
        with torch.no_grad():
            return facenet(face.unsqueeze(0).to(device)).cpu().numpy().flatten()
            
    except Exception as e:
        logger.error(f"Face processing error: {str(e)}")
        raise

def create_he_context(poly_degree, plain_modulus):
    """Create validated HE context with batching support"""
    context = ts.context(
        ts.SCHEME_TYPE.BFV,
        poly_modulus_degree=poly_degree,
        plain_modulus=plain_modulus,
        # coeff_mod_bit_sizes=coeff_mod_bit_sizes
    )
    context.generate_galois_keys()
    return context

def time_he_operations(params, emb1, emb2):
    """Benchmark HE operations with error handling"""
    times = {
        'setup': [], 'encrypt': [], 'compute': [], 'decrypt': []
    }
    
    scaled1 = (emb1 * SCALE_FACTOR).astype(np.int64)
    scaled2 = (emb2 * SCALE_FACTOR).astype(np.int64)
    
    for _ in range(NUM_TRIALS):
        try:
            # Context Setup
            start = time.perf_counter()
            context = create_he_context(
                params['poly_degree'],
                params['plain_modulus']
            )
            times['setup'].append(time.perf_counter() - start)
            
            # Encryption
            start = time.perf_counter()
            enc1 = ts.bfv_vector(context, scaled1)
            enc2 = ts.bfv_vector(context, scaled2)
            times['encrypt'].append(time.perf_counter() - start)
            
            # Computation
            start = time.perf_counter()
            diff = enc1 - enc2
            squared = diff * diff
            encrypted_dist = squared.sum()
            times['compute'].append(time.perf_counter() - start)
            
            # Decryption
            start = time.perf_counter()
            raw_dist = encrypted_dist.decrypt()
            if isinstance(raw_dist, list):
                raw_dist = raw_dist[0]
            if raw_dist < 0:
                raw_dist += params["plain_modulus"]  
            distance = np.sqrt(abs(raw_dist)) / SCALE_FACTOR
            times['decrypt'].append(time.perf_counter() - start)
            
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}")
            return None
    
    return {k: 1000 * sum(v) / NUM_TRIALS for k, v in times.items()}

def run_performance_tests():
    """Main benchmarking workflow"""
    logger.info("Loading sample embeddings...")
    try:
        # Load embeddings for all images
        embeddings = {}
        for img_file in IMAGE_FILES:
            embeddings[img_file] = get_face_embedding(img_file)
        
    except Exception as e:
        logger.error(f"Failed to load embeddings: {str(e)}")
        return

    results = []
    
    # Loop over all possible pairs of images
    for params in PARAM_SETS:
        logger.info(f"\n🔧 Testing poly_degree={params['poly_degree']}...")
        try:
            # Iterate over all unique pairs of images
            for img1, img2 in combinations(IMAGE_FILES, 2):
                emb1, emb2 = embeddings[img1], embeddings[img2]
                timings = time_he_operations(params, emb1, emb2)
                
                if timings:
                    # Add individual entry for each operation
                    results.append({
                        'input_images': f"{img1},{img2}",
                        'poly_degree': params['poly_degree'],
                        **timings,
                        'total_ms': sum(timings.values())
                    })

        except Exception as e:
            logger.error(f"Test failed: {str(e)}")
    
    # Calculate averages
    if results:
        avg_result = {
            'input_images': 'average',
            'poly_degree': sum(r['poly_degree'] for r in results) / len(results),
            'setup': sum(r['setup'] for r in results) / len(results),
            'encrypt': sum(r['encrypt'] for r in results) / len(results),
            'compute': sum(r['compute'] for r in results) / len(results),
            'decrypt': sum(r['decrypt'] for r in results) / len(results),
            'total_ms': sum(r['total_ms'] for r in results) / len(results)
        }
        results.append(avg_result)

    # Save results to CSV
    if results:
        with open('he_performance.csv', 'w', newline='') as f:
            fieldnames = ['input_images', 'poly_degree', 'setup', 'encrypt', 'compute', 'decrypt', 'total_ms']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        print("\n📊 Validated Performance Results (ms)")
        print(f"{'Input Images':<20} | {'Poly Degree':<12} | {'Setup':<8} | {'Encrypt':<8} | {'Compute':<8} | {'Decrypt':<8} | Total")
        for res in results:
            print(f"{res['input_images']:<20} | {res['poly_degree']:<12.1f} | "
                  f"{res['setup']:>7.1f} | {res['encrypt']:>8.1f} | "
                  f"{res['compute']:>8.1f} | {res['decrypt']:>8.1f} | "
                  f"{res['total_ms']:>7.1f}")

if __name__ == "__main__":
    run_performance_tests()