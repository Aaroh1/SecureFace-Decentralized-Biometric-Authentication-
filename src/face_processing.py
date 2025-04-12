import cv2
import torch
import numpy as np
from facenet_pytorch import InceptionResnetV1, MTCNN
import logging

IMG_SIZE = 160
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load models
facenet = InceptionResnetV1(pretrained='vggface2').eval().to(device)
mtcnn = MTCNN(image_size=IMG_SIZE, margin=20, device=device)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FaceProcessing")


def capture_image():
    """Captures an image from the webcam and saves it as 'captured_image.jpg'."""
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Use DirectShow backend for Windows
    if not cap.isOpened():
        raise ValueError("❌ Webcam not detected!")

    print("📸 Press SPACE to capture your image")

    while True:
        ret, frame = cap.read()  # Capture frame-by-frame
        if not ret:
            continue

        cv2.imshow("Capture Image (Press SPACE)", frame)

        key = cv2.waitKey(1) & 0xFF  # Ensure compatibility
        if key == 32:  # SPACE key to capture
            cv2.imwrite("captured_image.jpg", frame)
            break
        elif key == 27:  # ESC to cancel
            print("❌ Capture canceled.")
            cap.release()
            cv2.destroyAllWindows()
            return None
    
    cap.release()
    cv2.destroyAllWindows()
    return "captured_image.jpg"

def get_face_embedding(image_path):
    """Extracts face embedding from an image captured via webcam."""
    try:
        img = cv2.cvtColor(cv2.imread(image_path), cv2.COLOR_BGR2RGB)
        if img is None:
            raise ValueError("❌ Image capture failed")

        face = mtcnn(img)
        if face is None:
            raise ValueError("❌ No face detected")

        with torch.no_grad():
            embedding = facenet(face.unsqueeze(0).to(device))
            return embedding.cpu().numpy().flatten()  # Return 1D NumPy array
    except Exception as e:
        logger.error(f"❌ Face processing failed: {str(e)}")
        raise
