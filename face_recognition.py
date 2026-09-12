"""
Face Recognition Module
Uses MediaPipe for face detection and simple recognition
"""

import mediapipe as mp
import cv2
import numpy as np
from pathlib import Path
import pickle
from datetime import datetime

class FaceRecognizer:
    """Simple face detection and tracking using MediaPipe"""
    
    def __init__(self):
        # Initialize MediaPipe Face Detection
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=0, min_detection_confidence=0.5
        )
        
        # Load pre-trained face data if exists
        self.known_faces = {}
        self.face_data_path = Path(__file__).parent / "face_data.pkl"
        self.load_face_data()
        
        self.camera = None
        self.running = False
        print("Face recognition initialized with MediaPipe")
    
    def load_face_data(self):
        """Load known face data from file"""
        try:
            if self.face_data_path.exists():
                with open(self.face_data_path, 'rb') as f:
                    self.known_faces = pickle.load(f)
                print(f"Loaded {len(self.known_faces)} known faces")
        except Exception as e:
            print(f"Could not load face data: {e}")
            self.known_faces = {}
    
    def save_face_data(self):
        """Save known face data to file"""
        try:
            with open(self.face_data_path, 'wb') as f:
                pickle.dump(self.known_faces, f)
            print(f"Saved {len(self.known_faces)} known faces")
        except Exception as e:
            print(f"Could not save face data: {e}")
    
    def detect_faces(self, frame):
        """Detect faces in a frame using MediaPipe"""
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(rgb_frame)
        
        faces = []
        if results.detections:
            for detection in results.detections:
                # Get bounding box
                bbox = detection.location_data.relative_bounding_box
                h, w, _ = frame.shape
                y_min = int(bbox.ymin * h)
                x_min = int(bbox.xmin * w)
                y_max = int(bbox.ymax * h)
                x_max = int(bbox.xmax * w)
                faces.append((x_min, y_min, x_max - x_min, y_max - y_min))
        
        return faces
    
    def enroll_face(self, name, num_samples=20):
        """Enroll a new face by capturing samples"""
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return "Could not open camera"
        
        face_samples = []
        collected = 0
        
        print(f"Enrolling face for '{name}'...")
        print(f"Collecting {num_samples} samples. Press 'q' to cancel.")
        
        while collected < num_samples:
            ret, frame = cap.read()
            if not ret:
                break
            
            faces = self.detect_faces(frame)
            
            for (x, y, w, h) in faces:
                # Extract face region
                face_region = frame[y:y+h, x:x+w]
                face_rgb = cv2.cvtColor(face_region, cv2.COLOR_BGR2RGB)
                face_samples.append(face_rgb)
                collected += 1
                
                # Draw rectangle around face
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, f"Sample {collected}/{num_samples}", (x, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            cv2.imshow('Face Enrollment', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cap.release()
                cv2.destroyAllWindows()
                return "Enrollment cancelled"
        
        cap.release()
        cv2.destroyAllWindows()
        
        if len(face_samples) > 0:
            # Save face samples
            self.known_faces[name] = face_samples
            self.save_face_data()
            return f"Successfully enrolled face for '{name}' with {len(face_samples)} samples"
        else:
            return "No faces detected during enrollment"
    
    def recognize_face(self, frame):
        """Recognize faces in frame (simple matching)"""
        faces = self.detect_faces(frame)
        
        if len(faces) == 0:
            return None, "No face detected"
        
        if len(self.known_faces) == 0:
            return None, "No enrolled faces"
        
        recognized_names = []
        
        for (x, y, w, h) in faces:
            # Extract face region
            face_region = frame[y:y+h, x:x+w]
            face_rgb = cv2.cvtColor(face_region, cv2.COLOR_BGR2RGB)
            
            # Resize to standard size for comparison
            face_resized = cv2.resize(face_rgb, (100, 100))
            
            # Simple matching with known faces
            best_match = None
            best_score = float('inf')
            
            for name, samples in self.known_faces.items():
                for sample in samples:
                    sample_resized = cv2.resize(sample, (100, 100))
                    # Calculate similarity using mean squared error
                    score = np.mean((face_resized - sample_resized) ** 2)
                    
                    if score < best_score:
                        best_score = score
                        best_match = name
            
            # Threshold for recognition
            if best_score < 5000:  # Threshold value
                recognized_names.append(best_match)
            else:
                recognized_names.append("Unknown")
        
        if recognized_names:
            # Return most common recognition
            from collections import Counter
            most_common = Counter(recognized_names).most_common(1)[0]
            return faces, most_common
        else:
            return faces, "Unknown"
    
    def start_face_detection(self, callback=None):
        """Start continuous face detection"""
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            return "Could not open camera"
        
        self.running = True
        
        print("Starting face detection. Press 'q' to stop.")
        
        while self.running:
            ret, frame = self.camera.read()
            if not ret:
                break
            
            faces, recognized = self.recognize_face(frame)
            
            # Draw rectangles and names
            for (x, y, w, h) in faces:
                color = (0, 255, 0) if recognized != "Unknown" else (0, 0, 255)
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                cv2.putText(frame, recognized, (x, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            cv2.imshow('Face Detection', frame)
            
            if callback:
                callback(recognized)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.running = False
                break
        
        self.camera.release()
        cv2.destroyAllWindows()
        return "Face detection stopped"
    
    def stop_face_detection(self):
        """Stop face detection"""
        self.running = False
    
    def capture_and_recognize(self):
        """Capture single frame and recognize face"""
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return None, "Could not open camera"
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return None, "Could not capture frame"
        
        faces, recognized = self.recognize_face(frame)
        
        return recognized if faces else None
    
    def list_enrolled_faces(self):
        """List all enrolled faces"""
        return list(self.known_faces.keys())
    
    def remove_face(self, name):
        """Remove an enrolled face"""
        if name in self.known_faces:
            del self.known_faces[name]
            self.save_face_data()
            return f"Removed face for '{name}'"
        else:
            return f"Face '{name}' not found"