from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import os
from apify_client import ApifyClient
import sys
import csv

app = Flask(__name__)

# --- Database config ---
DATABASE_URL = os.getenv("DATABASE_URL")  # ตัวอย่าง: postgres://user:pass@host:port/dbname
if not DATABASE_URL:
    raise RuntimeError("Missing DATABASE_URL environment variable.")

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Instagram Scraper ---
APIFY_TOKEN = os.getenv("APIFY_TOKEN")
if not APIFY_TOKEN:
    raise RuntimeError("Missing APIFY_TOKEN environment variable.")
client = ApifyClient(APIFY_TOKEN)

# --- Database model ---
class InstagramPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_name = db.Column(db.String(255))
    text = db.Column(db.Text)
    post_url = db.Column(db.String(500))
    post_date = db.Column(db.String(50))

# สร้างตาราง (ครั้งแรก)
with app.app_context():
    db.create_all()

@app.route("/")
def index():
    posts = InstagramPost.query.order_by(InstagramPost.id.desc()).all()
    return render_template("index.html", posts=posts)

@app.route("/pull", methods=["POST"])
def fetch_instagram_data():
    try:
        urls = request.form.get("urls", "")
        results_limit = int(request.form.get("results_limit", 40))
        start_urls = [u.strip() for u in urls.splitlines() if u.strip()]

sys.stdout.reconfigure(encoding='utf-8')
app = Flask(__name__)

# Apify Client
client = ApifyClient(os.getenv("APIFY_TOKEN", "your_apify_token_here"))

# หน้าเว็บหลัก
@app.route('/')
def index():
    return render_template('index.html')

# Route ดึงข้อมูล Instagram
@app.route('/pull', methods=['POST'])
def fetch_instagram_data():
    try:
        urls = request.form.get('urls')
        results_limit = int(request.form.get('results_limit', 40))
        start_urls = [url.strip() for url in urls.splitlines() if url.strip()]
        if not start_urls:
            return "กรุณาระบุ URL อย่างน้อย 1 รายการ", 400

        run_input = {
            "directUrls": start_urls,
            "resultsType": "posts",
            "resultsLimit": results_limit,
            "addParentData": True,
        }

        run = client.actor("apify/instagram-scraper").call(run_input=run_input)

        # ดึงข้อมูลจาก dataset
        dataset_client = client.dataset(run["defaultDatasetId"])
        items = list(dataset_client.list_items().items)
        count = 0
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            post = InstagramPost(
                page_name=item.get("ownerFullName") or item.get("ownerUsername") or "N/A",
                text=item.get("caption", "No caption"),
                post_url=item.get("url", "No URL"),
                post_date=item.get("timestamp", "No date")
            )
            db.session.add(post)
            count += 1
        db.session.commit()

        return jsonify({"message": f"ดึงข้อมูลสำเร็จ {count} โพสต์", "count": count}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

        data = []
        for item in items:
            data.append({
                'Page Name': item.get("ownerFullName", "N/A"),
                'Text': item.get("caption", "No caption"),
                'Post URL': item.get("url", "No URL"),
                'Post Date': item.get("timestamp", "No date"),
            })

        # ส่งข้อมูลไปแสดงบน HTML
        return render_template('results.html', data=data)
        
        # สร้าง CSV เก็บด้วย (ถ้าต้องการดาวน์โหลด)
        os.makedirs("data", exist_ok=True)
        csv_file = os.path.join("data", "Instagram_data.csv")
        with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=['Page Name','Text','Post URL','Post Date'])
            writer.writeheader()
            writer.writerows(data)

        # ส่ง JSON กลับไป frontend
        return jsonify({
            "message": "Data fetched successfully",
            "count": len(data),
            "download": f"/download/Instagram_data.csv"
        })

    except Exception as e:
        return f"เกิดข้อผิดพลาด: {str(e)}", 500

# Health check
@app.route('/healthz')
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

