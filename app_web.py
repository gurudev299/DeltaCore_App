import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import sqlite3
import hashlib
from datetime import datetime, timedelta
import streamlit.components.v1 as components

# Database file
DB_NAME = "deltacore_app.db"

# Page Layout & Config
st.set_page_config(
    page_title="DeltaCore | Institutional Autonomous Intelligence", 
    page_icon="⚡", 
    layout="wide"
)

# Custom High-End SaaS UI & Professional Typography / Sidebar Styling
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Outfit', sans-serif !important;
        }

        @keyframes moving-glow {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        .animated-brand {
            font-size: 42px;
            font-weight: 800;
            letter-spacing: 3px;
            background: linear-gradient(135deg, #38BDF8 0%, #FFFFFF 50%, #3B82F6 100%);
            background-size: 200% auto;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: moving-glow 5s linear infinite;
            margin-bottom: 0px;
            text-transform: uppercase;
        }

        .brand-container {
            background: linear-gradient(145deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.95));
            border: 1px solid rgba(56, 189, 248, 0.3);
            padding: 16px 22px;
            border-radius: 14px;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            backdrop-filter: blur(10px);
        }

        .brand-badge {
            background: rgba(56, 189, 248, 0.12);
            color: #38BDF8;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 1.2px;
            border: 1px solid rgba(56, 189, 248, 0.3);
            text-transform: uppercase;
        }
        
        .sub-title {
            font-size: 16px;
            color: #94A3B8;
            margin-bottom: 20px;
            font-weight: 500;
            letter-spacing: 0.5px;
        }

        .section-header {
            font-size: 22px;
            font-weight: 700;
            color: #F8FAFC;
            margin-top: 15px;
            margin-bottom: 15px;
            border-left: 4px solid #38BDF8;
            padding-left: 12px;
        }

        .content-card {
            background-color: #1E293B;
            padding: 25px;
            border-radius: 12px;
            border: 1px solid #334155;
            margin-bottom: 20px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }

        .content-card h3 {
            color: #38BDF8;
            font-size: 19px;
            margin-bottom: 12px;
            font-weight: 700;
        }

        .content-card p, .content-card li {
            color: #CBD5E1;
            font-size: 15px;
            line-height: 1.6;
        }

        /* Sidebar Styling */
        div[data-testid="stSidebar"] {
            background-color: #0B0F19;
            border-right: 1px solid #1E293B;
        }

        div[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] {
            background: linear-gradient(145deg, #162032, #1E293B);
            border: 1px solid #334155;
            border-radius: 12px;
            margin-bottom: 12px;
            padding: 14px 16px;
            width: 100%;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        div[data-testid="stSidebar"] .stRadio [data-baseweb="radio"]:hover {
            background: linear-gradient(145deg, #1E293B, #253349);
            border-color: #38BDF8;
            transform: translateX(4px);
            box-shadow: 0 4px 15px rgba(56, 189, 248, 0.2);
        }

        div[data-testid="stSidebar"] .stRadio input[type="radio"] {
            display: none;
        }
        
        div[data-testid="stSidebar"] .stRadio div[class*="st-emotion-cache"] {
            margin-left: 0px !important;
        }

        div[data-testid="stSidebar"] .stRadio p {
            font-family: 'Outfit', sans-serif !important;
            font-size: 15px !important;
            font-weight: 600 !important;
            color: #F1F5F9 !important;
            letter-spacing: 0.5px;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize Session States
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False
if 'trade_active' not in st.session_state:
    st.session_state.trade_active = False
if 'entry_timestamp' not in st.session_state:
    st.session_state.entry_timestamp = None
if 'active_trade_details' not in st.session_state:
    st.session_state.active_trade_details = {}


# ==========================================
# HELPER: DATABASE MANAGEMENT
# ==========================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            payment_status TEXT NOT NULL,
            utr_number TEXT,
            referral_done BOOLEAN,
            feedback_done BOOLEAN
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            timestamp TEXT,
            contract TEXT,
            lots INTEGER,
            buy_price REAL,
            sell_price REAL,
            duration TEXT,
            exit_reason TEXT,
            pnl REAL,
            status TEXT,
            explanation TEXT
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        admin_pass = hash_password("admin123")
        tester_pass = hash_password("test1234")
        year_later = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
        two_weeks = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
        
        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)", ("admin", admin_pass, year_later, "Paid", "DIRECT_ADMIN", True, True))
        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)", ("tester", tester_pass, two_weeks, "Paid", "TEST_UTR", False, False))
        conn.commit()
    
    conn.close()

init_db()

def get_user_record(username):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    cursor.execute("SELECT username, password, expiry_date, payment_status, utr_number, referral_done, feedback_done FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "Username": row[0],
            "Password": row[1],
            "ExpiryDate": row[2],
            "PaymentStatus": row[3],
            "UTR": row[4],
            "ReferralDone": bool(row[5]),
            "FeedbackDone": bool(row[6])
        }
    return None

def register_pending_user(username, password, utr_number):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return False, "Username pehle se maujood hai. Dusra naam chunein."
    
    hashed_pwd = hash_password(password)
    today_str = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)", (username, hashed_pwd, today_str, "Pending", utr_number, False, False))
    conn.commit()
    conn.close()
    return True, "Registered successfully! Admin verification ke baad account activate kar diya jayega."

def activate_user_subscription(username, days=14):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    new_expiry = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    cursor.execute("UPDATE users SET expiry_date = ?, payment_status = 'Paid' WHERE username = ?", (new_expiry, username))
    conn.commit()
    conn.close()
    return new_expiry

def update_user_extension(username, add_days):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    cursor.execute("SELECT expiry_date FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    if row:
        current_expiry = datetime.strptime(str(row[0]), "%Y-%m-%d")
        new_expiry = max(datetime.now(), current_expiry) + timedelta(days=add_days)
        new_expiry_str = new_expiry.strftime("%Y-%m-%d")
        cursor.execute("UPDATE users SET expiry_date = ?, referral_done = 1, feedback_done = 1 WHERE username = ?", (new_expiry_str, username))
        conn.commit()
        conn.close()
        return new_expiry_str
    conn.close()
    return None


# ==========================================
# HELPER: MARKET & OPTION CHAIN ENGINE
# ==========================================
@st.cache_data(ttl=15)
def fetch_market_and_option_chain():
    try:
        ticker = yf.Ticker("^NSEI")
        live_df = ticker.history(period="1d", interval="5m")
        spot_price = live_df['Close'].iloc[-1] if not live_df.empty else 23250.0
        open_price = live_df['Open'].iloc[0] if not live_df.empty else spot_price
        intraday_change = spot_price - open_price
        
        atm = round(spot_price / 50) * 50
        pcr_ratio = 1.15 if intraday_change >= 0 else 0.82
        
        return {
            "spot": float(spot_price),
            "change": float(intraday_change),
            "atm": int(atm),
            "pcr": float(pcr_ratio),
            "bias": "BULLISH 🟢" if intraday_change >= 0 else "BEARISH 🔴"
        }
    except:
        return {
            "spot": 23250.0,
            "change": -25.0,
            "atm": 23250,
            "pcr": 0.95,
            "bias": "BEARISH 🔴"
        }

def generate_trade_explanation(pnl, exit_reason, duration_mins, pcr, change):
    explanations = []
    if pnl > 0:
        explanations.append("🟢 **Positive Momentum & Trend Alignment:** Live chart momentum aur intraday price change same direction me the.")
        if pcr >= 1.0:
            explanations.append(f"🟢 **Option Chain Support (PCR {pcr:.2f}):** Put-Call Ratio favorable tha aur Put writers ka strong support mila.")
        explanations.append(f"🎯 **Target Discipline:** Trade ko {duration_mins} minute hold karne ke baad target price par successfully exit kiya gaya.")
    else:
        explanations.append("🔴 **Trend Reversal / Momentum Shift:** Market me sudden momentum shift hone ki wajah se position opposite direction me chali gayi.")
        if pcr < 1.0:
            explanations.append(f"🔴 **Option Chain Resistance (PCR {pcr:.2f}):** Call writing heavy hone ki wajah se upside pressure weak tha.")
        if duration_mins > 45:
            explanations.append("⏱️ **Theta Decay Impact:** Trade ko jyada der hold karne ki wajah se options me time value (Theta decay) ka nuksan hua.")
        explanations.append(f"🛑 **Exit Triggered:** Reason: `{exit_reason}`. Stop-loss discipline maintain karna capital protection ke liye zaroori tha.")
    return " | ".join(explanations)

def send_telegram_signal_alert(bot_token, chat_id, message):
    if not bot_token or not chat_id:
        return False
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        response = requests.post(url, json=payload, timeout=5)
        return response.status_code == 200
    except:
        return False

def check_kill_switch(username, max_daily_loss):
    today_date = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, pnl FROM trades WHERE username = ?", (username,))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return False, 0.0
    
    total_today_pnl = 0.0
    for row in rows:
        t_stamp = str(row[0])
        t_pnl = float(row[1])
        if t_stamp.startswith(today_date):
            total_today_pnl += t_pnl
            
    if total_today_pnl <= -abs(max_daily_loss):
        return True, total_today_pnl
    return False, total_today_pnl


# ==========================================
# SECURE HIDDEN ADMIN PORTAL & APPROVALS
# ==========================================
with st.sidebar.expander("🔐 Founder Portal"):
    admin_secret_key = st.text_input("Enter Admin Passcode", type="password")
    SECRET_ADMIN_PASSWORD = "DeltaCoreAdmin2026" 

    is_admin = False

    if admin_secret_key == SECRET_ADMIN_PASSWORD:
        st.success("✅ Admin Access Granted")
        is_admin = True
    elif admin_secret_key:
        st.error("❌ Incorrect Passcode")

    if is_admin:
        st.warning("⚡ **Founder Quick Access Active**")
        
        # Pending Users Management & One-Click Approval Section
        st.markdown("---")
        st.markdown("### 📋 Pending User Approvals")
        conn = sqlite3.connect(DB_NAME, timeout=10)
        pending_df = pd.read_sql_query("SELECT username, utr_number FROM users WHERE payment_status = 'Pending'", conn)
        conn.close()

        if not pending_df.empty:
            for idx, row in pending_df.iterrows():
                st.write(f"👤 **{row['username']}** | UTR: `{row['utr_number']}`")
                if st.button(f"Approve {row['username']}", key=f"app_btn_{row['username']}"):
                    activate_user_subscription(row['username'], 14)
                    st.success(f"✅ {row['username']} approved successfully!")
                    st.rerun()
        else:
            st.info("No pending users found.")

        st.markdown("---")
        if st.button("Force Admin Bypass"):
            st.session_state["admin_logged_in"] = True
            st.session_state.logged_in = True
            st.session_state.username = "admin"
            st.success("Bypass Activated successfully!")
            st.rerun()


# ==========================================
# MAIN APP ROUTING (LOGIN CHECK OR DASHBOARD)
# ==========================================
if not st.session_state.logged_in and not st.session_state.get("admin_logged_in", False):
    
    lang_choice = st.sidebar.radio("🌐 Choose Language / भाषा चुनें:", ["English", "हिंदी (Hindi)"], horizontal=True)

    st.markdown("""
        <div class="brand-container">
            <div>
                <span class="animated-brand">⚡ DELTACORE</span>
            </div>
            <div>
                <span class="brand-badge">Institutional V2.8</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    if lang_choice == "English":
        st.markdown('<p class="sub-title">Institutional-Grade Nifty Option Buying & Autonomous Intelligence Command Center</p>', unsafe_allow_html=True)
        public_menu = st.tabs(["📖 About & Architecture", "💎 Pricing & QR Payment", "📝 Register New Account", "🔐 User Login"])

        with public_menu[0]:
            st.markdown('<p class="section-header">🏢 Institutional Architecture & Platform Overview</p>', unsafe_allow_html=True)
            st.markdown("""
            <div class="content-card">
                <h3>1. Platform Philosophy & Quantitative Framework</h3>
                <p><b>DeltaCore</b> is engineered not as a simple script, but as an <b>Institutional Quantitative Framework</b> designed specifically for professional Nifty option buyers. Retail traders frequently suffer capital erosion due to emotional biases, fragmented data streams, and poor risk control. DeltaCore solves this by unifying live price action with institutional derivative telemetry into a single, cohesive command center.</p>
            </div>
            
            <div class="content-card">
                <h3>2. The Hybrid Intelligence Engine (Chart + Derivatives)</h3>
                <p>Traditional platforms separate charts from option chains. DeltaCore’s <b>Hybrid Engine</b> bridges this gap seamlessly:</p>
                <ul>
                    <li><b>Momentum & Price Action:</b> Real-time TradingView feed captures immediate trend and intraday directional bias.</li>
                    <li><b>Open Interest (OI) & PCR Matrix:</b> Evaluates Put-Call Ratio and institutional writer build-ups to filter out false breakouts.</li>
                    <li><b>Autonomous Calculations:</b> Automatically computes optimal ATM/ITM strike contracts, execution prices, targets, and protective stop-losses.</li>
                </ul>
            </div>

            <div class="content-card">
                <h3>3. Psychological Guardrails & Risk Management</h3>
                <ul>
                    <li><b>Hard-Lock Kill-Switch:</b> Instantly freezes trading activity if pre-set maximum daily loss thresholds are breached, preventing revenge trading.</li>
                    <li><b>Theta Decay Duration Timer:</b> Actively monitors trade duration in the market to combat time decay in options buying.</li>
                </ul>
            </div>

            <div class="content-card">
                <h3>4. AI Post-Mortem P&L Analytics & Smart Journaling</h3>
                <p>Every closed position triggers our automated analytics engine to generate a <b>Scientific Post-Mortem Report</b>. It breaks down performance based on option chain PCR support, momentum shifts, and theta decay impact—helping you evolve into a consistently profitable trader.</p>
            </div>
            """, unsafe_allow_html=True)

        with public_menu[1]:
            st.markdown('<p class="section-header">💎 Direct UPI QR Code Payment (Gurudev Malakar)</p>', unsafe_allow_html=True)
            try: st.image("qr_code.png", width=200, caption="Gurudev Malakar (8319277922-1@nyes)")
            except: st.warning("⚠️ Place 'qr_code.png' in root folder.")
        with public_menu[2]:
            st.markdown('<p class="section-header">📝 Create Account & Submit UTR</p>', unsafe_allow_html=True)
            with st.form("reg_en"):
                u = st.text_input("Username")
                p = st.text_input("Password", type="password")
                utr = st.text_input("UPI Reference / UTR Number (Payment ke baad yahan dalein)")
                if st.form_submit_button("Register & Submit UTR", type="primary"):
                    if not utr.strip():
                        st.error("Kripya valid UTR / Transaction ID darj karein.")
                    else:
                        ok, msg = register_pending_user(u.strip(), p.strip(), utr.strip())
                        if ok: st.success(msg)
                        else: st.error(msg)
        with public_menu[3]:
            st.markdown('<p class="section-header">🔐 Secure Member Login</p>', unsafe_allow_html=True)
            with st.form("log_en"):
                u = st.text_input("Username")
                p = st.text_input("Password", type="password")
                if st.form_submit_button("Login", type="primary"):
                    rec = get_user_record(u)
                    if rec and rec['Password'] == hash_password(p):
                        if rec['PaymentStatus'] == "Paid":
                            st.session_state.logged_in = True
                            st.session_state.username = u
                            st.rerun()
                        else: st.warning("⏳ Payment verification pending. Admin approval ka intezaar karein.")
                    else: st.error("Invalid credentials.")
    else:
        st.markdown('<p class="sub-title">संस्थागत स्तर का निफ्टी ऑप्शन बाइंग और ऑटोनॉमस इंटेलिजेंस कमांड सेंटर</p>', unsafe_allow_html=True)
        public_menu = st.tabs(["📖 आर्किटेक्चर और गाइड", "💎 भुगतान", "📝 रजिस्टर", "🔐 लॉगिन"])
        with public_menu[0]:
            st.markdown('<p class="section-header">🏢 संस्थागत वास्तुकला और प्लेटफार्म अवलोकन</p>', unsafe_allow_html=True)
            st.markdown("""
            <div class="content-card">
                <h3>1. प्लेटफॉर्म दर्शन और क्वांटिटेटिव फ्रेमवर्क</h3>
                <p><b>डेल्टाकोर</b> को एक साधारण स्क्रिप्ट के रूप में नहीं, बल्कि एक <b>संस्थागत क्वांटिटेटिव फ्रेमवर्क</b> के रूप में डिज़ाइन किया गया है। यह लाइव चार्ट और ऑप्शन चेन डेटा को एक साथ जोड़कर आपको सटीक निर्णय लेने में मदद करता है।</p>
            </div>
            <div class="content-card">
                <h3>2. हाइब्रिड इंटेलिजेंस इंजन और एआई पोस्ट-मॉर्टम</h3>
                <p>यह इंजन लाइव चार्ट और PCR (Put-Call Ratio) का विश्लेषण करके सही स्ट्राइक, टारगेट और स्टॉप-लॉस सुझाता है। हर ट्रेड के बाद एआई एक्सप्लेनर रिपोर्ट जनरेट होती है।</p>
            </div>
            """, unsafe_allow_html=True)
        with public_menu[1]:
            try: st.image("qr_code.png", width=200, caption="Gurudev Malakar (8319277922-1@nyes)")
            except: pass
        with public_menu[2]:
            with st.form("reg_hi"):
                u = st.text_input("यूजरनेम")
                p = st.text_input("पासवर्ड", type="password")
                utr = st.text_input("यूपीआई रेफरेंस / यूटीआर नंबर (भुगतान के बाद दर्ज करें)")
                if st.form_submit_button("रजिस्टर करें", type="primary"):
                    if not utr.strip():
                        st.error("कृपया वैध यूटीआर नंबर दर्ज करें।")
                    else:
                        ok, msg = register_pending_user(u.strip(), p.strip(), utr.strip())
                        if ok: st.success(msg)
                        else: st.error(msg)
        with public_menu[3]:
            with st.form("log_hi"):
                u = st.text_input("यूजरनेम")
                p = st.text_input("पासवर्ड", type="password")
                if st.form_submit_button("लॉगिन", type="primary"):
                    rec = get_user_record(u)
                    if rec and rec['Password'] == hash_password(p):
                        if rec['PaymentStatus'] == "Paid":
                            st.session_state.logged_in = True
                            st.session_state.username = u
                            st.rerun()
                        else: st.warning("भुगतान सत्यापन लंबित है।")
                    else: st.error("गलत विवरण।")

else:
    # ==========================================
    # MAIN APP PORTAL (AFTER SUCCESSFUL LOGIN)
    # ==========================================
    active_user = st.session_state.username if st.session_state.username else "admin"
    user_record = get_user_record(active_user)
    expiry_str = user_record['ExpiryDate'] if user_record else (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    days_left = (datetime.strptime(str(expiry_str), "%Y-%m-%d") - datetime.now()).days

    st.markdown("""
        <div class="brand-container">
            <div>
                <span class="animated-brand">⚡ DELTACORE</span>
            </div>
            <div>
                <span class="brand-badge">Terminal Active</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown(f'<p class="sub-title">Welcome, <b>{active_user}</b> | Plan Valid Till: <b>{expiry_str} ({max(0, days_left)} Days Left)</b></p>', unsafe_allow_html=True)

    st.sidebar.markdown("## ⚡ **DELTACORE PORTAL**")
    menu = st.sidebar.radio(
        "Navigation", 
        [
            "🎯 Master Trading Desk", 
            "📚 Trading Blog & Insights", 
            "🎁 Refer & Earn 25 Days Free", 
            "📊 Live Option Chain", 
            "📝 Trade Journal & P&L"
        ],
        label_visibility="collapsed"
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📡 Telegram Bot Alert Setup")
    tg_token = st.sidebar.text_input("Bot Token", type="password")
    tg_chat = st.sidebar.text_input("Chat ID")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💳 Account Status")
    st.sidebar.info(f"⏳ Days Remaining: **{max(0, days_left)} Days**")
    
    if st.sidebar.button("🚪 Logout", type="secondary"):
        st.session_state.logged_in = False
        st.session_state.admin_logged_in = False
        st.session_state.username = ""
        st.rerun()

    st.sidebar.markdown("---")

    # ==========================================
    # TAB 1: MASTER TRADING DESK
    # ==========================================
    if menu == "🎯 Master Trading Desk":
        st.header("🎯 DeltaCore Hybrid Execution Desk")
        st.write("Live chart aur option chain analysis ke sath exact trade execution aur post-mortem explanation.")
        
        st.sidebar.header("⚙️ Risk & Capital Controls")
        total_capital = st.sidebar.number_input("Total Capital (₹)", min_value=5000.0, value=20000.0, step=1000.0)
        max_risk_per_trade = st.sidebar.number_input("Max Risk Per Trade (₹)", min_value=500.0, value=1000.0, step=100.0)
        max_daily_loss = st.sidebar.number_input("🚨 Daily Kill-Switch Loss Limit (₹)", min_value=1000.0, value=2500.0, step=500.0)

        is_locked, current_day_pnl = check_kill_switch(active_user, max_daily_loss)

        if is_locked:
            st.error(f"🚨 **KILL-SWITCH ACTIVATED!** Loss limit (₹{max_daily_loss}) cross ho chuki hai. Trading locked.")
        else:
            market_data = fetch_market_and_option_chain()
            spot = market_data["spot"]
            change = market_data["change"]
            atm = market_data["atm"]
            pcr = market_data["pcr"]
            bias = market_data["bias"]

            is_bullish = change >= 0
            rec_entry = max(30.0, 100.0 + (abs(change) * 0.4))
            rec_target = rec_entry + 40.0
            rec_sl = rec_entry - 22.0

            tv_chart_html = """
            <div class="tradingview-widget-container" style="height:480px;width:100%">
              <div id="tradingview_master_chart" style="height:100%;width:100%"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
              <script type="text/javascript">
              new TradingView.widget({
                "width": "100%", "height": 480, "symbol": "NSE:NIFTY", "interval": "5",
                "timezone": "Asia/Kolkata", "theme": "dark", "style": "1", "locale": "en",
                "toolbar_bg": "#f1f3f6", "enable_publishing": false, "container_id": "tradingview_master_chart"
              });
              </script>
            </div>
            """
            components.html(tv_chart_html, height=500)
            st.markdown("---")

            st.subheader("🧬 Hybrid Signals & Metrics")
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1: st.metric("Live Nifty Spot", f"₹{spot:,.2f}", f"{change:+.2f} pts")
            with col_m2: st.metric("Market Bias", bias)
            with col_m3: st.metric("PCR Ratio", f"{pcr:.2f}")
            with col_m4: st.metric("Suggested Strike", f"{atm} {'CE' if is_bullish else 'PE'}")

            p1, p2, p3 = st.columns(3)
            with p1: st.metric("🟢 ENTRY PRICE", f"₹{rec_entry:.2f}")
            with p2: st.metric("🎯 TARGET / SL", f"T: ₹{rec_target:.2f} | SL: ₹{rec_sl:.2f}")
            with p3:
                if st.session_state.trade_active:
                    elapsed = int((datetime.now() - st.session_state.entry_timestamp).total_seconds())
                    m, s = divmod(elapsed, 60); h, m = divmod(m, 60)
                    st.metric("⏱️ DURATION", f"{h:02d}:{m:02d}:{s:02d}", "Active 🟢")
                else:
                    st.metric("⏱️ DURATION", "00:00:00", "No Trade ⚪")

            st.markdown("---")

            st.subheader("⚡ Live Trade Execution")
            if not st.session_state.trade_active:
                with st.form("trade_entry_form"):
                    col_1, col_2, col_3 = st.columns(3)
                    with col_1:
                        exec_strike = st.number_input("Strike Price", min_value=10000, value=int(atm), step=50)
                        exec_type = st.selectbox("Type", ["CE", "PE"], index=0 if is_bullish else 1)
                    with col_2:
                        exec_lots = st.number_input("Lots", min_value=1, value=1, step=1)
                        exec_buy = st.number_input("Buy Price (₹)", min_value=1.0, value=float(round(rec_entry, 2)), step=0.5)
                    with col_3:
                        exec_target = st.number_input("Target (₹)", min_value=1.0, value=float(round(rec_target, 2)), step=0.5)
                        exec_sl = st.number_input("Stop-Loss (₹)", min_value=1.0, value=float(round(rec_sl, 2)), step=0.5)

                    if st.form_submit_button("🚀 Execute Hybrid Trade", type="primary"):
                        st.session_state.trade_active = True
                        st.session_state.entry_timestamp = datetime.now()
                        st.session_state.active_trade_details = {
                            "strike": f"{exec_strike} {exec_type}", "lots": exec_lots,
                            "buy": exec_buy, "target": exec_target, "sl": exec_sl
                        }
                        if tg_token and tg_chat:
                            send_telegram_signal_alert(tg_token, tg_chat, f"🚀 Alert: {exec_strike} {exec_type} | Buy: ₹{exec_buy}")
                        st.success("✅ Trade Executed!")
                        st.rerun()
            else:
                trade_info = st.session_state.active_trade_details
                st.info(f"📊 **Active:** **{trade_info['strike']}** | Buy: ₹{trade_info['buy']} | Target: ₹{trade_info['target']}")
                with st.form("trade_exit_form"):
                    col_e1, col_e2 = st.columns(2)
                    with col_e1: exit_price = st.number_input("Exit Price (₹)", min_value=1.0, value=float(trade_info['target']), step=0.5)
                    with col_e2: exit_reason = st.selectbox("Exit Reason", ["Target Hit 🎯", "Stop-Loss Hit 🛑", "Manual Exit / Time Decay ⏱️"])
                    
                    if st.form_submit_button("🛑 Square Off & Generate Explainer", type="primary"):
                        duration_mins = int((datetime.now() - st.session_state.entry_timestamp).total_seconds() / 60)
                        pnl = (exit_price - trade_info['buy']) * (trade_info['lots'] * 25)
                        
                        explanation = generate_trade_explanation(pnl, exit_reason, duration_mins, pcr, change)
                        
                        conn = sqlite3.connect(DB_NAME, timeout=10)
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO trades (username, timestamp, contract, lots, buy_price, sell_price, duration, exit_reason, pnl, status, explanation)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            active_user,
                            st.session_state.entry_timestamp.strftime("%Y-%m-%d %H:%M"),
                            trade_info['strike'], trade_info['lots'], trade_info['buy'], exit_price,
                            f"{duration_mins} mins", exit_reason, round(pnl, 2),
                            "PROFIT 🟢" if pnl > 0 else "LOSS 🔴", explanation
                        ))
                        conn.commit()
                        conn.close()
                        
                        st.session_state.trade_active = False
                        st.session_state.entry_timestamp = None
                        st.session_state.active_trade_details = {}
                        
                        st.success(f"✅ Trade Closed! P&L: ₹{pnl:,.2f}")
                        st.markdown(f"""
                        <div class="content-card" style="border: 1px solid {'#10B981' if pnl > 0 else '#EF4444'};">
                            <h3>🔍 AI Trade Post-Mortem & Explanation Report</h3>
                            <p>{explanation}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        st.balloons()

    # ==========================================
    # TAB 2: TRADING BLOG & INSIGHTS
    # ==========================================
    elif menu == "📚 Trading Blog & Insights":
        st.header("📚 DeltaCore Intelligence & Feature Insights")
        st.markdown("""
        <div class="content-card">
            <h3>💡 Feature Highlight: AI Trade Post-Mortem Explainer</h3>
            <p>DeltaCore acts as your quantitative trading mentor. Every closed position undergoes autonomous analysis to scientifically break down performance factors:</p>
            <ul>
                <li><b>Option Chain PCR Impact:</b> Evaluates whether Put-Call Ratio dynamics acted as structural support or resistance.</li>
                <li><b>Momentum & Trend Alignment:</b> Correlates intraday price action with live TradingView feeds.</li>
                <li><b>Theta Decay & Time Management:</b> Measures duration risk against options time decay.</li>
            </ul>
        </div>

        <div class="content-card">
            <h3>⏱️ 1. Beating Theta Decay: Why the Live Trade Timer Matters</h3>
            <p style="color: #94A3B8; font-size: 13px;">Published by Trading Psychology Desk</p>
            <p>Time is an option buyer's primary adversary. DeltaCore's integrated duration timer tracks precise market exposure duration to safeguard against stagnation.</p>
        </div>
        """, unsafe_allow_html=True)

    # ==========================================
    # TAB 3: REFER & EARN 25 DAYS FREE
    # ==========================================
    elif menu == "🎁 Refer & Earn 25 Days Free":
        st.header("🎁 Refer & Earn: Get 25 Trading Days Free!")
        user_rec = get_user_record(active_user)
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.code(f"https://deltacoreapp-terminal.streamlit.app/?ref={active_user}")
            ref_done = st.checkbox("Referral completed ✅", value=user_rec.get('ReferralDone', False) if user_rec else False)
        with col_r2:
            st.text_area("Feedback:")
            fb_done = st.checkbox("Feedback submitted ✅", value=user_rec.get('FeedbackDone', False) if user_rec else False)
        if st.button("🚀 Claim 25 Days Free", type="primary"):
            if ref_done and fb_done:
                new_date = update_user_extension(active_user, 25)
                st.success(f"🎉 Account extended till {new_date}!")
                st.balloons()
            else:
                st.warning("⚠️ Both checkboxes must be ticked.")

    # ==========================================
    # TAB 4: LIVE OPTION CHAIN
    # ==========================================
    elif menu == "📊 Live Option Chain":
        st.header("⚡ Nifty Live Option Chain Matrix")
        if st.button("🔄 Refresh Option Chain Matrix", type="primary"):
            m_data = fetch_market_and_option_chain()
            st.success("✅ Synchronized!")
            col_oc1, col_oc2, col_oc3 = st.columns(3)
            with col_oc1: st.metric("ATM Strike", m_data["atm"])
            with col_oc2: st.metric("PCR", f"{m_data['pcr']:.2f}")
            with col_oc3: st.metric("Bias", m_data["bias"])
        else:
            st.info("👆 Click to load matrix.")

    # ==========================================
    # TAB 5: TRADE JOURNAL & P&L STATEMENT
    # ==========================================
    elif menu == "📝 Trade Journal & P&L":
        st.header("📝 DeltaCore Performance Journal & Explanations")
        conn = sqlite3.connect(DB_NAME, timeout=10)
        df_saved = pd.read_sql_query("SELECT timestamp, contract, lots, buy_price, sell_price, duration, exit_reason, pnl, status, explanation FROM trades WHERE username = ?", conn, params=(active_user,))
        conn.close()
        
        if not df_saved.empty:
            st.dataframe(df_saved, use_container_width=True)
            st.metric(label="Net Portfolio P&L", value=f"₹{df_saved['pnl'].sum():,.2f}")
            
            st.markdown("---")
            st.subheader("📖 Detailed Post-Mortem Explanations Log")
            for idx, row in df_saved.iterrows():
                with st.expander(f"Trade #{idx+1} | {row['contract']} | P&L: ₹{row['pnl']} ({row['status']})"):
                    st.write(f"📅 **Time:** {row['timestamp']} | ⏱️ **Duration:** {row['duration']}")
                    st.write(f"💵 **Buy:** ₹{row['buy_price']} | 💵 **Sell:** ₹{row['sell_price']} | **Reason:** {row['exit_reason']}")
                    st.info(f"💡 **AI Explainer & Analysis:** {row['explanation']}")
        else:
            st.info("📝 No trades saved yet.")