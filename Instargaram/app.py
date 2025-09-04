import os
import sys
import csv
from flask import Flask, request, jsonify, render_template, send_from_directory, abort
from apify_client import ApifyClient

# Ensure UTF-8 output
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

app = Flask(__name__)

# --- Configuration ---
APIFY_TOKEN = os.getenv("APIFY_TOKEN")

if not APIFY_TOKEN:
    # Fail fast with a clear error if token isn't provided
    raise RuntimeError("Missing APIFY_TOKEN environment variable. Set it in your cloud service.")

client = ApifyClient(APIFY_TOKEN)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

@app.route("/healthz")
def healthz():
    return "ok", 200

# Home page with form
@app.route("/")
def index():
    return render_template("index.html")

# Fetch Instagram data via Apify
@app.route("/pull", methods=["POST"])
def fetch_instagram_data():
    try:
        urls = request.form.get("urls", "")
        results_limit = int(request.form.get("results_limit", 40))

        start_urls = [u.strip() for u in urls.splitlines() if u.strip()]
        if not start_urls:
            return jsonify({"error": "กรุณาระบุ URL อย่างน้อย 1 รายการ"}), 400

        run_input = {
            "directUrls": start_urls,
            "resultsType": "posts",
            "resultsLimit": results_limit,
            "addParentData": True,
        }

        run = client.actor("apify/instagram-scraper").call(run_input=run_input)

        if run.get("status") != "SUCCEEDED":
            return jsonify({"error": f"Actor ทำงานไม่สำเร็จ: {run.get('status')}", "runId": run.get("id")}), 500

        data = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            page_name = item.get("ownerFullName") or item.get("ownerUsername") or "N/A"
            text = item.get("caption", "No caption")
            post_url = item.get("url", "No URL")
            post_date = item.get("timestamp", "No date")

            data.append({
                "Page Name": page_name,
                "Text": text,
                "Post URL": post_url,
                "Post Date": post_date,
            })

        # Save CSV to a writable (ephemeral) directory
        csv_file = os.path.join(DATA_DIR, "Instagram_data.csv")
        with open(csv_file, "w", newline="", encoding="utf-8-sig") as csvfile:
            fieldnames = ["Page Name", "Text", "Post URL", "Post Date"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        # Provide a download link within this instance
        return jsonify({
            "message": "ดึงข้อมูลสำเร็จและบันทึก CSV แล้ว",
            "download": "/download/Instagram_data.csv",
            "count": len(data)
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/download/<path:filename>")
def download_file(filename):
    file_path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(file_path):
        abort(404)
    return send_from_directory(DATA_DIR, filename, as_attachment=True)

if __name__ == "__main__":
    # Use PORT from env if provided (Render/Railway pass it), else default to 8000 for local dev
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
