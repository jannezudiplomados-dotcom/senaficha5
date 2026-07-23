document.addEventListener("DOMContentLoaded", function () {
    let currentStep = 1;
    const totalSteps = 6;
    const MAX_APRENDICES = 5;

    const btnNext = document.getElementById("btn-next");
    const btnPrev = document.getElementById("btn-prev");
    const btnSubmit = document.getElementById("btn-submit");
    const tabs = document.querySelectorAll(".nav-link");
    const tabPanes = document.querySelectorAll(".tab-pane");

    // Datos temporales
    let aprendicesDisponibles = [];

    // Funciones de navegación
    function updateWizard() {
        tabs.forEach((tab, index) => {
            if (index < currentStep) {
                tab.classList.remove("disabled");
                if (index === currentStep - 1) {
                    tab.classList.add("active");
                } else {
                    tab.classList.remove("active");
                }
            } else {
                tab.classList.add("disabled");
                tab.classList.remove("active");
            }
        });

        tabPanes.forEach((pane, index) => {
            if (index === currentStep - 1) {
                pane.classList.add("show", "active");
            } else {
                pane.classList.remove("show", "active");
            }
        });

        btnPrev.classList.toggle("d-none", currentStep === 1);
        if (currentStep === totalSteps) {
            btnNext.classList.add("d-none");
            btnSubmit.classList.remove("d-none");
            buildArlTable(); // Construir tabla ARL antes de mostrar el paso 6
        } else {
            btnNext.classList.remove("d-none");
            btnSubmit.classList.add("d-none");
        }
    }

    btnNext.addEventListener("click", () => {
        if (validateStep(currentStep)) {
            currentStep++;
            updateWizard();
            if (currentStep === 2) {
                loadAprendicesDisponibles();
            }
        }
    });

    btnPrev.addEventListener("click", () => {
        if (currentStep > 1) {
            currentStep--;
            updateWizard();
        }
    });

    function validateStep(step) {
        const pane = document.getElementById(`paso${step}`);
        const inputs = pane.querySelectorAll('input[required], select[required]');
        let valid = true;
        inputs.forEach(input => {
            if (!input.value) {
                input.classList.add('is-invalid');
                valid = false;
            } else {
                input.classList.remove('is-invalid');
            }
        });
        
        if (step === 2) {
            const selectores = document.querySelectorAll('.aprendiz-select');
            if (selectores.length === 0) {
                alert("Debe agregar al menos un aprendiz.");
                valid = false;
            }
        }
        return valid;
    }

    // Cargar Programas al inicio
    fetch('/bitacoras-art-media/api/programas')
        .then(res => res.json())
        .then(data => {
            const select = document.getElementById('programa_id');
            data.forEach(p => {
                const opt = document.createElement('option');
                opt.value = p.id;
                opt.textContent = p.nombre;
                select.appendChild(opt);
            });
        });

    // Cargar Fichas cuando cambia programa
    document.getElementById('programa_id').addEventListener('change', function() {
        const progId = this.value;
        const fichaSelect = document.getElementById('ficha_id');
        fichaSelect.innerHTML = '<option value="">Seleccione una ficha...</option>';
        if (progId) {
            fetch(`/bitacoras-art-media/api/fichas?programa_id=${progId}`)
                .then(res => res.json())
                .then(data => {
                    data.forEach(f => {
                        const opt = document.createElement('option');
                        opt.value = f.id;
                        opt.textContent = f.numero;
                        fichaSelect.appendChild(opt);
                    });
                    fichaSelect.disabled = false;
                });
        } else {
            fichaSelect.disabled = true;
        }
    });

    // Cargar Plantillas 'grupal'
    fetch('/bitacoras-art-media/api/plantillas?tipo=grupal&activa=1')
        .then(res => res.json())
        .then(data => {
            const select = document.getElementById('plantilla_id');
            data.forEach(pl => {
                const opt = document.createElement('option');
                opt.value = pl.id;
                opt.textContent = pl.nombre;
                select.appendChild(opt);
            });
        });

    // Paso 2: Aprendices
    function loadAprendicesDisponibles() {
        const fichaId = document.getElementById('ficha_id').value;
        fetch(`/bitacoras-art-media/api/aprendices?ficha_id=${fichaId}`)
            .then(res => res.json())
            .then(data => {
                aprendicesDisponibles = data;
                if (document.querySelectorAll('.aprendiz-row').length === 0) {
                    addAprendizRow();
                }
            });
    }

    document.getElementById('btn-add-aprendiz').addEventListener('click', function() {
        const currentCount = document.querySelectorAll('.aprendiz-row').length;
        if (currentCount < MAX_APRENDICES) {
            addAprendizRow();
        } else {
            alert(`Máximo ${MAX_APRENDICES} aprendices permitidos.`);
        }
    });

    function addAprendizRow() {
        const container = document.getElementById('aprendices-container');
        const idx = document.querySelectorAll('.aprendiz-row').length;
        
        let options = '<option value="">Seleccione aprendiz...</option>';
        aprendicesDisponibles.forEach(a => {
            options += `<option value="${a.id}">${a.identificacion} - ${a.apellidos} ${a.nombres}</option>`;
        });

        const row = document.createElement('div');
        row.className = 'row mb-3 aprendiz-row';
        row.dataset.index = idx;
        row.innerHTML = `
            <div class="col-md-5">
                <select class="form-select aprendiz-select" name="aprendices[]" required>
                    ${options}
                </select>
            </div>
            <div class="col-md-5">
                <div class="datos-aprendiz text-muted small mt-1"></div>
            </div>
            <div class="col-md-2">
                <button type="button" class="btn btn-outline-danger btn-sm px-2 py-1 fw-bold" onclick="this.closest('.aprendiz-row').remove()">X</button>
            </div>
        `;
        
        container.appendChild(row);

        const select = row.querySelector('.aprendiz-select');
        select.addEventListener('change', function() {
            const aid = this.value;
            const infoDiv = row.querySelector('.datos-aprendiz');
            if (aid) {
                fetch(`/bitacoras-art-media/api/aprendiz/${aid}`)
                    .then(res => res.json())
                    .then(data => {
                        infoDiv.innerHTML = `
                            <strong>Tel:</strong> ${data.telefono || ''}<br>
                            <strong>Correo:</strong> ${data.correo_institucional || data.correo_personal || ''}<br>
                            ${data.url_firma_png ? '<span class="text-success">✓ Firma registrada</span>' : '<span class="text-warning">⚠ Sin firma</span>'}
                        `;
                    });
            } else {
                infoDiv.innerHTML = '';
            }
        });

        row.querySelector('.btn-remove-aprendiz').addEventListener('click', function() {
            row.remove();
        });
    }

    // Paso 5: Actividades
    const tbodyActividades = document.getElementById('actividades-body');
    
    function addActividadRow() {
        const tr = document.createElement('tr');
        tr.className = 'actividad-row';
        tr.innerHTML = `
            <td><input type="text" class="form-control" name="act_desc[]" required></td>
            <td><input type="text" class="form-control" name="act_comp[]" placeholder="Opcional"></td>
            <td><input type="date" class="form-control" name="act_fini[]" required></td>
            <td><input type="date" class="form-control" name="act_ffin[]" required></td>
            <td>
                <select class="form-select" name="act_evid[]">
                    <option value="Documento">Documento</option>
                    <option value="Proceso">Proceso</option>
                    <option value="Producto">Producto</option>
                    <option value="Entregable">Entregable</option>
                </select>
            </td>
            <td><input type="text" class="form-control" name="act_obs[]"></td>
            <td><button type="button" class="btn btn-sm btn-outline-danger btn-remove-act fw-bold">X</button></td>
        `;
        tbodyActividades.appendChild(tr);
        
        tr.querySelector('.btn-remove-act').addEventListener('click', function() {
            tr.remove();
        });
    }

    document.getElementById('btn-add-actividad').addEventListener('click', addActividadRow);

    // Inicializar 5 filas
    for(let i=0; i<5; i++) addActividadRow();


    // Paso 6: Construir tabla ARL
    function buildArlTable() {
        const tbody = document.getElementById('arl-body');
        tbody.innerHTML = '';
        const selects = document.querySelectorAll('.aprendiz-select');
        
        selects.forEach((select, i) => {
            if(select.value) {
                const text = select.options[select.selectedIndex].text;
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>
                        <input type="hidden" name="arl_aprendiz_id[]" value="${select.value}">
                        ${text.split('-')[1].trim()}
                    </td>
                    <td>
                        <select class="form-select" name="arl_afil[]">
                            <option value="SI">SI</option>
                            <option value="NO">NO</option>
                        </select>
                    </td>
                    <td>
                        <select class="form-select" name="arl_riesgo[]">
                            <option value="1">1</option>
                            <option value="2">2</option>
                            <option value="3">3</option>
                            <option value="4">4</option>
                            <option value="5">5</option>
                        </select>
                    </td>
                    <td>
                        <select class="form-select" name="arl_corr[]">
                            <option value="SI">SI</option>
                            <option value="NO">NO</option>
                        </select>
                    </td>
                    <td>
                        <select class="form-select" name="arl_epp[]">
                            <option value="SI">SI</option>
                            <option value="NO">NO</option>
                            <option value="NA">NA</option>
                        </select>
                    </td>
                `;
                tbody.appendChild(tr);
            }
        });
    }

    // Submit
    btnSubmit.addEventListener('click', function() {
        if (!validateStep(currentStep)) return;
        
        const form = document.getElementById('bitacoraForm');
        const formData = new FormData(form);
        
        // Simulación visual
        document.getElementById('submit-spinner').classList.remove('d-none');
        btnSubmit.disabled = true;
        
        fetch('/bitacoras-art-media/api/generar', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.getElementById('csrf_token').value
            }
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                window.location.href = "/bitacoras-art-media/historial";
            } else {
                alert("Error: " + data.message);
                document.getElementById('submit-spinner').classList.add('d-none');
                btnSubmit.disabled = false;
            }
        })
        .catch(err => {
            console.error(err);
            alert("Ocurrió un error al generar la bitácora.");
            document.getElementById('submit-spinner').classList.add('d-none');
            btnSubmit.disabled = false;
        });
    });
});
