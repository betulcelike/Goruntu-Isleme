# Kurumsal Sunum ve Temassız Etkileşim Platformu (GestureFlow Studio)

Bu proje; derin öğrenme ve bilgisayarlı görü (Computer Vision) tekniklerini kullanarak web kamerası üzerinden eş zamanlı el eklemleri takibi, yüz ifadesi (mimik) analizi ve temassız sunum yönetimi gerçekleştiren yapay zeka destekli interaktif bir **Kurumsal Sunum ve Tasarım Stüdyosu** (Enterprise Presentation Studio) platformudur.

Platform, özellikle iş toplantılarında, sunumlarda ve uzaktan eğitimlerde temassız bir biçimde ekranı kontrol etme, hava kalemiyle çizim yapma, not alma ve seans kayıtları alma ihtiyaçları için optimize edilmiştir.

---

## 🚀 Öne Çıkan Özellikler

*   **✍️ Hassas Sunum Tuvali (Precision Presentation Canvas):** Sunum esnasında ekrana dokunmadan havada çizim yapmanızı sağlayan yapay zeka tabanlı çizim motoru.
    *   ☝️ **Kalem Modu (☝️):** Sadece işaret parmağı açıkken ekrana pürüzsüz çizgilerle çizim yapar. Kareler arasındaki gecikmeyi sıfırlayan akıllı takip algoritması entegredir.
    *   ✌️ **Lazer İşaretçi Modu (✌️):** İşaret ve orta parmak açıkken sunum alanında parlayan fütüristik kırmızı bir lazer odağı (beyaz çekirdekli halka) yansıtır.
    *   🖐️ **Hava Silgisi Modu (🖐️):** Elinizi tamamen açtığınızda avuç içi merkezini baz alarak dairesel bir yarıçapta çizimleri temizler.
*   **🧹 Temassız Hızlı Sıfırlama (Contactless Hover Clear):** Arayüzün üst-orta kısmında duran yarı şeffaf `Sıfırla` butonuna işaret parmağınızla **1.2 saniye** odaklandığınızda çizim tuvali anında temizlenir. Bu buton tamamen web arayüzünde çizildiği için **çekilen fotoğraflarda kesinlikle görünmez**.
*   **📐 Kararlı Adım-Tabanlı Zoom:** Görüntü gürültüsünden kaynaklanan titremeleri önleyen kararlı yakınlaştırma motoru.
    *   🖐️ **5 Parmak Açık:** Kademeli yakınlaşma (`Zoom In` - maksimum 1.9x).
    *   ✊ **Yumruk (0 Parmak):** Kademeli uzaklaşma (`Zoom Out` - minimum 1.0x).
    *   *Diğer jestlerde veya çizim esnasında zoom miktarı kararlılık için kilitli kalır.*
*   **📸 Temassız Kamera Tetikleme (Thumbs Up 👍):** Kameraya yapılan 👍 işareti algılandığında 2 saniyelik görsel bir geri sayım tetiklenir, çizimlerinizle birlikte ekranın ekran görüntüsü anında diske kaydedilir.
*   **💻 Kurumsal Minimalist Durum Çubuğu (Status Bar):** Kameranın hemen altında yer alan tek satırlık Apple VisionOS stili gösterge paneli. Kamera durumunu, aktif el takibini, yüz ifadesini, kalem modunu ve sistem FPS'ini canlı olarak yansıtır.
*   **🎨 Sinematik Renk Sınıflandırma & Görüntü Filtreleri:** Canlı yayına ve çekilen fotoğraflara anlık uygulanabilen kurumsal filtreler (*Natural HD, Studio Glow, Warm Cinema, Cyber Cyan, Dramatic B&W, Vivid Pop*).

---

## 🛠️ Kullanılan Teknolojiler

*   **Backend:** Python 3.12, Flask, OpenCV (Görüntü İşleme), Multithreading (Asenkron İş Parçacıkları)
*   **AI / Machine Learning:** MediaPipe Tasks API (Hands & Face Landmarker)
*   **Frontend:** HTML5 (Semantik Arayüz), CSS3 (Modern Glassmorphism, Grid Layout), Vanilla JavaScript (Sıfır bağımlılık)

---

## 📦 Kurulum ve Çalıştırma

Projeyi yerel bilgisayarınızda çalıştırmak için aşağıdaki adımları uygulayabilirsiniz:

### 1. Depoyu Klonlayın
```bash
git clone https://github.com/betulcelike/Gercek-Zamanli-El-Hareketleri-ve-Yuz-ifadesi-Analiz-Platformu.git
cd Gercek-Zamanli-El-Hareketleri-ve-Yuz-ifadesi-Analiz-Platformu
```

### 2. Sanal Ortam Oluşturun ve Aktifleştirin
```bash
python -m venv venv
# Windows için:
venv\Scripts\activate
# macOS/Linux için:
source venv/bin/activate
```

### 3. Gerekli Kütüphaneleri Yükleyin
```bash
pip install -r requirements.txt
```

### 4. Uygulamayı Başlatın
```bash
python app.py
```
*Uygulama başlatıldığında tarayıcınızda otomatik olarak `http://127.0.0.1:5000` adresi açılacaktır. Alternatif olarak proje ana dizinindeki `baslat.bat` dosyasına çift tıklayarak da çalıştırabilirsiniz.*

---

## 📂 Proje Yapısı

```text
├── app.py                  # Flask Sunucusu ve Asenkron Yapay Zeka İşleme Döngüsü
├── requirements.txt        # Gerekli Python Paketleri
├── baslat.bat              # Kolay Çalıştırma Scripti (Windows venv uyumlu)
├── README.md               # Proje Açıklama Dokümanı
├── static/
│   ├── captured/           # Çekilen Sunum Fotoğraflarının Kaydedildiği Dizin
│   ├── style.css           # Modern Glassmorphic CSS Arayüz Tasarımları
│   └── script.js           # Telemetri Güncellemeleri, Temassız Hover Takibi, Arayüz Mantığı
└── templates/
    └── index.html          # Minimalist Sunum Sahnesi ve Sidebar Arayüzü
```

---

## 🛡️ Lisans
Bu proje eğitim ve kurumsal sunum geliştirme amacıyla tasarlanmıştır. Serbestçe kullanılabilir ve özelleştirilebilir.
