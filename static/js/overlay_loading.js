/**
 * overlay_loading.js
 * Módulo para gestionar el overlay de carga con temporizador para SIGDA.
 */

const SigdaOverlay = (function() {
    let timerInterval = null;
    let startTime = null;

    function formatTime(seconds) {
        const m = Math.floor(seconds / 60).toString().padStart(2, '0');
        const s = (seconds % 60).toString().padStart(2, '0');
        return `${m}:${s}`;
    }

    function show(text = 'Generando documentos...', subtext = 'Por favor espera un momento.') {
        const overlay = document.getElementById('sigda-overlay');
        if (!overlay) return;

        document.getElementById('sigda-overlay-text').textContent = text;
        document.getElementById('sigda-overlay-subtext').textContent = subtext;
        
        // Reset timer
        const timerEl = document.getElementById('sigda-overlay-timer');
        timerEl.textContent = '00:00';
        startTime = Date.now();
        
        if (timerInterval) clearInterval(timerInterval);
        timerInterval = setInterval(() => {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            timerEl.textContent = formatTime(elapsed);
        }, 1000);

        // Show overlay
        overlay.classList.remove('d-none');
        overlay.style.display = 'flex'; // Ensure flex layout
    }

    function hide() {
        const overlay = document.getElementById('sigda-overlay');
        if (!overlay) return;
        
        if (timerInterval) clearInterval(timerInterval);
        timerInterval = null;
        
        overlay.classList.add('d-none');
    }

    function showError(message) {
        hide();
        // Mostrar error usando toast o un alert incrustado. Por ahora alert sencillo.
        alert('Error: ' + message);
    }

    /**
     * Intercepta el submit de un form para enviarlo por AJAX/fetch
     * y poder descargar el Blob directamente, controlando el modal.
     */
    function attachToForm(formId) {
        const form = document.getElementById(formId);
        if (!form) return;

        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const btn = form.querySelector('button[type="submit"]') || form.querySelector('button');
            if (btn) {
                btn.disabled = true;
                btn.classList.add('disabled');
            }

            const loadingText = form.getAttribute('data-loading') || 'Procesando...';
            show(loadingText, 'Esto puede tomar hasta 1 minuto. No cierres la ventana.');

            try {
                const formData = new FormData(form);
                const response = await fetch(form.action, {
                    method: form.method || 'POST',
                    body: formData,
                    // Evitar que el browser siga redirects solos si queremos manejar errores
                    redirect: 'follow' 
                });

                if (!response.ok) {
                    throw new Error(`Error en el servidor: ${response.status}`);
                }

                // Intentar leer el nombre del archivo del header Content-Disposition
                let filename = 'documentos.zip';
                const disposition = response.headers.get('Content-Disposition');
                if (disposition && disposition.indexOf('attachment') !== -1) {
                    const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                    const matches = filenameRegex.exec(disposition);
                    if (matches != null && matches[1]) { 
                        filename = matches[1].replace(/['"]/g, '');
                    }
                }

                const blob = await response.blob();
                
                // Si la respuesta es JSON o HTML (por error), el blob será texto
                if (blob.type.includes('text/html') || blob.type.includes('application/json')) {
                    const text = await blob.text();
                    console.error("Respuesta inesperada (posible error del backend):", text);
                    showError('Error al generar el documento. Verifica los datos.');
                    return;
                }

                // Forzar la descarga del Blob
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                a.remove();
                
                hide();

            } catch (err) {
                console.error(err);
                showError('Hubo un problema de conexión o generación.');
            } finally {
                if (btn) {
                    btn.disabled = false;
                    btn.classList.remove('disabled');
                }
            }
        });
    }

    return { show, hide, attachToForm };
})();
