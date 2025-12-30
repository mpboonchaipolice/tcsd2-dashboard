# backend/main.py
import os
import time
import pandas as pd
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

app = FastAPI()
security = HTTPBasic()

# ---------- CORS (ให้ Vercel เรียกได้) ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ถ้าจะเข้มงวดค่อยเปลี่ยนเป็นโดเมน vercel ของคุณ
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- ENV ----------
SHEET_ID = os.getenv("SHEET_ID", "")
CASES_GID = os.getenv("CASES_GID", "")
SUSPECTS_GID = os.getenv("SUSPECTS_GID", "")
SEIZURES_GID = os.getenv("SEIZURES_GID", "")

APP_USER = os.getenv("APP_USER", "admin")
APP_PASS = os.getenv("APP_PASS", "admin")

def require_login(creds: HTTPBasicCredentials = Depends(security)):
    ok_user = secrets.compare_digest(creds.username, APP_USER)
    ok_pass = secrets.compare_digest(creds.password, APP_PASS)
    if not (ok_user and ok_pass):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True

def csv_url(gid: str) -> str:
    # ใส่ cache bust กัน Google/Proxy cache
    ts = int(time.time())
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}&t={ts}"

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/dashboard", dependencies=[Depends(require_login)])
def dashboard():
    if not SHEET_ID:
        raise HTTPException(status_code=500, detail="SHEET_ID not set")

    # อ่าน 3 ชีท
    df_cases = pd.read_csv(csv_url(CASES_GID))
    df_suspects = pd.read_csv(csv_url(SUSPECTS_GID))
    df_seizures = pd.read_csv(csv_url(SEIZURES_GID))

    # ทำสรุปแบบง่าย ๆ (คุณปรับสูตรเพิ่มได้)
    summary = {
        "cases_count": int(len(df_cases)),
        "suspects_count": int(len(df_suspects)),
        "seizures_count": int(len(df_seizures)),
    }

    # ส่งข้อมูลดิบกลับไปให้ frontend ด้วย (ถ้าอยาก)
    return {
        "summary": summary,
        "cases": df_cases.fillna("").to_dict(orient="records"),
        "suspects": df_suspects.fillna("").to_dict(orient="records"),
        "seizures": df_seizures.fillna("").to_dict(orient="records"),
    }
