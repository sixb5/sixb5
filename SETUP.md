# โปรไฟล์ GitHub ในรูปแบบเทอร์มินัล

ไฟล์เริ่มต้นใช้บัญชี `sixb5` ที่พบจาก GitHub CLI และอวตารสาธารณะของบัญชีนั้น
ฮีทแมปใช้ข้อมูลจริง ส่วน Now / Prev / Stack / Highlights เป็นข้อความตัวอย่างที่ต้องแก้เอง
เวิร์กโฟลว์รายวันอยู่ใน `.github/workflows/update-profile-art.yml`

## 1. ติดตั้ง

ต้องใช้ Python 3.11 ขึ้นไป เวิร์กโฟลว์รายวันใช้เฉพาะ requests กับ BeautifulSoup
การเตรียมรูปทำเฉพาะบนเครื่องและใช้ไลบรารีเพิ่มอีกชุด

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
./.venv/Scripts/Activate.ps1
python -m pip install -r scripts/requirements.txt -r scripts/requirements-portrait.txt
```

macOS / Linux:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r scripts/requirements.txt -r scripts/requirements-portrait.txt
```

## 2. เปลี่ยนชื่อและข้อมูล

แก้ `profile.json`: `username`, `name`, `subtitle`, `rows` และ `footer`
ค่า `value` ของแต่ละแถวเป็นข้อความหรือรายการข้อความได้ ข้อความยาวจะตัดขึ้นบรรทัดใหม่
การ์ดจะเพิ่มความสูงตามเนื้อหา ไม่ต้องแก้ตำแหน่ง SVG เอง
README กับการ์ดสร้างจากไฟล์นี้ ส่วนฮีทแมปอ้างชื่อบัญชีใน JSON ที่ดึงมา

## 3. เตรียมรูปและสร้าง SVG

เปลี่ยน `source-photo.png` เป็นรูปของคุณ แล้วรัน:

```sh
python scripts/prep_photo.py source-photo.png
python scripts/make_ascii_svg.py
python scripts/make_info_card.py
python scripts/fetch_contributions.py
python scripts/render_heatmap_svg.py
python scripts/make_readme.py
```

การเตรียมรูปปรับทิศตาม EXIF เพิ่มคอนทราสต์ด้วย CLAHE วางรูปบนพื้นขาว
และปรับช่วงความสว่างเพื่อให้พื้นหลังเกือบขาวกลายเป็นสีขาวบริสุทธิ์
หากรูปมีพื้นหลังรก ให้ติดตั้งและเรียก rembg เพิ่ม:

```sh
python -m pip install -r scripts/requirements-background.txt
python scripts/prep_photo.py source-photo.png --remove-background
python scripts/make_ascii_svg.py
```

rembg จะดาวน์โหลดโมเดลครั้งแรก จึงไม่อยู่ใน dependency ของเวิร์กโฟลว์รายวัน
รูปเริ่มต้นเป็นอวตาร ไม่ใช่ภาพถ่ายบุคคลที่สร้างขึ้นใหม่
ปรับความละเอียด ASCII ใน `portrait.columns` / `portrait.rows` ของ `profile.json`
สีขาวเป็นช่องว่างและสีดำเป็น `@` ภาพบุคคลใช้สีตัวอักษรเพียงสีเดียว

สคริปต์รับ `--help` และ `--output` ได้ทุกตัว สคริปต์การ์ด/README/ASCII รับ `--config`
สคริปต์ดึงข้อมูลรับ `--username` และ `--end YYYY-MM-DD` สำหรับตรวจช่วงวันที่เดิม
พาธผลลัพธ์เริ่มต้นอ้างจากโฟลเดอร์โปรเจกต์ จึงเรียกจากโฟลเดอร์อื่นได้

## 4. ดูตัวอย่างและเฟรมภาพนิ่ง

```sh
python -m http.server 8000 --bind 127.0.0.1
```

เปิด <http://127.0.0.1:8000/preview.html> แล้วรีโหลดเพื่อเล่นแอนิเมชันใหม่
README จริงใช้ HTML table ความกว้าง 370 + 490 และฮีทแมป 860 ตามสเปก
GitHub เพิ่มขอบและ padding ของตารางเอง จึงอาจต่างจากหน้า preview เล็กน้อย

สร้างภาพนิ่งไปยังพาธอื่นเพื่อไม่ทับไฟล์แอนิเมชัน:

```sh
python scripts/make_ascii_svg.py --static --output .preview/avatar-static.svg
python scripts/make_info_card.py --static --output .preview/info-static.svg
python scripts/render_heatmap_svg.py --static --output .preview/heatmap-static.svg
```

หรือใช้ `STATIC=1` บน macOS/Linux และ `$env:STATIC='1'` ใน PowerShell
SVG รองรับ `prefers-reduced-motion` และมีชื่อ/คำอธิบายสำหรับโปรแกรมอ่านหน้าจอ
แอนิเมชันทั้งหมดเล่นครั้งเดียว ไม่มี JavaScript หรือฟอนต์ภายนอก

## 5. เผยแพร่โปรไฟล์เมื่อพร้อม

ตรวจข้อมูลและรูปก่อน แล้วสร้าง public repository ชื่อตรงกับบัญชีของคุณ
ตัวอย่างสำหรับ `sixb5` (หากมี repository อยู่แล้ว ให้ใช้ repository เดิม):

```sh
git init -b main
git add .
git commit -m "feat: add terminal profile art"
gh repo create sixb5 --public --source . --remote origin --push
```

`.venv`, ไฟล์ cache, ภาพที่เตรียมแล้ว และ `.preview` ถูก ignore
รูปต้นฉบับ `source-photo.png` จะถูกรวมใน commit; หากไม่ต้องการเผยแพร่ให้เพิ่มลง `.gitignore` ก่อน
README ต้องอยู่บนสุดของ repository และ repository ต้องเป็น public จึงจะแสดงบนโปรไฟล์
ดู [ข้อกำหนด README โปรไฟล์ของ GitHub](https://docs.github.com/en/account-and-profile/how-tos/profile-customization/managing-your-profile-readme)

## 6. เปิดการรีเฟรชรายวัน

เวิร์กโฟลว์ `.github/workflows/update-profile-art.yml` จะทำงานเวลา **06:17 UTC ทุกวัน**
หรือสั่งเองจาก Actions → Update profile art → Run workflow
ไฟล์เวิร์กโฟลว์ต้องอยู่บน default branch; push trigger ตั้งเป็น `main` ตามตัวอย่าง
หากใช้ branch ชื่ออื่นให้แก้ `push.branches` ด้วย

เวิร์กโฟลว์ดึงข้อมูลใหม่ สร้างฮีทแมป แล้ว commit เฉพาะ `data/contributions.json`
และ `contrib-heatmap.svg` เมื่อมีการเปลี่ยนแปลง ใช้ `contents: write` และข้อความ `[skip ci]`
ไม่ต้องตั้ง PAT หรือ secret; bot ใช้ `GITHUB_TOKEN` ของ Actions ในขั้นตอน commit
หาก repository มีกฎห้าม bot push โดยตรง ต้องปรับกฎหรือเปลี่ยนเป็นขั้นตอน PR ของคุณ
เวลารัน cron อาจล่าช้าได้ตามภาระของ GitHub Actions
ดู [การข้าม workflow](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/skip-workflow-runs)
และ [เงื่อนไข workflow ที่ใช้ default branch](https://docs.github.com/en/actions/how-tos/troubleshoot-workflows)

## ข้อมูลและความหมายของสถิติ

- ดึง HTML สาธารณะจาก `https://github.com/users/<username>/contributions` แยกทีละปี
  แล้วรวมวันที่จริง 365 วันจนถึงวัน UTC ปัจจุบัน ไม่มีการสุ่มหรือสร้างกิจกรรมปลอม
- ตารางจัดสัปดาห์เริ่มวันอาทิตย์ มี 53 คอลัมน์ × 7 แถว ช่องนอกช่วงใช้กรอบประ
  และไม่นับในสถิติ
- อ่านจำนวนจาก tooltip ที่จับคู่ด้วย id หรือ `data-count` ของรูปแบบเดิม
  หากดึงไม่สำเร็จ ข้อมูลไม่ครบ หรือรูปแบบเปลี่ยน จะหยุดและคง JSON เก่าไว้
- ใช้ระดับสีของ GitHub; ระดับนีออนพิเศษใช้กับวันสูงสุดที่อยู่ระดับ 4 เท่านั้น
- Current streak ยอมให้วันนี้ยังเป็นศูนย์ได้ โดยนับต่อจากเมื่อวาน
  Longest streak นับเฉพาะ 365 วันที่แสดง ไม่ใช่สถิติตลอดชีพ
- `monthly_totals` เป็นยอดเฉพาะช่วงที่แสดง เดือนแรก/สุดท้ายอาจไม่เต็มเดือน
- ข้อมูลสาธารณะอาจไม่รวมกิจกรรมส่วนตัวที่บัญชีไม่ได้เปิดให้แสดง
- JSON ไม่มีเวลาระดับวินาที ผลลัพธ์จะเหมือนเดิมเมื่อข้อมูลและวัน UTC ยังไม่เปลี่ยน

## ตรวจสอบ

```sh
python -m unittest discover -s tests -v
```

ชุดทดสอบครอบคลุม count ใน tooltip/rect, leap day, วันที่หาย/ซ้ำ, streak,
ผลรวมรายเดือน, XML escaping, ความหนาแน่นตัวอักษร และการเรนเดอร์ภาพนิ่ง

โครงการนี้พัฒนาตามแนวทางตัวอย่างจาก
[AVIVASHISHTA29](https://github.com/AVIVASHISHTA29/AVIVASHISHTA29)
โดยเขียนสคริปต์ขึ้นใหม่และแยกข้อมูลส่วนตัวไว้ใน config
