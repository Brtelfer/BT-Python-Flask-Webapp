// ---- Config mirrors CONVERSIONS in app.py ----
const CONVERSIONS = {
    mp3_txt:  { accept: ".mp3,audio/mpeg",      label: "MP3 → TXT"  },
    mp4_mp3:  { accept: ".mp4,video/mp4",       label: "MP4 → MP3"  },
    pdf_epub: { accept: ".pdf,application/pdf", label: "PDF → ePub" },
};

let currentType = "mp3_txt";

const grid       = document.getElementById("conversionGrid");
const fileInput  = document.getElementById("fileInput");
const fileNameEl = document.getElementById("fileName");
const convertBtn = document.getElementById("convertBtn");
const resetBtn   = document.getElementById("resetBtn");
const statusEl   = document.getElementById("status");

// ---- Select a conversion type ----
grid?.addEventListener("click", (e) => {
    const btn = e.target.closest(".conv-option");
    if (!btn) return;

    grid.querySelectorAll(".conv-option")
        .forEach(el => el.classList.toggle("active", el === btn));

    currentType = btn.dataset.type;
    fileInput.accept = CONVERSIONS[currentType].accept;
    fileInput.value = "";                          // clear stale file
    fileNameEl.textContent = "No file selected";
    statusEl.textContent = "";
});

// ---- Show selected file name ----
fileInput?.addEventListener("change", () => {
    const f = fileInput.files[0];
    fileNameEl.textContent = f ? f.name : "No file selected";
});

// ---- Convert ----
convertBtn?.addEventListener("click", async () => {
    if (!fileInput.files.length) {
        statusEl.textContent = "Please choose a file first.";
        return;
    }

    const form = new FormData();
    form.append("conversion_type", currentType);
    form.append("file", fileInput.files[0]);

    convertBtn.disabled = true;
    statusEl.textContent = "Converting…";

    try {
        const res = await fetch("/convert", { method: "POST", body: form });
        const data = await res.json();

        if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
        statusEl.textContent = `Done — saved as ${data.output}`;
    } catch (err) {
        console.error(err);
        statusEl.textContent = `${err.message}`;
    } finally {
        convertBtn.disabled = false;
    }
});

// ---- Reset ----
resetBtn?.addEventListener("click", () => {
    fileInput.value = "";
    fileNameEl.textContent = "No file selected";
    statusEl.textContent = "";
});