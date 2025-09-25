import os
import csv
from io import StringIO
from flask import Flask, request, jsonify, render_template, Response, redirect, url_for
from apify_client import ApifyClient
import pandas as pd

app = Flask(__name__)

# --- Apify config ---
APIFY_TOKEN = os.getenv("APIFY_TOKEN")
if not APIFY_TOKEN:
    raise RuntimeError("Missing APIFY_TOKEN environment variable.")
client = ApifyClient(APIFY_TOKEN)

# --- CSV storage ---
CSV_FILE = "instagram_data.csv"

def save_post_to_csv(page_name, text, post_url, post_date):
    file_exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Page Name", "Text", "Post URL", "Post Date"])
        writer.writerow([page_name, text, post_url, post_date])

def load_posts_from_csv():
    if not os.path.exists(CSV_FILE):
        return []
    df = pd.read_csv(CSV_FILE)
    return df.tail(50).to_dict(orient="records")  # แสดงล่าสุด 50 รายการ


# --- Routes ---
@app.route("/")
def index():
    data = load_posts_from_csv()
    return render_template("index.html", data=data)

@app.route("/pull", methods=["POST"])
def trigger_instagram_data():
    try:
        urls = request.form.get("urls", "")
        results_limit = max(1, min(int(request.form.get("results_limit", 1)), 20))  # limit 20
        start_urls = [u.strip() for u in urls.splitlines() if u.strip()]
        if not start_urls:
            return jsonify({"error": "กรุณาระบุ URL อย่างน้อย 1 รายการ"}), 400

        # จำกัดจำนวน URL ไม่ให้มากเกินไป
        start_urls = start_urls[:5]

        run_input = {
            "directUrls": start_urls,
            "resultsType": "posts",
            "resultsLimit": results_limit,
            "addParentData": True,
        }

        # รัน actor แล้วดึงผลลัพธ์กลับมา
        run = client.actor("apify/instagram-scraper").call(run_input=run_input)
        dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items

        # เซฟลง CSV
        for item in dataset_items:
            save_post_to_csv(
                page_name=item.get("ownerUsername", ""),
                text=item.get("caption", ""),
                post_url=item.get("url", ""),
                post_date=item.get("timestamp", "")
            )

        return redirect(url_for("index"))

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/download")
def download_csv():
    if not os.path.exists(CSV_FILE):
        return {"error": "ยังไม่มีข้อมูล"}, 400
    def generate():
        with open(CSV_FILE, encoding="utf-8") as f:
            for line in f:
                yield line
    return Response(generate(), mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=Instagram_data.csv"})

@app.get("/healthz")
def healthz():
    return "ok", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
