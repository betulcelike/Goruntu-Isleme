/**
 * GestureFlow AI — Vision Intelligence Studio
 * Apple Pro Vision Minimalist Controller
 */

document.addEventListener('DOMContentLoaded', function () {
    // ---------------------------------------------------------------
    // 1. Core DOM Elements & Settings
    // ---------------------------------------------------------------
    const videoStream = document.getElementById('video-stream');
    const filterButtons = document.querySelectorAll('.filter-btn');
    const brightnessSlider = document.getElementById('brightness');
    const saturationSlider = document.getElementById('saturation');
    const contrastSlider = document.getElementById('contrast');

    const brightnessValue = document.getElementById('brightness-value');
    const saturationValue = document.getElementById('saturation-value');
    const contrastValue = document.getElementById('contrast-value');

    let currentFilter = 'normal';
    let settings = {
        brightness: 100,
        saturation: 100,
        contrast: 100
    };

    // Accordion Studio Cards Toggle
    const accordionCards = document.querySelectorAll('.accordion-card');
    accordionCards.forEach(card => {
        const header = card.querySelector('.card-header');
        if (header) {
            header.addEventListener('click', () => {
                card.classList.toggle('collapsed');
            });
        }
    });

    // ---------------------------------------------------------------
    // 2. Video Filters, Tuning & Cinematic Grading Presets
    // ---------------------------------------------------------------
    let activePreset = 'natural';

    const presetConfigs = {
        'natural': { filterExtra: '' },
        'studio_glow': { filterExtra: 'drop-shadow(0 0 10px rgba(255, 214, 10, 0.15))' },
        'warm_cinema': { filterExtra: 'sepia(22%)' },
        'cyber_cyan': { filterExtra: 'hue-rotate(180deg)' },
        'dramatic_bw': { filterExtra: 'grayscale(100%)' },
        'vivid_pop': { filterExtra: 'saturate(135%)' }
    };

    function applyFilters() {
        if (!videoStream) return;
        let filterStr = '';
        filterStr += `brightness(${settings.brightness}%) `;
        filterStr += `saturate(${settings.saturation}%) `;
        filterStr += `contrast(${settings.contrast}%) `;

        if (currentFilter === 'grayscale') {
            filterStr += 'grayscale(100%) ';
        }

        if (presetConfigs[activePreset] && presetConfigs[activePreset].filterExtra) {
            filterStr += presetConfigs[activePreset].filterExtra + ' ';
        }

        videoStream.style.filter = filterStr.trim();
    }

    filterButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            filterButtons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');

            currentFilter = this.dataset.filter;
            applyFilters();
        });
    });

    const presetButtons = document.querySelectorAll('.filter-preset-btn');
    presetButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            presetButtons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');

            activePreset = this.dataset.preset;
            
            // Preset ayarlarına göre sliderları hafifçe optimize et
            if (activePreset === 'studio_glow') {
                settings.brightness = 106;
                settings.saturation = 114;
                settings.contrast = 108;
            } else if (activePreset === 'warm_cinema') {
                settings.brightness = 103;
                settings.saturation = 120;
                settings.contrast = 106;
            } else if (activePreset === 'cyber_cyan') {
                settings.brightness = 102;
                settings.saturation = 125;
                settings.contrast = 115;
            } else if (activePreset === 'dramatic_bw') {
                settings.brightness = 96;
                settings.saturation = 0;
                settings.contrast = 135;
            } else if (activePreset === 'vivid_pop') {
                settings.brightness = 102;
                settings.saturation = 140;
                settings.contrast = 112;
            } else {
                settings.brightness = 100;
                settings.saturation = 100;
                settings.contrast = 100;
            }

            if (brightnessSlider) brightnessSlider.value = settings.brightness;
            if (saturationSlider) saturationSlider.value = settings.saturation;
            if (contrastSlider) contrastSlider.value = settings.contrast;
            if (brightnessValue) brightnessValue.textContent = `${settings.brightness}%`;
            if (saturationValue) saturationValue.textContent = `${settings.saturation}%`;
            if (contrastValue) contrastValue.textContent = `${settings.contrast}%`;

            applyFilters();
        });
    });

    if (brightnessSlider) {
        brightnessSlider.addEventListener('input', function () {
            settings.brightness = this.value;
            if (brightnessValue) brightnessValue.textContent = `${this.value}%`;
            applyFilters();
        });
    }

    if (saturationSlider) {
        saturationSlider.addEventListener('input', function () {
            settings.saturation = this.value;
            if (saturationValue) saturationValue.textContent = `${this.value}%`;
            applyFilters();
        });
    }

    if (contrastSlider) {
        contrastSlider.addEventListener('input', function () {
            settings.contrast = this.value;
            if (contrastValue) contrastValue.textContent = `${this.value}%`;
            applyFilters();
        });
    }

    // ---------------------------------------------------------------
    // 4. Emotion Chart.js (Apple Minimalist Dark Theme)
    // ---------------------------------------------------------------
    let expressionChart = null;
    const expressionCounts = { 'Normal': 0, 'Mutlu': 0, 'Saskin': 0, 'Uzgun': 0 };

    function initChart() {
        const ctx = document.getElementById('expressionChart');
        if (!ctx) return;
        expressionChart = new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['Normal', 'Mutlu', 'Şaşkın', 'Üzgün'],
                datasets: [{
                    label: 'Duygu',
                    data: [0, 0, 0, 0],
                    backgroundColor: ['#6e6e73', '#0071e3', '#ff9f0a', '#ff453a'],
                    borderWidth: 0,
                    borderRadius: 6,
                    barPercentage: 0.65
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(22, 25, 34, 0.95)',
                        titleColor: '#f5f5f7',
                        bodyColor: '#a1a1a6',
                        cornerRadius: 8,
                        padding: 8
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: { stepSize: 1, color: '#6e6e73', font: { size: 9, family: 'Plus Jakarta Sans' } },
                        grid: { color: 'rgba(255, 255, 255, 0.04)' }
                    },
                    y: {
                        ticks: { color: '#a1a1a6', font: { size: 10, weight: '600', family: 'Plus Jakarta Sans' } },
                        grid: { display: false }
                    }
                }
            }
        });
    }
    initChart();

    // ---------------------------------------------------------------
    // 5. Emoji Rain Animation
    // ---------------------------------------------------------------
    function triggerEmojiRain() {
        const container = document.getElementById('emoji-container');
        if (!container) return;

        const emojis = ['✨', '😊', '🎉', '🌟', '👍', '🌸', '🥳'];
        const count = 6;
        for (let i = 0; i < count; i++) {
            const emojiEl = document.createElement('span');
            emojiEl.className = 'floating-emoji';
            emojiEl.textContent = emojis[Math.floor(Math.random() * emojis.length)];
            emojiEl.style.left = (Math.random() * 85 + 5) + '%';
            emojiEl.style.animationDuration = (1.8 + Math.random() * 1.2) + 's';
            emojiEl.style.fontSize = (20 + Math.random() * 14) + 'px';

            container.appendChild(emojiEl);
            setTimeout(() => { emojiEl.remove(); }, 3000);
        }
    }

    // ---------------------------------------------------------------
    // 6. Mimic Challenge Game
    // ---------------------------------------------------------------
    let gameActive = false;
    let gameScore = 0;
    let gameTarget = null;
    let gameTimeLeft = 5;
    let gameInterval = null;

    const gameStartBtn = document.getElementById('game-start-btn');
    const gameStatusBox = document.getElementById('game-status-box');
    const gameTargetVal = document.getElementById('game-target-val');
    const gameTimerVal = document.getElementById('game-timer-val');
    const gameScoreVal = document.getElementById('game-score-val');

    const gameChallenges = [
        { label: 'Gülümse! 😊 (Mutlu Yüz)', check: (data) => data.face_expression === 'Mutlu' },
        { label: 'Şaşır! 😲 (Şaşkın Yüz)', check: (data) => data.face_expression === 'Saskin' },
        { label: 'Üzgün Yüz Yap! 😢', check: (data) => data.face_expression === 'Uzgun' },
        { label: 'Normal İfadeye Dön 😐', check: (data) => data.face_expression === 'Normal' },
        { label: 'Kameraya 2 El Göster! 🖐️🖐️', check: (data) => data.hand_count === 2 },
        { label: 'Kameraya Tek El Göster! 🖐️', check: (data) => data.hand_count === 1 },
        { label: 'Kameraya 5 Parmak Göster! 🖐️', check: (data) => data.total_fingers === 5 },
        { label: 'Başparmak Kaldır! 👍', check: (data) => data.thumbs_up_detected }
    ];

    function startNewChallenge() {
        let newChallenge;
        do {
            newChallenge = gameChallenges[Math.floor(Math.random() * gameChallenges.length)];
        } while (newChallenge === gameTarget && gameChallenges.length > 1);

        gameTarget = newChallenge;
        gameTimeLeft = 5;
        if (gameTargetVal) gameTargetVal.textContent = gameTarget.label;
        if (gameTimerVal) gameTimerVal.textContent = gameTimeLeft;
    }

    function toggleGame() {
        if (!gameStartBtn) return;
        gameActive = !gameActive;

        if (gameActive) {
            gameStartBtn.innerHTML = '<span>Oyunu Durdur</span>';
            gameStartBtn.classList.add('active');
            if (gameStatusBox) gameStatusBox.style.display = 'flex';

            gameScore = 0;
            if (gameScoreVal) gameScoreVal.textContent = gameScore;

            startNewChallenge();

            gameInterval = setInterval(() => {
                gameTimeLeft--;
                if (gameTimerVal) gameTimerVal.textContent = gameTimeLeft;

                if (gameTimeLeft <= 0) {
                    flashCameraStage('red');
                    startNewChallenge();
                }
            }, 1000);
        } else {
            gameStartBtn.innerHTML = '<span>Oyunu Başlat</span>';
            gameStartBtn.classList.remove('active');
            if (gameStatusBox) gameStatusBox.style.display = 'none';
            if (gameInterval) {
                clearInterval(gameInterval);
                gameInterval = null;
            }
            gameTarget = null;
        }
    }

    if (gameStartBtn) {
        gameStartBtn.addEventListener('click', toggleGame);
    }

    function flashCameraStage(color) {
        const stageFrame = document.querySelector('.stage-frame');
        if (!stageFrame) return;

        const flashOverlay = document.createElement('div');
        flashOverlay.style.position = 'absolute';
        flashOverlay.style.top = '0';
        flashOverlay.style.left = '0';
        flashOverlay.style.width = '100%';
        flashOverlay.style.height = '100%';
        flashOverlay.style.pointerEvents = 'none';
        flashOverlay.style.zIndex = '5';
        flashOverlay.style.borderRadius = 'var(--radius-lg)';
        flashOverlay.style.transition = 'opacity 0.35s ease';

        if (color === 'green') {
            flashOverlay.style.background = 'rgba(52, 199, 89, 0.2)';
            flashOverlay.style.boxShadow = 'inset 0 0 0 3px #34c759';
        } else {
            flashOverlay.style.background = 'rgba(255, 69, 58, 0.2)';
            flashOverlay.style.boxShadow = 'inset 0 0 0 3px #ff453a';
        }

        stageFrame.appendChild(flashOverlay);
        setTimeout(() => {
            flashOverlay.style.opacity = '0';
            setTimeout(() => { flashOverlay.remove(); }, 350);
        }, 150);
    }

    // ---------------------------------------------------------------
    // 7. FPS Counter
    // ---------------------------------------------------------------
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
    updateFPS();

    // ---------------------------------------------------------------
    // 8. Capture Trigger, Countdown & Flash
    // ---------------------------------------------------------------
    let isCountingDown = false;
    let cooldownActive = false;
    const countdownOverlay = document.getElementById('countdown-overlay');

    async function triggerCapture() {
        try {
            triggerShutterFlash();
            const response = await fetch('/capture_now', { method: 'POST' });
            const data = await response.json();
            if (data.status === 'success') {
                loadPhotos();
            }
        } catch (error) {
            console.error('Fotoğraf çekilemedi:', error);
        }
    }

    function triggerShutterFlash() {
        const flash = document.getElementById('shutter-flash');
        if (flash) {
            flash.classList.add('flash');
            setTimeout(() => {
                flash.classList.remove('flash');
            }, 90);
        }
    }

    function startCountdown() {
        if (isCountingDown || cooldownActive) return;
        isCountingDown = true;

        let seconds = 2;
        if (countdownOverlay) {
            countdownOverlay.textContent = seconds;
            countdownOverlay.classList.add('show');
        }

        const interval = setInterval(() => {
            seconds--;
            if (seconds > 0) {
                if (countdownOverlay) countdownOverlay.textContent = seconds;
            } else {
                clearInterval(interval);
                if (countdownOverlay) countdownOverlay.classList.remove('show');
                triggerCapture();
                isCountingDown = false;

                cooldownActive = true;
                setTimeout(() => { cooldownActive = false; }, 4000);
            }
        }, 1000);
    }

    // ---------------------------------------------------------------
    // 9. Lightbox Modal & Post-Effect Editor
    // ---------------------------------------------------------------
    const lightboxModal = document.getElementById('lightbox-modal');
    const lightboxImg = document.getElementById('lightbox-img');
    const lightboxDate = document.getElementById('lightbox-date');
    const lightboxDeleteBtn = document.getElementById('lightbox-delete-btn');
    const lightboxCloseBtn = document.getElementById('lightbox-close-btn');
    const lightboxDownloadBtn = document.getElementById('lightbox-download-btn');
    const effectButtons = document.querySelectorAll('.effect-btn');
    const saveEffectBtn = document.getElementById('save-effect-btn');

    let activePhotoFilename = '';
    let activeEffect = 'normal';

    function openLightbox(url, timestamp) {
        if (!lightboxModal) return;
        activePhotoFilename = url.split('/').pop();

        if (lightboxImg) {
            lightboxImg.src = url + '?t=' + new Date().getTime();
            lightboxImg.style.filter = 'none';
        }

        const dateObj = new Date(timestamp);
        const formattedDate = dateObj.toLocaleDateString('tr-TR') + ' ' + dateObj.toLocaleTimeString('tr-TR');
        if (lightboxDate) lightboxDate.textContent = formattedDate;

        activeEffect = 'normal';
        effectButtons.forEach(btn => {
            btn.classList.remove('active');
            if (btn.getAttribute('data-effect') === 'normal') {
                btn.classList.add('active');
            }
        });

        lightboxModal.style.display = 'flex';
    }

    function closeLightbox() {
        if (lightboxModal) {
            lightboxModal.style.display = 'none';
        }
    }

    if (lightboxCloseBtn) {
        lightboxCloseBtn.addEventListener('click', closeLightbox);
    }

    if (lightboxModal) {
        lightboxModal.addEventListener('click', function (e) {
            if (e.target.classList.contains('lightbox-backdrop') || e.target === lightboxModal) {
                closeLightbox();
            }
        });
    }

    if (lightboxDownloadBtn) {
        lightboxDownloadBtn.addEventListener('click', () => {
            if (activePhotoFilename) {
                const link = document.createElement('a');
                link.href = `/static/captured/${activePhotoFilename}`;
                link.download = activePhotoFilename;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }
        });
    }

    effectButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            effectButtons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');

            activeEffect = this.getAttribute('data-effect');
            let filterStr = 'none';
            if (activeEffect === 'grayscale') {
                filterStr = 'grayscale(100%)';
            }
            if (lightboxImg) lightboxImg.style.filter = filterStr;
        });
    });

    if (saveEffectBtn) {
        saveEffectBtn.addEventListener('click', async () => {
            if (!activePhotoFilename || activeEffect === 'normal') {
                alert('Lütfen kaydetmek için önce farklı bir filtre seçin.');
                return;
            }

            saveEffectBtn.disabled = true;
            const originalText = saveEffectBtn.innerHTML;
            saveEffectBtn.textContent = 'Kaydediliyor...';

            try {
                const response = await fetch('/apply_filter_to_photo', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        filename: activePhotoFilename,
                        filter_type: activeEffect
                    })
                });
                const data = await response.json();
                if (data.status === 'success') {
                    const originalUrl = `/static/captured/${activePhotoFilename}`;
                    if (lightboxImg) {
                        lightboxImg.src = originalUrl + '?t=' + new Date().getTime();
                        lightboxImg.style.filter = 'none';
                    }

                    effectButtons.forEach(b => b.classList.remove('active'));
                    const normalBtn = Array.from(effectButtons).find(b => b.getAttribute('data-effect') === 'normal');
                    if (normalBtn) normalBtn.classList.add('active');
                    activeEffect = 'normal';

                    loadPhotos();
                } else {
                    alert('Efekt uygulanamadı: ' + data.message);
                }
            } catch (error) {
                console.error('Efekt kaydetme hatası:', error);
            } finally {
                saveEffectBtn.disabled = false;
                saveEffectBtn.innerHTML = originalText;
            }
        });
    }

    async function deletePhoto(filename) {
        if (!confirm('Bu fotoğrafı silmek istediğinize emin misiniz?')) return;
        try {
            const response = await fetch(`/delete_photo/${filename}`, { method: 'POST' });
            const data = await response.json();
            if (data.status === 'success') {
                closeLightbox();
                loadPhotos();
            } else {
                alert('Fotoğraf silinemedi: ' + data.message);
            }
        } catch (error) {
            console.error('Silme hatası:', error);
        }
    }

    if (lightboxDeleteBtn) {
        lightboxDeleteBtn.addEventListener('click', () => {
            if (activePhotoFilename) {
                deletePhoto(activePhotoFilename);
            }
        });
    }

    // ---------------------------------------------------------------
    // 10. Photo Gallery Reel & Multi-Select Batch Actions
    // ---------------------------------------------------------------
    let isSelectionMode = false;
    let selectedPhotos = new Set();

    const selectModeBtn = document.getElementById('select-mode-btn');
    const batchDownloadBtn = document.getElementById('batch-download-btn');
    const batchDeleteBtn = document.getElementById('batch-delete-btn');

    function toggleSelectionMode() {
        if (!selectModeBtn) return;
        isSelectionMode = !isSelectionMode;
        selectedPhotos.clear();

        if (isSelectionMode) {
            selectModeBtn.textContent = 'İptal';
            selectModeBtn.classList.add('active');
            if (batchDownloadBtn) batchDownloadBtn.style.display = 'inline-block';
            if (batchDeleteBtn) batchDeleteBtn.style.display = 'inline-block';
            updateBatchButtonStates();

            document.querySelectorAll('.gallery-photo-item').forEach(item => {
                item.classList.add('selection-active');
            });
        } else {
            selectModeBtn.textContent = 'Seç';
            selectModeBtn.classList.remove('active');
            if (batchDownloadBtn) batchDownloadBtn.style.display = 'none';
            if (batchDeleteBtn) batchDeleteBtn.style.display = 'none';

            document.querySelectorAll('.gallery-photo-item').forEach(item => {
                item.classList.remove('selection-active');
                item.classList.remove('selected');
            });
        }
    }

    function updateBatchButtonStates() {
        const count = selectedPhotos.size;
        if (batchDownloadBtn) {
            batchDownloadBtn.textContent = `İndir (${count})`;
            batchDownloadBtn.disabled = count === 0;
        }
        if (batchDeleteBtn) {
            batchDeleteBtn.textContent = `Sil (${count})`;
            batchDeleteBtn.disabled = count === 0;
        }
    }

    if (selectModeBtn) {
        selectModeBtn.addEventListener('click', toggleSelectionMode);
    }

    if (batchDownloadBtn) {
        batchDownloadBtn.addEventListener('click', () => {
            if (selectedPhotos.size === 0) return;
            selectedPhotos.forEach(filename => {
                const link = document.createElement('a');
                link.href = `/static/captured/${filename}`;
                link.download = filename;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            });
            toggleSelectionMode();
        });
    }

    if (batchDeleteBtn) {
        batchDeleteBtn.addEventListener('click', async () => {
            const count = selectedPhotos.size;
            if (count === 0) return;
            if (!confirm(`Seçilen ${count} fotoğrafı silmek istediğinize emin misiniz?`)) return;

            batchDeleteBtn.disabled = true;
            batchDeleteBtn.textContent = 'Siliniyor...';

            try {
                const response = await fetch('/delete_photos_batch', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filenames: Array.from(selectedPhotos) })
                });
                const data = await response.json();
                if (data.status === 'success') {
                    toggleSelectionMode();
                    loadPhotos();
                } else {
                    alert('Toplu silme hatası: ' + data.message);
                }
            } catch (error) {
                console.error('Batch delete hatası:', error);
            } finally {
                batchDeleteBtn.disabled = false;
                updateBatchButtonStates();
            }
        });
    }

    async function loadPhotos() {
        const gallery = document.getElementById('photo-gallery');
        if (!gallery) return;

        try {
            const response = await fetch('/list_photos');
            const data = await response.json();

            gallery.innerHTML = '';

            if (!data.photos || data.photos.length === 0) {
                gallery.innerHTML = '<span class="no-photos-msg">Henüz fotoğraf çekilmedi. Kameraya 👍 işareti yapın.</span>';
                if (selectModeBtn) selectModeBtn.style.display = 'none';
                return;
            }

            if (selectModeBtn) selectModeBtn.style.display = 'inline-block';

            data.photos.forEach(photo => {
                const item = document.createElement('div');
                item.className = 'gallery-photo-item';
                if (isSelectionMode) {
                    item.className += ' selection-active';
                    if (selectedPhotos.has(photo.filename)) {
                        item.className += ' selected';
                    }
                }
                item.setAttribute('data-url', photo.url);
                item.setAttribute('data-filename', photo.filename);
                item.innerHTML = `
                    <img src="${photo.url}" alt="Captured Photo">
                    <span class="select-checkbox"></span>
                    <span class="gallery-photo-badge">Zamanlayıcı</span>
                    <button class="gallery-photo-delete-icon" title="Fotoğrafı Sil">
                        <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                    </button>
                `;

                item.addEventListener('click', (e) => {
                    if (isSelectionMode) {
                        e.stopPropagation();
                        if (selectedPhotos.has(photo.filename)) {
                            selectedPhotos.delete(photo.filename);
                            item.classList.remove('selected');
                        } else {
                            selectedPhotos.add(photo.filename);
                            item.classList.add('selected');
                        }
                        updateBatchButtonStates();
                    } else {
                        if (!e.target.closest('.gallery-photo-delete-icon')) {
                            openLightbox(photo.url, photo.timestamp);
                        }
                    }
                });

                item.querySelector('.gallery-photo-delete-icon').addEventListener('click', (e) => {
                    e.stopPropagation();
                    if (!isSelectionMode) {
                        deletePhoto(photo.filename);
                    }
                });

                gallery.appendChild(item);
            });
        } catch (error) {
            console.error('Fotoğraflar yüklenemedi:', error);
        }
    }

    // ---------------------------------------------------------------
    // 11. Live Telemetry Polling & Hand/Face Stats
    // ---------------------------------------------------------------
    const liveFingersVal = document.getElementById('live-fingers-val');
    const liveHandsVal = document.getElementById('live-hands-val');
    const liveHandTypeVal = document.getElementById('live-hand-type-val');
    const liveFacesVal = document.getElementById('live-faces-val');
    const liveExpressionVal = document.getElementById('live-expression-val');
    const detectedObjectsVal = document.getElementById('detected-objects-val');
    let lastProcessedSwipeTime = 0;

    async function updateStats() {
        try {
            const response = await fetch('/stats');
            const data = await response.json();

            // Telemetri Değerleri
            if (liveFingersVal) liveFingersVal.textContent = data.total_fingers !== undefined ? data.total_fingers : '0';
            if (liveHandsVal) liveHandsVal.textContent = data.hand_count !== undefined ? data.hand_count : '0';
            if (liveHandTypeVal) liveHandTypeVal.textContent = data.hand_types || 'Hiçbiri';
            if (liveFacesVal) liveFacesVal.textContent = data.face_count !== undefined ? data.face_count : '0';
            if (liveExpressionVal) liveExpressionVal.textContent = data.face_expression || 'Normal';

            if (detectedObjectsVal) {
                if (data.detected_objects && data.detected_objects.length > 0) {
                    const uniqueObjects = [...new Set(data.detected_objects)];
                    detectedObjectsVal.textContent = uniqueObjects.join(', ');
                } else {
                    detectedObjectsVal.textContent = 'Hiçbiri';
                }
            }

            // Thumbs Up ile Fotoğraf Tetikleme
            if (data.thumbs_up_detected) {
                startCountdown();
            }

            // Duygu Grafiği Güncelleme
            if (expressionChart) {
                const currentExpr = data.face_expression || 'Normal';
                let key = 'Normal';
                if (currentExpr === 'Mutlu' || currentExpr === 'Happy') {
                    key = 'Mutlu';
                    triggerEmojiRain();
                } else if (currentExpr === 'Saskin' || currentExpr === 'Surprised') {
                    key = 'Saskin';
                } else if (currentExpr === 'Uzgun' || currentExpr === 'Sad') {
                    key = 'Uzgun';
                }

                expressionCounts[key]++;
                expressionChart.data.datasets[0].data = [
                    expressionCounts['Normal'],
                    expressionCounts['Mutlu'],
                    expressionCounts['Saskin'],
                    expressionCounts['Uzgun']
                ];
                expressionChart.update();
            }

            // Mimik Oyunu Kontrolü
            if (gameActive && gameTarget) {
                const success = gameTarget.check(data);
                if (success) {
                    flashCameraStage('green');
                    gameScore++;
                    if (gameScoreVal) gameScoreVal.textContent = gameScore;
                    startNewChallenge();
                }
            }

            // Açık El / Yumruk ile Dinamik Zoom Kontrolü & Rozet Gösterimi
            if (data.zoom_factor !== undefined && videoStream) {
                videoStream.style.transition = 'transform 0.1s ease-out';
                videoStream.style.transform = `scale(${data.zoom_factor})`;

                const zoomPill = document.getElementById('zoom-indicator-pill');
                const zoomText = document.getElementById('zoom-level-text');
                if (zoomPill && zoomText) {
                    if (data.zoom_factor > 1.05) {
                        zoomPill.style.display = 'flex';
                        zoomText.textContent = `${data.zoom_factor.toFixed(1)}x Zoom`;
                    } else {
                        zoomPill.style.display = 'none';
                    }
                }
            }

            // Temassız Swipe (Filtre Değiştirme)
            if (data.swipe_event && data.swipe_timestamp > lastProcessedSwipeTime) {
                lastProcessedSwipeTime = data.swipe_timestamp;
                const activeBtn = document.querySelector('.filter-btn.active');
                if (activeBtn) {
                    const btnsArray = Array.from(filterButtons);
                    let currIdx = btnsArray.indexOf(activeBtn);
                    if (data.swipe_event === 'right') {
                        currIdx = (currIdx + 1) % btnsArray.length;
                    } else if (data.swipe_event === 'left') {
                        currIdx = (currIdx - 1 + btnsArray.length) % btnsArray.length;
                    }
                    btnsArray[currIdx].click();
                }
            }
        } catch (error) {
            // Sessiz yakalama
        }
    }

    // Başlangıç
    loadPhotos();
    // 80ms ultra-hızlı senkronizasyon (Anlık el tepkisi)
    setInterval(updateStats, 80);
    updateStats();

    // Klavye kısayolları
    document.addEventListener('keydown', function (e) {
        if (e.key === '1') document.querySelector('[data-filter="normal"]')?.click();
        if (e.key === '2') document.querySelector('[data-filter="grayscale"]')?.click();
    });
});
