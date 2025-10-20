# api_app.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import pandas as pd
import os
from fastapi.middleware.cors import CORSMiddleware

API_CSV = "appointments.csv"

app = FastAPI(title="Appointment API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure file exists
if not os.path.exists(API_CSV):
    df_init = pd.DataFrame(columns=[
        "first_name","last_name","sex","mobile","dob","email",
        "partner_included","partner_first","partner_last","department",
        "doctor","date","time_slot","reason","summary"
    ])
    df_init.to_csv(API_CSV, index=False)

class Appointment(BaseModel):
    first_name: str
    last_name: str
    sex: str
    mobile: str
    dob: str
    email: str
    partner_included: bool = False
    partner_first: str = ""
    partner_last: str = ""
    department: str
    doctor: str
    date: str
    time_slot: str
    reason: str
    summary: str = ""

@app.get("/api/appointments", response_model=List[Appointment])
def get_appointments():
    df = pd.read_csv(API_CSV)
    return df.to_dict(orient="records")

@app.post("/api/appointments", status_code=201)
def create_appointment(appt: Appointment):
    df = pd.read_csv(API_CSV)
    df = pd.concat([df, pd.DataFrame([appt.dict()])], ignore_index=True)
    df.to_csv(API_CSV, index=False)
    return {"status":"ok", "message":"appointment saved"}

@app.get("/")
def read_root():
    return {"message": "Appointment API is running"}