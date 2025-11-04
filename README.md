# ⚽ EURO_GOALS v9.4.4 PRO+ – Full Unified Edition
*(Successor of EURO_GOALS_NEXTGEN_UNIFIED)*

---

## 🧠 Overview
Η πλατφόρμα **EURO_GOALS** είναι ένα ενιαίο, επαγγελματικό σύστημα παρακολούθησης και ανάλυσης ποδοσφαιρικών δεδομένων, αποδόσεων και “Smart Money” κινήσεων.  
Ενσωματώνει ιστορικά και ζωντανά δεδομένα από πολλαπλές πηγές (FootballData, TheSportsDB, SportMonks, Besoccer API, OpenFootball κ.ά.) και παρέχει real-time monitoring μέσω **FastAPI + Render**.

Υποστηρίζει πλήρως:
- Τοπική εκτέλεση (SQLite)
- Cloud hosting (Render / PostgreSQL)
- Αυτόματη εναλλαγή fallback (σε περίπτωση αποτυχίας cloud)
- Real-time ειδοποιήσεις, γραφήματα, backup και πλήρη έλεγχο κατάστασης

---

## 🚀 Quick Start

### 1️⃣ Εγκατάσταση Εξαρτήσεων
```bash
pip install -r requirements.txt
2️⃣ Δημιουργία .env
Περιλαμβάνει όλες τις μεταβλητές λειτουργίας για DB, APIs και monitoring.

env
Αντιγραφή κώδικα
# =====================================================
# DATABASE SETTINGS
# =====================================================
DATABASE_URL=sqlite:///matches.db
# ή PostgreSQL (Render)
# DATABASE_URL=postgresql+psycopg2://user:pass@host/dbname

# =====================================================
# RENDER MONITOR SETTINGS
# =====================================================
RENDER_API_KEY=your_render_api_key
RENDER_SERVICE_ID=your_service_id
RENDER_HEALTH_URL=https://eurogoals-v9-4-4-proplus.onrender.com/health

# =====================================================
# LOCAL SYSTEM SETTINGS
# =====================================================
EURO_GOALS_REFRESH=3600
SMARTMONEY_REFRESH_INTERVAL=60
BACKUP_INTERVAL_DAYS=30

# =====================================================
# DATA PROVIDERS API KEYS
# =====================================================
FOOTBALLDATA_API_KEY=your_footballdata_key
THESPORTSDB_API_KEY=your_thesportsdb_key
SPORTMONKS_API_KEY=your_sportmonks_key
BESOCCER_API_KEY=your_besoccer_key

# =====================================================
# BACKUP & DRIVE SETTINGS
# =====================================================
GOOGLE_DRIVE_FOLDER_ID=your_drive_folder_id
BACKUP_FILENAME=EURO_GOALS_BACKUP
3️⃣ Εκκίνηση
bash
Αντιγραφή κώδικα
uvicorn main:app --reload
Άνοιξε:

cpp
Αντιγραφή κώδικα
http://127.0.0.1:8000
🧩 API Testing (Postman)
Για δοκιμές όλων των endpoints υπάρχει έτοιμη συλλογή:

pgsql
Αντιγραφή κώδικα
EURO_GOALS_Postman/EURO_GOALS_v9.4.4_PRO+.postman_collection.json
Άνοιξε το Postman

Εισήγαγε το αρχείο παραπάνω

Θέσε μεταβλητή:

ini
Αντιγραφή κώδικα
BASE_URL = http://127.0.0.1:8000
ή:

ini
Αντιγραφή κώδικα
BASE_URL = https://eurogoals-v9-4-4-proplus.onrender.com
⚙️ Core Endpoints
Κατηγορία	Endpoint	Μέθοδος	Περιγραφή
System	/health	GET	Έλεγχος λειτουργίας πλατφόρμας
Database	/system/db_summary	GET	Επισκόπηση κατάστασης βάσης
Render Monitor	/system/render_status	GET	Κατάσταση υπηρεσίας Render
Auto Refresh	/system/refresh_status	GET	Κατάσταση auto-refresh
Smart Money	/smartmoney/status	GET	Ανάλυση κινήσεων SmartMoney
Feeds	/feeds/goals	GET	Ζωντανή ροή/ιστορικό γκολ
Alerts	/alerts/history	GET	Ιστορικό ειδοποιήσεων
Backup	/system/backup_now	POST	Δημιουργία χειροκίνητου backup

🧱 System Modules
🩺 1. System Status Panel
Παρέχει πλήρη εικόνα συστήματος:

💾 Database state

❤️ Health check

🔁 Auto Refresh toggle

💰 Smart Money engine

🌐 Render service

☁️ Backup sync

💰 2. Smart Money Detector
Αναλύει αλλαγές αποδόσεων (Pinnacle, Bet365, Stoiximan, PameStoixima)
και εντοπίζει “sharp” κινήσεις με όρια μεταβολών (π.χ. >5% σε 10 λεπτά).
Δείχνει:

Match ID

Παλαιά / νέα απόδοση

Πηγή

Timestamp

Volume (όπου διαθέσιμο)

🧮 3. Alert Center
Ενιαίο κέντρο παρακολούθησης ειδοποιήσεων:

Φίλτρα ανά ημερομηνία, πρωτάθλημα ή τύπο alert

Ειδοποιήσεις με ήχο και χρώμα

Καταγραφή στο alerts_history.db

Εμφάνιση “Active Alerts” στον πίνακα ελέγχου

🗄️ 4. Backup Manager
Αυτόματη και χειροκίνητη δημιουργία αντιγράφων ασφαλείας:

Δημιουργεί .sql αρχείο με timestamp (π.χ. EURO_GOALS_BACKUP_2025_11.sql)

Ανέβασμα στο Google Drive

Αυτόματος καθαρισμός παλαιών αντιγράφων

Υποστηρίζει και πλήρη export όλων των πινάκων

🔄 5. Render Auto-Refresh
Scheduler που ελέγχει:

CPU / RAM usage (μέσω API)

Auto restart εάν η υπηρεσία είναι ανενεργή

Ειδοποίηση μέσω System Panel

⚽ 6. Goal Feeds
Δεδομένα από Flashscore / Sofascore / OpenFootball / TheSportsDB.
Ενοποιεί όλες τις ευρωπαϊκές λίγκες:

Αγγλία (Premier–League 1–2–3)

Γερμανία (Bundesliga 1–2–3)

Ελλάδα (SuperLeague 1–2)

Ισπανία, Ιταλία, Γαλλία

Ευρωπαϊκές διοργανώσεις (UCL, UEL, Conference)

🧰 Tech Stack
Layer	Τεχνολογία
Backend	FastAPI (Python 3.11)
Database	SQLite (Local) / PostgreSQL (Render)
ORM	SQLAlchemy + Alembic
Frontend	Jinja2 + TailwindCSS
Scheduler	Auto refresh threads (async)
Monitoring	Custom Status Panel + Render Health API
Deployment	Render.com + GitHub auto deploy
Storage	Google Drive (Backups)
Audio Alerts	playsound / pydub
Data Handling	Pandas + OpenPyXL

🧾 Changelog
🆕 v9.4.4 PRO+ (Νοέμβριος 2025)
Ενοποιημένο README με Postman setup

Βελτιωμένο SmartMoney Detector v2

Νέο Backup Manager με Drive upload

Health & Render Monitor ανασχεδιασμένο

Προσθήκη πλήρους System Panel

Προετοιμασία για Goal Volume Analytics

🔁 Από v9.4.3
Ενοποίηση NextGen module

Καθαρισμός endpoints & UI templates

Σταθερότητα σε auto-refresh και fallback

📦 Folder Structure
arduino
Αντιγραφή κώδικα
EURO_GOALS/
│
├── main.py
├── templates/
│   ├── index.html
│   ├── system_status.html
│   ├── alert_history.html
│   ├── goal_feed.html
│   └── ...
│
├── static/
│   ├── css/
│   ├── js/
│   ├── icons/
│   └── sounds/
│
├── EURO_GOALS_Postman/
│   └── EURO_GOALS_v9.4.4_PRO+.postman_collection.json
│
├── db/
│   ├── matches.db
│   ├── alerts_history.db
│   └── backups/
│
├── utils/
│   ├── backup_manager.py
│   ├── render_monitor.py
│   ├── smartmoney.py
│   └── ...
│
├── requirements.txt
├── .env
└── README.md
🔮 Future Development
Πλήρης “Smart Volume Analytics” από ασιατικές αγορές

Συγχρονισμός Flashscore/Sofascore → unified DB

Αναλυτική mobile προβολή (responsive UI)

AI μοντέλο “SmartMoney Predictor” (probability mapping)

Integration με Telegram / Email alerts

📅 Credits
EURO_GOALS Project (2023–2025)
Lead Developer: Pierros
Architecture: EURO_GOALS Labs
Built with ❤️ using FastAPI, Tailwind & Render

© 2025 EURO_GOALS Project – All Rights Reserved.