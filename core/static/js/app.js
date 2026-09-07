
let tableroData = {
    pendientes: [],
    progreso: [],
    completadas: [],
    solo_lectura: false,
    stats: {
        total: 0,
        pendientes: 0,
        completadas: 0,
        porcentaje: 0,
    },
};
let filtroActual = "total";
let weeklyChart = null;
let statisticsChart = null;

document.addEventListener("DOMContentLoaded", () => {

    if (document.getElementById("dashboard-board")) {
        cargarTablero();
        filtrar("total");
    }

    if (document.getElementById("activities-board")) {
        activarDrag();
    }

    if (document.getElementById("weeklyChart")) {
        cargarCargaSemanal();

        const weeklyTrackingForm = document.querySelector(".weekly-tracking-form");
        if (weeklyTrackingForm) {
            weeklyTrackingForm.addEventListener("submit", guardarTrackingSemanalSinRecargar);
        }
    }

    if (document.getElementById("statsChart")) {
        configurarEstadisticasSemanal();
    }

    
    inicializarScratchCard();

});

function activarDrag() {
    const boards = document.querySelectorAll(".board, #dashboard-board, #activities-board");

    boards.forEach((board) => {
        if (board.dataset.readonly === "1") return;

        const cards = board.querySelectorAll(".card");
        const columns = board.querySelectorAll(".column");

        cards.forEach((card) => {

            
            if (card.dataset.dragInitialized === "true") return;
            card.dataset.dragInitialized = "true";

            card.setAttribute("draggable", "true");

            let isDragging = false;

           
            card.addEventListener("dragstart", (e) => {
                draggedCard = card;
                isDragging = true;

                e.dataTransfer.setData("text/plain", card.dataset.id || "");
                e.dataTransfer.effectAllowed = "move";

                const ghost = card.cloneNode(true);
                ghost.style.position = "absolute";
                ghost.style.top = "-1000px";
                ghost.style.left = "-1000px";
                ghost.style.width = getComputedStyle(card).width;
                ghost.style.transform = "rotate(3deg) scale(1.05)";
                ghost.style.boxShadow = "0 25px 40px rgba(0,0,0,0.25)";
                ghost.style.opacity = "0.95";

                document.body.appendChild(ghost);
                e.dataTransfer.setDragImage(ghost, 20, 20);
                setTimeout(() => ghost.remove(), 0);

                card.classList.add("dragging");
            });

            
            card.addEventListener("dragend", () => {
                isDragging = false;
                card.classList.remove("dragging");
            });

           
            card.addEventListener("click", (e) => {
                if (isDragging || card.classList.contains("dragging")) return;

                const url = card.dataset.url;

                if (url) {
                    window.location.href = url;
                }
            });
        });

        
        columns.forEach((column) => {

            column.addEventListener("dragover", (e) => {
                e.preventDefault();
                column.classList.add("drag-over");
            });

            column.addEventListener("dragleave", () => {
                column.classList.remove("drag-over");
            });

            column.addEventListener("drop", async (e) => {
                e.preventDefault();
                column.classList.remove("drag-over");

                if (!draggedCard) return;

                const id = draggedCard.dataset.id;
                const estado = column.dataset.estado;
                const cardToAnimate = draggedCard;

                cardToAnimate.style.transition = "all 0.25s cubic-bezier(0.2, 0.9, 0.2, 1)";
                cardToAnimate.style.transform = "scale(0.92) rotate(-2deg)";

                try {
                    const response = await fetch("/mover/", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/x-www-form-urlencoded",
                            "X-CSRFToken": getCookie("csrftoken"),
                        },
                        body: `id=${encodeURIComponent(id)}&estado=${encodeURIComponent(estado)}`,
                    });

                    if (response.ok) {

                        cardToAnimate.classList.add("drop-pop");
                        column.classList.add("drop-bounce");

                        setTimeout(() => {
                            cardToAnimate.classList.remove("drop-pop");
                            column.classList.remove("drop-bounce");

                            cardToAnimate.style.transform = "";
                            cardToAnimate.style.transition = "";

                            if (document.getElementById("activities-board")) {
                                window.location.reload();
                            } else {
                                cargarTablero();
                            }
                        }, 300);
                    }
                } catch (error) {
                    console.error(error);
                }

                draggedCard = null;
            });
        });
    });
}
async function cargarTablero() {
    try {
        const response = await fetch("/api/tablero/", {
            cache: "no-store",
        });

        const data = await response.json();
        tableroData = data;

        pintarColumna("PENDIENTE", data.pendientes);
        pintarColumna("PROGRESO", data.progreso);
        pintarColumna("COMPLETADO", data.completadas);

        const total = document.getElementById("total");
        const pendientesCount = document.getElementById("pendientes-count");
        const completadasCount = document.getElementById("completadas-count");
        const porcentaje = document.getElementById("porcentaje");

        if (total) total.textContent = data.stats.total;
        if (pendientesCount) pendientesCount.textContent = data.stats.pendientes;
        if (completadasCount) completadasCount.textContent = data.stats.completadas;
        if (porcentaje) porcentaje.textContent = `${data.stats.porcentaje}%`;

        activarDrag();
        renderFiltro(filtroActual);
    } catch (error) {
        console.error(error);
    }
}

function pintarColumna(nombre, actividades) {
    const columna = document.querySelector(`[data-estado="${nombre}"]`);

    if (!columna) return;

    let titulo = "";

    if (nombre === "PENDIENTE") titulo = "Pendiente";
    if (nombre === "PROGRESO") titulo = "En progreso";
    if (nombre === "COMPLETADO") titulo = "Completado";

    columna.innerHTML = `<h2>${titulo}</h2>`;

    if (!actividades.length) {
        columna.innerHTML += `<p>No hay tareas</p>`;
        return;
    }

    actividades.forEach((actividad) => {
        const progreso = Number(actividad.progreso || 0);
        const propietario = actividad.propietario ? `<div class="task-owner">Propietario: ${actividad.propietario}</div>` : "";
        const draggable = tableroData.solo_lectura ? "false" : "true";
        columna.innerHTML += `
            <div class="card" draggable="${draggable}" data-id="${actividad.id}" data-progreso="${progreso}">
                <div class="card-head">
                    <strong>${actividad.titulo}</strong>
                    <span class="private-progress-label">${progreso}%</span>
                </div>
                <p>${actividad.tipo}</p>
                ${propietario}
                <div class="card-progress"><span style="width: ${progreso}%"></span></div>
            </div>
        `;
    });
}

function filtrar(tipo) {
    filtroActual = tipo;
    renderFiltro(tipo);
}

function renderFiltro(tipo) {
    const title = document.getElementById("activity-panel-title");
    const subtitle = document.getElementById("activity-panel-subtitle");
    const count = document.getElementById("activity-panel-count");
    const list = document.getElementById("activity-panel-list");

    if (!title || !subtitle || !count || !list) return;

    const todas = [
        ...tableroData.pendientes,
        ...tableroData.progreso,
        ...tableroData.completadas,
    ];

    let actividades = todas;
    let label = "Todas las actividades";
    let helper = "Resumen general del tablero.";

    if (tipo === "pendientes") {
        actividades = tableroData.pendientes;
        label = "Actividades pendientes";
        helper = "Tareas todavía sin terminar.";
    } else if (tipo === "completadas") {
        actividades = tableroData.completadas;
        label = "Actividades completadas";
        helper = "Tareas ya cerradas.";
    } else if (tipo === "progreso") {
        actividades = tableroData.progreso;
        label = "Actividades en progreso";
        helper = "Tareas moviéndose entre columnas.";
    }

    title.textContent = label;
    subtitle.textContent = helper;
    count.textContent = `${actividades.length} actividad${actividades.length === 1 ? "" : "es"}`;

    if (!actividades.length) {
        list.innerHTML = `<div class="activity-row"><strong>No hay actividades en esta categoría.</strong></div>`;
        return;
    }

    list.innerHTML = actividades
        .map((actividad) => {
            const progreso = Number(actividad.progreso || 0);
            const actividadId = `progress-${actividad.id}`;

            return `
                <div class="activity-row">
                    <div class="activity-row-top">
                        <div>
                            <strong>${actividad.titulo}</strong>
                            <div class="activity-row-meta">${actividad.tipo} · ${actividad.estado}</div>
                        </div>
                        <strong>${progreso}%</strong>
                    </div>
                    <div class="activity-row-progress"><span style="width: ${progreso}%"></span></div>
                    <div class="activity-row-controls">
                        <input id="${actividadId}" type="range" min="0" max="100" value="${progreso}">
                        <button type="button" onclick="guardarProgreso('${actividad.id}', '${actividadId}')">Guardar progreso</button>
                    </div>
                </div>
            `;
        })
        .join("");
}

async function guardarProgreso(actividadId, inputId) {
    const input = document.getElementById(inputId);

    if (!input) return;

    try {
        const response = await fetch("/api/actividad/progreso/", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            body: `actividad_id=${encodeURIComponent(actividadId)}&progreso=${encodeURIComponent(input.value)}`,
        });

        if (response.ok) {
            await cargarTablero();
            filtrar(filtroActual);
        }
    } catch (error) {
        console.error(error);
    }
}

async function cargarCargaSemanal() {
    try {
        const response = await fetch("/api/carga-semanal/", {
            cache: "no-store",
        });

        const data = await response.json();

        pintarCargaSemanal(data);
    } catch (error) {
        console.error(error);
    }
}

function pintarCargaSemanal(data) {
    const summary = document.getElementById("weekly-summary");

    if (summary) {
        summary.textContent = data.summary;
    }

    const ctx = document.getElementById("weeklyChart");
    if (!ctx || typeof Chart === "undefined") return;

    if (weeklyChart) {
        weeklyChart.destroy();
    }

    weeklyChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: data.labels,
            datasets: [{
                label: "Carga del día (1-5)",
                data: data.data,
                borderColor: "#7FA8D6",
                backgroundColor: "rgba(127,168,214,0.2)",
                tension: 0.4,
                fill: true,
                pointRadius: 5,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    min: 0,
                    max: 5,
                    ticks: {
                        stepSize: 1,
                    },
                },
            },
        },
    });
}

async function guardarTrackingSemanalSinRecargar(event) {
    event.preventDefault();

    const form = event.currentTarget;
    const formData = new FormData(form);

    try {
        const response = await fetch(form.action, {
            method: "POST",
            headers: {
                "X-Requested-With": "XMLHttpRequest",
            },
            body: formData,
        });

        if (!response.ok) {
            throw new Error("No se pudo guardar el seguimiento semanal");
        }

        const data = await response.json();
        pintarCargaSemanal(data);
    } catch (error) {
        console.error(error);
    }
}

function configurarEstadisticasSemanal() {
    const buttons = document.querySelectorAll("[data-week-button]");

    if (!buttons.length) return;

    buttons.forEach((button) => {
        button.addEventListener("click", () => {
            cargarEstadisticasSemanal(button.dataset.week);
        });
    });

    const activeButton = document.querySelector("[data-week-button].is-active") || buttons[0];
    if (activeButton) {
        cargarEstadisticasSemanal(activeButton.dataset.week);
    }
}

async function cargarEstadisticasSemanal(weekStart) {
    const summary = document.getElementById("stats-week-summary");
    const title = document.getElementById("stats-week-label");
    const average = document.getElementById("stats-week-average");

    try {
        const response = await fetch(`/api/estadisticas/semanales/?week=${encodeURIComponent(weekStart)}`, {
            cache: "no-store",
        });

        const data = await response.json();

        if (summary) summary.textContent = data.summary;
        if (title) title.textContent = data.week_label;
        if (average) average.textContent = `${data.average}`;

        document.querySelectorAll("[data-week-button]").forEach((button) => {
            button.classList.toggle("is-active", button.dataset.week === data.week_start);
        });

        const ctx = document.getElementById("statsChart");
        if (!ctx || typeof Chart === "undefined") return;

        if (statisticsChart) {
            statisticsChart.destroy();
        }

        statisticsChart = new Chart(ctx, {
            type: "line",
            data: {
                labels: data.labels,
                datasets: [{
                    label: "Carga del día (1-5)",
                    data: data.data,
                    borderColor: "#6FA8DC",
                    backgroundColor: "rgba(111,168,220,0.2)",
                    tension: 0.4,
                    fill: true,
                    pointRadius: 5,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        min: 0,
                        max: 5,
                        ticks: {
                            stepSize: 1,
                        },
                    },
                },
            },
        });

    } catch (error) {
        console.error(error);
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

window.filtrar = filtrar;
window.guardarProgreso = guardarProgreso;
window.cargarEstadisticasSemanal = cargarEstadisticasSemanal;


function inicializarScratchCard() {

    const modal = document.getElementById("scratchModal");
    if (!modal) return;

    const canvas = document.getElementById("scratchCanvas");
    const closeBtn = document.getElementById("closeScratch");
    const phraseEl = document.getElementById("phrase");

    if (!canvas || !closeBtn || !phraseEl) return;

    const frases = [
        "La disciplina es elegir entre lo que quieres ahora y lo que quieres conseguir.",
        "Hoy es un buen día para avanzar aunque sea un 1%.",
        "Lo que haces hoy construye tu futuro.",
        "No tienes que ser perfecto, solo constante.",
        "Pequeños pasos diarios crean grandes resultados.",
        "Sigue aunque sea lento, pero no te detengas."
    ];

    phraseEl.textContent = frases[Math.floor(Math.random() * frases.length)];

    const ctx = canvas.getContext("2d");
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    crearCapa(ctx, canvas);

    let raspando = false;

    canvas.addEventListener("mousedown", () => raspando = true);
    window.addEventListener("mouseup", () => raspando = false);

    canvas.addEventListener("mousemove", (e) => {
        if (!raspando) return;
        raspar(e, canvas, ctx);
    });

    canvas.addEventListener("touchstart", () => raspando = true);
    canvas.addEventListener("touchend", () => raspando = false);

    canvas.addEventListener("touchmove", (e) => {
        e.preventDefault();
        if (!raspando) return;
        rasparTouch(e, canvas, ctx);
    });

    closeBtn.addEventListener("click", async () => {

    try {
        const res = await fetch("/scratch/marcar/", {
            method: "POST",
            credentials: "same-origin",
            headers: {
                "X-CSRFToken": getCookie("csrftoken")
            }
        });

        const data = await res.json();
        console.log("SCRATCH SAVED:", data);

    } catch (err) {
        console.log("ERROR SCRATCH:", err);
    }

    modal.style.display = "none";
    });
}



function crearCapa(ctx,canvas){

    ctx.fillStyle="#dce9fa";

    ctx.fillRect(0,0,canvas.width,canvas.height);

    for(let i=0;i<250;i++){

        ctx.beginPath();

        ctx.fillStyle=Math.random()>.5
            ? "rgba(255,255,255,.65)"
            : "rgba(185,167,245,.45)";

        ctx.arc(

            Math.random()*canvas.width,

            Math.random()*canvas.height,

            Math.random()*2+1,

            0,

            Math.PI*2

        );

        ctx.fill();

    }

}

function raspar(event,canvas,ctx,closeBtn){

    const rect=canvas.getBoundingClientRect();

    borrar(

        event.clientX-rect.left,

        event.clientY-rect.top,

        ctx

    );

    revisar(canvas,ctx,closeBtn);

}

function rasparTouch(event,canvas,ctx,closeBtn){

    const rect=canvas.getBoundingClientRect();

    const touch=event.touches[0];

    borrar(

        touch.clientX-rect.left,

        touch.clientY-rect.top,

        ctx

    );

    revisar(canvas,ctx, closeBtn);

}

function borrar(x,y,ctx){

    ctx.globalCompositeOperation="destination-out";

    ctx.beginPath();

    ctx.arc(x,y,22,0,Math.PI*2);

    ctx.fill();

}

function revisar(canvas, ctx, closeBtn) {

    const pixels = ctx.getImageData(
        0,
        0,
        canvas.width,
        canvas.height
    ).data;

    let transparentes = 0;

    for (let i = 3; i < pixels.length; i += 4) {
        if (pixels[i] === 0) {
            transparentes++;
        }
    }

    const total = pixels.length / 4;
    const porcentaje = transparentes / total;

    if (porcentaje > 0.20) {

        canvas.style.transition = ".8s";
        canvas.style.opacity = "0";
        canvas.style.pointerEvents = "none";

        if (closeBtn) {
            closeBtn.classList.add("show");
        }
    }
}



function eliminarActividad(btn) {

    const id = btn.dataset.id;

    if (!confirm("¿Seguro que quieres eliminar esta tarea?")) return;

    fetch(`/actividad/eliminar-ajax/${id}/`, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCookie("csrftoken"),
        }
    })
    .then(res => res.json())
    .then(data => {

        if (data.ok) {
            // eliminar del DOM
            btn.closest(".card").remove();
        }

    });

}