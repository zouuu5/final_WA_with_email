import re
from collections import Counter

import pandas as pd
import seaborn as sns
import streamlit as st
from collections import Counter
import matplotlib.pyplot as plt
import urlextract
import emoji
from wordcloud import WordCloud
import io  # Add this import for BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from datetime import datetime


def generateDataFrame(file):
    data = file.read().decode("utf-8")
    data = data.replace('\u202f', ' ')
    data = data.replace('\n', ' ')
    dt_format = '\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s?(?:AM\s|PM\s|am\s|pm\s)?-\s'
    msgs = re.split(dt_format, data)[1:]
    date_times = re.findall(dt_format, data)
    date = []
    time = []
    for dt in date_times:
        date.append(re.search('\d{1,2}/\d{1,2}/\d{2,4}', dt).group())
        time.append(re.search('\d{1,2}:\d{2}\s?(?:AM|PM|am|pm)?', dt).group())
    users = []
    message = []
    for m in msgs:
        s = re.split('([\w\W]+?):\s', m)
        if (len(s) < 3):
            users.append("Notifications")
            message.append(s[0])
        else:
            users.append(s[1])
            message.append(s[2])
    df = pd.DataFrame(list(zip(date, time, users, message)), columns=["Date", "Time(U)", "User", "Message"])
    return df


def getUsers(df):
    users = df['User'].unique().tolist()
    users.sort()
    users.remove('Notifications')
    users.insert(0, 'Everyone')
    return users


def PreProcess(df,dayf):
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=dayf)
    df['Time'] = pd.to_datetime(df['Time(U)']).dt.time
    df['year'] = df['Date'].apply(lambda x: int(str(x)[:4]))
    df['month'] = df['Date'].apply(lambda x: int(str(x)[5:7]))
    df['date'] = df['Date'].apply(lambda x: int(str(x)[8:10]))
    df['day'] = df['Date'].apply(lambda x: x.day_name())
    df['hour'] = df['Time'].apply(lambda x: int(str(x)[:2]))
    df['month_name'] = df['Date'].apply(lambda x: x.month_name())
    return df


def getStats(df):
    media = df[df['Message'] == "<Media omitted> "]
    media_cnt = media.shape[0]
    df.drop(media.index, inplace=True)
    deleted_msgs = df[df['Message'] == "This message was deleted "]
    deleted_msgs_cnt = deleted_msgs.shape[0]
    df.drop(deleted_msgs.index, inplace=True)
    temp = df[df['User'] == 'Notifications']
    df.drop(temp.index, inplace=True)
    print("h4")
    extractor = urlextract.URLExtract()
    print("h3")
    links = []
    for msg in df['Message']:
        x = extractor.find_urls(msg)
        if x:
            links.extend(x)
    links_cnt = len(links)
    word_list = []
    for msg in df['Message']:
        word_list.extend(msg.split())
    word_count = len(word_list)
    msg_count = df.shape[0]
    return df, media_cnt, deleted_msgs_cnt, links_cnt, word_count, msg_count


def getEmoji(df):
    emojis = []
    for message in df['Message']:
        emojis.extend([c for c in message if c in emoji.EMOJI_DATA])
    return pd.DataFrame(Counter(emojis).most_common(len(Counter(emojis))))


def getMonthlyTimeline(df):

    df.columns = df.columns.str.strip()
    df=df.reset_index()
    timeline = df.groupby(['year', 'month']).count()['Message'].reset_index()
    time = []
    for i in range(timeline.shape[0]):
        time.append(str(timeline['month'][i]) + "-" + str(timeline['year'][i]))
    timeline['time'] = time
    return timeline


def MostCommonWords(df):
    f = open('stop_hinglish.txt')
    stop_words = f.read()
    f.close()
    words = []
    for message in df['Message']:
        for word in message.lower().split():
            if word not in stop_words:
                words.append(word)
    return pd.DataFrame(Counter(words).most_common(20))

def dailytimeline(df):
    df['taarek'] = df['Date']
    daily_timeline = df.groupby('taarek').count()['Message'].reset_index()
    fig, ax = plt.subplots()
    #ax.figure(figsize=(100, 80))
    ax.plot(daily_timeline['taarek'], daily_timeline['Message'])
    ax.set_ylabel("Messages Sent")
    st.title('Daily Timeline')
    st.pyplot(fig)

def WeekAct(df):
    x = df['day'].value_counts()
    fig, ax = plt.subplots()
    ax.bar(x.index, x.values)
    ax.set_xlabel("Days")
    ax.set_ylabel("Message Sent")
    plt.xticks(rotation='vertical')
    st.pyplot(fig)

def MonthAct(df):
    x = df['month_name'].value_counts()
    fig, ax = plt.subplots()
    ax.bar(x.index, x.values)
    ax.set_xlabel("Months")
    ax.set_ylabel("Message Sent")
    plt.xticks(rotation='vertical')
    st.pyplot(fig)

def activity_heatmap(df):
    period = []
    for hour in df[['day', 'hour']]['hour']:
        if hour == 23:
            period.append(str(hour) + "-" + str('00'))
        elif hour == 0:
            period.append(str('00') + "-" + str(hour + 1))
        else:
            period.append(str(hour) + "-" + str(hour + 1))

    df['period'] = period
    user_heatmap = df.pivot_table(index='day', columns='period', values='Message', aggfunc='count').fillna(0)
    return user_heatmap

def create_wordcloud(df):

    f = open('stop_hinglish.txt', 'r')
    stop_words = f.read()
    f.close()
    def remove_stop_words(message):
        y = []
        for word in message.lower().split():
            if word not in stop_words:
                y.append(word)
        return " ".join(y)

    wc = WordCloud(width=500,height=500,min_font_size=10,background_color='white')
    df['Message'] = df['Message'].apply(remove_stop_words)
    df_wc = wc.generate(df['Message'].str.cat(sep=" "))
    return df_wc

def calculate_response_times(df):

    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    
    # Make sure df is sorted chronologically
    df = df.sort_values(by=['Date', 'Time'])
    
    # Create a datetime column for accurate time difference calculation
    df['DateTime'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str))
    
    # Initialize lists to store response data
    responding_user = []
    initiating_user = []
    response_times = []
    
    # Iterate through messages to calculate response times
    for i in range(1, len(df)):
        current_user = df.iloc[i]['User']
        previous_user = df.iloc[i-1]['User']
        
        # Only calculate response time when the sender changes
        if current_user != previous_user:
            time_diff = (df.iloc[i]['DateTime'] - df.iloc[i-1]['DateTime']).total_seconds() / 60  # in minutes
            
            # Filter out unreasonably long response times (e.g., more than 24 hours)
            if time_diff <= 24 * 60:  # 24 hours in minutes
                responding_user.append(current_user)
                initiating_user.append(previous_user)
                response_times.append(time_diff)
    
    # Create DataFrame with all response times
    response_times_df = pd.DataFrame({
        'Responder': responding_user,
        'Initiator': initiating_user,
        'ResponseTime_Minutes': response_times
    })
    
    # Calculate statistics for each user
    user_stats = []
    
    # Get unique users excluding 'Notifications'
    unique_users = df['User'].unique()
    unique_users = [user for user in unique_users if user != 'Notifications']
    
    for user in unique_users:
        # Get responses by this user
        user_responses = response_times_df[response_times_df['Responder'] == user]
        
        if not user_responses.empty:
            avg_time = user_responses['ResponseTime_Minutes'].mean()
            median_time = user_responses['ResponseTime_Minutes'].median()
            max_time = user_responses['ResponseTime_Minutes'].max()
            min_time = user_responses['ResponseTime_Minutes'].min()
            response_count = len(user_responses)
            
            # Calculate responsiveness percentage
            total_responses_to_user = len(response_times_df[response_times_df['Initiator'] == user])
            total_messages_to_user = total_responses_to_user  # Simplified metric
            
            responsiveness = 0 if total_messages_to_user == 0 else (response_count / total_messages_to_user) * 100
            
            user_stats.append({
                'User': user,
                'Avg_Response_Time_Min': round(avg_time, 2),
                'Median_Response_Time_Min': round(median_time, 2),
                'Max_Response_Time_Min': round(max_time, 2),
                'Min_Response_Time_Min': round(min_time, 2),
                'Response_Count': response_count,
                'Responsiveness': round(responsiveness, 2)
            })
    
    # Create DataFrame with user statistics
    user_response_stats_df = pd.DataFrame(user_stats)
    
    return response_times_df, user_response_stats_df

def generate_enhanced_pdf_report(df, media_cnt, deleted_msgs_cnt, links_cnt, word_count, msg_count, selected_user, emoji_df=None, common_words=None):
    """Generate a PDF report with visualizations from chat analysis data"""
    import io
    import matplotlib.pyplot as plt
    from datetime import datetime
    import numpy as np
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
    from reportlab.lib.units import inch
    
    buffer = io.BytesIO()
    
    # Create the PDF object
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor("#075E54"),
        spaceAfter=12,
        alignment=1  # Center alignment
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor("#128C7E"),
        spaceAfter=8
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=6
    )
    
    # Add title
    elements.append(Paragraph(f"WhatsApp Chat Analysis Report - {selected_user}", title_style))
    elements.append(Spacer(1, 12))
    
    # Add date
    elements.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}", normal_style))
    elements.append(Spacer(1, 20))
    
    # Add chat statistics section
    elements.append(Paragraph("Chat Overview", subtitle_style))
    
    # Create statistics table
    stats_data = [
        ["Metric", "Value"],
        ["Total Messages", str(msg_count)],
        ["Total Words", str(word_count)],
        ["Media Shared", str(media_cnt)],
        ["Links Shared", str(links_cnt)],
        ["Deleted Messages", str(deleted_msgs_cnt)]
    ]
    
    stats_table = Table(stats_data, colWidths=[250, 100])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor("#128C7E")),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(stats_table)
    elements.append(Spacer(1, 20))
    
    # Add user activity section if it's for Everyone
    if selected_user == "Everyone":
        elements.append(Paragraph("User Activity Distribution", subtitle_style))
        
        # Create user activity pie chart instead of table
        fig, ax = plt.subplots(figsize=(7, 5))
        user_counts = df['User'].value_counts()
        user_counts = user_counts[user_counts.index != 'Notifications']  # Remove notifications
        ax.pie(user_counts, labels=user_counts.index, autopct='%1.1f%%', startangle=90, 
               shadow=True, explode=[0.05]*len(user_counts), wedgeprops={'edgecolor': 'white'})
        ax.axis('equal')
        plt.title('Message Distribution by User')
        
        # Save the pie chart to a BytesIO object
        img_byte_arr = io.BytesIO()
        plt.savefig(img_byte_arr, format='png', dpi=300, bbox_inches='tight')
        img_byte_arr.seek(0)
        plt.close(fig)
        
        # Add the chart to the PDF
        img = Image(img_byte_arr)
        img.drawHeight = 3.5 * inch
        img.drawWidth = 5 * inch
        elements.append(img)
        elements.append(Spacer(1, 12))
        
        # Add a small table with exact message counts
        elements.append(Paragraph("Message Count per User", normal_style))
        user_data = [["User", "Message Count", "Percentage"]]
        
        for user, count in user_counts.items():
            percentage = round((count / user_counts.sum()) * 100, 2)
            user_data.append([user, str(count), f"{percentage}%"])
        
        user_table = Table(user_data, colWidths=[150, 100, 100])
        user_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#128C7E")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(user_table)
        elements.append(Spacer(1, 20))
    
    # Add timeline visualization
    elements.append(Paragraph("Message Timeline", subtitle_style))
    
    # Create a line chart of messages over time
    timeline = getMonthlyTimeline(df)
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(timeline['time'], timeline['Message'], marker='o', linestyle='-', linewidth=2, markersize=6, color='#128C7E')
    ax.set_xlabel('Month-Year')
    ax.set_ylabel('Number of Messages')
    ax.set_title('Message Activity Over Time')
    plt.xticks(rotation=45)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    # Save the timeline chart to a BytesIO object
    img_byte_arr = io.BytesIO()
    plt.savefig(img_byte_arr, format='png', dpi=300, bbox_inches='tight')
    img_byte_arr.seek(0)
    plt.close(fig)
    
    # Add the chart to the PDF
    img = Image(img_byte_arr)
    img.drawHeight = 3 * inch
    img.drawWidth = 6 * inch
    elements.append(img)
    elements.append(Spacer(1, 20))
    
    # Add daily activity pattern
    elements.append(Paragraph("Day of Week Activity", subtitle_style))
    
    # Create a bar chart for messages by day of week
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_counts = df['day'].value_counts().reindex(day_order)
    
    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(day_counts.index, day_counts.values, color='#128C7E')
    ax.set_xlabel('Day of Week')
    ax.set_ylabel('Number of Messages')
    ax.set_title('Message Activity by Day of Week')
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 5,
                f'{height}', ha='center', va='bottom')
    plt.tight_layout()
    
    # Save the day activity chart to a BytesIO object
    img_byte_arr = io.BytesIO()
    plt.savefig(img_byte_arr, format='png', dpi=300, bbox_inches='tight')
    img_byte_arr.seek(0)
    plt.close(fig)
    
    # Add the chart to the PDF
    img = Image(img_byte_arr)
    img.drawHeight = 3 * inch
    img.drawWidth = 6 * inch
    elements.append(img)
    elements.append(Spacer(1, 20))
    
    # Add hourly activity heatmap
    elements.append(Paragraph("Hourly Activity Heatmap", subtitle_style))
    elements.append(Paragraph("When messages are sent throughout the day", normal_style))
    
    # Create activity heatmap
    user_heatmap = activity_heatmap(df)
    fig, ax = plt.subplots(figsize=(10, 6))
    heatmap = sns.heatmap(user_heatmap, cmap='Greens', linewidths=0.5, ax=ax)
    plt.title('Activity Heatmap: Message Timing by Day and Hour')
    plt.tight_layout()
    
    # Save the heatmap to a BytesIO object
    img_byte_arr = io.BytesIO()
    plt.savefig(img_byte_arr, format='png', dpi=300, bbox_inches='tight')
    img_byte_arr.seek(0)
    plt.close(fig)
    
    # Add the heatmap to the PDF
    img = Image(img_byte_arr)
    img.drawHeight = 4 * inch
    img.drawWidth = 7 * inch
    elements.append(img)
    elements.append(Spacer(1, 20))
    
    # Add emoji visualization if available
    if emoji_df is not None and not emoji_df.empty:
        elements.append(Paragraph("Top Emojis Used", subtitle_style))
        
        # Create emoji bar chart (top 10)
        emoji_df.columns = ['Emoji', 'Count']
        top_emojis = emoji_df.head(10)
        
        fig, ax = plt.subplots(figsize=(8, 4))
        bars = ax.barh(top_emojis['Emoji'], top_emojis['Count'], color='#25D366')
        ax.set_xlabel('Count')
        ax.set_title('Top 10 Emojis Used')
        ax.invert_yaxis()  # To have the highest count at the top
        
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax.text(width + 1, bar.get_y() + bar.get_height()/2, 
                   f'{width}', ha='left', va='center')
        
        plt.tight_layout()
        
        # Save the emoji chart to a BytesIO object
        img_byte_arr = io.BytesIO()
        plt.savefig(img_byte_arr, format='png', dpi=300, bbox_inches='tight')
        img_byte_arr.seek(0)
        plt.close(fig)
        
        # Add the chart to the PDF
        img = Image(img_byte_arr)
        img.drawHeight = 3.5 * inch
        img.drawWidth = 6 * inch
        elements.append(img)
        elements.append(Spacer(1, 20))
    
    # Add word cloud visualization
    elements.append(Paragraph("Word Cloud Analysis", subtitle_style))
    
    # Generate word cloud
    wordcloud = create_wordcloud(df)
    
    # Plot the word cloud
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    plt.tight_layout()
    
    # Save the word cloud to a BytesIO object
    img_byte_arr = io.BytesIO()
    plt.savefig(img_byte_arr, format='png', dpi=300, bbox_inches='tight')
    img_byte_arr.seek(0)
    plt.close(fig)
    
    # Add the word cloud to the PDF
    img = Image(img_byte_arr)
    img.drawHeight = 4 * inch
    img.drawWidth = 6 * inch
    elements.append(img)
    elements.append(Spacer(1, 20))
    
    # Add common words visualization
    if common_words is not None and not common_words.empty:
        elements.append(Paragraph("Most Common Words", subtitle_style))
        
        # Create common words bar chart
        common_words.columns = ['Word', 'Count']
        
        fig, ax = plt.subplots(figsize=(8, 5))
        bars = ax.barh(common_words['Word'][:15], common_words['Count'][:15], color='#34B7F1')
        ax.set_xlabel('Count')
        ax.set_title('Most Common Words Used')
        ax.invert_yaxis()  # To have the highest count at the top
        
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax.text(width + 1, bar.get_y() + bar.get_height()/2, 
                   f'{width}', ha='left', va='center')
        
        plt.tight_layout()
        
        # Save the common words chart to a BytesIO object
        img_byte_arr = io.BytesIO()
        plt.savefig(img_byte_arr, format='png', dpi=300, bbox_inches='tight')
        img_byte_arr.seek(0)
        plt.close(fig)
        
        # Add the chart to the PDF
        img = Image(img_byte_arr)
        img.drawHeight = 4 * inch
        img.drawWidth = 6 * inch
        elements.append(img)
        elements.append(Spacer(1, 20))
    
    # If we have at least 2 users and selected "Everyone", add response time analysis
    if selected_user == "Everyone" and len(df['User'].unique()) > 2:
        elements.append(Paragraph("Response Time Analysis", subtitle_style))
        
        # Calculate response times
        response_times_df, user_response_stats_df = calculate_response_times(df)
        
        if not user_response_stats_df.empty:
            # Create response time comparison chart
            fig, ax = plt.subplots(figsize=(8, 5))
            bars = ax.bar(user_response_stats_df['User'], 
                         user_response_stats_df['Avg_Response_Time_Min'],
                         color='#128C7E')
            ax.set_ylabel('Average Response Time (minutes)')
            ax.set_title('Average Response Time by User')
            plt.xticks(rotation=45)
            
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                       f'{height:.1f}', ha='center', va='bottom')
                
            plt.tight_layout()
            
            # Save the response time chart to a BytesIO object
            img_byte_arr = io.BytesIO()
            plt.savefig(img_byte_arr, format='png', dpi=300, bbox_inches='tight')
            img_byte_arr.seek(0)
            plt.close(fig)
            
            # Add the chart to the PDF
            img = Image(img_byte_arr)
            img.drawHeight = 3.5 * inch
            img.drawWidth = 6 * inch
            elements.append(img)
            elements.append(Spacer(1, 12))
            
            # Add response statistics table
            elements.append(Paragraph("Detailed Response Statistics", normal_style))
            
            # Format the response stats table data
            response_data = [["User", "Avg Time (min)", "Median Time (min)", "Response Count"]]
            for _, row in user_response_stats_df.iterrows():
                response_data.append([
                    row['User'],
                    f"{row['Avg_Response_Time_Min']:.1f}",
                    f"{row['Median_Response_Time_Min']:.1f}",
                    str(row['Response_Count'])
                ])
            
            response_table = Table(response_data, colWidths=[120, 100, 120, 100])
            response_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#128C7E")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            elements.append(response_table)
            elements.append(Spacer(1, 20))
    
    # Add footer with credits
    elements.append(Paragraph("WhatsApp Chat Analysis Report • Generated with Python", 
                            ParagraphStyle('Footer', fontSize=8, textColor=colors.grey)))
    
    # Build the PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

