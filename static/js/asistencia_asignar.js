document.addEventListener('DOMContentLoaded', () => {
    // 1. Buscador de Programas
    const searchProgramas = document.getElementById('searchProgramas');
    if (searchProgramas) {
        searchProgramas.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('#tablaProgramas tbody tr');
            let visibles = 0;
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(query)) {
                    row.style.display = '';
                    visibles++;
                } else {
                    row.style.display = 'none';
                }
            });
            
            const badge = document.getElementById('badgeProgramasVisibles');
            if (badge) badge.textContent = visibles;
        });
    }

    // 2. Buscador Global de Fichas
    const searchFichas = document.getElementById('searchFichas');
    if (searchFichas) {
        searchFichas.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            const details = document.querySelectorAll('.asig-details');
            
            details.forEach(detail => {
                const rows = detail.querySelectorAll('tbody tr');
                let hasMatch = false;
                
                rows.forEach(row => {
                    const text = row.textContent.toLowerCase();
                    if (text.includes(query)) {
                        row.style.display = '';
                        hasMatch = true;
                    } else {
                        row.style.display = 'none';
                    }
                });
                
                if (query !== '' && hasMatch) {
                    detail.open = true;
                }
                
                // Si ninguna fila hace match y hay query, ocultamos todo el detail
                if (query !== '' && !hasMatch) {
                    detail.style.display = 'none';
                } else {
                    detail.style.display = '';
                }
            });
        });
    }

    // 3. Checkbox "Seleccionar todos" para programas
    const chkAllProgramas = document.getElementById('chkAllProgramas');
    if (chkAllProgramas) {
        chkAllProgramas.addEventListener('change', (e) => {
            const isChecked = e.target.checked;
            // Solo afectar a los visibles
            const visibleCheckboxes = document.querySelectorAll('#tablaProgramas tbody tr:not([style*="display: none"]) .chk-programa');
            visibleCheckboxes.forEach(chk => {
                chk.checked = isChecked;
            });
            updateContadorProgramas();
        });
    }
    
    // Contadores de programas seleccionados
    const chkProgramas = document.querySelectorAll('.chk-programa');
    chkProgramas.forEach(chk => {
        chk.addEventListener('change', updateContadorProgramas);
    });
    
    function updateContadorProgramas() {
        const sel = document.querySelectorAll('.chk-programa:checked').length;
        const total = document.querySelectorAll('.chk-programa').length;
        const badge = document.getElementById('badgeProgramasSeleccionados');
        if (badge) badge.textContent = `${sel} de ${total} seleccionados`;
    }

    // 4. Checkbox "Seleccionar todos" para fichas (por grupo)
    const chkAllFichasGroups = document.querySelectorAll('.chk-all-fichas');
    chkAllFichasGroups.forEach(chkGroup => {
        chkGroup.addEventListener('change', (e) => {
            const isChecked = e.target.checked;
            const targetProg = e.target.getAttribute('data-prog');
            const checkboxes = document.querySelectorAll(`.chk-ficha[data-prog="${targetProg}"]:not([style*="display: none"])`);
            
            checkboxes.forEach(chk => {
                chk.checked = isChecked;
            });
            updateContadoresFichas(targetProg);
        });
    });

    const chkFichas = document.querySelectorAll('.chk-ficha');
    chkFichas.forEach(chk => {
        chk.addEventListener('change', (e) => {
            const prog = e.target.getAttribute('data-prog');
            updateContadoresFichas(prog);
        });
    });
    
    function updateContadoresFichas(progId) {
        const sel = document.querySelectorAll(`.chk-ficha[data-prog="${progId}"]:checked`).length;
        const total = document.querySelectorAll(`.chk-ficha[data-prog="${progId}"]`).length;
        const badge = document.getElementById(`badgeFichas_${progId}`);
        if (badge) badge.textContent = `${sel} seleccionadas`;
        
        // Actualizar global
        const selGlobal = document.querySelectorAll('.chk-ficha:checked').length;
        const totalGlobal = document.querySelectorAll('.chk-ficha').length;
        const badgeGlobal = document.getElementById('badgeFichasGlobal');
        if (badgeGlobal) badgeGlobal.textContent = `${selGlobal} de ${totalGlobal} seleccionadas`;
    }

    // Inicializar contadores
    updateContadorProgramas();
    document.querySelectorAll('.chk-all-fichas').forEach(g => {
        updateContadoresFichas(g.getAttribute('data-prog'));
    });

    // 5. Prevención de doble submit
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const btn = this.querySelector('button[type="submit"]');
            if (btn) {
                // Prevenir doble click
                if (btn.hasAttribute('disabled')) {
                    e.preventDefault();
                    return;
                }
                btn.setAttribute('disabled', 'disabled');
                const originalText = btn.innerHTML;
                btn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Guardando...`;
                
                // Habilitar en caso de fallo despues de 10s
                setTimeout(() => {
                    btn.removeAttribute('disabled');
                    btn.innerHTML = originalText;
                }, 10000);
            }
        });
    });
});
