import os
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

KEYWORDS = ["nutrition", "gut health", "fiber", "protein diet", "GLP-1", "fibermaxxing", 
            "longevity diet", "anti inflammatory", "ZOE nutrition", "whole foods"]

def get_youtube_service():
    return build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

def search_trending_videos(query, max_results=15):
    youtube = get_youtube_service()
    published_after = (datetime.utcnow() - timedelta(days=30)).isoformat() + "Z"
    
    request = youtube.search().list(
        part="snippet",
        q=query,
        type="video",
        order="viewCount",
        maxResults=max_results,
        publishedAfter=published_after,
        regionCode="US"
    )
    response = request.execute()
    
    videos = []
    for item in response.get("items", []):
        video_id = item["id"]["videoId"]
        videos.append({
            "title": item["snippet"]["title"],
            "channel": item["snippet"]["channelTitle"],
            "video_id": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"]
        })
    return videos

def send_email(report: str):
    if not all([EMAIL_FROM, EMAIL_TO, EMAIL_PASSWORD]):
        return False, "Email credentials missing"
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO
    msg['Subject'] = f"🥗 Weekly Nutrition Trends - {datetime.now().strftime('%B %d, %Y')}"
    
    msg.attach(MIMEText(report, 'plain'))
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)
        return True, "Success"
    except Exception as e:
        return False, str(e)

def generate_report(videos):
    report = f"# 🥗 Weekly Nutrition Trends Report\n**Generated:** {datetime.now().strftime('%B %d, %Y')}\n\n"
    report += "## Top Trending Topics (May 2026)\n"
    topics = ["Fibermaxxing", "Protein Quality + GLP-1", "Gut Health & Fermented Foods", 
              "Whole Foods Reset", "Longevity Eating", "Anti-Inflammatory Foods", 
              "Realistic What I Eat in a Day", "Personalized Nutrition"]
    for i, topic in enumerate(topics, 1):
        report += f"{i}. **{topic}**\n"
    
    report += "\n\n## Top Trending Videos\n"
    for i, v in enumerate(videos[:10], 1):
        report += f"\n{i}. **{v['title']}**\n   {v['channel']}\n   {v['url']}\n"
    return report

# ---------------- STREAMLIT APP ----------------
st.set_page_config(page_title="Supergrok Nutrition Agent", layout="wide")
st.title("🥗 Supergrok Nutrition Trends Agent")
st.caption("Automated weekly YouTube nutrition insights")

if st.button("🔄 Refresh Latest Trends", type="primary"):
    with st.spinner("Searching YouTube (this may take 15-30 seconds)..."):
        all_videos = []
        for kw in KEYWORDS[:6]:   # Limit to stay under quota
            videos = search_trending_videos(kw)
            all_videos.extend(videos)
        
        # Remove duplicates
        unique_videos = {v['video_id']: v for v in all_videos}.values()
        df = pd.DataFrame(unique_videos)
        
        st.session_state.videos_df = df
        st.session_state.report = generate_report(list(unique_videos))

if "videos_df" in st.session_state:
    df = st.session_state.videos_df
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("🎥 Top Trending Videos")
        for _, row in df.head(10).iterrows():
            st.image(row['thumbnail'], width=320)
            st.markdown(f"**{row['title']}**  \n{row['channel']}  \n[▶ Watch Video]({row['url']})")
            st.divider()
    
    with col2:
        st.subheader("📋 Summary Report")
        st.markdown(st.session_state.report)
        
        if st.button("📧 Send Report to Email"):
            success, msg = send_email(st.session_state.report)
            if success:
                st.success("✅ Report sent successfully!")
            else:
                st.error(f"Failed to send: {msg}")
else:
    st.info("👆 Click the button above to load the latest trends.")
