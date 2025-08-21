from apify_client import ApifyClient
import sys
import csv
import os
from flask import Flask, request, jsonify, render_template

# ตั้งค่า encoding
sys.stdout.reconfigure(encoding='utf-8')

app = Flask(__name__)

# ตั้งค่า Apify Client ด้วย API Token
client = ApifyClient("apify_api_m8mL70xkBstdWBVZKmrzDEm3TbVnfj0DIww8")

# Route สำหรับแสดงฟอร์ม HTML
@app.route('/')
def index():
    return render_template('index.html')

# Route สำหรับดึงข้อมูล Instagram
@app.route('/pull', methods=['POST'])
def fetch_instagram_data():
    try:
        # รับค่าอินพุตจากฟอร์ม
        urls = request.form.get('urls')  # URLs เป็นข้อความหลายบรรทัด
        results_limit = int(request.form.get('results_limit', 40))  # ค่า default เป็น 40

        # ตรวจสอบว่ามี URL หรือไม่
        start_urls = [url.strip() for url in urls.splitlines() if url.strip()]
        if not start_urls:
            return jsonify({"error": "กรุณาระบุ URL อย่างน้อย 1 รายการ"}), 400

        # ตั้งค่าข้อมูลสำหรับ Apify Actor
        run_input = {
            "directUrls": start_urls,
            "resultsType": "posts",
            "resultsLimit": results_limit,
            "addParentData": True,
        }

        # เรียกใช้ Actor บน Apify
        run = client.actor("apify/instagram-scraper").call(run_input=run_input)

        # ตรวจสอบสถานะการทำงาน
        if run["status"] != "SUCCEEDED":
            return jsonify({"error": f"Actor ทำงานไม่สำเร็จ: {run['status']}"}), 500

        # ดึงผลลัพธ์จาก Dataset
        data = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            page_name = item.get("ownerFullName", "N/A")
            text = item.get("caption", "No caption")
            post_url = item.get("url", "No URL")
            post_date = item.get("timestamp", "No date")

            data.append({
                'Page Name': page_name,
                'Text': text,
                'Post URL': post_url,
                'Post Date': post_date,
            })

        # บันทึกข้อมูลลง CSV
        csv_file = "Instagram_data.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['Page Name', 'Text', 'Post URL', 'Post Date']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        # ส่งผลลัพธ์กลับไปยังผู้ใช้
        return jsonify({"message": "Data fetched and saved successfully.", "file": csv_file}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# เริ่มต้น Flask Application
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    app.run(debug=True)
