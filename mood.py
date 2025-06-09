import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

# --- MoodEntry Class ---
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

# --- File Path ---
DATA_FILE = "mood_entries.json"

# --- Data Handling Functions ---
def load_mood_entries():
    if not os.path.exists(DATA_FILE) or os.stat(DATA_FILE).st_size == 0:
        return []
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            return [MoodEntry.from_dict(entry) for entry in data]
    except:
        return []

def save_mood_entries(entries):
    data = [entry.to_dict() for entry in entries]
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)
        return True
    except:
        return False

# --- Streamlit App ---
st.title("🌈 Mood Tracker")

# Tabs
tabs = st.tabs(["Log Mood", "View History", "Mood Analysis"])

# --- Log Mood Tab ---
with tabs[0]:
    st.header("Log Your Mood")

    mood_options = ["Happy", "Neutral", "Sad", "Angry", "Anxious", "Tired", "Excited"]
    mood = st.selectbox("How are you feeling today?", mood_options)
    note = st.text_area("Add a note (optional)")
    if st.button("Submit Mood"):
        new_entry = MoodEntry(mood, note if note.strip() else None)
        all_entries = load_mood_entries()
        all_entries.append(new_entry)
        if save_mood_entries(all_entries):
            st.success("Mood logged successfully!")
        else:
            st.error("Failed to save mood.")

# --- View History Tab ---
with tabs[1]:
    st.header("Mood History")
    all_entries = load_mood_entries()
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
    all_entries = load_mood_entries()
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
