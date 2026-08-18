"""
GestureFlow AI — Vision Intelligence Studio
Yüksek Performansli, Çok İş Parçacikli (Multi-Threaded) ve Düşük Gecikmeli Kamera & AI Motoru
"""

from flask import Flask, render_template, Response, request
import cv2
import numpy as np
import atexit
import webbrowser
import os
import time
import threading
from threading import Timer, Lock

app = Flask(__name__)

# Senkronizasyon ve Kilitler
process_lock = Lock()

# MediaPipe Dedektörleri
hands_detector = None
mp_hands = None
mp_drawing = None

# Yüz Tanıma ve İfadeler
face_mesh = None
face_mesh_ready = False
current_face_expression = "Normal"

# Jest ve Zoom Değişkenleri
hand_x_history = []
swipe_event = None
swipe_time = 0.0
zoom_factor = 1.0
pinch_active = False
initial_pinch_dist = None
base_zoom_factor = 1.0
thumbs_up_counter = 0

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

# Hava Tuvali (Air Canvas) Durum Değişkenleri
air_canvas_enabled = False
drawing_canvas = None
active_brush_color = (255, 132, 10)  # BGR olarak Tech Blue (#0a84ff)
active_brush_size = 6
last_pointer_pos = {}
smoothed_pointer_pos = {}
live_canvas_gesture = "Standby"

# Önbellek Verileri
cached_faces = []
cached_hands = []

# Klasörü otomatik oluştur
os.makedirs("static/captured", exist_ok=True)

# El İskelet Bağlantıları
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (9, 10), (10, 11), (11, 12),
    (13, 14), (14, 15), (15, 16),
    (0, 17), (17, 18), (18, 19), (19, 20),
    (5, 9), (9, 13), (13, 17)
]

def init_mediapipe():
    """MediaPipe el, yüz ve nesne modellerini başlat"""
    global hands_detector, mp_hands, mp_drawing, face_mesh, face_mesh_ready
    hands_ready = False
    
    # 1. El Takipçi
    try:
        import mediapipe as mp
        mp_hands = mp.solutions.hands
        mp_drawing = mp.solutions.drawing_utils
        hands_detector = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.5
        )
        print("MediaPipe Hands basariyla yuklendi!")
        hands_ready = True
    except Exception:
        try:
            import mediapipe as mp
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision
            
            base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                num_hands=2,
                min_hand_detection_confidence=0.6,
                min_tracking_confidence=0.5
            )
            hands_detector = vision.HandLandmarker.create_from_options(options)
            print("MediaPipe Tasks HandLandmarker API basariyla yuklendi!")
            hands_ready = True
        except Exception as e_tasks:
            print(f"MediaPipe Hands yuklenemedi: {e_tasks}")
            hands_ready = False

    # 2. Yüz Mesh & Mimik Analizi
    try:
        import mediapipe as mp
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision
        
        face_options = vision.FaceLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path='face_landmarker.task'),
            output_face_blendshapes=True,
            output_facial_transformation_matrixes=False,
            num_faces=2
        )
        face_mesh = vision.FaceLandmarker.create_from_options(face_options)
        face_mesh_ready = True
        print("MediaPipe FaceLandmarker basariyla yuklendi!")
    except Exception as e_face:
        print(f"FaceLandmarker yuklenemedi: {e_face}")
        face_mesh_ready = False

    return hands_ready

mediapipe_ready = init_mediapipe()

# ---------------------------------------------------------------
# 1. Asenkron & Sıfır Gecikmeli Kamera Akış Sınıfı (Threading)
# ---------------------------------------------------------------
class FastCameraStream:
    """Arka planda bağımsız çalışan, tampon gecikmesi (lag) yapmayan kamera iş parçacığı"""
    def __init__(self, src=0):
        # Windows için DirectShow (DSHOW) hızlı başlatma ve anlık erişim sağlar
        if os.name == 'nt':
            self.stream = cv2.VideoCapture(src, cv2.CAP_DSHOW)
        else:
            self.stream = cv2.VideoCapture(src)
            
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.stream.set(cv2.CAP_PROP_FPS, 30)
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1) # Tampon birikmesini önle (0ms lag)
        
        self.grabbed, self.frame = self.stream.read()
        self.started = False
        self.read_lock = Lock()
        self.stopped = False

    def start(self):
        if self.started:
            return self
        self.started = True
        self.thread = threading.Thread(target=self.update, daemon=True)
        self.thread.start()
        return self

    def update(self):
        while not self.stopped:
            grabbed, frame = self.stream.read()
            if not grabbed:
                time.sleep(0.01)
                continue
            with self.read_lock:
                self.grabbed = grabbed
                self.frame = frame
            time.sleep(0.005) # Aşırı CPU yükünü önlemek için mikro bekleme

    def read(self):
        with self.read_lock:
            if self.frame is not None:
                return self.grabbed, self.frame.copy()
            return False, None

    def stop(self):
        self.stopped = True
        if self.stream.isOpened():
            self.stream.release()

camera_stream = None

def get_camera_stream():
    global camera_stream
    if camera_stream is None:
        camera_stream = FastCameraStream(0).start()
    return camera_stream

def count_fingers(landmarks, hand_type):
    """Parmak sayısını hesapla"""
    if len(landmarks) < 21:
        return 0
    fingers_up = 0
    tip_x, tip_y = landmarks[4]
    mcp_x, mcp_y = landmarks[2]
    
    if hand_type == "Right":
        if tip_x < mcp_x - 10:
            fingers_up += 1
    else:
        if tip_x > mcp_x + 10:
            fingers_up += 1
            
    tips = [8, 12, 16, 20]
    pips = [6, 10, 14, 18]
    for tip_idx, pip_idx in zip(tips, pips):
        if landmarks[tip_idx][1] < landmarks[pip_idx][1]:
            fingers_up += 1
            
    return fingers_up


def get_finger_states(landmarks, hand_type):
    """
    Kullanıcının elindeki parmakların açık (True) veya kapalı (False) durumlarını döner.
    Dönen liste sırasıyla: [Başparmak, İşaret, Orta, Yüzük, Serçe]
    """
    if len(landmarks) < 21:
        return [False, False, False, False, False]
        
    finger_states = [False] * 5
    
    # 1. Başparmak (Thumb)
    # Sağ ve sol el yönelimine göre yatay pozisyon kontrolü
    tip_x, tip_y = landmarks[4]
    mcp_x, mcp_y = landmarks[2]
    if hand_type == "Right":
        if tip_x < mcp_x - 10:
            finger_states[0] = True
    else:
        if tip_x > mcp_x + 10:
            finger_states[0] = True
            
    # 2. Diğer parmaklar (İşaret, Orta, Yüzük, Serçe)
    # Uç noktasının (tip) eklem noktasından (pip) daha yukarıda (y değerinin küçük olması) kontrolü
    tips = [8, 12, 16, 20]
    pips = [6, 10, 14, 18]
    for i, (tip_idx, pip_idx) in enumerate(zip(tips, pips)):
        if landmarks[tip_idx][1] < landmarks[pip_idx][1]:
            finger_states[i + 1] = True
            
    return finger_states


def get_canvas_gesture(finger_states):
    """
    Parmak durumlarına göre tuval jestini sınıflandırır.
    Geri dönüş değeri: 'pen', 'laser', 'eraser' veya 'idle'
    """
    thumb, index, middle, ring, pinky = finger_states
    
    # Kalem: İşaret parmağı açık; başparmak da dahil diğerleri kapalı
    if index and not thumb and not middle and not ring and not pinky:
        return "pen"
    # Lazer İşaretçi: İşaret ve orta parmak açık; başparmak ve diğerleri kapalı
    elif index and middle and not thumb and not ring and not pinky:
        return "laser"
    # Silgi: İşaret, orta, yüzük ve serçe parmakların hepsi açık
    elif index and middle and ring and pinky:
        return "eraser"
    else:
        return "idle"


# ---------------------------------------------------------------
# 2. Asenkron Arka Plan AI Çıkarım Motoru (Inference Worker)
# ---------------------------------------------------------------
class AsyncAIWorker:
    """Yapay zeka modellerini video akışını hiç duraksatmadan arka planda çalıştıran iş parçacığı"""
    def __init__(self):
        self.latest_frame = None
        self.lock = Lock()
        self.stopped = False
        self.frame_count = 0
        self.thread = threading.Thread(target=self.loop, daemon=True)

    def start(self):
        self.thread.start()
        return self

    def feed_frame(self, frame):
        with self.lock:
            self.latest_frame = frame

    def loop(self):
        global current_face_expression, cached_faces, cached_hands
        global live_hand_count, live_total_fingers, live_hand_types, live_face_count
        global thumbs_up_active, hand_x_history, swipe_event, swipe_time, zoom_factor
        global pinch_active, initial_pinch_dist, base_zoom_factor, thumbs_up_counter
        
        while not self.stopped:
            frame_to_process = None
            with self.lock:
                if self.latest_frame is not None:
                    frame_to_process = self.latest_frame
                    self.latest_frame = None

            if frame_to_process is None:
                time.sleep(0.008)
                continue

            self.frame_count += 1
            h, w = frame_to_process.shape[:2]
            
            # AI için optimize edilmiş ultra-hafif boyut (256x144)
            frame_small = cv2.resize(frame_to_process, (256, 144))
            rgb_small = cv2.cvtColor(frame_small, cv2.COLOR_BGR2RGB)

            # 1. Yüz ve Mimik Analizi
            if face_mesh_ready and face_mesh is not None and self.frame_count % 2 == 0:
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
                            
                            x_coords = [lm.x * w for lm in face_lm]
                            y_coords = [lm.y * h for lm in face_lm]
                            fx_min = max(0, int(min(x_coords)))
                            fx_max = min(w, int(max(x_coords)))
                            fy_min = max(0, int(min(y_coords)))
                            fy_max = min(h, int(max(y_coords)))
                            
                            new_cached_faces.append({
                                'bbox': (fx_min, fy_min, fx_max, fy_max),
                                'label': f"Yuz: {face_expr}"
                            })
                            
                    with process_lock:
                        cached_faces = new_cached_faces
                        current_face_expression = new_expression
                        live_face_count = new_face_count
                except Exception as e_face:
                    if "shutdown" not in str(e_face).lower():
                        pass

            # 2. El ve Parmak Takibi
            new_cached_hands = []
            try:
                if mp_hands is not None:
                    results = hands_detector.process(rgb_small)
                    if results.multi_hand_landmarks and results.multi_handedness:
                        for hand_lm, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                            original_type = handedness.classification[0].label
                            hand_type = "Right" if original_type == "Left" else "Left"
                            
                            x_coords = [lm.x * w for lm in hand_lm.landmark]
                            y_coords = [lm.y * h for lm in hand_lm.landmark]
                            x_min = max(0, int(min(x_coords)) - 15)
                            x_max = min(w, int(max(x_coords)) + 15)
                            y_min = max(0, int(min(y_coords)) - 15)
                            y_max = min(h, int(max(y_coords)) + 15)
                            
                            landmarks_px = [(int(lm.x * w), int(lm.y * h)) for lm in hand_lm.landmark]
                            fingers = count_fingers(landmarks_px, hand_type)
                            
                            new_cached_hands.append({
                                'bbox': (x_min, y_min, x_max - x_min, y_max - y_min),
                                'fingers': fingers,
                                'type': hand_type,
                                'landmarks_px': landmarks_px
                            })
                elif hands_detector is not None:
                    import mediapipe as mp
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_small)
                    results = hands_detector.detect(mp_image)
                    if results.hand_landmarks:
                        for idx, hand_lm in enumerate(results.hand_landmarks):
                            original_type = results.handedness[idx][0].category_name if results.handedness else "Left"
                            hand_type = "Right" if original_type == "Left" else "Left"
                            
                            x_coords = [lm.x * w for lm in hand_lm]
                            y_coords = [lm.y * h for lm in hand_lm]
                            x_min = max(0, int(min(x_coords)) - 15)
                            x_max = min(w, int(max(x_coords)) + 15)
                            y_min = max(0, int(min(y_coords)) - 15)
                            y_max = min(h, int(max(y_coords)) + 15)
                            
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
            except Exception:
                pass
            is_thumbs_up = False
            for hand in new_cached_hands:
                if hand['fingers'] == 0:
                    landmarks = hand['landmarks_px']
                    if len(landmarks) >= 21:
                        if landmarks[4][1] < landmarks[2][1]:
                            is_thumbs_up = True
                            break
                            
            if is_thumbs_up:
                thumbs_up_counter += 1
            else:
                thumbs_up_counter = 0
                
            current_time = time.time()
            if swipe_event and current_time - swipe_time > 1.5:
                swipe_event = None
                
            if new_cached_hands:
                hand = new_cached_hands[0]
                landmarks = hand.get('landmarks_px', [])
                hand_type = hand.get('type', 'Right')
                
                # 1. Sezgisel Pinch-to-Zoom Kontrolü
                if air_canvas_enabled:
                    pinch_active = False
                    initial_pinch_dist = None
                    if zoom_factor > 1.01:
                        zoom_factor = float(zoom_factor * 0.90 + 1.0 * 0.10)
                    else:
                        zoom_factor = 1.0
                else:
                    if len(landmarks) >= 21:
                        finger_states = get_finger_states(landmarks, hand_type)
                        thumb, index, middle, ring, pinky = finger_states
                        is_pinch = thumb and index and not middle and not ring and not pinky
                        
                        if is_pinch:
                            # El boyutunu hesapla (wrist-0 ile middle MCP-9 arası mesafe)
                            wrist = landmarks[0]
                            mcp = landmarks[9]
                            hand_size = np.hypot(wrist[0] - mcp[0], wrist[1] - mcp[1])
                            if hand_size < 1.0:
                                hand_size = 1.0
                                
                            # Başparmak ucu (4) ile işaret parmağı ucu (8) arası mesafe
                            thumb_tip = landmarks[4]
                            index_tip = landmarks[8]
                            pinch_dist = np.hypot(thumb_tip[0] - index_tip[0], thumb_tip[1] - index_tip[1]) / hand_size
                            
                            if not pinch_active:
                                pinch_active = True
                                initial_pinch_dist = pinch_dist
                                base_zoom_factor = zoom_factor
                            else:
                                if initial_pinch_dist > 0.01:
                                    ratio = pinch_dist / initial_pinch_dist
                                    # Hassasiyet çarpanı: Zoom hızını kontrol eder
                                    sensitivity = 1.5
                                    target_zoom = base_zoom_factor + (ratio - 1.0) * sensitivity
                                    # Pürüzsüz geçiş için üstel filtre
                                    zoom_factor = float(np.clip(zoom_factor * 0.6 + target_zoom * 0.4, 1.0, 1.9))
                        else:
                            pinch_active = False
                            initial_pinch_dist = None
                            
                # 2. Temassız Kaydırma (Swipe) Tespiti
                if len(landmarks) >= 21:
                    cx = landmarks[9][0]
                    hand_x_history.append((cx, current_time))
                    hand_x_history = [p for p in hand_x_history if current_time - p[1] < 0.4]
                    if len(hand_x_history) >= 5:
                        dx = hand_x_history[-1][0] - hand_x_history[0][0]
                        dt = hand_x_history[-1][1] - hand_x_history[0][1]
                        if dt > 0.08:
                            speed = dx / dt
                            if abs(speed) > 1000:
                                swipe_event = "right" if speed > 1000 else "left"
                                swipe_time = current_time
                                hand_x_history.clear()
            else:
                # El yoksa hızlıca ve pürüzsüzce 1.0x normal boyuta dön
                pinch_active = False
                initial_pinch_dist = None
                if zoom_factor > 1.01:
                    zoom_factor = float(zoom_factor * 0.85 + 1.0 * 0.15)
                else:
                    zoom_factor = 1.0
                    
            with process_lock:
                thumbs_up_active = (thumbs_up_counter >= 5)
                live_hand_count = len(new_cached_hands)
                live_total_fingers = sum(h['fingers'] for h in new_cached_hands)
                if len(new_cached_hands) == 1:
                    live_hand_types = "Sağ El" if new_cached_hands[0]['type'] == 'Right' else "Sol El"
                elif len(new_cached_hands) == 2:
                    live_hand_types = "Sağ ve Sol El"
                else:
                    live_hand_types = "Hiçbiri"

            time.sleep(0.01)

ai_worker = AsyncAIWorker().start()

# ---------------------------------------------------------------
# 3. Yüksek Hızlı Çizim ve Video Akışı (60 FPS Stream)
# ---------------------------------------------------------------
def draw_overlays(frame):
    """Önbellekteki AI sonuçlarini kare üzerine mikro saniyeler içinde uygula ve Hava Tuvalini yönetir"""
    global drawing_canvas, last_pointer_pos, live_canvas_gesture
    with process_lock:
        local_hands = list(cached_hands)
        local_faces = list(cached_faces)

    # 1. Yüz Biyometrik Vizörleri
    for face in local_faces:
        fx_min, fy_min, fx_max, fy_max = face['bbox']
        fw = fx_max - fx_min
        fh = fy_max - fy_min
        blen = min(20, max(8, fw // 4), max(8, fh // 4))
        color_face = (255, 140, 0) # Cyan/Blue
        
        cv2.line(frame, (fx_min, fy_min), (fx_min + blen, fy_min), color_face, 2, cv2.LINE_AA)
        cv2.line(frame, (fx_min, fy_min), (fx_min, fy_min + blen), color_face, 2, cv2.LINE_AA)
        cv2.line(frame, (fx_max, fy_min), (fx_max - blen, fy_min), color_face, 2, cv2.LINE_AA)
        cv2.line(frame, (fx_max, fy_min), (fx_max, fy_min + blen), color_face, 2, cv2.LINE_AA)
        cv2.line(frame, (fx_min, fy_max), (fx_min + blen, fy_max), color_face, 2, cv2.LINE_AA)
        cv2.line(frame, (fx_min, fy_max), (fx_min, fy_max - blen), color_face, 2, cv2.LINE_AA)
        cv2.line(frame, (fx_max, fy_max), (fx_max - blen, fy_max), color_face, 2, cv2.LINE_AA)
        cv2.line(frame, (fx_max, fy_max), (fx_max, fy_max - blen), color_face, 2, cv2.LINE_AA)
        
        label = face['label']
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        badge_y = max(fy_min - 8, 25)
        cv2.rectangle(frame, (fx_min, badge_y - th - 6), (fx_min + tw + 10, badge_y + 4), (16, 18, 24), -1)
        cv2.rectangle(frame, (fx_min, badge_y - th - 6), (fx_min + tw + 10, badge_y + 4), color_face, 1)
        cv2.putText(frame, label, (fx_min + 5, badge_y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

    # 2. El İskeleti ve Takibi
    for hand in local_hands:
        x, y, w, h = hand['bbox']
        fingers = hand['fingers']
        hand_type = "Sağ" if hand['type'] == "Right" else "Sol"
        
        # Eklem ve İskelet Çizimi
        if 'landmarks_px' in hand:
            px = hand['landmarks_px']
            for connection in HAND_CONNECTIONS:
                s_idx, e_idx = connection
                if s_idx < len(px) and e_idx < len(px):
                    cv2.line(frame, px[s_idx], px[e_idx], (255, 210, 0), 2, cv2.LINE_AA)
            for pt in px:
                cv2.circle(frame, pt, 4, (255, 255, 255), -1, cv2.LINE_AA)
                cv2.circle(frame, pt, 6, (255, 180, 0), 1, cv2.LINE_AA)
        
        # Zarif Köşe Braketleri
        blen = min(18, max(8, w // 4), max(8, h // 4))
        color_b = (255, 210, 0)
        cv2.line(frame, (x, y), (x + blen, y), color_b, 2, cv2.LINE_AA)
        cv2.line(frame, (x, y), (x, y + blen), color_b, 2, cv2.LINE_AA)
        cv2.line(frame, (x + w, y), (x + w - blen, y), color_b, 2, cv2.LINE_AA)
        cv2.line(frame, (x + w, y), (x + w, y + blen), color_b, 2, cv2.LINE_AA)
        cv2.line(frame, (x, y + h), (x + blen, y + h), color_b, 2, cv2.LINE_AA)
        cv2.line(frame, (x, y + h), (x, y + h - blen), color_b, 2, cv2.LINE_AA)
        cv2.line(frame, (x + w, y + h), (x + w - blen, y + h), color_b, 2, cv2.LINE_AA)
        cv2.line(frame, (x + w, y + h), (x + w, y + h - blen), color_b, 2, cv2.LINE_AA)
        
        # Rozet
        badge_text = f"{hand_type} • {fingers} Parmak"
        (tw, th), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        badge_y = max(y - 8, 25)
        cv2.rectangle(frame, (x, badge_y - th - 6), (x + tw + 12, badge_y + 4), (16, 18, 24), -1)
        cv2.rectangle(frame, (x, badge_y - th - 6), (x + tw + 12, badge_y + 4), (255, 200, 0), 1)
        cv2.putText(frame, badge_text, (x + 6, badge_y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)



    # 4. Hava Tuvali (Air Canvas) Mantığı
    if drawing_canvas is None:
        h, w = frame.shape[:2]
        drawing_canvas = np.zeros((h, w, 3), dtype=np.uint8)

    active_gesture = "Standby"
    
    if air_canvas_enabled and len(local_hands) > 0:
        hand = local_hands[0]
        hand_type = hand['type']
        
        if 'landmarks_px' in hand:
            px = hand['landmarks_px']
            finger_states = get_finger_states(px, hand_type)
            gesture = get_canvas_gesture(finger_states)
            
            # Koordinatlar
            if len(px) >= 21:
                ix, iy = px[8] # İşaret parmağı ucu
                mx, my = px[9] # Silgi için avuç içi (orta parmak mcp)
                
                # İmleç (İşaret parmağı ucu) için Dinamik EMA Pürüzsüzleştirme
                prev_smoothed = smoothed_pointer_pos.get(hand_type)
                if prev_smoothed is None:
                    six, siy = ix, iy
                else:
                    dx = ix - prev_smoothed[0]
                    dy = iy - prev_smoothed[1]
                    dist = np.hypot(dx, dy)
                    
                    # Dinamik alpha: yavaş hareketlerde daha pürüzsüz (küçük alpha), hızlı hareketlerde tepkisel (büyük alpha)
                    alpha = max(0.15, min(0.75, dist / 90.0))
                    six = int(prev_smoothed[0] + alpha * dx)
                    siy = int(prev_smoothed[1] + alpha * dy)
                
                smoothed_pointer_pos[hand_type] = (six, siy)
                
                # Silgi koordinatları için Dinamik EMA Pürüzsüzleştirme
                prev_smoothed_eraser = smoothed_pointer_pos.get(hand_type + "_eraser")
                if prev_smoothed_eraser is None:
                    smx, smy = mx, my
                else:
                    dx = mx - prev_smoothed_eraser[0]
                    dy = my - prev_smoothed_eraser[1]
                    dist = np.hypot(dx, dy)
                    alpha = max(0.15, min(0.75, dist / 90.0))
                    smx = int(prev_smoothed_eraser[0] + alpha * dx)
                    smy = int(prev_smoothed_eraser[1] + alpha * dy)
                    
                smoothed_pointer_pos[hand_type + "_eraser"] = (smx, smy)
                
                if gesture == "pen":
                    active_gesture = "Kalem Modu"
                    last_pos = last_pointer_pos.get(hand_type)
                    if last_pos is not None:
                        dist = np.hypot(six - last_pos[0], siy - last_pos[1])
                        if dist < 120:
                            cv2.line(drawing_canvas, last_pos, (six, siy), active_brush_color, active_brush_size, cv2.LINE_AA)
                    last_pointer_pos[hand_type] = (six, siy)
                    
                    # Kalem ucu görselleştirme (kamera karesine geçici olarak çizilir)
                    cv2.circle(frame, (six, siy), active_brush_size + 2, (255, 255, 255), -1, cv2.LINE_AA)
                    cv2.circle(frame, (six, siy), active_brush_size, active_brush_color, -1, cv2.LINE_AA)
                    
                elif gesture == "eraser":
                    active_gesture = "Silgi"
                    eraser_radius = 45
                    cv2.circle(drawing_canvas, (smx, smy), eraser_radius, (0, 0, 0), -1)
                    
                    # Ekrana geçici silgi halkası çizelim
                    cv2.circle(frame, (smx, smy), eraser_radius, (255, 255, 255), 2, cv2.LINE_AA)
                    cv2.circle(frame, (smx, smy), eraser_radius + 4, (100, 100, 100), 1, cv2.LINE_AA)
                    cv2.putText(frame, "SILGI", (smx - 20, smy + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
                    
                    last_pointer_pos[hand_type] = None
                    
                elif gesture == "laser":
                    active_gesture = "Lazer İşaretçi"
                    # Lazer parlama efekti (geçiçi)
                    cv2.circle(frame, (six, siy), 12, (0, 0, 255), 2, cv2.LINE_AA)
                    cv2.circle(frame, (six, siy), 6, (0, 0, 255), -1, cv2.LINE_AA)
                    cv2.circle(frame, (six, siy), 2, (255, 255, 255), -1, cv2.LINE_AA)
                    
                    last_pointer_pos[hand_type] = None
                    
                else: # idle
                    active_gesture = "Standby"
                    last_pointer_pos[hand_type] = None
                    
                    # İnce bir hedefleme halkası gösterelim
                    cv2.circle(frame, (six, siy), 5, (255, 255, 255), 1, cv2.LINE_AA)
                    cv2.circle(frame, (six, siy), 2, (180, 180, 180), -1, cv2.LINE_AA)
    else:
        last_pointer_pos.clear()
        smoothed_pointer_pos.clear()
        
    live_canvas_gesture = active_gesture

    # Tuval maskesini ana kareye uygulayalım
    if air_canvas_enabled and drawing_canvas is not None:
        if drawing_canvas.shape[:2] != frame.shape[:2]:
            drawing_canvas = cv2.resize(drawing_canvas, (frame.shape[1], frame.shape[0]), interpolation=cv2.INTER_NEAREST)
        gray = cv2.cvtColor(drawing_canvas, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
        frame[mask > 0] = drawing_canvas[mask > 0]

    return frame

def generate_frames():
    stream = get_camera_stream()
    
    while True:
        success, frame = stream.read()
        if not success or frame is None:
            time.sleep(0.01)
            continue
        
        # Ayna Yansıtma
        frame = cv2.flip(frame, 1)
        
        # AI Arka Plan İş Parçacığına Kareyi Gönder (Kesmeksizin / Non-blocking)
        ai_worker.feed_frame(frame)
        
        # Anlık Çizimleri Ekle (< 1 milisaniye)
        frame = draw_overlays(frame)
        
        global latest_processed_frame
        with process_lock:
            latest_processed_frame = frame.copy()
        
        # Yüksek Kaliteli ve Hızlı JPEG Sıkıştırma (86 Kalite)
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 86])
        if ret:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        
        # Pürüzsüz 60 FPS yayın zamanlaması
        time.sleep(0.016)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stats')
def stats():
    ptr_x = -1
    ptr_y = -1
    with process_lock:
        local_hands = list(cached_hands)
    if air_canvas_enabled and len(local_hands) > 0:
        hand = local_hands[0]
        hand_type = hand['type']
        smoothed_pos = smoothed_pointer_pos.get(hand_type)
        if smoothed_pos is not None:
            ptr_x, ptr_y = smoothed_pos
        elif 'landmarks_px' in hand and len(hand['landmarks_px']) >= 21:
            ptr_x, ptr_y = hand['landmarks_px'][8]
            
    return {
        'status': 'active',
        'mediapipe_ready': mediapipe_ready,
        'latest_photo': latest_photo_url,
        'latest_photo_reason': latest_photo_reason,
        'latest_photo_timestamp': latest_photo_timestamp,
        'face_expression': current_face_expression,
        'thumbs_up_detected': thumbs_up_active,
        'hand_count': live_hand_count,
        'total_fingers': live_total_fingers,
        'hand_types': live_hand_types,
        'face_count': live_face_count,
        'zoom_factor': round(zoom_factor, 2),
        'swipe_event': swipe_event,
        'swipe_timestamp': int(swipe_time * 1000),
        'air_canvas_enabled': air_canvas_enabled,
        'canvas_gesture': live_canvas_gesture,
        'brush_color': f"#{active_brush_color[2]:02x}{active_brush_color[1]:02x}{active_brush_color[0]:02x}",
        'pointer_x': ptr_x,
        'pointer_y': ptr_y
    }

@app.route('/canvas_settings', methods=['POST'])
def canvas_settings():
    global air_canvas_enabled, active_brush_color, active_brush_size
    data = request.json or {}
    
    if 'enabled' in data:
        air_canvas_enabled = bool(data['enabled'])
        
    if 'color' in data:
        hex_color = data['color'].lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        active_brush_color = (b, g, r)
        
    if 'size' in data:
        active_brush_size = int(data['size'])
        
    return {
        'status': 'success',
        'enabled': air_canvas_enabled,
        'color': data.get('color', '#0a84ff'),
        'size': active_brush_size
    }

@app.route('/clear_canvas', methods=['POST'])
def clear_canvas():
    global drawing_canvas
    with process_lock:
        if drawing_canvas is not None:
            drawing_canvas.fill(0)
    return {'status': 'success', 'message': 'Hava tuvali temizlendi'}

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
                'timestamp': latest_photo_timestamp
            }
    return {'status': 'error', 'message': 'Görüntü yakalanamadi'}, 500

@app.route('/list_photos')
def list_photos():
    photos = []
    capture_dir = "static/captured"
    if os.path.exists(capture_dir):
        files = [f for f in os.listdir(capture_dir) if f.endswith(('.jpg', '.png'))]
        files.sort(key=lambda x: os.path.getmtime(os.path.join(capture_dir, x)), reverse=True)
        
        for f in files:
            path = os.path.join(capture_dir, f)
            mtime = os.path.getmtime(path)
            photos.append({
                'filename': f,
                'url': f"/static/captured/{f}",
                'timestamp': int(mtime * 1000)
            })
    return {'photos': photos}

@app.route('/delete_photo/<filename>', methods=['POST'])
def delete_photo(filename):
    safe_filename = os.path.basename(filename)
    path = os.path.join("static/captured", safe_filename)
    if os.path.exists(path):
        os.remove(path)
        return {'status': 'success', 'message': 'Fotoğraf silindi'}
    return {'status': 'error', 'message': 'Dosya bulunamadı'}, 404

@app.route('/delete_photos_batch', methods=['POST'])
def delete_photos_batch():
    data = request.json or {}
    filenames = data.get('filenames', [])
    deleted_count = 0
    capture_dir = "static/captured"
    
    for fname in filenames:
        safe_name = os.path.basename(fname)
        path = os.path.join(capture_dir, safe_name)
        if os.path.exists(path):
            try:
                os.remove(path)
                deleted_count += 1
            except Exception as e:
                print(f"Dosya silinemedi: {fname}, hata: {e}")
                
    return {'status': 'success', 'deleted_count': deleted_count}

@app.route('/apply_filter_to_photo', methods=['POST'])
def apply_filter_to_photo():
    data = request.json or {}
    filename = data.get('filename')
    filter_type = data.get('filter_type', 'normal')
    
    if not filename:
        return {'status': 'error', 'message': 'Dosya adı belirtilmedi'}, 400
        
    safe_filename = os.path.basename(filename)
    photo_path = os.path.join("static/captured", safe_filename)
    
    if not os.path.exists(photo_path):
        return {'status': 'error', 'message': 'Fotoğraf bulunamadı'}, 404
        
    img = cv2.imread(photo_path)
    if img is None:
        return {'status': 'error', 'message': 'Görüntü okunamadı'}, 500
        
    if filter_type == 'grayscale':
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        
    cv2.imwrite(photo_path, img)
    return {'status': 'success', 'message': 'Filtre başarıyla kaydedildi'}

def open_browser():
    time.sleep(1.2)
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
