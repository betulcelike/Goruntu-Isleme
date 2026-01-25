"""
El Takip Web Uygulaması - MediaPipe Tasks API
Flask + MediaPipe Hands (Yeni API)
Sadece eli tespit eder, temiz ve profesyonel görünüm
"""

from flask import Flask, render_template, Response
import cv2
import numpy as np

app = Flask(__name__)

# Kamera
camera = None

# MediaPipe Hands
hands_detector = None
mp_hands = None
mp_drawing = None

def init_mediapipe():
    """MediaPipe el tespitini başlat"""
    global hands_detector, mp_hands, mp_drawing
    try:
        import mediapipe as mp
        mp_hands = mp.solutions.hands
        mp_drawing = mp.solutions.drawing_utils
        hands_detector = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        print("✅ MediaPipe Hands başarıyla yüklendi!")
        return True
    except AttributeError:
        # Yeni API dene
        try:
            import mediapipe as mp
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision
            
            # Model dosyasını indir
            import urllib.request
            import os
            
            model_path = "hand_landmarker.task"
            if not os.path.exists(model_path):
                print("📥 Model indiriliyor...")
                url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
                urllib.request.urlretrieve(url, model_path)
            
            base_options = python.BaseOptions(model_asset_path=model_path)
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                num_hands=2,
                min_hand_detection_confidence=0.7,
                min_tracking_confidence=0.5
            )
            hands_detector = vision.HandLandmarker.create_from_options(options)
            print("✅ MediaPipe Tasks API yüklendi!")
            return True
        except Exception as e2:
            print(f"❌ Yeni API de yüklenemedi: {e2}")
            return False
    except Exception as e:
        print(f"❌ MediaPipe yüklenemedi: {e}")
        return False

# Başlangıçta MediaPipe'ı yükle
mediapipe_ready = init_mediapipe()

def get_camera():
    global camera
    if camera is None:
        camera = cv2.VideoCapture(0)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    return camera

def count_fingers(hand_landmarks, w, h, hand_type):
    """Parmak sayısını hesapla - geliştirilmiş algoritma"""
    if hand_landmarks is None:
        return 0
    
    # Landmark koordinatları
    landmarks = []
    for lm in hand_landmarks.landmark:
        landmarks.append((lm.x * w, lm.y * h))
    
    # Parmak uçları ve MCP (orta eklem) noktaları
    tips = [4, 8, 12, 16, 20]  # Parmak uçları
    pip = [2, 6, 10, 14, 18]   # PIP/MCP eklemleri
    
    fingers_up = 0
    
    # Başparmak - ayna efekti nedeniyle sol el için ters kontrol
    # Görüntü flip edildiği için Right aslında Left olarak görünüyor
    if hand_type == "Right":  # Görüntüde sağda = gerçekte sol el
        if landmarks[tips[0]][0] > landmarks[pip[0]][0]:
            fingers_up += 1
    else:  # Left - görüntüde solda = gerçekte sağ el
        if landmarks[tips[0]][0] < landmarks[pip[0]][0]:
            fingers_up += 1
    
    # Diğer 4 parmak - uç, MCP'den yukarıda mı?
    for i in range(1, 5):
        # Parmak ucu, PIP ekleminden yukarıda ise parmak açık
        if landmarks[tips[i]][1] < landmarks[pip[i]][1]:
            fingers_up += 1
    
    return fingers_up

def process_frame(frame):
    """Kareyi işle"""
    if not mediapipe_ready or hands_detector is None:
        return frame, []
    
    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    hands = []
    
    try:
        if mp_hands is not None:
            # Eski API
            results = hands_detector.process(rgb)
            
            if results.multi_hand_landmarks and results.multi_handedness:
                for hand_lm, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                    # Ayna goruntusu: kullanicinin SAG eli ekranda SOLDA gorunur
                    # MediaPipe ekrandaki konuma gore soylediginden ters ceviriyoruz
                    original_type = handedness.classification[0].label
                    # Kullanicinin gercek eli: MediaPipe Left diyorsa -> kullanici Sag eli
                    hand_type = "Right" if original_type == "Left" else "Left"
                    
                    # Bounding box
                    x_coords = [lm.x * w for lm in hand_lm.landmark]
                    y_coords = [lm.y * h for lm in hand_lm.landmark]
                    
                    x_min = max(0, int(min(x_coords)) - 20)
                    x_max = min(w, int(max(x_coords)) + 20)
                    y_min = max(0, int(min(y_coords)) - 20)
                    y_max = min(h, int(max(y_coords)) + 20)
                    
                    fingers = count_fingers(hand_lm, w, h, original_type)
                    
                    hands.append({
                        'bbox': (x_min, y_min, x_max - x_min, y_max - y_min),
                        'fingers': fingers,
                        'type': hand_type,
                        'landmarks': hand_lm
                    })
        else:
            # Yeni Tasks API
            import mediapipe as mp
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            results = hands_detector.detect(mp_image)
            
            if results.hand_landmarks:
                for idx, hand_lm in enumerate(results.hand_landmarks):
                    hand_type = results.handedness[idx][0].category_name if results.handedness else "Unknown"
                    
                    x_coords = [lm.x * w for lm in hand_lm]
                    y_coords = [lm.y * h for lm in hand_lm]
                    
                    x_min = max(0, int(min(x_coords)) - 20)
                    x_max = min(w, int(max(x_coords)) + 20)
                    y_min = max(0, int(min(y_coords)) - 20)
                    y_max = min(h, int(max(y_coords)) + 20)
                    
                    # Basit parmak sayımı
                    tips = [4, 8, 12, 16, 20]
                    pip = [3, 6, 10, 14, 18]
                    fingers = 0
                    if hand_lm[tips[0]].x < hand_lm[pip[0]].x:
                        fingers += 1
                    for i in range(1, 5):
                        if hand_lm[tips[i]].y < hand_lm[pip[i]].y:
                            fingers += 1
                    
                    hands.append({
                        'bbox': (x_min, y_min, x_max - x_min, y_max - y_min),
                        'fingers': fingers,
                        'type': hand_type
                    })
    except Exception as e:
        print(f"İşleme hatası: {e}")
    
    return frame, hands

def draw_hands(frame, hands):
    """Elleri ciz"""
    for hand in hands:
        x, y, w, h = hand['bbox']
        fingers = hand['fingers']
        # Kullanicinin bakis acisindan el tipi
        hand_type = "Sag" if hand['type'] == "Right" else "Sol"
        
        # Dikdörtgen
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 180), 3)
        
        # Üst etiket
        label = f"{hand_type} El"
        cv2.rectangle(frame, (x, y-30), (x + 80, y), (0, 255, 180), -1)
        cv2.putText(frame, label, (x+5, y-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        
        # Alt etiket
        finger_text = f"{fingers} Parmak"
        cv2.rectangle(frame, (x, y+h), (x + 90, y+h+25), (40, 40, 40), -1)
        cv2.putText(frame, finger_text, (x+5, y+h+18),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 180), 2)
    
    return frame

def generate_frames():
    cam = get_camera()
    
    while True:
        success, frame = cam.read()
        if not success:
            break
        
        frame = cv2.flip(frame, 1)
        frame, hands = process_frame(frame)
        frame = draw_hands(frame, hands)
        
        # Bilgi paneli
        cv2.rectangle(frame, (10, 10), (180, 70), (20, 20, 20), -1)
        cv2.rectangle(frame, (10, 10), (180, 70), (0, 255, 180), 2)
        
        hand_count = len(hands)
        total_fingers = sum(h['fingers'] for h in hands)
        
        cv2.putText(frame, f"El: {hand_count}", (20, 35),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 180), 2)
        cv2.putText(frame, f"Parmak: {total_fingers}", (20, 55),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stats')
def stats():
    return {'status': 'active', 'mediapipe_ready': mediapipe_ready}

if __name__ == '__main__':
    print("🖐️ El Takip Sistemi")
    print("📍 http://127.0.0.1:5000")
    print(f"{'✅' if mediapipe_ready else '❌'} MediaPipe: {'Aktif' if mediapipe_ready else 'Pasif'}")
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
