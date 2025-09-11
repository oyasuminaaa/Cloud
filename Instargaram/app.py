import os
from flask import Flask, request, jsonify, render_template, Response
from apify_client import ApifyClient
import csv
from io import StringIO
from models import db, Post


app = Flask(__name__)

# --- Database config ---
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Missing DATABASE_URL environment variable.")

# Render ให้ค่าเป็น postgres:// แต่ SQLAlchemy+psycopg ต้องการ postgresql+psycopg://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# --- Apify config ---
APIFY_TOKEN = os.getenv("APIFY_TOKEN")
if not APIFY_TOKEN:
    raise RuntimeError("Missing APIFY_TOKEN environment variable.")
client = ApifyClient(APIFY_TOKEN)

# --- Routes ---
@app.route("/")
def index():
    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template("index.html", posts=posts)

@app.route("/pull", methods=["POST"])
def trigger_instagram_data():
    if request.method == "POST":
        return jsonify({"message": "โปรดส่ง POST request พร้อม URLs"}), 400
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

        # Trigger run แต่ไม่รอให้เสร็จ
        run = client.actor("apify/instagram-scraper").start(run_input=run_input)

        return jsonify({
            "message": "เริ่มดึงข้อมูลแล้ว",
            "runId": run["id"],
            "statusUrl": f"/status/{run['id']}",
            "fetchUrl": f"/fetch/{run['id']}"
        }), 202

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/download")
def download_csv():
    try:
        posts = Post.query.order_by(Post.id.desc()).all()
        si = StringIO()
        writer = csv.writer(si)
        writer.writerow(["Page Name", "Text", "Post URL", "Post Date"])
        for post in posts:
            writer.writerow([post.page_name, post.text, post.post_url, post.post_date])
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
