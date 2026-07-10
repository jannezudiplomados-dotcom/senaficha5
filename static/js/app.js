// Signature pad para el formulario de aprendices
// Usa HiDPI rendering para firmas nítidas en cualquier pantalla
document.addEventListener('DOMContentLoaded', function () {
  const canvas = document.getElementById('firmaCanvas');
  if (!canvas) return;

  // --- HiDPI: escalar el backing store para máxima nitidez ---
  const dpr = Math.max(window.devicePixelRatio || 1, 2); // mínimo 2x
  const cssW = 400;
  const cssH = 150;
  canvas.width = cssW * dpr;            // backing store grande (ej. 800×300)
  canvas.height = cssH * dpr;
  canvas.style.width  = cssW + 'px';    // tamaño visual igual
  canvas.style.height = cssH + 'px';

  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);                  // escalar contexto para dibujar en coords CSS
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
      // Exportar a alta resolución
      const exportCanvas = document.createElement('canvas');
      exportCanvas.width = canvas.width;   // 800+ px
      exportCanvas.height = canvas.height; // 300+ px
      const ectx = exportCanvas.getContext('2d');
      // Copiar la firma manteniendo el fondo transparente original
      ectx.drawImage(canvas, 0, 0);
      campo.value = exportCanvas.toDataURL('image/png');
    }
  });
});

