const state = { url: "", quality: "best", heights: [] };
const $ = (selector) => document.querySelector(selector);

function setMessage(text, error = false) {
  const message = $("#message");
  message.textContent = text;
  message.classList.toggle("error", error);
}

function renderQualities(heights) {
  const values = ["best", ...heights];
  const container = $("#qualities");
  container.innerHTML = "";
  values.forEach((value, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `quality-option${index === 0 ? " selected" : ""}`;
    button.dataset.quality = value;
    button.textContent = value === "best" ? "Melhor" : `${value}p`;
    button.addEventListener("click", () => {
      state.quality = value;
      document.querySelectorAll(".quality-option").forEach((item) => item.classList.remove("selected"));
      button.classList.add("selected");
    });
    container.appendChild(button);
  });
}

async function inspect() {
  const url = $("#url").value.trim();
  if (!url) {
    setMessage("Cole um link antes de pesquisar.", true);
    $("#url").focus();
    return;
  }
  state.url = url;
  const button = $("#inspect");
  button.disabled = true;
  button.innerHTML = "Pesquisando...";
  $("#result").classList.add("hidden");
  setMessage("Consultando título, duração e qualidades disponíveis...");
  try {
    const response = await fetch("/api/inspect", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ url, no_watermark: $("#no-watermark").checked }) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Não foi possível pesquisar.");
    $("#title").textContent = data.title;
    $("#meta").textContent = [data.uploader, data.duration].filter(Boolean).join("  ·  ");
    state.heights = data.heights || [];
    state.quality = "best";
    renderQualities(state.heights);
    $("#result").classList.remove("hidden");
    $("#download").disabled = false;
    setMessage("Vídeo encontrado. Escolha uma opção e baixe.");
  } catch (error) {
    setMessage(error.message, true);
  } finally {
    button.disabled = false;
    button.innerHTML = '<span class="button-icon">⌕</span> Pesquisar';
  }
}

async function download() {
  const button = $("#download");
  button.disabled = true;
  button.querySelector("span").textContent = "Preparando arquivo...";
  setMessage("O servidor está preparando seu download...");
  try {
    const response = await fetch("/api/download", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ url: state.url, quality: state.quality, audio_only: $("#audio").checked, no_watermark: $("#no-watermark").checked }) });
    const job = await response.json();
    if (!response.ok) throw new Error(job.error || "O download falhou.");
    let status = "queued";
    while (status === "queued" || status === "downloading") {
      await new Promise((resolve) => setTimeout(resolve, 1200));
      const statusResponse = await fetch(`/api/download/${job.job_id}`);
      const statusData = await statusResponse.json();
      if (!statusResponse.ok) throw new Error(statusData.error || "O download falhou.");
      status = statusData.status;
      setMessage(status === "queued" ? "Download aguardando na fila..." : "Baixando e preparando seu arquivo...");
    }
    const fileResponse = await fetch(`/api/download/${job.job_id}/file`);
    if (!fileResponse.ok) throw new Error("O arquivo não ficou disponível.");
    const blob = await fileResponse.blob();
    const disposition = fileResponse.headers.get("Content-Disposition") || "";
    const filename = disposition.match(/filename="?([^";]+)"?/)?.[1] || "savevideo-download";
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
    URL.revokeObjectURL(link.href);
    setMessage("Download concluído. O arquivo foi salvo pelo navegador.");
  } catch (error) {
    setMessage(error.message, true);
  } finally {
    button.disabled = false;
    button.querySelector("span").textContent = "Baixar agora";
  }
}

$("#inspect").addEventListener("click", inspect);
$("#download").addEventListener("click", download);
$("#url").addEventListener("keydown", (event) => { if (event.key === "Enter") inspect(); });
