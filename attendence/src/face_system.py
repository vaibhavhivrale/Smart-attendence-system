import os
import cv2
import pickle
import numpy as np
import time

from config import DATA_DIR, MODELS_DIR, CAMERA_INDICES, FACE_TOLERANCE, TRAINING_SAMPLES
from src.logger import get_logger

log = get_logger("face_system")

TRAINER_FILE = os.path.join(MODELS_DIR, 'trainer.yml')
LABEL_MAP_FILE = os.path.join(MODELS_DIR, 'label_map.pkl')

def get_camera(indices=None):
    """Try to open camera using multiple indices. Return first successful cap or None."""
    if indices is None:
        indices = CAMERA_INDICES
    for index in indices:
        log.debug("Attempting to open webcam at index %d...", index)
        cap = cv2.VideoCapture(index)
        if cap is not None and cap.isOpened():
            log.info("Webcam index %d successfully opened.", index)
            return cap
        if cap is not None:
            cap.release()
    log.error("Failed to open any webcam index from %s.", indices)
    return None

def capture_training_images(student_id, name, num_samples=None):
    if num_samples is None:
        num_samples = TRAINING_SAMPLES
    user_dir = os.path.join(DATA_DIR, str(student_id))
    os.makedirs(user_dir, exist_ok=True)
    
    cap = get_camera()
    if cap is None:
        yield "Error: Cannot open webcam. Please check permissions or other apps using it."
        return

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    count = 0
    yield f"Starting camera... Please look at the camera."
    time.sleep(2)
    
    while count < num_samples:
        ret, frame = cap.read()
        if not ret:
            log.error("Failed to grab frame during capture for %s.", student_id)
            yield "Error: Failed to grab frame."
            break
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        for (x, y, w, h) in faces:
            count += 1
            filename = os.path.join(user_dir, f"{count}.jpg")
            cv2.imwrite(filename, gray[y:y+h, x:x+w])
            
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            log.debug("Captured face sample %d/%d for %s", count, num_samples, student_id)
            break
            
        yield frame 
        time.sleep(0.1) 
        
    cap.release()
    log.info("Finished capturing %d images for %s (%s).", count, name, student_id)
    yield f"Completed! Captured {count} images."

def generate_encodings():
    log.info("Generating encodings (LBPH Training)...")
    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
    except AttributeError:
        log.error("cv2.face not available. Install opencv-contrib-python.")
        return False, "cv2.face not available. Please install opencv-contrib-python."
        
    faces = []
    labels = []
    label_map = {}  # int_id: student_id_str
    current_id = 0
    
    for student_id in os.listdir(DATA_DIR):
        user_dir = os.path.join(DATA_DIR, student_id)
        if not os.path.isdir(user_dir):
            continue
        
        label_map[current_id] = student_id
        
        for image_name in os.listdir(user_dir):
            if not image_name.endswith('.jpg'):
                continue
            image_path = os.path.join(user_dir, image_name)
            gray_img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            
            if gray_img is not None:
                faces.append(gray_img)
                labels.append(current_id)
            else:
                log.warning("Could not read image %s", image_path)
            
        current_id += 1
                
    if len(faces) == 0:
        log.error("No face data available to train.")
        return False, "No data available to train."
        
    recognizer.train(faces, np.array(labels))
    recognizer.save(TRAINER_FILE)
    log.info("Successfully trained %d face samples across %d users.", len(faces), len(label_map))
    
    with open(LABEL_MAP_FILE, 'wb') as f:
        pickle.dump(label_map, f)
        
    return True, f"Trained {len(faces)} face samples successfully."

def load_encodings():
    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
    except AttributeError:
        return None, {}
        
    if os.path.exists(TRAINER_FILE) and os.path.exists(LABEL_MAP_FILE):
        recognizer.read(TRAINER_FILE)
        with open(LABEL_MAP_FILE, 'rb') as f:
            label_map = pickle.load(f)
        log.info("Loaded encodings with %d user templates.", len(label_map))
        return recognizer, label_map
    else:
        log.debug("No existing Trainer/Label Map found.")
    return None, {}

def recognize_faces(frame, recognizer, label_map, tolerance=None):
    if tolerance is None:
        tolerance = FACE_TOLERANCE
    if recognizer is None:
        return frame, []
        
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(100, 100))
    
    detected_students = []
    
    for (x, y, w, h) in faces:
        roi_gray = gray[y:y+h, x:x+w]
        id_, distance = recognizer.predict(roi_gray)
        log.debug("Face at (%d,%d): ID=%d, dist=%.2f (threshold=%d)", x, y, id_, distance, tolerance)
        
        if distance < tolerance:
            student_id = label_map.get(id_, "Unknown")
            if student_id != "Unknown":
                detected_students.append(student_id)
                confidence_str = f"  {round(100 - distance)}%"
                log.debug("Match: %s (%.0f%% confidence)", student_id, 100 - distance)
            else:
                confidence_str = ""
        else:
            student_id = "Unknown"
            confidence_str = ""
            
        color = (0, 255, 0) if student_id != "Unknown" else (0, 0, 255)
        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
        
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, str(student_id) + confidence_str, (x + 5, y - 5), font, 0.8, color, 1)

    return frame, detected_students
