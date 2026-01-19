Görüntü İşleme 
Bu proje, Python, Flask ve MediaPipe kullanılarak geliştirilmiş, web tabanlı bir gerçek zamanlı görüntü işleme uygulamasıdır. Kullanıcının kamerasından alınan görüntüyü analiz ederek el eklem noktalarını (landmarks) tespit eder ve tarayıcı üzerinden interaktif bir arayüz sunar.

🚀 Özellikler
Gerçek Zamanlı El Takibi: MediaPipe kütüphanesi ile el üzerindeki eklem noktalarının tespiti ve görselleştirilmesi.

Web Tabanlı Arayüz: Flask backend yapısı ile video akışının tarayıcıya düşük gecikmeli aktarımı.

İnteraktif Filtreler: JavaScript ve CSS kullanılarak görüntü üzerinde dinamik filtreleme seçenekleri.

Gelişmiş Tasarım: Modern, karanlık tema destekli ve kullanıcı dostu dashboard arayüzü.

🛠️ Kullanılan Teknolojiler
Backend: Python, Flask

Görüntü İşleme: OpenCV, MediaPipe

Frontend: HTML5, CSS3, JavaScript

📂 Dosya Yapısı
app.py: Flask sunucusu ve MediaPipe/OpenCV görüntü işleme mantığı.

templates/index.html: Web arayüzünün iskeleti.

static/style.css: Dashboard tasarımı ve modern görsel efektler.

static/script.js: Filtre yönetimi ve frontend etkileşimleri.

🚧 Mevcut Durum ve Gelecek Geliştirmeler
Proje şu anda el üzerindeki 21 temel eklem noktasını başarıyla tespit edebilmekte ve görselleştirebilmektedir.

Geliştirme Aşamasında: Tespit edilen eklem verileri kullanılarak belirli el hareketlerinin (gesture recognition) anlamlandırılması ve bu hareketlerin komut sistemine (örneğin; el hareketiyle filtre değiştirme) dönüştürülmesi üzerine çalışmalar devam etmektedir.

🔧 Kurulum
Gerekli kütüphaneleri yükleyin:

Bash

pip install opencv-python flask mediapipe
Uygulamayı çalıştırın:

Bash

python app.py
Tarayıcınızda http://127.0.0.1:5000 adresine gidin.
