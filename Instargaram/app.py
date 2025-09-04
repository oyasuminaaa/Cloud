from apify_client import ApifyClient
import sys
import csv
import os
from flask import Flask, request, jsonify, render_template

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
