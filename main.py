import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import seaborn as sns
import functions
import auth
import time
from datetime import datetime
import os
# No need to import io here as it's now in functions.py
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from functions import generate_enhanced_pdf_report


# Set page configuration
st.set_page_config(
    page_title="WhatsApp Chat Analyzer",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
auth.init_session_state()

# Apply custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #25D366;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #128C7E;
        margin-bottom: 1rem;
    }
    .card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stat-number {
        font-size: 2rem;
        font-weight: bold;
        color: #075E54;
    }
    .stat-label {
        color: #128C7E;
        font-weight: bold;
    }
    .sidebar-content {
        padding: 20px 0;
    }
    .footer {
        text-align: center;
        margin-top: 50px;
        padding: 20px;
        font-size: 0.8rem;
        color: #666;
    }
    .user-info {
        padding: 10px;
        background-color: #128C7E; 
        color: white;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .login-container {
        max-width: 500px;
        margin: 0 auto;
    }
    .btn-custom {
        background-color: #25D366;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        font-weight: bold;
    }
    .section-divider {
        margin: 40px 0;
        border-top: 1px solid #ddd;
    }
    .emoji-table {
        font-family: Arial, sans-serif;
        width: 100%;
        margin-bottom: 15px;
    }
    .emoji-table th {
        background-color: #128C7E;
        color: white;
        padding: 8px;
        text-align: center;
    }
    .emoji-table td {
        padding: 8px;
        text-align: center;
        border-bottom: 1px solid #ddd;
    }
    .emoji-cell {
        font-size: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar user section
with st.sidebar:
    st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
    
    # User Authentication Section
    if not st.session_state.logged_in:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/WhatsApp.svg/1200px-WhatsApp.svg.png", width=100)
        st.markdown("### WhatsApp Analyzer")
        
        # Create tabs for login and signup
        login_tab, signup_tab = st.tabs(["Login", "Sign Up"])        
        with login_tab:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit_login = st.form_submit_button("Login")
                
                if submit_login:
                    if username and password:
                        success, message = auth.authenticate(username, password)
                        if success:
                            auth.login_user(username)
                            st.success(message)
                            st.rerun()  # Fixed: Changed from experimental_rerun to rerun
                        else:
                            st.error(message)
                    else:
                        st.warning("Please enter both username and password")
        
        with signup_tab:
            with st.form("signup_form"):
                new_username = st.text_input("Choose Username")
                new_email = st.text_input("Email")
                new_password = st.text_input("Choose Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                submit_signup = st.form_submit_button("Create Account")
                
                if submit_signup:
                    if new_username and new_email and new_password and confirm_password:
                        if new_password != confirm_password:
                            st.error("Passwords do not match")
                        else:
                            success, message = auth.create_user(new_username, new_password, new_email)
                            if success:
                                st.success(message)
                                st.info("Please login with your new account")
                            else:
                                st.error(message)
                    else:
                        st.warning("Please fill all fields")
        
        
    
    # Logged in user section
    else:
        # User info card
        st.markdown(f"""
        <div class="user-info">
            <h3>👤 {st.session_state.username}</h3>
            <p>Session duration: {auth.get_session_duration()} min</p>
        </div>
        """, unsafe_allow_html=True)
        
        
            # Show user history
        with st.expander("Your Analysis History"):
                history = auth.get_user_history(st.session_state.username)
                if history:
                    for i, entry in enumerate(reversed(history)):
                        if i >= 5:  # Show only last 5 analyses
                            break
                        st.write(f"📊 {entry['file_name']} - {entry['timestamp'].strftime('%d %b, %H:%M')}")
                else:
                    st.write("No analysis history yet")
        
        # Logout button
        if st.button("Logout"):
            auth.logout_user()
            st.rerun()  # Fixed: Changed from experimental_rerun to rerun
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Only show analysis options if logged in
    if st.session_state.logged_in:
        st.markdown("### Analysis Options")
        
        # This will be populated later when a file is uploaded
        if 'users' in st.session_state:
            users = st.session_state.users
            users_s = st.selectbox("Select User to View Analysis", users)
            
            if st.button("Show Analysis"):
                st.session_state.selected_user = users_s
                
                # Record this analysis in user history
                if st.session_state.username != "" and 'file_name' in st.session_state:
                    auth.record_analysis(
                        st.session_state.username, 
                        st.session_state.file_name, 
                        f"Analysis for {users_s}"
                    )

# Main page content
if st.session_state.logged_in:
    # Page Header
    st.markdown('<h1 class="main-header">📱 WhatsApp Chat Analyzer By Bhoomika</h1>', unsafe_allow_html=True)
    
    # Introduction section in a card
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("""
    ### 📊 Analyze Your WhatsApp Chats with Ease
    
    This tool helps you analyze your WhatsApp conversations to uncover interesting patterns and statistics. 
    Export your chat (without media) from WhatsApp and upload the text file here to get started.
    
    **Features:**
    - Message frequency analysis
    - Emoji usage statistics
    - Most common words
    - Activity patterns by day and time
    - Monthly and daily timeline visualization
    - Word cloud generation
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # File upload section
    st.markdown('<h2 class="sub-header">Upload Your Chat File</h2>', unsafe_allow_html=True)
    
    file = st.file_uploader("Choose WhatsApp chat export file (.txt)", type=["txt"])
    
    # Process the uploaded file
    if file:
        st.session_state.file_name = file.name
        
        with st.spinner('Processing your chat file...'):
            try:
                df = functions.generateDataFrame(file)
                
                # Storing users in session state for sidebar
                users = functions.getUsers(df)
                st.session_state.users = users
                
                # Date format selection with improved UI
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.subheader("Configure Chat Settings")
                dayfirst = st.radio(
                    "Select Date Format in the chat file:",
                    ('dd-mm-yy', 'mm-dd-yy'),
                    horizontal=True
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
                if dayfirst == 'dd-mm-yy':
                    dayfirst = True
                else:
                    dayfirst = False
                
                # Check if user has selected analysis in sidebar
                if 'selected_user' in st.session_state:
                    selected_user = st.session_state.selected_user
                    
                    st.markdown(f'<h2 class="sub-header">Analysis Results for: {selected_user}</h2>', unsafe_allow_html=True)
                    
                    df = functions.PreProcess(df, dayfirst)
                    if selected_user != "Everyone":
                        df = df[df['User'] == selected_user]
                    
                    # Get statistics
                    df, media_cnt, deleted_msgs_cnt, links_cnt, word_count, msg_count = functions.getStats(df)
                    
                    # Display chat statistics in an attractive layout
                    st.markdown('<h2 class="sub-header">Chat Overview</h2>', unsafe_allow_html=True)
                    
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    with col1:
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        st.markdown('<p class="stat-label">Total Messages</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="stat-number">{msg_count}</p>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        st.markdown('<p class="stat-label">Total Words</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="stat-number">{word_count}</p>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        st.markdown('<p class="stat-label">Media Shared</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="stat-number">{media_cnt}</p>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with col4:
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        st.markdown('<p class="stat-label">Links Shared</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="stat-number">{links_cnt}</p>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with col5:
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        st.markdown('<p class="stat-label">Deleted Messages</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="stat-number">{deleted_msgs_cnt}</p>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Add a divider
                    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
                    
                    
                    
                    # User Activity Count (only for Everyone)
                    if selected_user == 'Everyone':
                        st.markdown('<h2 class="sub-header">User Activity Analysis</h2>', unsafe_allow_html=True)
                        
                        # User count visualization
                        user_counts = df['User'].value_counts()
                        
                        # Create two columns for the user activity
                        user_col1, user_col2 = st.columns(2)
                        
                        with user_col1:
                            st.markdown('<div class="card">', unsafe_allow_html=True)
                            st.subheader("Message Count by User")
                            fig, ax = plt.subplots()
                            bars = ax.bar(user_counts.index, user_counts.values, color=sns.color_palette("viridis", len(user_counts)))
                            plt.xticks(rotation='vertical')
                            plt.ylabel("Number of Messages")
                            st.pyplot(fig)
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        with user_col2:
                            st.markdown('<div class="card">', unsafe_allow_html=True)
                            st.subheader("Message Percentage by User")
                            fig, ax = plt.subplots()
                            plt.pie(user_counts.values, labels=user_counts.index, autopct='%1.1f%%', startangle=90, 
                                   colors=sns.color_palette("viridis", len(user_counts)))
                            plt.axis('equal')
                            st.pyplot(fig)
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Add a divider
                        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
                    
                    # Emoji Analysis
                    st.markdown('<h2 class="sub-header">Emoji Analysis</h2>', unsafe_allow_html=True)
                    
                    emoji_df = functions.getEmoji(df)
                    
                    if not emoji_df.empty:
                        emoji_df.columns = ['Emoji', 'Count']
                        
                        # Create three columns for emoji analysis
                        emoji_col1, emoji_col2, emoji_col3 = st.columns([2, 2, 1])
                        
                        with emoji_col1:
                            st.markdown('<div class="card">', unsafe_allow_html=True)
                            st.subheader("Top Emojis Used")
                            
                            # Make sure we have emojis to display
                            if len(emoji_df) > 0:
                                fig, ax = plt.subplots()
                                # Show only top 10 emojis
                                top_emojis = emoji_df.head(10)
                                bars = ax.bar(top_emojis['Emoji'], top_emojis['Count'], color=sns.color_palette("YlOrRd", len(top_emojis)))
                                plt.xticks(rotation='vertical', fontsize=14)  # Increase font size for emojis
                                plt.ylabel("Frequency")
                                plt.tight_layout()
                                st.pyplot(fig)
                            else:
                                st.info("No emojis found in the selected chat.")
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        with emoji_col2:
                            st.markdown('<div class="card">', unsafe_allow_html=True)
                            st.subheader("Emoji Distribution")
                            
                            # Make sure we have emojis to display
                            if len(emoji_df) > 0:
                                # Limit to top 8 for better visualization
                                top_emojis = emoji_df.head(8)
                                fig, ax = plt.subplots()
                                plt.pie(top_emojis['Count'], labels=top_emojis['Emoji'], autopct='%1.1f%%', startangle=90,
                                       colors=sns.color_palette("YlOrRd", len(top_emojis)), textprops={'fontsize': 14})
                                plt.axis('equal')
                                st.pyplot(fig)
                            else:
                                st.info("No emojis found in the selected chat.")
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        with emoji_col3:
                            st.markdown('<div class="card">', unsafe_allow_html=True)
                            st.subheader("Emoji Stats")
                            
                            # Make sure we have emojis to display
                            if len(emoji_df) > 0:
                                total_emojis = emoji_df['Count'].sum()
                                unique_emojis = len(emoji_df)
                                
                                st.markdown(f"<p><span class='stat-label'>Total Emojis:</span> <span class='stat-number'>{total_emojis}</span></p>", unsafe_allow_html=True)
                                st.markdown(f"<p><span class='stat-label'>Unique Emojis:</span> <span class='stat-number'>{unique_emojis}</span></p>", unsafe_allow_html=True)
                                
                                # Calculate emoji frequency per message
                                emoji_per_msg = round(total_emojis / msg_count, 2) if msg_count > 0 else 0
                                st.markdown(f"<p><span class='stat-label'>Emojis per Message:</span> <span class='stat-number'>{emoji_per_msg}</span></p>", unsafe_allow_html=True)
                            else:
                                st.info("No emojis found in the selected chat.")
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Display emoji table
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        st.subheader("Top 15 Emojis")
                        
                        if len(emoji_df) > 0:
                            top_n_emojis = emoji_df.head(15)
                            
                            display_df = pd.DataFrame({
                            'Rank': range(1, len(top_n_emojis) + 1),
                            'Emoji': top_n_emojis['Emoji'],
                            'Count': top_n_emojis['Count'],
                            'Percentage': [f"{round((count / emoji_df['Count'].sum()) * 100, 2)}%" 
                                        for count in top_n_emojis['Count']]
                        })
                        
                        # Use Streamlit's dataframe with custom styling
                        st.dataframe(
                            display_df,
                            column_config={
                                "Emoji": st.column_config.TextColumn(
                                    "Emoji",
                                    width="medium",
                                    help="Emoji symbol"
                                ),
                                "Count": st.column_config.NumberColumn(
                                    "Count",
                                    help="Number of times this emoji was used",
                                    format="%d"
                                ),
                                "Percentage": st.column_config.TextColumn(
                                    "Percentage",
                                    help="Percentage of total emoji usage"
                                )
                            },
                            hide_index=True,
                            use_container_width=True
                          )
                    else:
                        st.info("No emojis found in the selected chat.")
                        st.markdown('</div>', unsafe_allow_html=True)
                                            
                    # Add a divider
                    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
                    
                    # Most Common Words Analysis
                    st.markdown('<h2 class="sub-header">Most Common Words</h2>', unsafe_allow_html=True)
                    
                    common_words = functions.MostCommonWords(df)
                    if not common_words.empty:
                        common_words.columns = ['Word', 'Count']
                        
                        words_col1, words_col2 = st.columns(2)
                        
                        with words_col1:
                            st.markdown('<div class="card">', unsafe_allow_html=True)
                            st.subheader("Top Words")
                            
                            fig, ax = plt.subplots()
                            y_pos = np.arange(len(common_words.head(10)))
                            ax.barh(y_pos, common_words.head(10)['Count'], align='center', color=sns.color_palette("Blues_r", len(common_words.head(10))))
                            ax.set_yticks(y_pos)
                            ax.set_yticklabels(common_words.head(10)['Word'])
                            ax.invert_yaxis()
                            plt.xlabel('Frequency')
                            st.pyplot(fig)
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        with words_col2:
                            st.markdown('<div class="card">', unsafe_allow_html=True)
                            st.subheader("Word Cloud")
                            
                            try:
                                word_cloud = functions.create_wordcloud(df)
                                fig, ax = plt.subplots()
                                plt.imshow(word_cloud, interpolation='bilinear')
                                plt.axis('off')
                                st.pyplot(fig)
                            except Exception as e:
                                st.error(f"Error generating wordcloud: {e}")
                            st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.info("No common words found after filtering stop words.")
                    
                    # Add a divider
                    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
                    
                    # Activity Patterns
                    st.markdown('<h2 class="sub-header">Activity Patterns</h2>', unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        st.subheader("Daily Activity")
                        functions.WeekAct(df)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        st.subheader("Monthly Activity")
                        functions.MonthAct(df)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Daily timeline
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    functions.dailytimeline(df)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Activity heatmap
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.subheader("Activity Heatmap")
                    
                    user_heatmap = functions.activity_heatmap(df)
                    fig, ax = plt.subplots(figsize=(12, 8))
                    sns.heatmap(user_heatmap, cmap="YlGnBu", ax=ax)
                    plt.title('Activity Heat Map')
                    plt.xlabel('Hour of Day')
                    plt.ylabel('Day of Week')
                    st.pyplot(fig)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Add a divider
                    #st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
                    
                                        # Add this code to main.py right after the Activity Patterns section
                    # (before the "Add a divider" line that comes before the PDF report section)

                    # Response Time Analysis
                    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
                    st.markdown('<h2 class="sub-header">Response Time Analysis</h2>', unsafe_allow_html=True)

                    # Only show response analysis if there are multiple users (not for individual user analysis)
                    if selected_user == 'Everyone' and len(df['User'].unique()) > 1:
                        try:
                            st.markdown('<div class="card">', unsafe_allow_html=True)
                            
                            # Calculate response times
                            with st.spinner("Calculating response times..."):
                                response_times_df, user_response_stats_df = functions.calculate_response_times(df)
                                
                                if not user_response_stats_df.empty:
                                    # Display statistics about response times
                                    st.subheader("Response Time Statistics by User")
                                    
                                    # Format the time values to be more readable
                                    for col in ['Avg_Response_Time_Min', 'Median_Response_Time_Min', 'Min_Response_Time_Min', 'Max_Response_Time_Min']:
                                        user_response_stats_df[col] = user_response_stats_df[col].apply(
                                            lambda x: f"{int(x // 60)}h {int(x % 60)}m" if x >= 60 else f"{round(x, 1)}m"
                                        )
                                    
                                    # Add responsiveness percentage as a progress bar column
                                    user_response_stats_df['Responsiveness'] = user_response_stats_df['Responsiveness'].apply(
                                        lambda x: f"{round(x, 1)}%"
                                    )
                                    
                                    # Show the stats table
                                    st.dataframe(
                                        user_response_stats_df,
                                        column_config={
                                            "User": st.column_config.TextColumn("User", help="Username"),
                                            "Avg_Response_Time_Min": st.column_config.TextColumn("Avg Response Time", help="Average time to respond"),
                                            "Median_Response_Time_Min": st.column_config.TextColumn("Median Response Time", help="Median time to respond"),
                                            "Min_Response_Time_Min": st.column_config.TextColumn("Min Response Time", help="Minimum time to respond"),
                                            "Max_Response_Time_Min": st.column_config.TextColumn("Max Response Time", help="Maximum time to respond"),
                                            "Response_Count": st.column_config.NumberColumn("# of Responses", help="Number of responses by this user"),
                                            "Responsiveness": st.column_config.TextColumn("Responsiveness", help="How often this user responds when mentioned")
                                        },
                                        hide_index=True,
                                        use_container_width=True
                                    )
                                    
                                    # Create visualizations
                                    viz_col1, viz_col2 = st.columns(2)
                                    
                                    with viz_col1:
                                        st.subheader("Average Response Time by User")
                                        
                                        # Prepare data for visualization
                                        viz_data = user_response_stats_df.copy()
                                        
                                        # Convert time string back to float for plotting
                                        def convert_time_to_minutes(time_str):
                                            if 'h' in time_str:
                                                h, m = time_str.split('h ')
                                                return float(h) * 60 + float(m.replace('m', ''))
                                            else:
                                                return float(time_str.replace('m', ''))
                                        
                                        viz_data['Avg_Minutes'] = user_response_stats_df['Avg_Response_Time_Min'].apply(convert_time_to_minutes)
                                        
                                        # Create bar chart
                                        fig, ax = plt.subplots()
                                        bars = ax.bar(viz_data['User'], viz_data['Avg_Minutes'], color=sns.color_palette("viridis", len(viz_data)))
                                        plt.xticks(rotation='vertical')
                                        plt.ylabel("Average Response Time (minutes)")
                                        plt.tight_layout()
                                        st.pyplot(fig)
                                    
                                    with viz_col2:
                                        st.subheader("Response Count Comparison")
                                        fig, ax = plt.subplots()
                                        plt.pie(user_response_stats_df['Response_Count'], 
                                            labels=user_response_stats_df['User'], 
                                            autopct='%1.1f%%', 
                                            startangle=90,
                                            colors=sns.color_palette("viridis", len(user_response_stats_df)))
                                        plt.axis('equal')
                                        st.pyplot(fig)
                                    
                                    # Response time distribution histogram
                                    st.subheader("Response Time Distribution")
                                    # Filter to responses under 60 minutes for better visualization
                                    quick_responses = response_times_df[response_times_df['ResponseTime_Minutes'] <= 60]
                                    
                                    # If we have quick responses, show their distribution
                                    if not quick_responses.empty:
                                        fig, ax = plt.subplots(figsize=(10, 6))
                                        sns.histplot(data=quick_responses, x='ResponseTime_Minutes', hue='Responder', 
                                                    bins=20, kde=True, element="step", ax=ax)
                                        plt.xlabel("Response Time (minutes)")
                                        plt.ylabel("Frequency")
                                        plt.title("Distribution of Response Times (up to 60 minutes)")
                                        plt.tight_layout()
                                        st.pyplot(fig)
                                    
                                    # Display most responsive pairs
                                    st.subheader("Most Responsive Conversation Pairs")
                                    
                                    # Calculate average response time between each pair of users
                                    pair_response_times = []
                                    
                                    for initiator in user_response_stats_df['User']:
                                        for responder in user_response_stats_df['User']:
                                            if initiator != responder:
                                                pair_data = response_times_df[
                                                    (response_times_df['Initiator'] == initiator) & 
                                                    (response_times_df['Responder'] == responder)
                                                ]
                                                
                                                if not pair_data.empty:
                                                    avg_time = pair_data['ResponseTime_Minutes'].mean()
                                                    count = len(pair_data)
                                                    
                                                    pair_response_times.append({
                                                        'Initiator': initiator,
                                                        'Responder': responder,
                                                        'Avg_Response_Time_Min': round(avg_time, 2),
                                                        'Interaction_Count': count
                                                    })
                                    
                                    if pair_response_times:
                                        pair_df = pd.DataFrame(pair_response_times)
                                        
                                        # Sort by response time (ascending) to show fastest responders
                                        pair_df = pair_df.sort_values('Avg_Response_Time_Min')
                                        
                                        # Format the time values
                                        pair_df['Avg_Response_Time_Min'] = pair_df['Avg_Response_Time_Min'].apply(
                                            lambda x: f"{int(x // 60)}h {int(x % 60)}m" if x >= 60 else f"{round(x, 1)}m"
                                        )
                                        
                                        # Show the pair stats table
                                        st.dataframe(
                                            pair_df,
                                            column_config={
                                                "Initiator": st.column_config.TextColumn("Message Sender", help="Person who sent the initial message"),
                                                "Responder": st.column_config.TextColumn("Responder", help="Person who responded"),
                                                "Avg_Response_Time_Min": st.column_config.TextColumn("Avg Response Time", help="Average response time"),
                                                "Interaction_Count": st.column_config.NumberColumn("# of Interactions", help="Number of exchanges between this pair")
                                            },
                                            hide_index=True,
                                            use_container_width=True
                                        )
                                else:
                                    st.info("Not enough data to analyze response times.")
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        except Exception as e:
                            st.error(f"Error analyzing response times: {e}")
                    else:
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        st.info("Response time analysis is available only when analyzing the entire chat (Everyone). Please select 'Everyone' from the user dropdown to view response time metrics.")
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    
                    
                    
                    # Enhanced PDF Report Generation
                    st.markdown('<h2 class="sub-header">Generate Enhanced PDF Report</h2>', unsafe_allow_html=True)
                    st.markdown('<div class="card">', unsafe_allow_html=True)

                    col1, col2 = st.columns([1, 1])

                    with col1:
                        if st.button("Generate Enhanced PDF Report", key="enhanced_pdf_report"):
                            with st.spinner("Generating enhanced PDF report..."):
                                try:
                                    pdf_buffer = functions.generate_enhanced_pdf_report(
                                        df,
                                        media_cnt,
                                        deleted_msgs_cnt,
                                        links_cnt,
                                        word_count,
                                        msg_count,
                                        selected_user,
                                        emoji_df=emoji_df if 'emoji_df' in locals() else None,
                                        common_words=common_words if 'common_words' in locals() else None
                                    )

                                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    filename = f"enhanced_whatsapp_analysis_{selected_user}_{timestamp}.pdf"

                                    st.session_state.pdf_buffer = pdf_buffer  # Store PDF in session state for email sending
                                    st.session_state.pdf_filename = filename

                                    st.download_button(
                                        label="Download Enhanced PDF Report",
                                        data=pdf_buffer,
                                        file_name=filename,
                                        mime="application/pdf",
                                        key="enhanced_pdf_download"
                                    )

                                    st.success("Enhanced PDF report generated successfully!")

                                    # Log the download
                                    if st.session_state.username:
                                        auth.record_analysis(
                                            st.session_state.username,
                                            st.session_state.file_name,
                                            f"Downloaded Enhanced PDF Report for {selected_user}"
                                        )

                                except Exception as e:
                                    st.error(f"Error generating enhanced PDF report: {e}")

                    with col2:
                        # Only show email option if user is logged in and PDF is generated
                        if st.session_state.logged_in and st.session_state.username and 'pdf_buffer' in st.session_state:
                            if st.button("Email PDF Report", key="email_pdf_report"):
                                with st.spinner("Sending PDF report to your email..."):
                                    try:
                                        # Get user email from auth system
                                        users = auth.load_users()
                                        user_email = users[st.session_state.username]['email']
                                        
                                        # Import email utility
                                        from email_util import send_pdf_report
                                        
                                        # Send the email
                                        success, message = send_pdf_report(
                                            user_email, 
                                            st.session_state.pdf_buffer,
                                            st.session_state.pdf_filename,
                                            user_name=st.session_state.username
                                        )
                                        
                                        if success:
                                            st.success(message)
                                            # Log the email action
                                            auth.record_analysis(
                                                st.session_state.username,
                                                st.session_state.file_name,
                                                f"Emailed Enhanced PDF Report for {selected_user}"
                                            )
                                        else:
                                            st.error(message)
                                    
                                    except Exception as e:
                                        st.error(f"Error sending email: {e}")
                        elif st.session_state.logged_in and 'pdf_buffer' not in st.session_state:
                            st.info("Please generate a PDF report first before sending via email.")
                        elif not st.session_state.logged_in:
                            st.info("Please log in to use the email feature.")

                    st.markdown('</div>', unsafe_allow_html=True)
                                                    
                                
                    

                    
            except Exception as e:
                st.error(f"Error processing file: {e}")
                st.error("Please make sure you've uploaded a valid WhatsApp chat export file.")
    
    # Footer
    st.markdown('<div class="footer">', unsafe_allow_html=True)
    st.markdown("WhatsApp Chat Analyzer Project by Bhoomika N ")
    st.markdown("Export your WhatsApp chat (without media) and upload the .txt file to analyze.")
    st.markdown('</div>', unsafe_allow_html=True)

else:
    # Display login page for users who aren't logged in
    st.markdown('<h1 class="main-header">📱 WhatsApp Chat Analyzer by Bhoomika</h1>', unsafe_allow_html=True)
    
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)


    st.markdown(
    """
    
    ## Follow these steps to analyze your WhatsApp chats:
    1️⃣ **Open WhatsApp** on your phone.  
    2️⃣ **Select the chat** (individual or group) you want to export.  
    3️⃣ **Tap the three-dot menu** (on Android) or **tap the chat name** (on iPhone).  
    4️⃣ **Choose "More"** and select **"Export Chat"**.  
    5️⃣ **Select "Export without media"** to save only text messages.  
    6️⃣ **Choose your export method** (email, Google Drive, or another app).  
    7️⃣ **Send or save the file** to your preferred location.  

    📂 **Your chat will be saved as a `.txt` file. Use this file for analysis!**

    ---

    # 🔐 Please Log In or Create an Account  
    ## Unlock ALL THE FEATURES:
    ✅ **Detailed Chat Analysis** – Get a comprehensive explanation of your chat history.  
    ✅ **Customized Insights** – Filter and analyze messages by individual participants.  
    ✅ **Report Generation** – Summarize your chat analysis into a structured report.  
    ✅ **PDF Export** – Download your generated report in a convenient PDF format.  

    🚀 Start exploring your chats like never before!
    
    """
)
    
    
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)