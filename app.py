from __future__ import annotations

import shutil
import tempfile
import threading
import time
import uuid
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, jsonify, render_template, request, send_file

from savevideo import inspect_video, download_video

app = Flask(__name__)
logger = logging.getLogger(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024

ALLOWED_HOSTS = ("youtube.com", "youtu.be", "instagram.com", "tiktok.com")
RATE_LIMITS = {"inspect": (10, 60), "download": (3, 600)}
rate_history: dict[tuple[str, str], list[float]] = {}
rate_lock = threading.Lock()
executor = ThreadPoolExecutor(max_workers=2)
jobs: dict[str, dict] = {}
jobs_lock = threading.Lock()


def client_ip() -> str:
    return request.remote_addr or "unknown"


def allowed_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower().rstrip(".")
        return parsed.scheme in {"http", "https"} and any(
            hostname == host or hostname.endswith(f".{host}") for host in ALLOWED_HOSTS
        )
    except ValueError:
        return False


def check_rate_limit(action: str) -> bool:
    limit, window = RATE_LIMITS[action]
    now = time.monotonic()
    key = (client_ip(), action)
    with rate_lock:
        history = [stamp for stamp in rate_history.get(key, []) if now - stamp < window]
        if len(history) >= limit:
            rate_history[key] = history
            return False
        history.append(now)
        rate_history[key] = history
    return True


@app.before_request
def cleanup_expired_jobs() -> None:
    cutoff = time.time() - 1800
    with jobs_lock:
        expired = [job_id for job_id, job in jobs.items() if job.get("created", 0) < cutoff]
        old_jobs = [jobs.pop(job_id) for job_id in expired]
    for job in old_jobs:
        if job.get("work_dir"):
            shutil.rmtree(job["work_dir"], ignore_errors=True)


def format_duration(seconds: int | float | None) -> str:
    if not seconds:
        return "Duração não informada"
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, seconds_left = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds_left:02d}"
    return f"{minutes}:{seconds_left:02d}"


def format_for_quality(quality: str | None) -> str:
    if quality == "best" or not quality:
        return "bestvideo+bestaudio/best"
    try:
        height = int(quality)
    except (TypeError, ValueError) as exc:
        raise ValueError("Qualidade inválida") from exc
    if height < 1 or height > 4320:
        raise ValueError("Qualidade inválida")
    return f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/termos")
def terms():
    return render_template("terms.html")


@app.get("/privacidade")
def privacy():
    return render_template("privacy.html")


@app.get("/health")
def health():
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    return jsonify({"status": "ok", "ffmpeg": bool(ffmpeg), "ffprobe": bool(ffprobe)})


@app.post("/api/inspect")
def api_inspect():
    if not check_rate_limit("inspect"):
        return jsonify({"error": "Muitas pesquisas. Aguarde um minuto e tente novamente."}), 429
    data = request.get_json(silent=True) or {}
    url = str(data.get("url", "")).strip()
    if not url:
        return jsonify({"error": "Cole uma URL para pesquisar."}), 400
    if not allowed_url(url):
        return jsonify({"error": "Use uma URL do YouTube, Instagram ou TikTok."}), 400

    try:
        info = inspect_video(url, no_watermark=bool(data.get("no_watermark")))
        return jsonify(
            {
                "title": info["title"],
                "uploader": info["uploader"],
                "duration": format_duration(info["duration"]),
                "heights": info["heights"],
            }
        )
    except Exception as exc:
        return jsonify({"error": f"Não foi possível consultar este link: {exc}"}), 422


def run_download_job(job_id: str, url: str, format_string: str, audio_only: bool, no_watermark: bool) -> None:
    work_dir = Path(tempfile.mkdtemp(prefix=f"savevideo-{job_id}-"))
    try:
        with jobs_lock:
            jobs[job_id]["status"] = "downloading"
        download_video(
            url=url,
            output_dir=str(work_dir),
            format_string=format_string,
            audio_only=audio_only,
            no_playlist=True,
            no_watermark=no_watermark,
            cookie_file=None,
        )
        files = [path for path in work_dir.iterdir() if path.is_file()]
        if not files:
            raise FileNotFoundError("Nenhum arquivo foi gerado.")
        result = max(files, key=lambda path: path.stat().st_mtime)
        with jobs_lock:
            jobs[job_id].update({"status": "ready", "path": result, "work_dir": work_dir, "filename": result.name})
    except SystemExit:
        shutil.rmtree(work_dir, ignore_errors=True)
        logger.exception("Download failed with SystemExit for job %s", job_id)
        with jobs_lock:
            jobs[job_id].update({"status": "error", "error": "O servidor não conseguiu gerar o arquivo. Verifique os logs do deploy."})
    except Exception as exc:
        shutil.rmtree(work_dir, ignore_errors=True)
        logger.exception("Download failed for job %s", job_id)
        with jobs_lock:
            jobs[job_id].update({"status": "error", "error": str(exc)})


@app.post("/api/download")
def api_download():
    if not check_rate_limit("download"):
        return jsonify({"error": "Limite de downloads atingido. Aguarde alguns minutos."}), 429
    data = request.get_json(silent=True) or {}
    url = str(data.get("url", "")).strip()
    if not url:
        return jsonify({"error": "Cole uma URL para baixar."}), 400
    if not allowed_url(url):
        return jsonify({"error": "Use uma URL do YouTube, Instagram ou TikTok."}), 400

    try:
        format_string = format_for_quality(data.get("quality"))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    job_id = uuid.uuid4().hex
    with jobs_lock:
        jobs[job_id] = {"status": "queued", "created": time.time()}
    executor.submit(run_download_job, job_id, url, format_string, bool(data.get("audio_only")), bool(data.get("no_watermark")))
    return jsonify({"job_id": job_id}), 202


@app.get("/api/download/<job_id>")
def download_status(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            return jsonify({"error": "Download não encontrado."}), 404
        if job["status"] == "error":
            return jsonify({"status": "error", "error": job["error"]}), 422
        return jsonify({"status": job["status"]})


@app.get("/api/download/<job_id>/file")
def download_file(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job or job.get("status") != "ready":
            return jsonify({"error": "O arquivo ainda não está pronto."}), 404
        result = Path(job["path"])
        work_dir = Path(job["work_dir"])
        filename = job["filename"]
        job["status"] = "sent"

    response = send_file(result, as_attachment=True, download_name=filename)
    response.call_on_close(lambda: (shutil.rmtree(work_dir, ignore_errors=True), jobs.pop(job_id, None)))
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
