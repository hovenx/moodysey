import streamlit as st
import json
import os
from datetime import datetime, timedelta
import pandas as pd
import bcrypt
import pathlib

# --- Encapsulation: MoodEntry Class ---
# This class encapsulates mood data and provides methods to convert to/from dictionary.
class MoodEntry:
    def __init__(self, mood: str, note: str = None, timestamp: datetime = None):
        if not isinstance(mood, str) or not mood:
            raise ValueError("Mood must be a non-empty string.")
        self._mood = mood
        self._note = note
        self._timestamp = timestamp if timestamp else datetime.utcnow()

    # Properties for controlled access (encapsulation)
    @property
    def mood(self) -> str:
        return self._mood

    @property
    def note(self) -> str:
        return self._note

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    def to_dict(self) -> dict:
        return {
            "mood": self._mood,
            "note": self._note,
            "timestamp": self._timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict):
        timestamp = datetime.fromisoformat(data["timestamp"])
        return cls(data["mood"], data.get("note"), timestamp)

# --- Abstraction & Encapsulation: DataManager Base Class ---
# This abstract base class provides a common interface for loading and saving data.
class DataManager:
    def __init__(self, file_path: str):
        self._file_path = file_path

    def _load_raw_data(self) -> dict:
        """Loads raw JSON data from the file."""
        if not os.path.exists(self._file_path) or os.stat(self._file_path).st_size == 0:
            return {}
        try:
            with open(self._file_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError) as e:
            st.warning(f"Corrupted or empty data file '{self._file_path}'. Starting fresh. Error: {e}")
            return {}
        except Exception as e:
            st.error(f"An unexpected error occurred loading data from '{self._file_path}': {e}")
            return {}

    def _save_raw_data(self, data: dict) -> bool:
        """Saves raw JSON data to the file."""
        try:
            with open(self._file_path, "w") as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            st.error(f"Error saving data to '{self._file_path}': {e}")
            return False

    # These methods are placeholders for concrete implementations (abstraction)
    def load(self):
        raise NotImplementedError("Subclasses must implement 'load' method.")

    def save(self, data):
        raise NotImplementedError("Subclasses must implement 'save' method.")

# --- Encapsulation & Inheritance: UserDataManager ---
# Manages user authentication data.
class UserDataManager(DataManager):
    def __init__(self, file_path: str = "users.json"):
        super().__init__(file_path)

    def load(self) -> dict:
        """Loads user data (username -> hashed_password)."""
        return self._load_raw_data()

    def save(self, users: dict) -> bool:
        """Saves user data."""
        return self._save_raw_data(users)

    def register_user(self, username: str, password: str) -> tuple[bool, str]:
        users = self.load()
        if username in users:
            return False, "Username already exists."

        hashed_pass = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        users[username] = {"hashed_password": hashed_pass}

        if self.save(users):
            return True, "Account created successfully! You can now log in."
        else:
            return False, "Failed to create account due to a saving error."

    def authenticate_user(self, username: str, password: str) -> tuple[bool, str]:
        users = self.load()
        if username not in users:
            return False, "Username not found."

        if bcrypt.checkpw(password.encode('utf-8'), users[username]['hashed_password'].encode('utf-8')):
            return True, "Logged in successfully!"
        else:
            return False, "Incorrect password."

# --- Encapsulation & Inheritance: MoodEntriesDataManager ---
# Manages user-specific mood entries.
class MoodEntriesDataManager(DataManager):
    def __init__(self):
        # File path is dynamically generated based on username, so not set in constructor.
        super().__init__("") # Dummy path, will be set in load/save

    def load(self, username: str) -> list[MoodEntry]:
        """Loads mood entries for a specific user."""
        self._file_path = f"mood_entries_{username}.json" # Set file path dynamically
        raw_entries = self._load_raw_data()
        return [MoodEntry.from_dict(entry) for entry in raw_entries] if raw_entries else []

    def save(self, username: str, entries: list[MoodEntry]) -> bool:
        """Saves mood entries for a specific user."""
        self._file_path = f"mood_entries_{username}.json" # Set file path dynamically
        data = [entry.to_dict() for entry in entries]
        return self._save_raw_data(data)

# --- Instantiation of Data Managers (Singletons) ---
user_data_manager = UserDataManager()
mood_entries_data_manager = MoodEntriesDataManager()

# --- Streamlit App Configuration ---
st.set_page_config(page_title="Moodyssey", layout="centered")

# Initialize session state for authentication and page navigation
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'page' not in st.session_state:
    st.session_state.page = "home" # Initial page

# --- Mood Categorization for Analysis ---
MOOD_CATEGORIES = {
    "Positive": ["Happy", "Excited"],
    "Neutral": ["Neutral"],
    "Negative": ["Sad", "Angry", "Anxious", "Tired"]
}

def get_mood_category(mood: str) -> str:
    for category, moods in MOOD_CATEGORIES.items():
        if mood in moods:
            return category
    return "Unknown" # Fallback, though ideally all moods are categorized

# --- UI Components (Page Functions) ---

def add_sidebar_elements():
    """Adds common sidebar elements like logo, username, and logout button."""
    #try:
    #    st.sidebar.image("logo.png", use_container_width=True) # Updated to use_container_width
    #    st.sidebar.markdown("---")
    #except FileNotFoundError:
    #    st.sidebar.warning("Logo image 'logo.png' not found. Please add it to your app's directory.")

    if st.session_state.logged_in:
        st.sidebar.write(f"Logged in as: **{st.session_state.username}**")
        st.sidebar.button("Logout", on_click=lambda: (st.session_state.update(logged_in=False, username=None, page="home"), st.rerun()))

def load_css(file_path):
    with open(file_path) as f:
        st.html(f"<style>{f.read()}</style>")

css_path = pathlib.Path("assets/style.css")
load_css(css_path)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@200..700&display=swap');

html, body, [class*="css"]  {
    font-family: 'Oswald', sans-serif;
}
h1, h2, h3, h4, h5, h6 {
    font-family: 'Oswald', sans-serif !important;
}

</style>
""", unsafe_allow_html=True)

def home_page():
    
    """Renders the initial landing page with Login/Sign Up options."""
    st.title("Moodyssey")
    st.header("Life can be a little less stressful when you're in the mood for something good.")

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Log In", use_container_width=True, key="blue"):
            st.session_state.page = "login"
            st.rerun()
    with col2:
        if st.button("Sign Up", use_container_width=True):
            st.session_state.page = "signup"
            st.rerun()

def login_page():
    """Renders the user login form."""
    st.title("Login to Moodyssey")
    
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Login", use_container_width=True):
            success, message = user_data_manager.authenticate_user(username, password)
            if success:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.page = "welcome_authenticated"
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    with col_btn2:
        if st.button("Back to Welcome", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()

def signup_page():
    """Renders the user registration form."""
    st.title("Sign Up for Moodyssey")
    
    new_username = st.text_input("New Username", key="signup_username")
    new_password = st.text_input("New Password", type="password", key="signup_password")
    confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Create Account", use_container_width=True):
            if not new_username or not new_password or not confirm_password:
                st.warning("Please fill in all fields.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                success, message = user_data_manager.register_user(new_username, new_password)
                if success:
                    st.success(message)
                    st.session_state.page = "login"
                    st.rerun()
                else:
                    st.error(message)
    with col_btn2:
        if st.button("Back to Welcome", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()

def welcome_authenticated_page():
    """Renders the welcome page shown after successful login/signup."""
    add_sidebar_elements()

    st.title(f"Hey! It's nice to see you, {st.session_state.username}!")
    st.write("What would you like to do today?")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Check In (Log Mood)", use_container_width=True):
            st.session_state.page = "mood_input"
            st.rerun()
    with col2:
        if st.button("Go to Dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()

def mood_input_page():
    """Renders the form for logging a new mood entry."""
    add_sidebar_elements()

    st.header("Log Your Mood Today 📝")

    mood_options = ["Happy", "Neutral", "Sad", "Angry", "Anxious", "Tired", "Excited"]
    mood = st.selectbox("How are you feeling right now?", mood_options)
    note = st.text_area("Add a note (optional)")
    
    if st.button("Submit Mood", use_container_width=True):
        new_entry = MoodEntry(mood, note if note.strip() else None)
        all_entries = mood_entries_data_manager.load(st.session_state.username)
        all_entries.append(new_entry)
        if mood_entries_data_manager.save(st.session_state.username, all_entries):
            st.success("Mood logged successfully!")
            st.info("You can now view your updated dashboard.")
            st.session_state.page = "dashboard" # Redirect to dashboard after logging
            st.rerun()
        else:
            st.error("Failed to save mood.")
    
    st.markdown("---")
    if st.button("Back to Dashboard", use_container_width=True):
        st.session_state.page = "dashboard"
        st.rerun()

def dashboard_page():
    """Renders the user's mood dashboard with progress tracking, patterns, and history."""
    add_sidebar_elements()

    st.title("📊 Your Mood Dashboard")

    all_entries = mood_entries_data_manager.load(st.session_state.username)

    if not all_entries:
        st.info("No mood entries found yet. Log your first mood to see your dashboard!")
        if st.button("Log My First Mood", key="log_first_mood_dash", use_container_width=True):
            st.session_state.page = "mood_input"
            st.rerun()
        return # Exit the function if no data

    # Create DataFrame from MoodEntry objects
    df = pd.DataFrame([{
        "Timestamp": e.timestamp,
        "Mood": e.mood,
        "Note": e.note if e.note else ""
    } for e in all_entries])

    # Ensure Timestamp column is datetime objects for proper operations
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])

    df['Date'] = df['Timestamp'].dt.date
    df['DayOfWeek'] = df['Timestamp'].dt.day_name()
    df['HourOfDay'] = df['Timestamp'].dt.hour
    df['MoodCategory'] = df['Mood'].apply(get_mood_category)

    # --- Navigation to other pages from Dashboard ---
    st.markdown("---")
    col_dash_nav1, col_dash_nav2 = st.columns(2)
    with col_dash_nav1:
        if st.button("Log Another Mood", use_container_width=True):
            st.session_state.page = "mood_input"
            st.rerun()
    with col_dash_nav2:
        if st.button("Back to Welcome Page", use_container_width=True):
            st.session_state.page = "welcome_authenticated"
            st.rerun()
    st.markdown("---")


    # --- Section: Tracking Progress ---
    st.header("📈 Tracking Your Mood Progress")
    st.write("See how your mood categories have shifted over time.")

    today = datetime.now().date()
    
    if len(df['Date'].unique()) < 2:
        st.info("Not enough unique dates for a meaningful comparison. Keep logging your moods!")
    else:
        recent_period_days = st.slider("Select recent period (days)", 1, 30, 7)
        previous_period_days = st.slider("Select previous period (days)", 1, 30, 7)

        recent_start_date = today - timedelta(days=recent_period_days - 1)
        previous_start_date = recent_start_date - timedelta(days=previous_period_days)
        
        recent_df = df[df['Date'] >= recent_start_date]
        previous_df = df[(df['Date'] >= previous_start_date) & (df['Date'] < recent_start_date)]

        if not recent_df.empty and not previous_df.empty:
            st.subheader(f"Mood Category Distribution (Last {recent_period_days} Days vs. Previous {previous_period_days} Days)")

            recent_counts = recent_df['MoodCategory'].value_counts(normalize=True) * 100
            previous_counts = previous_df['MoodCategory'].value_counts(normalize=True) * 100

            comparison_df = pd.DataFrame({
                f'Last {recent_period_days} Days (%)': recent_counts,
                f'Previous {previous_period_days} Days (%)': previous_counts
            }).fillna(0).sort_index()

            st.dataframe(comparison_df.style.format("{:.1f}%"), use_container_width=True)

            st.markdown("**Changes:**")
            for category in comparison_df.index:
                change = comparison_df.loc[category, f'Last {recent_period_days} Days (%)'] - comparison_df.loc[category, f'Previous {previous_period_days} Days (%)']
                if change > 0:
                    st.markdown(f"- **{category}**: Increased by _{change:.1f}%_ (⬆️)")
                elif change < 0:
                    st.markdown(f"- **{category}**: Decreased by _{abs(change):.1f}%_ (⬇️)")
                else:
                    st.markdown(f"- **{category}**: No significant change.")
        else:
            st.info("Not enough data for this specific period comparison. Adjust date ranges or log more moods.")

    st.markdown("---")


    # --- Section: Mood Pattern Reviews ---
    st.header("✨ Mood Pattern Reviews")

    st.subheader("1. Overall Mood Frequency")
    mood_counts = df["Mood"].value_counts().sort_index()
    st.bar_chart(mood_counts, use_container_width=True)

    st.subheader("2. Mood Trend Over Time (by Category)")
    daily_mood_category_counts = df.groupby(['Date', 'MoodCategory']).size().unstack().fillna(0)
    st.line_chart(daily_mood_category_counts, use_container_width=True)

    st.subheader("3. Mood Distribution by Day of Week")
    order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    daily_category_pivot = pd.pivot_table(df, index='DayOfWeek', columns='MoodCategory', aggfunc='size', fill_value=0)
    daily_category_pivot = daily_category_pivot.reindex(order, fill_value=0)
    st.bar_chart(daily_category_pivot, use_container_width=True)

    if len(df['HourOfDay'].unique()) > 1: # Only show if more than one hour is recorded
        st.subheader("4. Mood Distribution by Hour of Day")
        hourly_category_pivot = pd.pivot_table(df, index='HourOfDay', columns='MoodCategory', aggfunc='size', fill_value=0)
        st.bar_chart(hourly_category_pivot, use_container_width=True)

    st.markdown("---")

    # --- Section: Mood History Table ---
    st.header("🗒️ Full Mood History")
    # Sort again by timestamp descending for display
    all_entries.sort(key=lambda e: e.timestamp, reverse=True)
    history_df = pd.DataFrame([{
        "Date": e.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "Mood": e.mood,
        "Note": e.note if e.note else ""
    } for e in all_entries])
    st.dataframe(history_df, use_container_width=True)

# --- Main Page Routing Logic ---
if st.session_state.logged_in:
    if st.session_state.page == "welcome_authenticated":
        welcome_authenticated_page()
    elif st.session_state.page == "mood_input":
        mood_input_page()
    elif st.session_state.page == "dashboard":
        dashboard_page()
    else:
        # Default for logged-in users if page is not explicitly set (e.g., first login)
        st.session_state.page = "welcome_authenticated"
        st.rerun()
else:
    if st.session_state.page == "home":
        home_page()
    elif st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "signup":
        signup_page()
    else:
        # If an unauthenticated user somehow lands on an invalid page, redirect to home
        st.session_state.page = "home"
        st.rerun()