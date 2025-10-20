# streamlit_app.py
import streamlit as st
import pandas as pd
import os
import requests
from datetime import datetime
from euriai import EuriaiClient
from dotenv import load_dotenv
load_dotenv()

# ---------- Configuration ----------
EURI_KEY = os.environ.get("EURI_API_KEY")
EURI_MODEL = "gpt-4.1-mini"
API_BACKEND = os.getenv("POC_API_URL", "http://localhost:8000/api/appointments")
APPT_CSV = "appointments.csv"

# Initialize Euri client
if not EURI_KEY:
    st.error("EURI_API_KEY environment variable not found. Please set it and restart.")
    st.stop()

client = EuriaiClient(api_key=EURI_KEY, model=EURI_MODEL)

# ---------- Clinic Data ----------
CLINIC_LOCATION = "Avenir Fertility Centre, San Diego, California"
CLINIC_HOURS = "Mon-Sat, 9:00 AM - 7:00 PM"
CLINIC_PHONE = "+1 (619) 555-0123"

DUMMY_DATA = {
    "Fertility / IVF": [
        {"name": "Dr. Priya Nair", "slots": ["10:00 AM", "10:30 AM", "11:00 AM"]},
        {"name": "Dr. Rhea Thomas", "slots": ["2:00 PM", "3:00 PM", "5:00 PM"]},
        {"name": "Dr. Vikram Singh", "slots": ["9:00 AM", "1:00 PM", "4:00 PM"]}
    ],
    "Andrology": [
        {"name": "Dr. Arun Menon", "slots": ["11:00 AM", "1:00 PM", "4:00 PM"]},
        {"name": "Dr. Sanjay Gupta", "slots": ["10:30 AM", "2:30 PM", "3:30 PM"]},
        {"name": "Dr. Rohit Verma", "slots": ["9:30 AM", "12:30 PM", "5:30 PM"]}
    ],
    "Genetic Testing": [
        {"name": "Dr. Meera Kapoor", "slots": ["9:30 AM", "10:30 AM","11:30 AM"]},
        {"name": "Dr. Anil Desai", "slots": ["1:30 PM", "3:30 PM", "4:30 PM"]},
        {"name": "Dr. Leena Shah", "slots": ["11:30 AM", "4:30 PM", "5:30 PM"]}
    ],
    "Counselling": [
        {"name": "Dr. Kavita Rao", "slots": ["12:00 PM", "2:30 PM", "4:00 PM"]},
        {"name": "Dr. Nisha Patel", "slots": ["10:00 AM", "1:00 PM", "3:00 PM"]},
        {"name": "Dr. Suresh Iyer", "slots": ["9:00 AM", "11:00 AM", "5:00 PM"]}
    ],
    "Gynecology / Reproductive Endocrinology": [
        {"name": "Dr. Seema Iyer", "slots": ["3:30 PM", "4:30 PM","5:30 PM"]},
        {"name": "Dr. Ananya Sen", "slots": ["9:30 AM", "12:30 PM", "2:30 PM"]},
        {"name": "Dr. Ritu Malhotra", "slots": ["10:30 AM", "1:30 PM", "3:30 PM"]}
    ]
}

TREATMENT_COSTS = {
    "IVF / ICSI": "$12,00 - $15,00",
    "IUI": "$800 - $1,200",
    "Egg Freezing": "$7,00 - $10,00",
    "Genetic Testing": "$5,00 - $8,00",
    "Male Infertility": "$3,00 - $6,00",
    "Donor Programs": "$20,00 - $30,00"
}

# Ensure CSV file exists
if not os.path.exists(APPT_CSV):
    df_init = pd.DataFrame(columns=[
        "first_name","last_name","sex","mobile","dob","email",
        "partner_included","partner_first","partner_last","department",
        "doctor","date","time_slot","reason","summary","created_at"
    ])
    df_init.to_csv(APPT_CSV, index=False)

# ---------- Streamlit UI ----------
st.set_page_config(page_title="Avenir Fertility Clinic", layout="centered")
st.title("🏥 Avenir Fertility Clinic - San Diego")
st.write("**Your journey to parenthood begins here. We're here to help you every step of the way.**")

# Initialize session state
if "step" not in st.session_state:
    st.session_state.step = 0
    st.session_state.form = {}
    st.session_state.messages = []
    st.session_state.current_menu = "main"
    st.session_state.welcome_shown = False

# Helper to add bot message
def bot_say(text):
    st.session_state.messages.append({"who":"bot","text":text})

# Helper to add user message
def user_say(text):
    st.session_state.messages.append({"who":"user","text":text})

# Show messages
def render_messages():
    for i, m in enumerate(st.session_state.messages):
        if m["who"] == "bot":
            st.markdown(f"{m['text']}")
        else:
            st.markdown(f"**You:** {m['text']}")

# Main menu options - show only once
def show_main_menu():
    if not st.session_state.welcome_shown:
        bot_say("""Hi there! 👨‍⚕️ Welcome to *Avenir Fertility Clinic*!
I'm your virtual assistant. How can I help you today?

**Options:**
1️⃣ Book an Appointment
2️⃣ Learn About Treatments
3️⃣ Cost / Packages
4️⃣ Talk to a Fertility Expert
5️⃣ Know About Success Stories
6️⃣ Get Clinic Location & Timings""")
        st.session_state.welcome_shown = True

# Cost information
def show_cost_info():
    bot_say("""**💰 Treatment Costs & Packages**

Our treatment plans are customized based on your medical needs. Here are estimated costs:""")
    
    for treatment, cost in TREATMENT_COSTS.items():
        st.write(f"**{treatment}:** {cost}")
    
    st.markdown("---")
    st.info(f"💡 **For detailed pricing and personalized quotes, please call us at {CLINIC_PHONE}**")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📅 Book Consultation", key="cost_book"):
            user_say("Book an Appointment")
            st.session_state.current_menu = "appointment"
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button("🔙 Back to Main", key="cost_back"):
            user_say("Back to Main Menu")
            st.session_state.current_menu = "main"
            st.rerun()

# Location information
def show_location_info():
    bot_say(f"""**📍 Clinic Location & Timings**

🏥 **{CLINIC_LOCATION}**
⏰ **Hours:** {CLINIC_HOURS}
📞 **Phone:** {CLINIC_PHONE}

We're conveniently located in San Diego with ample parking and easy access.""")
    
    # Generate location description using EURI
    try:
        location_prompt = f"""Generate a brief, welcoming description of a fertility clinic location in San Diego, California. 
        Include positive aspects about accessibility, neighborhood, and facilities. Keep it to 2-3 sentences."""
        resp = client.generate_completion(prompt=location_prompt, temperature=0.3, max_tokens=100)
        location_desc = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
        st.write(location_desc)
    except:
        st.write("Our state-of-the-art facility in San Diego offers comfortable, private consultation rooms and advanced medical equipment.")
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📅 Book Appointment", key="loc_book"):
            user_say("Book an Appointment")
            st.session_state.current_menu = "appointment"
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button("🔙 Back to Main", key="loc_back"):
            user_say("Back to Main Menu")
            st.session_state.current_menu = "main"
            st.rerun()

# Treatments information
def show_treatments_info():
    bot_say("""** 👨‍⚕️💡 Learn About Treatments**

Which treatment would you like to know more about?""")
    
    treatment = st.selectbox("Select Treatment", list(TREATMENT_COSTS.keys()) + ["All Treatments"])
    
    if st.button("Get Treatment Info", key="treatment_info"):
        user_say(f"Learn about {treatment}")
        
        try:
            prompt = f"""Provide a concise 2-3 sentence description of {treatment} fertility treatment. 
            Focus on what the treatment involves and who it's for. Keep it patient-friendly and informative."""
            resp = client.generate_completion(prompt=prompt, temperature=0.3, max_tokens=150)
            treatment_info = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
            bot_say(f"**{treatment}**\n\n{treatment_info}")
        except Exception as e:
            bot_say(f"**{treatment}**\n\nThis treatment helps patients on their fertility journey. Our specialists can provide detailed information during your consultation.")
        
        st.rerun()
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📅 Book Consultation", key="treat_book"):
            user_say("Book an Appointment")
            st.session_state.current_menu = "appointment"
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button("🔙 Back to Main", key="treat_back"):
            user_say("Back to Main Menu")
            st.session_state.current_menu = "main"
            st.rerun()

# Expert consultation
# Expert consultation
def show_expert_consultation():
    bot_say("""**👨‍⚕️ Talk to a Fertility Expert**

We'd be happy to connect you with our fertility specialists! Please share your details and we'll contact you.""")
    
    col1, col2 = st.columns(2)
    with col1:
        exp_name = st.text_input("Your Name", key="exp_name")
        exp_phone = st.text_input("Mobile Number", key="exp_phone")
    with col2:
        exp_email = st.text_input("Email ID", key="exp_email")
        exp_preference = st.selectbox("Preferred Contact", ["Phone Call", "Video Consultation", "Either"], key="exp_pref")
    
    if st.button("Request Expert Callback", key="exp_callback"):
        if exp_name and exp_phone:
            user_say(f"Requested callback from {exp_name}")
            
            # Generate confirmation message using EURI
            try:
                prompt = f"""Create a warm confirmation message for a fertility clinic callback request. 
                Include: thanking the patient by name, confirming contact method, and reassuring them about the callback timing.
                End with: Warm regards, Avenir Fertility Clinic
                
                Patient: {exp_name}
                Contact: {exp_phone}
                Method: {exp_preference}"""
                resp = client.generate_completion(prompt=prompt, temperature=0.2, max_tokens=150)
                callback_msg = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
            except:
                callback_msg = f"Thank you {exp_name}! Our fertility expert will contact you within 24 hours at {exp_phone} via {exp_preference.lower()}.\n\nWarm regards,\nAvenir Fertility Clinic Thank you for connecting with Avenir Fertility!"
            
            bot_say(callback_msg)
            
            # Save callback request to database
            callback_record = {
                "name": exp_name,
                "phone": exp_phone,
                "email": exp_email,
                "preference": exp_preference,
                "type": "expert_callback",
                "created_at": datetime.now().isoformat()
            }
            
            # Append to CSV or database
            try:
                callback_df = pd.read_csv(APPT_CSV)
                callback_df = pd.concat([callback_df, pd.DataFrame([callback_record])], ignore_index=True)
                callback_df.to_csv(APPT_CSV, index=False)
            except Exception as e:
                st.error(f"Error saving callback request: {e}")
            
            st.success("✅ Expert callback requested successfully!")
            st.rerun()
        else:
            st.warning("Please provide at least your name and mobile number.")
    
    st.markdown("---")
    if st.button("🔙 Back to Main", key="exp_back"):
        user_say("Back to Main Menu")
        st.session_state.current_menu = "main"
        st.rerun()

# Success stories
def show_success_stories():
    bot_say("""**🌟 Patient Success Stories**

Here are some inspiring stories from our patients:""")
    
    try:
        stories_prompt = """Generate 2 brief, inspiring fertility treatment success stories (2-3 sentences each). 
        Make them positive and hopeful, but keep them generic without specific names."""
        resp = client.generate_completion(prompt=stories_prompt, temperature=0.4, max_tokens=200)
        stories = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
        st.write(stories)
    except:
        st.write("""
        *"After years of trying, the compassionate team at Avenir helped us welcome our beautiful daughter. The entire journey was supported with care and expertise."*
        
        *"The genetic testing and IVF treatment gave us the confidence we needed. We're now expecting twins and couldn't be happier with our decision."*
        """)
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📅 Start Your Journey", key="stories_book"):
            user_say("Book an Appointment")
            st.session_state.current_menu = "appointment"
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button("🔙 Back to Main", key="stories_back"):
            user_say("Back to Main Menu")
            st.session_state.current_menu = "main"
            st.rerun()

# Appointment booking flow
QUESTIONS = [
    {"key":"first_name","q":"Please enter your first name:"},
    {"key":"last_name","q":"Please enter your last name:"},
    {"key":"sex","q":"Sex assigned at birth (Female / Male / Prefer not to say):"},
    {"key":"mobile","q":"Mobile number (for confirmation):"},
    {"key":"dob","q":"Date of birth (DD/MM/YYYY):"},
    {"key":"email","q":"Email ID:"},
    {"key":"partner_included","q":"Would you like to add partner details? (yes/no)"},
    {"key":"department","q":"Which department would you like to book an appointment with?"},
    {"key":"doctor","q":"Choose a doctor from the list:"},
    {"key":"date","q":"Please pick a preferred Date (DD/MM/YYYY):"},
    {"key":"time_slot","q":"Please pick a time slot:"},
    {"key":"reason","q":"Briefly tell us your reason for appointment:"},
]

def parse_yes_no(val):
    v = str(val).strip().lower()
    if v in ["yes","y","true","1"]:
        return True
    return False

# Render appropriate content based on current menu
render_messages()

# Show main menu buttons only when in main menu
if st.session_state.current_menu == "main":
    show_main_menu()
    st.markdown("---")
    st.write("**Choose an option:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📅 Book Appointment", use_container_width=True):
            user_say("Book an Appointment")
            st.session_state.current_menu = "appointment"
            st.session_state.step = 1
            st.rerun()
        if st.button("💰 Cost / Packages", use_container_width=True):
            user_say("Cost / Packages")
            st.session_state.current_menu = "cost"
            st.rerun()
    with col2:
        if st.button("💡 Learn Treatments", use_container_width=True):
            user_say("Learn About Treatments")
            st.session_state.current_menu = "treatments"
            st.rerun()
        if st.button("📍 Location & Hours", use_container_width=True):
            user_say("Get Clinic Location & Timings")
            st.session_state.current_menu = "location"
            st.rerun()
    with col3:
        if st.button("👨‍⚕️ Talk to Expert", use_container_width=True):
            user_say("Talk to a Fertility Expert")
            st.session_state.current_menu = "expert"
            st.rerun()
        if st.button("🌟 Success Stories", use_container_width=True):
            user_say("Know About Success Stories")
            st.session_state.current_menu = "stories"
            st.rerun()

elif st.session_state.current_menu == "cost":
    show_cost_info()
elif st.session_state.current_menu == "location":
    show_location_info()
elif st.session_state.current_menu == "treatments":
    show_treatments_info()
elif st.session_state.current_menu == "expert":
    show_expert_consultation()
elif st.session_state.current_menu == "stories":
    show_success_stories()
elif st.session_state.current_menu == "appointment":
    st.markdown("---")
    step = st.session_state.step

    # Appointment booking steps with Enter key support
    if step >= 1 and step <= 6:
        q = QUESTIONS[step-1]["q"]
        user_input = st.text_input(q, key=f"input_{step}")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("Submit", key=f"submit_{step}", use_container_width=True):
                val = user_input.strip()
                if not val:
                    st.warning("Please enter a value.")
                else:
                    user_say(val)
                    st.session_state.form[QUESTIONS[step-1]["key"]] = val
                    if QUESTIONS[step-1]["key"] == "partner_included" and parse_yes_no(val):
                        st.session_state.step = 7
                    else:
                        st.session_state.step += 1
                    st.rerun()
        with col2:
            if st.button("🔙 Back", key=f"back_{step}", use_container_width=True):
                st.session_state.step = max(1, step - 1)
                st.rerun()

    elif step == 7:
        val = st.text_input("Partner's First Name:", key="partner_first")
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("Submit", key="partner_first_submit", use_container_width=True):
                v = val.strip()
                if v:
                    user_say(v)
                    st.session_state.form["partner_first"] = v
                    st.session_state.step = 8
                    st.rerun()
                else:
                    st.warning("Enter partner first name.")
        with col2:
            if st.button("🔙 Back", key="back_partner_first", use_container_width=True):
                st.session_state.step = 6
                st.rerun()
                
    elif step == 8:
        val = st.text_input("Partner's Last Name:", key="partner_last")
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("Submit", key="partner_last_submit", use_container_width=True):
                v = val.strip()
                if v:
                    user_say(v)
                    st.session_state.form["partner_last"] = v
                    st.session_state.step = 9
                    st.rerun()
                else:
                    st.warning("Enter partner last name.")
        with col2:
            if st.button("🔙 Back", key="back_partner_last", use_container_width=True):
                st.session_state.step = 7
                st.rerun()

    elif step == 9:
        st.write("Select Department:")
        dept = st.selectbox("Departments", options=list(DUMMY_DATA.keys()), key="dept_select")
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("Select Department", key="dept_submit", use_container_width=True):
                user_say(dept)
                st.session_state.form["department"] = dept
                st.session_state.step = 10
                st.rerun()
        with col2:
            if st.button("🔙 Back", key="back_dept", use_container_width=True):
                st.session_state.step = 8 if st.session_state.form.get("partner_included") and parse_yes_no(st.session_state.form.get("partner_included")) else 7
                st.rerun()

    elif step == 10:
        dept = st.session_state.form.get("department")
        doctors = [d["name"] for d in DUMMY_DATA.get(dept, [])]
        doctor = st.selectbox("Available Doctors", options=doctors, key="doctor_select")
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("Choose Doctor", key="doctor_submit", use_container_width=True):
                user_say(doctor)
                st.session_state.form["doctor"] = doctor
                st.session_state.step = 11
                st.rerun()
        with col2:
            if st.button("🔙 Back", key="back_doctor", use_container_width=True):
                st.session_state.step = 9
                st.rerun()

    elif step == 11:
        date_input = st.text_input("Preferred Date (DD/MM/YYYY)", key="date_input")
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("Submit Date", key="date_submit", use_container_width=True):
                v = date_input.strip()
                try:
                    datetime.strptime(v, "%d/%m/%Y")
                    user_say(v)
                    st.session_state.form["date"] = v
                    st.session_state.step = 12
                    st.rerun()
                except:
                    st.warning("Invalid date format. Use DD/MM/YYYY")
        with col2:
            if st.button("🔙 Back", key="back_date", use_container_width=True):
                st.session_state.step = 10
                st.rerun()

    elif step == 12:
        dept = st.session_state.form.get("department")
        doctor = st.session_state.form.get("doctor")
        slots = []
        for d in DUMMY_DATA.get(dept, []):
            if d["name"] == doctor:
                slots = d["slots"]
                break
        if not slots:
            st.write("No slots available. Please choose another doctor.")
            if st.button("Choose another doctor"):
                st.session_state.step = 10
                st.rerun()
        else:
            slot = st.selectbox("Choose a time slot", options=slots, key="slot_select")
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button("Select slot", key="slot_submit", use_container_width=True):
                    user_say(slot)
                    st.session_state.form["time_slot"] = slot
                    st.session_state.step = 13
                    st.rerun()
            with col2:
                if st.button("🔙 Back", key="back_slot", use_container_width=True):
                    st.session_state.step = 11
                    st.rerun()

    elif step == 13:
        reason = st.text_area("Reason for appointment (brief):", key="reason_input")
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("Submit Reason", key="reason_submit", use_container_width=True):
                v = reason.strip()
                user_say(v)
                st.session_state.form["reason"] = v
                st.session_state.step = 14
                st.rerun()
        with col2:
            if st.button("🔙 Back", key="back_reason", use_container_width=True):
                st.session_state.step = 12
                st.rerun()

    elif step == 14:
        form = st.session_state.form
        st.markdown("### 📋 Appointment Summary")
        summary_df = pd.DataFrame([form]).T.rename(columns={0: "Value"})
        st.dataframe(summary_df, use_container_width=True)
        
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("✅ Confirm Appointment", type="primary", use_container_width=True):
                user_say("Confirm appointment")
                
                # Generate confirmation message using EURI
                try:
                    prompt = f"""Create a warm, professional confirmation message for a fertility clinic appointment. 
                    Include: patient name, doctor, date/time, and a reassuring tone. Keep it to 3-4 sentences and also include Thank you for connecting with Avenir Fertility! 
                    Our team will reach out soon. 
                    Would you like to receive fertility tips, treatment updates, and success stories on WhatsApp? 
                    (Yes/No) .
                    
                    Details: {form}"""
                    resp = client.generate_completion(prompt=prompt, temperature=0.2, max_tokens=200)
                    confirmation_msg = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
                except:
                    confirmation_msg = f"Thank you {form.get('first_name', '')}! Your appointment with {form.get('doctor', '')} on {form.get('date', '')} at {form.get('time_slot', '')} has been confirmed. We look forward to seeing you! Warm regards, Avenir Fertility Clinic"
                
                # Save to CSV
                record = {
                    "first_name": form.get("first_name",""),
                    "last_name": form.get("last_name",""),
                    "sex": form.get("sex",""),
                    "mobile": form.get("mobile",""),
                    "dob": form.get("dob",""),
                    "email": form.get("email",""),
                    "partner_included": parse_yes_no(form.get("partner_included","no")),
                    "partner_first": form.get("partner_first",""),
                    "partner_last": form.get("partner_last",""),
                    "department": form.get("department",""),
                    "doctor": form.get("doctor",""),
                    "date": form.get("date",""),
                    "time_slot": form.get("time_slot",""),
                    "reason": form.get("reason",""),
                    "summary": "Appointment booked via chatbot",
                    "created_at": datetime.now().isoformat()
                }
                df = pd.read_csv(APPT_CSV)
                df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
                df.to_csv(APPT_CSV, index=False)

                # POST to API
                try:
                    r = requests.post(API_BACKEND, json=record, timeout=5)
                    if r.status_code in (200,201):
                        st.success("✅ Appointment saved successfully!")
                    else:
                        st.warning("Appointment saved locally but API returned an error.")
                except:
                    st.success("✅ Appointment saved locally!")

                bot_say(confirmation_msg)
                st.session_state.step = 0
                st.session_state.form = {}
                st.session_state.current_menu = "main"
                st.rerun()
        
        with col2:
            if st.button("✏️ Edit Details", use_container_width=True):
                user_say("Edit appointment details")
                st.session_state.step = 1
                st.rerun()
        
        with col3:
            if st.button("❌ Cancel", use_container_width=True):
                user_say("Cancel appointment")
                st.info("Appointment cancelled.")
                st.session_state.step = 0
                st.session_state.form = {}
                st.session_state.current_menu = "main"
                st.rerun()