import streamlit as st
import json
import os
import hashlib
import datetime
from datetime import datetime, timedelta

# File to store user data
USER_DB_FILE = "user_data.json"

def init_session_state():
    """Initialize the session state variables if they don't exist"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'login_time' not in st.session_state:
        st.session_state.login_time = None

def hash_password(password):
    """Create a simple hash of the password"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """Load users from the JSON file"""
    if os.path.exists(USER_DB_FILE):
        try:
            with open(USER_DB_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            # If file is corrupted, return empty dict
            return {}
    return {}

def save_users(users):
    """Save users to the JSON file"""
    with open(USER_DB_FILE, 'w') as f:
        json.dump(users, f)

def create_user(username, password, email):
    """Create a new user"""
    users = load_users()
    
    # Check if username already exists
    if username in users:
        return False, "Username already exists"
    
    # Create user record
    users[username] = {
        'password': hash_password(password),
        'email': email,
        'created_at': datetime.now().isoformat(),
        'last_login': None,
        'history': []
    }
    
    save_users(users)
    return True, "Account created successfully"

def authenticate(username, password):
    """Authenticate a user"""
    users = load_users()
    
    if username not in users:
        return False, "Invalid username or password"
    
    hashed_password = hash_password(password)
    if users[username]['password'] != hashed_password:
        return False, "Invalid username or password"
    
    # Update last login
    users[username]['last_login'] = datetime.now().isoformat()
    save_users(users)
    
    return True, "Login successful"

def login_user(username):
    """Set user as logged in"""
    st.session_state.logged_in = True
    st.session_state.username = username
    st.session_state.login_time = datetime.now()

def logout_user():
    """Log out the user"""
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.login_time = None

def get_session_duration():
    """Get the session duration in minutes"""
    if st.session_state.login_time:
        delta = datetime.now() - st.session_state.login_time
        return round(delta.total_seconds() / 60)
    return 0

def record_analysis(username, file_name, description):
    """Record an analysis in the user's history"""
   
    
    users = load_users()
    
    if username in users:
        # Add the analysis to the user's history
        users[username]['history'].append({
            'file_name': file_name,
            'description': description,
            'timestamp': datetime.now().isoformat()
        })
        
        save_users(users)

def get_user_history(username):
    """Get the analysis history for a user"""
    
    
    users = load_users()
    
    if username in users and 'history' in users[username]:
        # Convert ISO timestamps to datetime objects
        history = users[username]['history']
        for entry in history:
            entry['timestamp'] = datetime.fromisoformat(entry['timestamp'])
        return history
    
    return []