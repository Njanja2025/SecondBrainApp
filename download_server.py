#!/usr/bin/env python3
import os
import json
import time
import hmac
import hashlib
from flask import Flask, send_from_directory, jsonify, request, abort, redirect, url_for
from pathlib import Path
from datetime import datetime
from threading import Lock
import requests

ARTIFACT_DIR = os.environ.get("ARTIFACT_DIR", "build/dist")
DOWNLOAD_LOG = os.environ.get("DOWNLOAD_LOG", "download_counts.json")
MANIFEST_FILE = os.environ.get(
    "MANIFEST_FILE", f"{ARTIFACT_DIR}/SecondBrain-2025-manifest.json"
)
SIGNED_URL_SECRET = os.environ.get("SIGNED_URL_SECRET", "changeme")
OAUTH_BEARER_TOKEN = os.environ.get("OAUTH_BEARER_TOKEN")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")
QUEUE_FILE = os.environ.get("BUILD_QUEUE_FILE", "build_queue.json")

app = Flask(__name__)
download_counts = {}
counts_lock = Lock()

# Load download counts
if os.path.exists(DOWNLOAD_LOG):
    with open(DOWNLOAD_LOG) as f:
        download_counts = json.load(f)
else:
    download_counts = {}


def save_counts():
    with counts_lock:
        with open(DOWNLOAD_LOG, "w") as f:
            json.dump(download_counts, f, indent=2)


def log_download(artifact):
    with counts_lock:
        download_counts.setdefault(artifact, 0)
        download_counts[artifact] += 1
        save_counts()
    # Slack notification
    if SLACK_WEBHOOK_URL:
        try:
            requests.post(
                SLACK_WEBHOOK_URL,
                json={
                    "text": f"Artifact downloaded: {artifact} ({download_counts[artifact]} total)"
                },
                timeout=5,
            )
        except Exception:
            pass


def generate_signed_url(artifact, expires_in=300):
    expires = int(time.time()) + expires_in
    data = f"{artifact}:{expires}"
    sig = hmac.new(
        SIGNED_URL_SECRET.encode(), data.encode(), hashlib.sha256
    ).hexdigest()
    return url_for(
        "api_download_signed",
        artifact=artifact,
        expires=expires,
        sig=sig,
        _external=True,
    )


def verify_signed_url(artifact, expires, sig):
    if int(expires) < int(time.time()):
        return False
    data = f"{artifact}:{expires}"
    expected = hmac.new(
        SIGNED_URL_SECRET.encode(), data.encode(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, sig)


def require_oauth():
    if OAUTH_BEARER_TOKEN:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            abort(401)
        token = auth.split(" ", 1)[1]
        if token != OAUTH_BEARER_TOKEN:
            abort(403)


@app.route("/api/status")
def api_status():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})


@app.route("/api/manifest")
def api_manifest():
    if os.path.exists(MANIFEST_FILE):
        with open(MANIFEST_FILE) as f:
            return jsonify(json.load(f))
    return abort(404)


@app.route("/api/downloads")
def api_downloads():
    return jsonify(download_counts)


@app.route("/api/download/<artifact>")
def api_download(artifact):
    require_oauth()
    # Redirect to signed URL
    signed_url = generate_signed_url(artifact)
    return redirect(signed_url)


@app.route("/api/download_signed/<artifact>")
def api_download_signed(artifact):
    expires = request.args.get("expires")
    sig = request.args.get("sig")
    if not (expires and sig and verify_signed_url(artifact, expires, sig)):
        return abort(403)
    artifact_path = Path(ARTIFACT_DIR) / artifact
    if not artifact_path.exists():
        return abort(404)
    log_download(artifact)
    return send_from_directory(ARTIFACT_DIR, artifact, as_attachment=True)


@app.route("/")
def index():
    return (
        "<h1>SecondBrain Artifact Server</h1><ul>"
        + "".join(
            f"<li><a href='/api/download/{f}'>{f}</a> ({download_counts.get(f,0)} downloads)</li>"
            for f in os.listdir(ARTIFACT_DIR)
            if not f.startswith(".")
        )
        + "</ul>"
    )


@app.route("/queue")
def queue_ui():
    return """
    <html><head><title>Build Queue</title>
    <script>
    async function loadQueue() {
        let resp = await fetch('/api/queue');
        let data = await resp.json();
        let q = document.getElementById('queue');
        q.innerHTML = '';
        data.forEach((item, i) => {
            q.innerHTML += `<li>#${i+1}: ${JSON.stringify(item.build_info)} (status: ${item.status})</li>`;
        });
    }
    window.onload = loadQueue;
    </script>
    </head><body>
    <h1>Build Queue</h1>
    <ul id='queue'></ul>
    </body></html>
    """


@app.route("/api/queue")
def api_queue():
    if not os.path.exists(QUEUE_FILE):
        return jsonify([])
    with open(QUEUE_FILE) as f:
        return jsonify(json.load(f))


@app.route("/analytics")
def analytics_ui():
    return """
    <html><head><title>Download Analytics</title>
    <script>
    async function loadAnalytics() {
        let resp = await fetch('/api/downloads');
        let data = await resp.json();
        let a = document.getElementById('analytics');
        a.innerHTML = '';
        Object.entries(data).forEach(([file, count]) => {
            a.innerHTML += `<li>${file}: <b>${count}</b> downloads</li>`;
        });
    }
    window.onload = loadAnalytics;
    </script>
    </head><body>
    <h1>Download Analytics</h1>
    <ul id='analytics'></ul>
    </body></html>
    """


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
