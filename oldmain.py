import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd
import bcrypt # pip install bcrypt

# --- MoodEntry Class (remains the same) ---
class MoodEntry:
    def __init__(self, mood, note=None, timestamp=None):
        self.mood = mood
        self.note = note
        self.timestamp = timestamp if timestamp else datetime.utcnow()

    def to_dict(self):
        return {
            "mood": self.mood,
            "note": self.note,
            "timestamp": self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data):
        timestamp = datetime.fromisoformat(data["timestamp"])
        return cls(data["mood"], data.get("note"), timestamp)

# --- File Paths ---
MOOD_DATA_FILE = "mood_entries.json"
USER_DATA_FILE = "users.json" # New file for user data

# --- Data Handling Functions for Mood Entries (slightly modified to be user-specific) ---
def load_mood_entries(username):
    user_mood_file = f"mood_entries_{username}.json"
    if not os.path.exists(user_mood_file) or os.stat(user_mood_file).st_size == 0:
        return []
    try:
        with open(user_mood_file, "r") as f:
            data = json.load(f)
            return [MoodEntry.from_dict(entry) for entry in data]
    except Exception as e:
        st.error(f"Error loading mood entries for {username}: {e}")
        return []

def save_mood_entries(username, entries):
    user_mood_file = f"mood_entries_{username}.json"
    data = [entry.to_dict() for entry in entries]
    try:
        with open(user_mood_file, "w") as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        st.error(f"Error saving mood entries for {username}: {e}")
        return False

# --- User Data Handling Functions ---
def load_users():
    if not os.path.exists(USER_DATA_FILE) or os.stat(USER_DATA_FILE).st_size == 0:
        return {}
    try:
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading user data: {e}")
        return {}

def save_users(users):
    try:
        with open(USER_DATA_FILE, "w") as f:
            json.dump(users, f, indent=4)
        return True
    except Exception as e:
        st.error(f"Error saving user data: {e}")
        return False

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

# --- Streamlit App ---
st.set_page_config(page_title="🌈 Mood Tracker", layout="centered")

# Initialize session state for authentication
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None

def app_main():
    st.title("🌈 Mood Tracker")

    # Tabs
    tabs = st.tabs(["Log Mood", "View History", "Mood Analysis"])

    # --- Log Mood Tab ---
    with tabs[0]:
        st.header(f"Log Your Mood, {st.session_state.username}!")

        mood_options = ["Happy", "Neutral", "Sad", "Angry", "Anxious", "Tired", "Excited"]
        mood = st.selectbox("How are you feeling today?", mood_options)
        note = st.text_area("Add a note (optional)")
        if st.button("Submit Mood"):
            new_entry = MoodEntry(mood, note if note.strip() else None)
            all_entries = load_mood_entries(st.session_state.username)
            all_entries.append(new_entry)
            if save_mood_entries(st.session_state.username, all_entries):
                st.success("Mood logged successfully!")
            else:
                st.error("Failed to save mood.")

    # --- View History Tab ---
    with tabs[1]:
        st.header("Mood History")
        all_entries = load_mood_entries(st.session_state.username)
        if all_entries:
            all_entries.sort(key=lambda e: e.timestamp, reverse=True)
            df = pd.DataFrame([{
                "Date": e.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "Mood": e.mood,
                "Note": e.note if e.note else ""
            } for e in all_entries])
            st.dataframe(df)
        else:
            st.info("No mood entries found.")

    # --- Mood Analysis Tab ---
    with tabs[2]:
        st.header("Mood Pattern Analysis")
        all_entries = load_mood_entries(st.session_state.username)
        if all_entries:
            df = pd.DataFrame([{
                "Timestamp": e.timestamp,
                "Mood": e.mood
            } for e in all_entries])

            # Mood frequency
            st.subheader("📊 Mood Frequency")
            mood_counts = df["Mood"].value_counts()
            st.bar_chart(mood_counts)

            # Mood trend over time
            st.subheader("📈 Mood Over Time")
            df['Date'] = df['Timestamp'].dt.date
            daily_mood_counts = df.groupby(['Date', 'Mood']).size().unstack().fillna(0)
            st.line_chart(daily_mood_counts)

        else:
            st.info("No data available for analysis.")

    st.sidebar.markdown("---")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.experimental_rerun()

def login_page():
    st.title("Welcome to Moodyssey!")
    st.subheader("Log-in / Sign Up")

    login_tab, signup_tab = st.tabs(["Login", "Sign Up"])

    with login_tab:
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login"):
            users = load_users()
            if username in users:
                if verify_password(password, users[username]['hashed_password']):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Incorrect password.")
            else:
                st.error("Username not found.")

    with signup_tab:
        st.subheader("Sign Up")
        new_username = st.text_input("New Username", key="signup_username")
        new_password = st.text_input("New Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password")

        if st.button("Sign Up"):
            users = load_users()
            if new_username in users:
                st.error("Username already exists. Please choose a different one.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            elif not new_username or not new_password:
                st.error("Username and password cannot be empty.")
            else:
                hashed_password = hash_password(new_password)
                users[new_username] = {"hashed_password": hashed_password}
                if save_users(users):
                    st.success("Account created successfully! You can now log in.")
                else:
                    st.error("Failed to create account.")

# Main app logic
if st.session_state.logged_in:
    app_main()
else:
    login_page()