# Instagram Scraper Flask (Apify)

แอป Flask ที่เรียกใช้ Apify Actor `apify/instagram-scraper` จากฟอร์ม HTML แล้วส่งออกเป็นไฟล์ CSV ให้ดาวน์โหลด

## โครงสร้างโปรเจกต์
```
.
├─ app.py
├─ requirements.txt
├─ Dockerfile              # ทางเลือก: ใช้ container build ได้ทั้ง Render/Railway
├─ render.yaml             # ทางเลือก: Render Blueprints
├─ Procfile                # ทางเลือก: บริการที่รองรับสไตล์ Heroku
├─ templates/
│  └─ index.html
└─ data/                   # โฟลเดอร์ชั่วคราวไว้เก็บ CSV (ephemeral)
```

## การตั้งค่า (สำคัญ)
- **อย่า** hard-code token ในโค้ด. ตั้งค่า `APIFY_TOKEN` เป็น Environment Variable ใน Cloud
- Token ที่เคย commit/แชร์ไปแล้ว ควร **rotate** ใน Apify Console

## รันแบบ Local
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export APIFY_TOKEN=your-token   # Windows PowerShell: $env:APIFY_TOKEN="your-token"
python app.py
# เปิด http://localhost:8000
```

## Deploy ขึ้น Render (ไม่ใช้ Docker)
1) สร้าง Git repo แล้ว push โค้ดนี้ขึ้น GitHub/GitLab/Bitbucket  
2) เข้า Render > **New +** > **Web Service** > เชื่อมต่อ repo
3) เลือก Runtime: **Python**
4) **Build Command**: `pip install -r requirements.txt`  
   **Start Command**: `gunicorn app:app`
5) ที่ **Environment** เพิ่มตัวแปร `APIFY_TOKEN` และใส่ค่า token ของคุณ
6) Deploy ได้เลย → รอ URL และทดสอบหน้าเว็บ
> ใช้ `render.yaml` ได้เช่นกัน โดยเลือก **Blueprint** แทน (ใส่ token ภายหลังใน Dashboard)

## Deploy ขึ้น Railway (ไม่ใช้ Docker)
1) สร้างโปรเจกต์ใหม่ใน Railway > **Provision from GitHub** แล้วเลือก repo
2) Railway จะตรวจพบ Python โดยอัตโนมัติ (Nixpacks)
3) ไปที่ Service Settings:
   - **Start Command**: `gunicorn app:app`
   - เพิ่ม Environment Variable: `APIFY_TOKEN`
4) Deploy และเปิด URL ทดสอบ

## Deploy แบบ Docker (Render/Railway)
- มี `Dockerfile` ให้พร้อมใช้งาน
- Render: New > Web Service > เลือก **Managed > Docker** แล้วชี้ไปยัง repo ที่มี Dockerfile
- Railway: New Project > Deploy from GitHub (มี Dockerfile) → ตั้ง `APIFY_TOKEN` แล้ว Deploy

## หมายเหตุ
- โฟลเดอร์ `data/` เป็น **ephemeral** บน Render/Railway: ไฟล์จะหายเมื่อรีสตาร์ท/รีดีพลอย
- หากต้องการเก็บถาวร แนะนำอัปโหลด CSV ไปยัง storage ภายนอก (เช่น S3, GCS) หรือใช้ Apify dataset export URL
- บริการฟรีอาจมี cold start/จำกัดเวลา ทำงานนานมากอาจ timeout
