import os
from flask import Flask, request, jsonify, render_template, Response , redirect, url_for
from apify_client import ApifyClient
import csv
from io import StringIO
from models import db, Post
import pandas as pd



app = Flask(__name__)

# --- Apify config ---
APIFY_TOKEN = os.getenv("APIFY_TOKEN")
if not APIFY_TOKEN:
    raise RuntimeError("Missing APIFY_TOKEN environment variable.")
client = ApifyClient(APIFY_TOKEN)

# --- EXCEL ---
EXCEL_FILE = "instagram_data.xlsx"

def save_post_to_excel(page_name, text, post_url, post_date):
    # ถ้ามีไฟล์แล้ว ให้อ่านเพิ่ม ถ้าไม่มีก็สร้างใหม่
    if os.path.exists(EXCEL_FILE):
        df = pd.read_excel(EXCEL_FILE)
    else:
        df = pd.DataFrame(columns=["Page Name", "Text", "Post URL", "Post Date"])

    # เพิ่มข้อมูลใหม่
    new_row = {"Page Name": page_name, "Text": text, "Post URL": post_url, "Post Date": post_date}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    # บันทึกกลับไปที่ไฟล์
    df.to_excel(EXCEL_FILE, index=False)
    return True

def load_posts_from_excel():
    if os.path.exists(EXCEL_FILE):
        return pd.read_excel(EXCEL_FILE).to_dict(orient="records")
    return []


# --- Routes ---
@app.route("/")
def index():
    posts = load_posts_from_excel()
    return render_template("index.html", posts=posts)

@app.route("/pull", methods=["POST"])
def trigger_instagram_data():
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

        # รัน actor แล้วดึงผลลัพธ์กลับมาเลย
        run = client.actor("apify/instagram-scraper").call(run_input=run_input)
        dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items

        # เซฟลง Excel
        for item in dataset_items:
            save_post_to_excel(
                page_name=item.get("ownerUsername", ""),
                text=item.get("caption", ""),
                post_url=item.get("url", ""),
                post_date=item.get("timestamp", "")
            )

        # เสร็จแล้วกลับไปหน้า index เพื่อแสดงผล
        return redirect(url_for("index"))

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/download")
def download_csv():
    try:
        if not os.path.exists(EXCEL_FILE):
            return {"error": "ยังไม่มีข้อมูล"}, 400
        df = pd.read_excel(EXCEL_FILE)
        si = StringIO()
        df.to_csv(si, index=False)
        return Response(
            si.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=Instagram_data.csv"}
        )
    except Exception as e:
        return {"error": str(e)}, 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
