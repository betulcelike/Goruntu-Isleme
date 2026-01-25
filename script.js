/**
 * El Takip Uygulaması - Frontend JavaScript
 * Filtre yönetimi ve interaktif kontroller
 */

document.addEventListener('DOMContentLoaded', function () {
    // DOM Elementleri
    const videoStream = document.getElementById('video-stream');
    const filterButtons = document.querySelectorAll('.filter-btn');
    const brightnessSlider = document.getElementById('brightness');
    const saturationSlider = document.getElementById('saturation');
    const contrastSlider = document.getElementById('contrast');

    // Değer göstergeleri
    const brightnessValue = document.getElementById('brightness-value');
    const saturationValue = document.getElementById('saturation-value');
    const contrastValue = document.getElementById('contrast-value');

    // Mevcut filtre durumu
    let currentFilter = 'normal';
    let settings = {
        brightness: 100,
        saturation: 100,
        contrast: 100
    };

    /**
     * CSS filtresini uygula
     */
    function applyFilters() {
        let filterStr = '';

        // Temel ayarlar
        filterStr += `brightness(${settings.brightness}%) `;
        filterStr += `saturate(${settings.saturation}%) `;
        filterStr += `contrast(${settings.contrast}%) `;

        // Özel filtreler
        switch (currentFilter) {
            case 'grayscale':
                filterStr += 'grayscale(100%) ';
                break;
            case 'sepia':
                filterStr += 'sepia(80%) ';
                break;
            case 'invert':
                filterStr += 'invert(100%) ';
                break;
            case 'blur':
                filterStr += 'blur(3px) ';
                break;
            case 'contrast':
                filterStr += 'contrast(150%) ';
                break;
            default:
                // Normal - ek filtre yok
                break;
        }

        videoStream.style.filter = filterStr.trim();
    }

    /**
     * Filtre butonlarını yönet
     */
    filterButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            // Aktif sınıfını güncelle
            filterButtons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');

            // Filtreyi uygula
            currentFilter = this.dataset.filter;
            applyFilters();

            // Görsel geri bildirim
            animateButton(this);
        });
    });

    /**
     * Slider değişikliklerini yönet
     */
    brightnessSlider.addEventListener('input', function () {
        settings.brightness = this.value;
        brightnessValue.textContent = `${this.value}%`;
        applyFilters();
    });

    saturationSlider.addEventListener('input', function () {
        settings.saturation = this.value;
        saturationValue.textContent = `${this.value}%`;
        applyFilters();
    });

    contrastSlider.addEventListener('input', function () {
        settings.contrast = this.value;
        contrastValue.textContent = `${this.value}%`;
        applyFilters();
    });

    /**
     * Buton tıklama animasyonu
     */
    function animateButton(button) {
        button.style.transform = 'scale(0.95)';
        setTimeout(() => {
            button.style.transform = 'translateY(-2px)';
        }, 100);
    }

    /**
     * FPS hesaplama
     */
    let frameCount = 0;
    let lastTime = performance.now();
    const fpsDisplay = document.getElementById('fps-value');

    function updateFPS() {
        frameCount++;
        const currentTime = performance.now();

        if (currentTime - lastTime >= 1000) {
            if (fpsDisplay) {
                fpsDisplay.textContent = frameCount;
            }
            frameCount = 0;
            lastTime = currentTime;
        }

        requestAnimationFrame(updateFPS);
    }

    // FPS sayacını başlat
    updateFPS();

    /**
     * Video stream hata yönetimi
     */
    videoStream.addEventListener('error', function () {
        console.error('Video stream yüklenemedi');
        videoStream.style.background = 'linear-gradient(135deg, #1a1a25, #0a0a0f)';
        videoStream.alt = 'Kamera bağlantısı kurulamadı. Lütfen sayfayı yenileyin.';
    });

    /**
     * Sidebar navigasyonu
     */
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function (e) {
            e.preventDefault();
            navItems.forEach(n => n.classList.remove('active'));
            this.classList.add('active');
        });
    });

    /**
     * Keyboard shortcuts
     */
    document.addEventListener('keydown', function (e) {
        // Filtre kısayolları
        const shortcuts = {
            '1': 'normal',
            '2': 'grayscale',
            '3': 'sepia',
            '4': 'invert',
            '5': 'blur',
            '6': 'contrast'
        };

        if (shortcuts[e.key]) {
            const btn = document.querySelector(`[data-filter="${shortcuts[e.key]}"]`);
            if (btn) btn.click();
        }

        // Reset (R tuşu)
        if (e.key.toLowerCase() === 'r') {
            resetSettings();
        }
    });

    /**
     * Ayarları sıfırla
     */
    function resetSettings() {
        settings = { brightness: 100, saturation: 100, contrast: 100 };

        brightnessSlider.value = 100;
        saturationSlider.value = 100;
        contrastSlider.value = 100;

        brightnessValue.textContent = '100%';
        saturationValue.textContent = '100%';
        contrastValue.textContent = '100%';

        currentFilter = 'normal';
        filterButtons.forEach(b => b.classList.remove('active'));
        document.querySelector('[data-filter="normal"]').classList.add('active');

        applyFilters();
    }

    /**
     * İstatistik güncellemesi
     */
    async function updateStats() {
        try {
            const response = await fetch('/stats');
            const data = await response.json();

            if (data.status === 'active') {
                document.querySelector('.status-dot').classList.add('active');
            }
        } catch (error) {
            console.log('Stats güncellenemedi');
        }
    }

    // Her 5 saniyede bir istatistikleri güncelle
    setInterval(updateStats, 5000);
    updateStats();

    // Başlangıç mesajı
    console.log('🖐️ El Takip Uygulaması başlatıldı');
    console.log('Klavye kısayolları: 1-6 filtreler, R sıfırlama');
});
