"""Flask dashboard for AI News Digest — manage sources, view digests, trigger runs."""

import json
import os
import glob
import threading
from datetime import datetime

import yaml
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder="templates/dashboard")
app.secret_key = os.urandom(24)

BASE_DIR = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(BASE_DIR, "config.yaml")
DATA_DIR = os.path.join(BASE_DIR, "data")

# Track background run status
_run_status = {"running": False, "last_message": "", "last_run": None}


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_config(config: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def get_run_history() -> list:
    """Get list of past runs sorted newest first."""
    if not os.path.exists(DATA_DIR):
        return []
    runs = []
    for d in sorted(glob.glob(os.path.join(DATA_DIR, "20*")), reverse=True):
        if os.path.isdir(d):
            name = os.path.basename(d)
            scores_path = os.path.join(d, "scores.json")
            email_path = os.path.join(d, "email.html")
            raw_path = os.path.join(d, "raw.json")

            info = {"name": name, "dir": d, "has_email": os.path.exists(email_path)}

            if os.path.exists(scores_path):
                with open(scores_path, "r", encoding="utf-8") as f:
                    scores = json.load(f)
                info["special_news_count"] = len(scores.get("special_news", []))
                info["recommended_count"] = len(scores.get("recommended_reads", []))
            if os.path.exists(raw_path):
                with open(raw_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                info["article_count"] = len(raw)

            runs.append(info)
    return runs[:20]


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    config = load_config()
    runs = get_run_history()
    return render_template("index.html", config=config, runs=runs, status=_run_status)


@app.route("/sources")
def sources():
    config = load_config()
    return render_template("sources.html", config=config)


@app.route("/sources/add", methods=["POST"])
def add_source():
    config = load_config()
    group = request.form.get("group")  # wechat_rss, x_rss, official_blogs
    url = request.form.get("url", "").strip()
    name = request.form.get("name", "").strip()

    if not url or not name or not group:
        flash("URL 和名称不能为空", "error")
        return redirect(url_for("sources"))

    entry = {"url": url, "name": name}
    if group == "official_blogs":
        vendor = request.form.get("vendor", "").strip()
        if vendor:
            entry["vendor"] = vendor

    if group not in config["sources"]:
        config["sources"][group] = []
    config["sources"][group].append(entry)
    save_config(config)
    flash(f"已添加: {name}", "success")
    return redirect(url_for("sources"))


@app.route("/sources/delete", methods=["POST"])
def delete_source():
    config = load_config()
    group = request.form.get("group")
    idx = int(request.form.get("index"))

    sources_list = config["sources"].get(group, [])
    if 0 <= idx < len(sources_list):
        removed = sources_list.pop(idx)
        save_config(config)
        flash(f"已删除: {removed.get('name', 'unknown')}", "success")
    return redirect(url_for("sources"))


@app.route("/sources/edit", methods=["POST"])
def edit_source():
    config = load_config()
    group = request.form.get("group")
    idx = int(request.form.get("index"))
    url = request.form.get("url", "").strip()
    name = request.form.get("name", "").strip()

    sources_list = config["sources"].get(group, [])
    if 0 <= idx < len(sources_list) and url and name:
        sources_list[idx]["url"] = url
        sources_list[idx]["name"] = name
        vendor = request.form.get("vendor", "").strip()
        if vendor:
            sources_list[idx]["vendor"] = vendor
        save_config(config)
        flash(f"已更新: {name}", "success")
    return redirect(url_for("sources"))


@app.route("/sync/wewerss", methods=["POST"])
def sync_wewerss():
    """Pull latest feed list from WeWeRSS and update config.yaml."""
    from src.sync import sync_wechat_sources
    config = load_config()
    wewerss_url = config.get("wewerss", {}).get("base_url", "")
    if not wewerss_url:
        flash("config.yaml 中未设置 wewerss.base_url", "error")
        return redirect(url_for("sources"))

    config, summary = sync_wechat_sources(config, wewerss_url)
    save_config(config)

    parts = []
    if summary["added"]:
        parts.append(f"新增 {len(summary['added'])} 个: {', '.join(summary['added'])}")
    if summary["removed"]:
        parts.append(f"移除 {len(summary['removed'])} 个: {', '.join(summary['removed'])}")
    parts.append(f"保留 {summary['unchanged']} 个")

    flash(f"同步完成 — {' | '.join(parts)}", "success")
    return redirect(url_for("sources"))


@app.route("/run", methods=["POST"])
def trigger_run():
    if _run_status["running"]:
        flash("已有任务在运行中，请稍候", "warning")
        return redirect(url_for("index"))

    dry_run = request.form.get("dry_run") == "1"

    def _background_run():
        _run_status["running"] = True
        _run_status["last_message"] = "运行中..."
        try:
            from main import run
            run(dry_run=dry_run)
            _run_status["last_message"] = f"✅ 完成 {'(dry-run)' if dry_run else ''}"
        except Exception as e:
            _run_status["last_message"] = f"❌ 失败: {str(e)[:200]}"
        finally:
            _run_status["running"] = False
            _run_status["last_run"] = datetime.now().strftime("%H:%M:%S")

    t = threading.Thread(target=_background_run, daemon=True)
    t.start()
    flash("任务已启动，请稍候刷新页面查看结果", "info")
    return redirect(url_for("index"))


@app.route("/run/status")
def run_status():
    return jsonify(_run_status)


@app.route("/preview/<run_name>")
def preview(run_name):
    email_path = os.path.join(DATA_DIR, run_name, "email.html")
    if os.path.exists(email_path):
        with open(email_path, "r", encoding="utf-8") as f:
            return f.read()
    return "邮件不存在", 404


@app.route("/api/config")
def api_config():
    return jsonify(load_config())


@app.route("/api/config", methods=["PUT"])
def api_update_config():
    config = request.get_json()
    save_config(config)
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)
    app.run(host="0.0.0.0", port=5001, debug=True)
