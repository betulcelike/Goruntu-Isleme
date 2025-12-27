// script.js

// 1. HTML'deki video elementini seçiyoruz
const video = document.querySelector('video');

/**
 * 2. Kamerayı Başlatma Fonksiyonu
 * navigator.mediaDevices.getUserMedia: Tarayıcıdan kamera/mikrofon izni ister.
 */
async function startCamera() {
    try {
        // Sadece görüntü (video) istiyoruz, ses (audio) istemiyoruz
        const stream = await navigator.mediaDevices.getUserMedia({ 
            video: { width: 1280, height: 720 }, 
            audio: false 
        });
        
        // Kameradan gelen görüntüyü video etiketine bağlıyoruz
        video.srcObject = stream;
    } catch (err) {
        // Eğer kullanıcı izin vermezse veya kamera yoksa hata verir
        console.error("Kamera acilirken bir hata oluştu: ", err);
        alert("Kameraya erişim reddedildi veya kamera bulunamadi. Lütfen tarayici ayarlarindan izin verin.");
    }
}

/**
 * 3. Filtre Uygulama Fonksiyonu
 * Bu fonksiyon, butonlara basıldığında çağrılır.
 * Parametre olarak 'blur(5px)' veya 'grayscale(100%)' gibi CSS değerleri alır.
 */
function setFilter(filterType) {
    if (video) {
        video.style.filter = filterType;
    }
}

// 4. Sayfa açılır açılmaz kamerayı otomatik olarak başlat
startCamera();
// Fotoğraf Çekme Fonksiyonu
function takePhoto() {
    const canvas = document.getElementById('canvas');
    const video = document.querySelector('video'); // Videoyu tekrar garantiye alalım
    
    if (!video || video.readyState !== 4) {
        alert("Video henüz hazır değil, lütfen bekleyin.");
        return;
    }

    const context = canvas.getContext('2d');
    
    // Canvas boyutlarını videonun gerçek çözünürlüğüne eşitle
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Filtreyi ve ayna efektini uygula
    context.filter = getComputedStyle(video).filter;
    
    // Ayna efekti için canvas'ı çevir
    context.translate(canvas.width, 0);
    context.scale(-1, 1);
    
    // Fotoğrafı çiz
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // İndirme işlemini başlat
    try {
        const dataUrl = canvas.toDataURL('image/png');
        const link = document.createElement('a');
        link.download = 'filtreli-fotograf.png';
        link.href = dataUrl;
        link.click();
        console.log("Fotoğraf başarıyla indirildi.");
    } catch (err) {
        console.error("Fotoğraf kaydedilirken hata:", err);
        alert("Tarayıcı güvenliği nedeniyle fotoğraf indirilemedi. Lütfen 'Go Live' ile açtığınızdan emin olun.");
    }
}