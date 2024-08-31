import streamlit as st
import requests
from datetime import datetime
from collections import Counter
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import hashlib
import sqlite3
import asyncio
import pandas as pd
import streamlit_cookies_manager as scm

async def async_sleep(seconds):
    await asyncio.sleep(seconds)

# Initialize cookies manager
cookies = scm.CookieManager()

# Login & Security
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

# DB for Passwords and Journal Entries
conn = sqlite3.connect('data.db')
c = conn.cursor()

def create_usertable():
    c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT UNIQUE, password TEXT)')

def add_userdata(username, password):
    c.execute('INSERT INTO userstable(username,password) VALUES (?,?)', (username, password))
    conn.commit()

def login_user(username, password):
    c.execute('SELECT * FROM userstable WHERE username = ? AND password = ?', (username, password))
    data = c.fetchall()
    return data

def view_all_users():
    c.execute('SELECT * FROM userstable')
    data = c.fetchall()
    return data

def create_journal_table():
    c.execute('CREATE TABLE IF NOT EXISTS journalstable(username TEXT, note TEXT, mood TEXT, date TIMESTAMP)')
    conn.commit()

def add_journal_entry(username, note, mood, date):
    c.execute('INSERT INTO journalstable(username, note, mood, date) VALUES (?, ?, ?, ?)', (username, note, mood, date))
    conn.commit()

def get_journal_entries(username):
    c.execute('SELECT note, mood, date FROM journalstable WHERE username = ?', (username,))
    data = c.fetchall()
    return [(note, mood, datetime.strptime(date, '%Y-%m-%d %H:%M:%S.%f')) for note, mood, date in data]

def choose_resources(mood, num_resources=3):
    resources = {
        'anger': [
            {"title": "Anger Management Techniques", "description": "Learn how to manage and control your anger.", "url": "https://www.mayoclinic.org/healthy-lifestyle/adult-health/in-depth/anger-management/art-20045434"},
            {"title": "Meditation for Anger", "description": "Meditation practices to help calm your mind.", "url": "https://example.com/meditation-anger"},
            {"title": "Therapy for Anger Issues", "description": "Find a therapist to help with anger issues.", "url": "https://example.com/therapy-anger"}
        ],
        'fear': [
            {"title": "Overcoming Fear", "description": "Techniques to overcome your fears.", "url": "https://www.psychologytoday.com/intl/blog/dysfunction-interrupted/202101/the-7-skills-necessary-overcome-fear"},
            {"title": "Fear and Anxiety Management", "description": "Learn to manage fear and anxiety effectively.", "url": "https://example.com/fear-anxiety-management"},
            {"title": "Therapy for Fear Issues", "description": "Find a therapist to help with fear issues.", "url": "https://example.com/therapy-fear"}
        ],
        'joy': [
            {"title": "Maintaining Happiness", "description": "Tips to maintain and increase your happiness.", "url": "https://www.psychologytoday.com/us/blog/click-here-happiness/201801/how-be-happy-23-ways-be-happier"},
            {"title": "Joyful Living", "description": "Strategies for a joyful life.", "url": "https://example.com/joyful-living"},
            {"title": "Sharing Joy", "description": "Learn how to spread joy to others.", "url": "https://example.com/sharing-joy"}
        ],
        'love': [
            {"title": "Building Loving Relationships", "description": "Tips to build and maintain loving relationships.", "url": "https://www.helpguide.org/articles/relationships-communication/relationship-help.htm"},
            {"title": "Love and Connection", "description": "Enhancing your connections with loved ones.", "url": "https://example.com/love-connection"},
            {"title": "Therapy for Relationship Issues", "description": "Find a therapist to help with relationship issues.", "url": "https://example.com/therapy-relationship"}
        ],
        'sadness': [
            {"title": "Coping with Sadness", "description": "Techniques to cope with sadness and depression.", "url": "https://www.wikihow.com/Overcome-Sadness"},
            {"title": "Support for Depression", "description": "Resources and support for dealing with depression.", "url": "https://example.com/support-depression"},
            {"title": "Therapy for Sadness", "description": "Find a therapist to help with sadness and depression.", "url": "https://example.com/therapy-sadness"}
        ],
        'surprise': [
            {"title": "Dealing with Surprises", "description": "Learn how to handle unexpected surprises.", "url": "https://www.successconsciousness.com/blog/tips-for-life/tips-for-dealing-with-surprises-and-unexpected-events/"},
            {"title": "Embracing the Unexpected", "description": "Strategies to embrace and enjoy surprises.", "url": "https://example.com/embracing-unexpected"},
            {"title": "Coping with Change", "description": "Techniques to cope with sudden changes in life.", "url": "https://example.com/coping-change"}
        ]
    }

    return resources.get(mood, [])[:num_resources]

def choose_support(index):
    support_recommendations = [
        {"title": "Talk to a Therapist", "description": "Find a licensed therapist to talk about your feelings.", "url": "https://example.com/find-therapist"},
        {"title": "Support Groups", "description": "Join support groups to share and listen to others' experiences.", "url": "https://example.com/support-groups"},
        {"title": "Emergency Hotlines", "description": "Reach out to emergency hotlines if you're in immediate need of help.", "url": "https://example.com/emergency-hotlines"}
    ]

    return support_recommendations[index % len(support_recommendations)]

def main():
    pages = {
        "Home": page_home,
        "Journal": page_journal,
        "Previous Journals": page_previous_journals,
        "Analytics": page_analytics,
        "Resources": page_resources,
        "Sign Up": page_signup,
    }

    if "page" not in st.session_state:
        st.session_state.update({
            "page": "Home",
            "username": "",
            "notes": [],
            "placeholder_text": "...",
            "logged_in": False
        })

    create_usertable()
    create_journal_table()

    with st.sidebar:
        st.title("better.me")
        if st.button("🏠 Home"): st.session_state.page = "Home"
        if st.button("📝 Journal"): st.session_state.page = "Journal"
        if st.button("📕 Previous Journals"): st.session_state.page = "Previous Journals"
        if st.button("📊 Analytics"): st.session_state.page = "Analytics"
        if st.button("📚 Recommendations"): st.session_state.page = "Resources"

    if st.session_state.logged_in:
        pages[st.session_state.page]()
    else:
        page_home()

    # Update cookies
    cookies.save()

def page_home():
    st.title("🏠 Home")
    st.subheader("Welcome to Better.Me. Please login below to access your personal AI powered diary.")
    username = st.text_input('Username')
    password = st.text_input("Password", type="password")

    if st.button('Login', key='login_button'):
        hashed_pswd = make_hashes(password)
        result = login_user(username, check_hashes(password, hashed_pswd))
        if result:
            st.success(f"Logged In as {username}")
            st.session_state.page = "Journal"
            st.session_state.username = username
            st.session_state.notes = get_journal_entries(username)
            st.session_state.logged_in = True

            # Set cookies
            cookies["logged_in"] = True
            cookies["username"] = username
            st.rerun()
        else:
            st.warning("Incorrect Username/Password")

    st.write('Not a member? Sign up from the button below')

    if st.button('Sign Me Up', key='signup_button'):
        st.session_state.page = "Sign Up"
        st.rerun()

def page_signup():
    st.title("Sign Up")

    new_username = st.text_input('New username', key="new_username")
    new_password = st.text_input("New password", type="password", key="new_password")

    if st.button('Sign Up', key='signup_submit_button'):
        if not new_username or not new_password:
            st.warning("Please input a username and/or password!")
        else:
            try:
                add_userdata(new_username, make_hashes(new_password))
                st.success("You have successfully created an account")
                st.session_state.page = "Home"
                st.rerun()
            except sqlite3.IntegrityError:
                st.warning("Username already exists")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

def page_journal():
    st.title("📝 Write a note")
    API_URL = "https://api-inference.huggingface.co/models/mrm8488/t5-base-finetuned-emotion"
    API_URL2 = "https://api-inference.huggingface.co/models/vibhorag101/roberta-base-suicide-prediction-phr-v2"

    API_TOKEN = "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"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}

    def query(payload, api_url):
        response = requests.post(api_url, headers=headers, json=payload)
        if response.ok:
            return response.json()
        else:
            st.error(f"Error making API request to {api_url}: {response.status_code} - {response.reason}")
            return None

    with st.form(key='my_form', clear_on_submit=True):
        note = st.text_area(label='Dear Diary, ', height=300)
        submit_button = st.form_submit_button(label='Submit')

        if submit_button and note:
            # Mood Prediction
            mood_output = query({"inputs": note}, API_URL)
            if mood_output:
                mood = mood_output[0].get('generated_text', 'Unknown')
                st.info(f"Mood Prediction: {mood}")
            else:
                st.error("Error retrieving mood prediction")

            # Suicide Prediction
            suicide_output = query({"text": note}, API_URL2)
            if suicide_output:
                suicide_prediction = suicide_output[0].get("label", "Unknown")
                st.info(f"Suicide Prediction: {suicide_prediction}")
                if suicide_prediction == "LABEL_1":
                    st.warning("Suicide warning detected. Providing support resources.")
                    s1, s2, s3 = choose_support(0), choose_support(1), choose_support(2)
                    st.header(s1['title'])
                    st.write(s1['description'])
                    st.markdown("[Learn More](%s)" % s1['url'], unsafe_allow_html=True)
                    st.header(s2['title'])
                    st.write(s2['description'])
                    st.markdown("[Learn More](%s)" % s2['url'], unsafe_allow_html=True)
                    st.header(s3['title'])
                    st.write(s3['description'])
                    st.markdown("[Learn More](%s)" % s3['url'], unsafe_allow_html=True)
                else:
                    add_journal_entry(st.session_state.username, note, mood, datetime.now())
                    st.session_state.notes = get_journal_entries(st.session_state.username)
                    st.success("Note added successfully!")
                    # Provide resources based on predicted mood
                    resources = choose_resources(mood, 3)
                    if resources:
                        st.title("Resources for Mood")
                        for resource in resources:
                            st.header(resource['title'])
                            st.write(resource['description'])
                            st.markdown("[Learn More](%s)" % resource['url'], unsafe_allow_html=True)
            else:
                st.error("Error retrieving suicide prediction. Please try again later.")






def page_previous_journals():
    st.title("📕 Previous Notes")

    if st.session_state.notes:
        notes_df = pd.DataFrame(st.session_state.notes, columns=['Note', 'Mood', 'Date'])
        st.dataframe(notes_df)
    else:
        st.write("You have no previous notes.")


def page_analytics():
    st.title("📊 Analytics")

    notes = st.session_state.notes

    if not notes:
        st.write("No data to display.")
        return

    mood_counts = Counter([mood for _, mood, _ in notes])
    dates = [date for _, _, date in notes]
    moods = [mood for _, mood, _ in notes]
    notes_text = [note for note, _, _ in notes]

    df = pd.DataFrame({
        'date': dates,
        'mood': moods,
        'note': notes_text
    })

    mood_summary = pd.DataFrame(mood_counts.items(), columns=['mood', 'count'])

    st.subheader('Mood Summary')
    st.dataframe(mood_summary)

    st.subheader('Mood Over Time')
    fig = px.line(df, x='date', y='mood', title='Mood Over Time')
    st.plotly_chart(fig)

    st.subheader('Mood Distribution')
    fig2 = px.pie(mood_summary, values='count', names='mood', title='Mood Distribution')
    st.plotly_chart(fig2)

def page_resources():
    st.title("📚 Resources")
    col1, col2, col3 = st.columns(3)

    # Example mood, change based on actual logic
    mood = "anger"

    resources = choose_resources(mood, 3)

    with col1:
        if len(resources) > 0:
            st.header(resources[0]['title'])
            st.write(resources[0]['description'])
            st.markdown("[Learn More](%s)" % resources[0]['url'], unsafe_allow_html=True)

    with col2:
        if len(resources) > 1:
            st.header(resources[1]['title'])
            st.write(resources[1]['description'])
            st.markdown("[Learn More](%s)" % resources[1]['url'], unsafe_allow_html=True)

    with col3:
        if len(resources) > 2:
            st.header(resources[2]['title'])
            st.write(resources[2]['description'])
            st.markdown("[Learn More](%s)" % resources[2]['url'], unsafe_allow_html=True)

    st.markdown("---")
    st.title("Recommended Support")

    col4, col5, col6 = st.columns(3)

    s1, s2, s3 = choose_support(0), choose_support(1), choose_support(2)
    with col4:
        st.header(s1['title'])
        st.write(s1['description'])
        st.markdown("[Learn More](%s)" % s1['url'], unsafe_allow_html=True)

    with col5:
        st.header(s2['title'])
        st.write(s2['description'])
        st.markdown("[Learn More](%s)" % s2['url'], unsafe_allow_html=True)

    with col6:
        st.header(s3['title'])
        st.write(s3['description'])
        st.markdown("[Learn More](%s)" % s3['url'], unsafe_allow_html=True)

if __name__ == "__main__":
    main()

