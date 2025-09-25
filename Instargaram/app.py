import os
import csv
from flask import Flask, request, jsonify, render_template, Response, redirect, url_for
from apify_client import ApifyClient

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

def load_posts_from_csv(page=1, per_page=10):
    if not os.path.exists(CSV_FILE):
        return [], 0
    with open(CSV_FILE, encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        posts = reader[-50:]  # ล่าสุด 50 รายการ
        total = len(posts)
        total_pages = (total + per_page - 1) // per_page

        # slice ตามหน้า
        start = (page - 1) * per_page
        end = start + per_page
        return posts[start:end], total_pages

# --- Routes ---
@app.route("/")
def index():
    page = int(request.args.get("page", 1))
    per_page = 10
    data, total_pages = load_posts_from_csv(page, per_page)
    return render_template("index.html", data=data, page=page, total_pages=total_pages)

@app.route("/pull", methods=["POST"])
def trigger_instagram_data():
    try:
        urls = request.form.get("urls", "")
        results_limit = max(1, min(int(request.form.get("results_limit", 1)), 20))
        start_urls = [u.strip() for u in urls.splitlines() if u.strip()][:5]
        if not start_urls:
            return jsonify({"error": "กรุณาระบุ URL อย่างน้อย 1 รายการ"}), 400

        run_input = {
            "directUrls": start_urls,
            "resultsType": "posts",
            "resultsLimit": results_limit,
            "addParentData": True,
        }

        run = client.actor("apify/instagram-scraper").start(run_input=run_input)
        dataset_id = run["defaultDatasetId"]

        return redirect(url_for("fetch_results", dataset_id=dataset_id))

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/fetch_results/<dataset_id>")
def fetch_results(dataset_id):
    try:
        items = client.dataset(dataset_id).list_items().items
        if not items:
            return "<p>⏳ กำลังดึงข้อมูลจาก Instagram... โปรดลองรีเฟรชอีกครั้ง</p>"

        for item in items:
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
