"""
El Takip Web Uygulaması - MediaPipe Tasks API
Flask + MediaPipe Hands (Yeni API)
Sadece eli tespit eder, temiz ve profesyonel görünüm
"""

from flask import Flask, render_template, Response, request
import cv2
import numpy as np
import atexit
import webbrowser
import os
import time
from threading import Timer, Lock

app = Flask(__name__)

# Kamera ve Senkronizasyon
camera = None
process_lock = Lock()

# MediaPipe
hands_detector = None
mp_hands = None
mp_drawing = None

# Yüz Tanıma ve İfadeler
face_mesh = None
face_mesh_ready = False
current_face_expression = "Normal"

# Nesne Tanıma
object_detector = None
object_detector_ready = False
detected_objects_summary = []

# Kare Atlama ve Performans Önbelleği (Lag Önleme)
frame_counter = 0
cached_faces = []
cached_objects = []
cached_hands = []

# Fotoğraf Çekme
latest_photo_url = None
latest_photo_reason = None
latest_photo_timestamp = 0
last_photo_time = 0
thumbs_up_active = False
latest_processed_frame = None

# Canlı Takip İstatistikleri
live_hand_count = 0
live_total_fingers = 0
live_hand_types = "Hiçbiri"
live_face_count = 0

# Klasörü otomatik oluştur
os.makedirs("static/captured", exist_ok=True)

# Hand skeleton connections mapping
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (9, 10), (10, 11), (11, 12),
    (13, 14), (14, 15), (15, 16),
    (0, 17), (17, 18), (18, 19), (19, 20),
    (5, 9), (9, 13), (13, 17)
]

def init_mediapipe():
    """MediaPipe el, yüz ve nesne tespitini başlat"""
    global hands_detector, mp_hands, mp_drawing, face_mesh, face_mesh_ready, object_detector, object_detector_ready
    hands_ready = False
    
    # 1. El Takipçi Başlatma
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
        print("MediaPipe Hands basariyla yuklendi!")
        hands_ready = True
    except AttributeError:
        # Yeni API dene
        try:
            import mediapipe as mp
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision
            import urllib.request
            import os
            
            model_path = "hand_landmarker.task"
            if not os.path.exists(model_path):
                print("Model indiriliyor...")
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
            print("MediaPipe Tasks API yuklendi!")
            hands_ready = True
        except Exception as e2:
            print(f"Yeni API de yuklenemedi: {e2}")
    except Exception as e:
        print(f"MediaPipe yuklenemedi: {e}")
        
    # 2. Yüz Tanıma (FaceLandmarker Tasks API) Başlatma (Çoklu yüz: num_faces=4)
    try:
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision
        import urllib.request
        import os
        
        face_model_path = "face_landmarker.task"
        if not os.path.exists(face_model_path):
            print("FaceModel indiriliyor...")
            url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
            urllib.request.urlretrieve(url, face_model_path)
            
        face_base_options = python.BaseOptions(model_asset_path=face_model_path)
        face_options = vision.FaceLandmarkerOptions(
            base_options=face_base_options,
            output_face_blendshapes=True,
            output_facial_transformation_matrixes=True,
            num_faces=4,
            min_face_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        face_mesh = vision.FaceLandmarker.create_from_options(face_options)
        face_mesh_ready = True
        print("MediaPipe FaceLandmarker Tasks API basariyla yuklendi!")
    except Exception as e_face:
        print(f"FaceMesh yuklenemedi (Sadece el takibi aktif): {e_face}")
        face_mesh_ready = False
        
    # 3. Nesne Tanıma (ObjectDetector Tasks API) Başlatma
    try:
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision
        import urllib.request
        import os
        
        object_model_path = "efficientdet_lite0.tflite"
        if not os.path.exists(object_model_path):
            print("Object model indiriliyor...")
            url = "https://storage.googleapis.com/mediapipe-models/object_detector/efficientdet_lite0/int8/1/efficientdet_lite0.tflite"
            urllib.request.urlretrieve(url, object_model_path)
            
        object_base_options = python.BaseOptions(model_asset_path=object_model_path)
        object_options = vision.ObjectDetectorOptions(
            base_options=object_base_options,
            score_threshold=0.5,
            max_results=5
        )
        object_detector = vision.ObjectDetector.create_from_options(object_options)
        object_detector_ready = True
        print("MediaPipe ObjectDetector Tasks API basariyla yuklendi!")
    except Exception as e_obj:
        print(f"ObjectDetector yuklenemedi (Nesne tanima pasif): {e_obj}")
        object_detector_ready = False
        
    return hands_ready

# Başlangıçta MediaPipe'ı yükle
mediapipe_ready = init_mediapipe()

def get_camera():
    global camera
    if camera is None:
        camera = cv2.VideoCapture(0)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        if not camera.isOpened():
            print("UYARI: Kamera acilamadi! Eger WSL (Linux) terminali kullaniyorsaniz kameraya erisilemez. Lutfen VS Code terminalini PowerShell veya Command Prompt (CMD) olarak degistirin.")
    return camera

def count_fingers(landmarks, hand_type):
    """Parmak sayısını doğru hesapla"""
    if len(landmarks) < 21:
        return 0
    
    fingers_up = 0
    
    # 1. Başparmak (Thumb)
    # Ayna görüntüsünde (flip edilmiş görüntülerde):
    # Kullanıcının fiziksel SAĞ eli ekranda SAĞDADIR, başparmak sola doğru açılır (Tip X < Joint X).
    # Kullanıcının fiziksel SOL eli ekranda SOLDADIR, başparmak sağa doğru açılır (Tip X > Joint X).
    tip_x, tip_y = landmarks[4]
    mcp_x, mcp_y = landmarks[2]
    
    if hand_type == "Right":
        if tip_x < mcp_x - 10:
            fingers_up += 1
    else:  # Left
        if tip_x > mcp_x + 10:
            fingers_up += 1
            
    # 2. Diğer 4 Parmak
    tips = [8, 12, 16, 20]
    pips = [6, 10, 14, 18]
    
    for tip_idx, pip_idx in zip(tips, pips):
        if landmarks[tip_idx][1] < landmarks[pip_idx][1]:
            fingers_up += 1
            
    return fingers_up

def process_frame(frame):
    """Kareyi işle (320x180 downscaling ve kare atlama optimizasyonları ile)"""
    global current_face_expression, latest_photo_url, latest_photo_reason, latest_photo_timestamp, last_photo_time
    global detected_objects_summary, frame_counter, cached_faces, cached_objects, cached_hands
    global live_hand_count, live_total_fingers, live_hand_types, live_face_count
    
    if not mediapipe_ready or hands_detector is None:
        return frame, []
    
    h, w = frame.shape[:2]
    frame_counter += 1
    
    # Performans için görüntüyü aşırı küçült (320x180) - İşlem hızını devasa oranda artırır
    frame_small = cv2.resize(frame, (320, 180))
    rgb_small = cv2.cvtColor(frame_small, cv2.COLOR_BGR2RGB)
    
    hands = []
    
    # 1. Çoklu Yüz İfadesi Algılama (Her 4 karede bir model çalışır, diğerlerinde önbellek kullanılır)
    if face_mesh_ready and face_mesh is not None:
        if frame_counter % 4 == 0 or not cached_faces:
            try:
                import mediapipe as mp
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_small)
                face_results = face_mesh.detect(mp_image)
                
                new_cached_faces = []
                new_expression = "Normal"
                new_face_count = len(face_results.face_landmarks) if (face_results and face_results.face_landmarks) else 0
                
                if face_results.face_landmarks and face_results.face_blendshapes:
                    for face_idx, face_lm in enumerate(face_results.face_landmarks):
                        blendshapes = face_results.face_blendshapes[face_idx]
                        
                        smile_score = 0
                        jaw_open_score = 0
                        frown_score = 0
                        
                        for category in blendshapes:
                            name = category.category_name
                            score = category.score
                            if name in ["mouthSmileLeft", "mouthSmileRight"]:
                                smile_score = max(smile_score, score)
                            elif name == "jawOpen":
                                jaw_open_score = score
                            elif name in ["mouthFrownLeft", "mouthFrownRight"]:
                                frown_score = max(frown_score, score)
                                
                        if jaw_open_score > 0.4:
                            face_expr = "Saskin"
                        elif smile_score > 0.35:
                            face_expr = "Mutlu"
                        elif frown_score > 0.25:
                            face_expr = "Uzgun"
                        else:
                            face_expr = "Normal"
                            
                        if face_idx == 0:
                            new_expression = face_expr
                        
                        # Yüz alanını belirle (Orijinal boyuta scale et)
                        x_coords = [lm.x * w for lm in face_lm]
                        y_coords = [lm.y * h for lm in face_lm]
                        fx_min = max(0, int(min(x_coords)))
                        fx_max = min(w, int(max(x_coords)))
                        fy_min = max(0, int(min(y_coords)))
                        fy_max = min(h, int(max(y_coords)))
                        
                        new_cached_faces.append({
                            'bbox': (fx_min, fy_min, fx_max, fy_max),
                            'label': f"Yuz #{face_idx+1}: {face_expr}"
                        })
                        
                with process_lock:
                    cached_faces = new_cached_faces
                    current_face_expression = new_expression
                    live_face_count = new_face_count
            except Exception as e_face:
                print(f"Yuz isleme hatasi: {e_face}")
        
        # Önbellekteki yüz kutularını çiz
        for face in cached_faces:
            fx_min, fy_min, fx_max, fy_max = face['bbox']
            cv2.rectangle(frame, (fx_min, fy_min), (fx_max, fy_max), (246, 102, 122), 1)
            cv2.putText(frame, face['label'], (fx_min, fy_min - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (246, 102, 122), 2)

    # 2. El Algılama (Her 2 karede bir model çalışır, diğerlerinde önbellek kullanılır)
    if frame_counter % 2 == 0 or not cached_hands:
        new_cached_hands = []
        try:
            if mp_hands is not None:
                # Eski API
                results = hands_detector.process(rgb_small)
                
                if results.multi_hand_landmarks and results.multi_handedness:
                    for hand_lm, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                        original_type = handedness.classification[0].label
                        hand_type = "Right" if original_type == "Left" else "Left"
                        
                        x_coords = [lm.x * w for lm in hand_lm.landmark]
                        y_coords = [lm.y * h for lm in hand_lm.landmark]
                        
                        x_min = max(0, int(min(x_coords)) - 20)
                        x_max = min(w, int(max(x_coords)) + 20)
                        y_min = max(0, int(min(y_coords)) - 20)
                        y_max = min(h, int(max(y_coords)) + 20)
                        
                        landmarks_px = [(int(lm.x * w), int(lm.y * h)) for lm in hand_lm.landmark]
                        fingers = count_fingers(landmarks_px, hand_type)
                        
                        new_cached_hands.append({
                            'bbox': (x_min, y_min, x_max - x_min, y_max - y_min),
                            'fingers': fingers,
                            'type': hand_type,
                            'landmarks_px': landmarks_px
                        })
            else:
                # Yeni Tasks API
                import mediapipe as mp
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_small)
                results = hands_detector.detect(mp_image)
                
                if results.hand_landmarks:
                    for idx, hand_lm in enumerate(results.hand_landmarks):
                        original_type = results.handedness[idx][0].category_name if results.handedness else "Left"
                        hand_type = "Right" if original_type == "Left" else "Left"
                        
                        x_coords = [lm.x * w for lm in hand_lm]
                        y_coords = [lm.y * h for lm in hand_lm]
                        
                        x_min = max(0, int(min(x_coords)) - 20)
                        x_max = min(w, int(max(x_coords)) + 20)
                        y_min = max(0, int(min(y_coords)) - 20)
                        y_max = min(h, int(max(y_coords)) + 20)
                        
                        landmarks_px = [(int(lm.x * w), int(lm.y * h)) for lm in hand_lm]
                        fingers = count_fingers(landmarks_px, hand_type)
                        
                        new_cached_hands.append({
                            'bbox': (x_min, y_min, x_max - x_min, y_max - y_min),
                            'fingers': fingers,
                            'type': hand_type,
                            'landmarks_px': landmarks_px
                        })
            with process_lock:
                cached_hands = new_cached_hands
        except Exception as e:
            print(f"El isleme hatasi: {e}")
            
    hands = cached_hands

    # 3. Nesne Algılama (Her 8 karede bir model çalışır, diğerlerinde önbellek kullanılır)
    if object_detector_ready and object_detector is not None:
        if frame_counter % 8 == 0 or not cached_objects:
            try:
                import mediapipe as mp
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_small)
                obj_results = object_detector.detect(mp_image)
                
                new_cached_objects = []
                new_objects_summary = []
                
                if obj_results.detections:
                    for detection in obj_results.detections:
                        category = detection.categories[0]
                        label = category.category_name
                        score = category.score
                        
                        if score < 0.5:
                            continue
                            
                        # Bounding box (320x180 modeline göre döndüğü için 1280x720'ye scale et)
                        bbox = detection.bounding_box
                        scale_x = w / 320.0
                        scale_y = h / 180.0
                        ox = int(bbox.origin_x * scale_x)
                        oy = int(bbox.origin_y * scale_y)
                        ow = int(bbox.width * scale_x)
                        oh = int(bbox.height * scale_y)
                        
                        new_cached_objects.append({
                            'bbox': (ox, oy, ox + ow, oy + oh),
                            'label': f"{label} ({int(score * 100)}%)"
                        })
                        new_objects_summary.append(label)
                        
                with process_lock:
                    cached_objects = new_cached_objects
                    detected_objects_summary = new_objects_summary
            except Exception as e_obj:
                print(f"Nesne isleme hatasi: {e_obj}")
        
        # Önbellekteki nesne kutularını çiz
        for obj in cached_objects:
            ox1, oy1, ox2, oy2 = obj['bbox']
            cv2.rectangle(frame, (ox1, oy1), (ox2, oy2), (255, 150, 50), 2)
            cv2.putText(frame, obj['label'], (ox1, oy1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 150, 50), 2)
            
    # 4. Başparmak Yukarı (👍) Zamanlayıcı Tetikleme Kontrolü
    # Parmak sayma fonksiyonu başparmağı saymadığı için thumbs-up yapıldığında fingers 0 döner.
    is_thumbs_up = False
    for hand in hands:
        if hand['fingers'] == 0:
            landmarks = hand['landmarks_px']
            if len(landmarks) >= 21:
                # Başparmak ucu (4) Y koordinatı, MCP (2) Y koordinatından daha yukarıda (küçük) olmalı
                thumb_up = landmarks[4][1] < landmarks[2][1]
                if thumb_up:
                    is_thumbs_up = True
                    break
                    
    with process_lock:
        global thumbs_up_active, live_hand_count, live_total_fingers, live_hand_types
        thumbs_up_active = is_thumbs_up
        live_hand_count = len(hands)
        live_total_fingers = sum(h['fingers'] for h in hands)
        if len(hands) == 1:
            live_hand_types = "Sağ El" if hands[0]['type'] == 'Right' else "Sol El"
        elif len(hands) == 2:
            live_hand_types = "Sağ ve Sol El"
        else:
            live_hand_types = "Hiçbiri"
        
    return frame, hands

def draw_hands(frame, hands):
    """Elleri ciz"""
    for hand in hands:
        x, y, w, h = hand['bbox']
        fingers = hand['fingers']
        # Kullanicinin bakis acisindan el tipi
        hand_type = "Sag" if hand['type'] == "Right" else "Sol"
        
        # Dikdörtgen (lila)
        cv2.rectangle(frame, (x, y), (x+w, y+h), (246, 160, 180), 2)
        
        # Eklem ve kemikleri çiz
        if 'landmarks_px' in hand:
            px = hand['landmarks_px']
            for connection in HAND_CONNECTIONS:
                start_idx, end_idx = connection
                if start_idx < len(px) and end_idx < len(px):
                    cv2.line(frame, px[start_idx], px[end_idx], (255, 255, 255), 2)
            for pt in px:
                cv2.circle(frame, pt, 5, (246, 102, 122), -1)
                cv2.circle(frame, pt, 6, (220, 80, 100), 1)
        
        # Üst etiket (lila zemin, beyaz yazı)
        label = f"{hand_type} El"
        label_y = max(y, 30)
        cv2.rectangle(frame, (x, label_y-30), (x + 80, label_y), (246, 102, 122), -1)
        cv2.putText(frame, label, (x+5, label_y-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        # Alt etiket (koyu slate zemin, lila yazı)
        finger_text = f"{fingers} Parmak"
        label_bottom_y = y + h if y + h + 25 < frame.shape[0] else y + h - 25
        cv2.rectangle(frame, (x, label_bottom_y), (x + 90, label_bottom_y+25), (90, 80, 110), -1)
        cv2.putText(frame, finger_text, (x+5, label_bottom_y+18),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (246, 160, 180), 2)
    
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
        
        # Bilgi paneli (Beyaz zemin, lila çerçeve)
        cv2.rectangle(frame, (10, 10), (180, 70), (255, 255, 255), -1)
        cv2.rectangle(frame, (10, 10), (180, 70), (246, 102, 122), 2)
        
        hand_count = len(hands)
        total_fingers = sum(h['fingers'] for h in hands)
        
        cv2.putText(frame, f"El: {hand_count}", (20, 35),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (246, 102, 122), 2)
        cv2.putText(frame, f"Parmak: {total_fingers}", (20, 55),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (120, 110, 130), 1)
        
        global latest_processed_frame
        with process_lock:
            latest_processed_frame = frame.copy()
        
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
    return {
        'status': 'active',
        'mediapipe_ready': mediapipe_ready,
        'latest_photo': latest_photo_url,
        'latest_photo_reason': latest_photo_reason,
        'latest_photo_timestamp': latest_photo_timestamp,
        'face_expression': current_face_expression,
        'detected_objects': detected_objects_summary,
        'thumbs_up_detected': thumbs_up_active,
        'hand_count': live_hand_count,
        'total_fingers': live_total_fingers,
        'hand_types': live_hand_types,
        'face_count': live_face_count
    }

@app.route('/capture_now', methods=['POST'])
def capture_now():
    global latest_photo_url, latest_photo_reason, latest_photo_timestamp, last_photo_time, latest_processed_frame
    with process_lock:
        if latest_processed_frame is not None:
            photo_filename = f"photo_{int(time.time())}.jpg"
            photo_path = os.path.join("static/captured", photo_filename)
            cv2.imwrite(photo_path, latest_processed_frame)
            
            latest_photo_url = f"/static/captured/{photo_filename}"
            latest_photo_reason = "Zamanlayıcı"
            latest_photo_timestamp = int(time.time() * 1000)
            last_photo_time = time.time()
            
            return {
                'status': 'success',
                'url': latest_photo_url,
                'filename': photo_filename,
                'reason': latest_photo_reason,
                'timestamp': latest_photo_timestamp
            }
    return {'status': 'error', 'message': 'Kamera karesi hazır değil'}, 500

@app.route('/delete_photo/<filename>', methods=['POST'])
def delete_photo(filename):
    global latest_photo_url
    if ".." in filename or "/" in filename or "\\" in filename:
        return {'status': 'error', 'message': 'Gecersiz dosya adi'}, 400
        
    photo_path = os.path.join("static/captured", filename)
    if os.path.exists(photo_path):
        try:
            os.remove(photo_path)
            if latest_photo_url and filename in latest_photo_url:
                latest_photo_url = None
            return {'status': 'success', 'message': 'Fotoğraf başarıyla silindi'}
        except Exception as e:
            return {'status': 'error', 'message': f'Silme hatasi: {str(e)}'}, 500
    return {'status': 'error', 'message': 'Dosya bulunamadi'}, 404

@app.route('/delete_photos_batch', methods=['POST'])
def delete_photos_batch():
    global latest_photo_url
    data = request.json
    filenames = data.get('filenames', [])
    
    if not filenames:
        return {'status': 'error', 'message': 'Silinecek dosya secilmedi'}, 400
        
    deleted_count = 0
    errors = []
    
    for filename in filenames:
        if ".." in filename or "/" in filename or "\\" in filename:
            errors.append(f"{filename}: Gecersiz dosya adi")
            continue
            
        photo_path = os.path.join("static/captured", filename)
        if os.path.exists(photo_path):
            try:
                os.remove(photo_path)
                deleted_count += 1
                if latest_photo_url and filename in latest_photo_url:
                    latest_photo_url = None
            except Exception as e:
                errors.append(f"{filename}: {str(e)}")
        else:
            errors.append(f"{filename}: Dosya bulunamadi")
            
    if errors and deleted_count == 0:
        return {'status': 'error', 'message': '; '.join(errors)}, 500
        
    return {
        'status': 'success', 
        'message': f'{deleted_count} fotograf silindi',
        'errors': errors
    }

@app.route('/apply_filter_to_photo', methods=['POST'])
def apply_filter_to_photo():
    data = request.json
    filename = data.get('filename')
    filter_type = data.get('filter_type')
    
    if not filename or not filter_type:
        return {'status': 'error', 'message': 'Gecersiz parametreler'}, 400
        
    if ".." in filename or "/" in filename or "\\" in filename:
        return {'status': 'error', 'message': 'Guvenlik ihlali'}, 400
        
    photo_path = os.path.join("static/captured", filename)
    if os.path.exists(photo_path):
        try:
            import numpy as np
            img = cv2.imread(photo_path)
            if img is None:
                return {'status': 'error', 'message': 'Resim dosyasi okunamadi'}, 500
                
            if filter_type == 'grayscale':
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            elif filter_type == 'sepia':
                kernel = np.array([[0.272, 0.534, 0.131],
                                   [0.349, 0.686, 0.168],
                                   [0.393, 0.769, 0.189]])
                img = cv2.transform(img, kernel)
            elif filter_type == 'invert':
                img = cv2.bitwise_not(img)
            elif filter_type == 'blur':
                img = cv2.GaussianBlur(img, (15, 15), 0)
            elif filter_type == 'warm':
                img = np.array(img, dtype=np.float32)
                img[:, :, 2] = np.clip(img[:, :, 2] * 1.18, 0, 255) # Red
                img[:, :, 0] = np.clip(img[:, :, 0] * 0.88, 0, 255) # Blue
                img = np.array(img, dtype=np.uint8)
            elif filter_type == 'cool':
                img = np.array(img, dtype=np.float32)
                img[:, :, 0] = np.clip(img[:, :, 0] * 1.22, 0, 255) # Blue
                img[:, :, 2] = np.clip(img[:, :, 2] * 0.82, 0, 255) # Red
                img = np.array(img, dtype=np.uint8)
                
            cv2.imwrite(photo_path, img)
            return {'status': 'success', 'message': 'Efekt basariyla uygulandi'}
        except Exception as e:
            return {'status': 'error', 'message': f'Filtre uygulama hatasi: {str(e)}'}, 500
            
    return {'status': 'error', 'message': 'Dosya bulunamadi'}, 404

@app.route('/list_photos')
def list_photos():
    folder = "static/captured"
    if not os.path.exists(folder):
        return {'photos': []}
    files = [f for f in os.listdir(folder) if f.endswith('.jpg')]
    files.sort(key=lambda x: os.path.getmtime(os.path.join(folder, x)), reverse=True)
    photos = []
    for f in files:
        photos.append({
            'url': f'/static/captured/{f}',
            'filename': f,
            'timestamp': int(os.path.getmtime(os.path.join(folder, f)) * 1000)
        })
    return {'photos': photos}

def cleanup():
    global camera
    if camera is not None:
        camera.release()
        print("Kamera serbest birakildi.")

atexit.register(cleanup)

def open_browser():
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == '__main__':
    print("El Takip Sistemi")
    print("Adres: http://127.0.0.1:5000")
    print(f"MediaPipe: {'Aktif' if mediapipe_ready else 'Pasif'}")
    
    # Flask debug modunda yeniden yuklemede tarayicinin iki kez acilmasini engeller
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        Timer(1.5, open_browser).start()
        
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False, threaded=True)
