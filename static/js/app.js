// ============================================================
// SIGDA — App JavaScript (Premium)
// ============================================================

document.addEventListener('DOMContentLoaded', function () {

  // ============================================================
  // 1. SIGNATURE PAD (HiDPI)
  // ============================================================
  const canvas = document.getElementById('firmaCanvas');
  if (canvas) {
    const dpr = Math.max(window.devicePixelRatio || 1, 2);
    const cssW = 400;
    const cssH = 150;
    canvas.width = cssW * dpr;
    canvas.height = cssH * dpr;
    canvas.style.width  = cssW + 'px';
    canvas.style.height = cssH + 'px';

    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);
    ctx.lineWidth = 2.5;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.strokeStyle = '#000';
    let dibujando = false;
    let haFirmado = false;

    function pos(e) {
      const r = canvas.getBoundingClientRect();
      const t = e.touches ? e.touches[0] : e;
      return { x: t.clientX - r.left, y: t.clientY - r.top };
    }
    function start(e) { dibujando = true; haFirmado = true; const p = pos(e); ctx.beginPath(); ctx.moveTo(p.x, p.y); e.preventDefault(); }
    function move(e) { if (!dibujando) return; const p = pos(e); ctx.lineTo(p.x, p.y); ctx.stroke(); e.preventDefault(); }
    function end() { dibujando = false; }

    canvas.addEventListener('mousedown', start);
    canvas.addEventListener('mousemove', move);
    canvas.addEventListener('mouseup', end);
    canvas.addEventListener('mouseout', end);
    canvas.addEventListener('touchstart', start, { passive: false });
    canvas.addEventListener('touchmove', move, { passive: false });
    canvas.addEventListener('touchend', end);

    const limpiar = document.getElementById('limpiarFirma');
    if (limpiar) limpiar.addEventListener('click', function () {
      ctx.clearRect(0, 0, cssW, cssH);
      haFirmado = false;
    });

    const form = canvas.closest('form');
    if (form) form.addEventListener('submit', function () {
      const campo = document.getElementById('firma_base64');
      if (campo && haFirmado) {
        const exportCanvas = document.createElement('canvas');
        exportCanvas.width = canvas.width;
        exportCanvas.height = canvas.height;
        const ectx = exportCanvas.getContext('2d');
        ectx.drawImage(canvas, 0, 0);
        campo.value = exportCanvas.toDataURL('image/png');
      }
    });
  }

  // ============================================================
  // 2. COUNTER ANIMATION (KPI VALUES)
  // ============================================================
  document.querySelectorAll('.kpi-value[data-count]').forEach(el => {
    const target = parseInt(el.getAttribute('data-count'), 10);
    if (isNaN(target) || target === 0) return;

    const duration = 1200; // ms
    const startTime = performance.now();
    el.textContent = '0';

    function animate(now) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(eased * target);
      el.textContent = current.toLocaleString('es-CO');
      if (progress < 1) requestAnimationFrame(animate);
    }
    requestAnimationFrame(animate);
  });

  // ============================================================
  // 3. AUTO-DISMISS FLASH MESSAGES
  // ============================================================
  document.querySelectorAll('.alert.alert-dismissible').forEach(alert => {
    setTimeout(() => {
      alert.classList.add('alert-fade-out');
      setTimeout(() => alert.remove(), 500);
    }, 6000);
  });

  // ============================================================
  // 4. LOADING SPINNER HELPER
  // ============================================================
  window.sigdaShowSpinner = function(text) {
    const overlay = document.createElement('div');
    overlay.className = 'sigda-loading';
    overlay.id = 'sigdaSpinner';
    overlay.innerHTML = `
      <div class="sigda-loading-content">
        <div class="sigda-spinner"></div>
        <div class="sigda-loading-text">${text || 'Procesando...'}</div>
      </div>
    `;
    document.body.appendChild(overlay);
  };

  window.sigdaHideSpinner = function() {
    const el = document.getElementById('sigdaSpinner');
    if (el) el.remove();
  };

  // Auto-attach spinner to forms with data-loading attribute
  document.querySelectorAll('form[data-loading]').forEach(form => {
    form.addEventListener('submit', function() {
      const msg = this.getAttribute('data-loading') || 'Procesando...';
      window.sigdaShowSpinner(msg);
      
      // Limpiar cookie previa si existiera
      document.cookie = "fileDownload=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
      
      // Chequear periodicamente si la descarga ya comenzó (la cookie fue seteada por el servidor)
      let downloadTimer = setInterval(function() {
        if (document.cookie.indexOf('fileDownload=true') !== -1) {
          clearInterval(downloadTimer);
          window.sigdaHideSpinner();
          // Limpiar la cookie para el proximo submit
          document.cookie = "fileDownload=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
        }
      }, 1000);
    });
  });

  // ============================================================
  // 5. STYLED CONFIRM DIALOG
  // ============================================================
  window.sigdaConfirm = function(message, onConfirm) {
    const overlay = document.createElement('div');
    overlay.className = 'sigda-confirm-overlay';
    overlay.innerHTML = `
      <div class="sigda-confirm-box">
        <div class="sigda-confirm-icon">
          <i class="bi bi-exclamation-triangle-fill"></i>
        </div>
        <div class="sigda-confirm-title">¿Estás seguro?</div>
        <div class="sigda-confirm-msg">${message}</div>
        <div class="sigda-confirm-actions">
          <button class="btn btn-outline-secondary sigda-cancel">Cancelar</button>
          <button class="btn btn-danger sigda-ok">Eliminar</button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);

    overlay.querySelector('.sigda-cancel').addEventListener('click', () => overlay.remove());
    overlay.querySelector('.sigda-ok').addEventListener('click', () => {
      overlay.remove();
      if (onConfirm) onConfirm();
    });
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) overlay.remove();
    });
  };

  // Replace native confirm on delete forms
  document.querySelectorAll('form[onsubmit*="confirm"]').forEach(form => {
    form.removeAttribute('onsubmit');
    form.addEventListener('submit', function(e) {
      e.preventDefault();
      const f = this;
      window.sigdaConfirm('Esta acción no se puede deshacer.', () => {
        f.removeEventListener('submit', arguments.callee);
        f.submit();
      });
    });
  });

  // ============================================================
  // 6. TOOLTIP INITIALIZATION (Bootstrap)
  // ============================================================
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(el => new bootstrap.Tooltip(el));

  // ============================================================
  // 7. WEBCAM (FOTO)
  // ============================================================
  const video = document.getElementById('webcamVideo');
  const webcamCanvas = document.getElementById('webcamCanvas');
  const startCameraBtn = document.getElementById('startCameraBtn');
  const takePhotoBtn = document.getElementById('takePhotoBtn');
  const retakePhotoBtn = document.getElementById('retakePhotoBtn');
  const fotoBase64 = document.getElementById('foto_base64');
  let stream = null;

  if (video && startCameraBtn) {
    startCameraBtn.addEventListener('click', async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } });
        video.srcObject = stream;
        video.style.display = 'block';
        startCameraBtn.style.display = 'none';
        takePhotoBtn.style.display = 'inline-block';
        webcamCanvas.style.display = 'none';
      } catch (err) {
        console.error('Error accediendo a la cámara:', err);
        alert('No se pudo acceder a la cámara. Asegúrate de dar los permisos correspondientes y estar en un entorno seguro (localhost o HTTPS).');
      }
    });

    takePhotoBtn.addEventListener('click', () => {
      if (!stream) return;
      const ctx = webcamCanvas.getContext('2d');
      
      // Redimensionar la imagen para que no sea muy pesada (max 400px de ancho)
      const MAX_WIDTH = 400;
      let width = video.videoWidth;
      let height = video.videoHeight;
      if (width > MAX_WIDTH) {
        height = Math.round(height * (MAX_WIDTH / width));
        width = MAX_WIDTH;
      }
      
      webcamCanvas.width = width;
      webcamCanvas.height = height;
      
      // Dibujar normal (el scaleX(-1) en CSS hace el efecto espejo visualmente)
      ctx.drawImage(video, 0, 0, width, height);
      
      // Exportar como JPEG con calidad 0.7 para asegurar que el string sea minúsculo
      fotoBase64.value = webcamCanvas.toDataURL('image/jpeg', 0.7);
      
      video.style.display = 'none';
      webcamCanvas.style.display = 'block';
      takePhotoBtn.style.display = 'none';
      retakePhotoBtn.style.display = 'inline-block';
    });

    retakePhotoBtn.addEventListener('click', () => {
      fotoBase64.value = '';
      webcamCanvas.style.display = 'none';
      video.style.display = 'block';
      retakePhotoBtn.style.display = 'none';
      takePhotoBtn.style.display = 'inline-block';
    });
    
    // Detener la cámara si se cambia de pestaña
    const uploadTab = document.getElementById('upload-foto-tab');
    if(uploadTab) {
        uploadTab.addEventListener('click', () => {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
                stream = null;
                video.style.display = 'none';
                startCameraBtn.style.display = 'inline-block';
                takePhotoBtn.style.display = 'none';
                retakePhotoBtn.style.display = 'none';
                webcamCanvas.style.display = 'none';
                fotoBase64.value = '';
            }
        });
    }
  }

});
