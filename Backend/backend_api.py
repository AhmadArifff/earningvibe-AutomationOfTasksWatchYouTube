# backend_api.py
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import threading, time, traceback

# Import dari app automation
from app import login_and_navigate, process_page, fetch_profile_info, init_driver


app = Flask(__name__)
CORS(app)

# ---------- GLOBAL STATE ----------
LOGS = []
STATS = {"tasks_done": 0, "reward_today": 0, "balance": "0 USDT"}
STOP_FLAG = {"stop": False}

# ---------- HELPER LOGGER ----------
def log_message(msg):
    LOGS.append(msg)
    print(msg, flush=True)

# ---------- API ENDPOINTS ----------
@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}
    email, password = data.get("email"), data.get("password")

    if not email or not password:
        return jsonify({"status": "error", "message": "Email dan password wajib diisi"}), 400

    try:
        login_and_navigate(email, password)
        # update balance setelah login
        email_acc, balance = fetch_profile_info()
        if balance:
            STATS["balance"] = balance
        log_message(f"✅ Login sukses untuk {email}")
        return jsonify({"status": "success"})
    except Exception as e:
        error_msg = f"❌ Login gagal: {e}"
        log_message(error_msg)
        print(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/start-tasks", methods=["POST"])
def start_tasks():
    drv = init_driver()  # pastikan driver ada
    if drv is None:
        return jsonify({"status": "error", "message": "Harus login dulu sebelum start tasks!"}), 400

    STOP_FLAG["stop"] = False
    log_message("🚀 Mulai menjalankan automation tasks...")

    def worker():
        page_num = 1
        while not STOP_FLAG["stop"]:
            log_message(f"\n📄 Sedang proses halaman {page_num}...")
            try:
                process_page()
                STATS["tasks_done"] += 1
                # update balance tiap selesai task
                _, balance = fetch_profile_info()
                if balance:
                    STATS["balance"] = balance
            except Exception as e:
                log_message(f"⚠️ Error di halaman {page_num}: {e}")
                print(traceback.format_exc())

            # jika stop ditekan saat proses_page
            if STOP_FLAG["stop"]:
                log_message("🛑 Stop flag terdeteksi, keluar dari loop.")
                break

            page_num += 1
            time.sleep(1.5)

        log_message("✅ Worker tasks selesai / dihentikan.")

    thread = threading.Thread(target=worker)
    thread.start()
    return jsonify({"status": "started"})


@app.route("/api/stop-tasks", methods=["POST"])
def stop_tasks():
    STOP_FLAG["stop"] = True
    log_message("🛑 Stop signal diterima, task akan berhenti...")
    return jsonify({"status": "stopping"})


@app.route("/api/logs", methods=["GET"])
def stream_logs():
    def event_stream():
        last_index = 0
        while True:
            if last_index < len(LOGS):
                for i in range(last_index, len(LOGS)):
                    yield f"data: {LOGS[i]}\n\n"
                last_index = len(LOGS)
            time.sleep(1)
    return Response(event_stream(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no"   # penting untuk nginx/proxy
    })


@app.route("/api/stats", methods=["GET"])
def get_stats():
    return jsonify(STATS)


# ---------- RUN SERVER ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
