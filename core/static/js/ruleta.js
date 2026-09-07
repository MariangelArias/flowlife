const canvas = document.getElementById("ruletaCanvas");
const ctx = canvas.getContext("2d");

const btn = document.getElementById("spinBtn");
const result = document.getElementById("resultado");

let angle = 0;
let speed = 0;
let spinning = false;

const items = (window.actividades || []).map(a => a.titulo);

const colors = [
    "#b48df9", // violeta
    "#5a9de5", // índigo
    "#90e9f9", // cyan
    "#91fcd8", // verde
    "#f9daa6"  // ámbar
];

function draw() {
    const center = 210;
    const radius = 200;

    ctx.clearRect(0, 0, 420, 420);

    // fondo moderno oscuro suave
    ctx.beginPath();
    ctx.fillStyle = "#111827";
    ctx.arc(center, center, radius, 0, Math.PI * 2);
    ctx.fill();

    if (!items.length) {
        ctx.fillStyle = "#050608";
        ctx.font = "16px sans-serif";
        ctx.fillText("Sin actividades", 145, 210);
        return;
    }

    const arc = (Math.PI * 2) / items.length;

    for (let i = 0; i < items.length; i++) {
        const start = angle + i * arc;

        // segmento
        ctx.beginPath();
        ctx.fillStyle = colors[i % colors.length];

        ctx.moveTo(center, center);
        ctx.arc(center, center, radius, start, start + arc);
        ctx.fill();

        // texto limpio y centrado
        ctx.save();
        ctx.translate(center, center);
        ctx.rotate(start + arc / 2);

        ctx.fillStyle = "rgba(16, 10, 10, 0.95)";
        ctx.font = "bold 13px sans-serif";
        ctx.textAlign = "right";

        ctx.fillText(items[i], 180, 5);

        ctx.restore();
    }

  
}

function animate() {
    draw();

    if (spinning) {
        angle += speed;
        speed *= 0.985;

        if (speed < 0.002) {
            spinning = false;
            finish();
        }
    }

    requestAnimationFrame(animate);
}

function spin() {
    if (!items.length) {
        result.textContent = "No hay actividades";
        return;
    }

    spinning = true;
    speed = Math.random() * 0.25 + 0.25;
}

function finish() {
    const arc = (Math.PI * 2) / items.length;
    const normalized = angle % (Math.PI * 2);

    const index = Math.floor(
        items.length - normalized / (Math.PI * 2) * items.length
    );

    result.innerHTML = `
        <div style="
            margin-top: 14px;
            padding: 10px 16px;
            display: inline-block;
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(148,121,200,0.35);
            border-radius: 12px;
            color: #9479c8;
            font-weight: 600;
            font-size: 20px;
            letter-spacing: 0.3px;
            box-shadow: 0 8px 20px rgba(148,121,200,0.15);
        ">
            Hoy haces: ${items[index % items.length]}
        </div>
    `;
}

btn.addEventListener("click", spin);
animate();