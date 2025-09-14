import streamlit as st
import requests
from time import sleep
from pytubefix import YouTube
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- CONFIG ---

API_KEY = st.secrets['api_key']

#---------------temp code-----------------------------
#st.write("API key loaded:", bool(API_KEY))
#import requests

#headers = {
 #   "authorization": API_KEY
#}

#response = requests.get("https://api.assemblyai.com/v2/transcript", headers=headers)
#st.write("Status code:", response.status_code)
#st.write("Response:", response.text)


# --- UI Setup ---
st.markdown('# 📝 **Transcriber App**')
bar = st.progress(0)
st.warning('Please enter a YouTube video URL in the sidebar.')

# --- Sidebar Input ---
st.sidebar.header('Input')
with st.sidebar.form(key='my_form'):
    URL = st.text_input('Enter YouTube video URL:')
    submit_button = st.form_submit_button(label='Transcribe')

# --- Backend Logic ---
def create_session():
    session = requests.Session()
    retry = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def download_audio(url: str) -> str:
    yt = YouTube(url)
    audio_stream = yt.streams.get_audio_only()
    return audio_stream.download()

def upload_audio(file_path: str, api_key: str) -> str:
    with open(file_path, 'rb') as f:
        audio_data = f.read()

    session = create_session()
    headers = {"authorization": api_key}
    response = session.post("https://api.assemblyai.com/v2/upload", headers=headers, data=audio_data)
    response.raise_for_status()
    return response.json()['upload_url']

def request_transcription(audio_url: str, api_key: str) -> str:
    session = create_session()
    headers = {"authorization": api_key, "content-type": "application/json"}
    response = session.post("https://api.assemblyai.com/v2/transcript", json={"audio_url": audio_url}, headers=headers)
    response.raise_for_status()
    return response.json()["id"]

def get_transcription_result(transcript_id: str, api_key: str) -> dict:
    session = create_session()
    endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
    headers = {"authorization": api_key}
    while True:
        response = session.get(endpoint, headers=headers)
        response.raise_for_status()
        status = response.json()['status']
        if status == 'completed':
            return response.json()
        elif status == 'error':
            raise Exception(f"Transcription failed: {response.json().get('error')}")
        sleep(5)

def save_transcript_files(text: str, transcript_id: str, api_key: str):
    with open("yt.txt", "w", encoding="utf-8") as txt_file:
        txt_file.write(text)
    srt_endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}/srt"
    session = create_session()
    headers = {"authorization": api_key}
    srt_response = session.get(srt_endpoint, headers=headers)
    srt_response.raise_for_status()
    with open("yt.srt", "w", encoding="utf-8") as srt_file:
        srt_file.write(srt_response.text)

# --- Main Workflow ---
if submit_button and URL:
    try:
        bar.progress(10)
        mp4_path = download_audio(URL)
        bar.progress(30)
        audio_url = upload_audio(mp4_path, API_KEY)
        bar.progress(50)
        transcript_id = request_transcription(audio_url, API_KEY)
        bar.progress(70)
        transcript_data = get_transcription_result(transcript_id, API_KEY)
        bar.progress(90)
        save_transcript_files(transcript_data["text"], transcript_id, API_KEY)
        bar.progress(100)

        st.success("✅ Transcription completed!")
        st.text_area("📝 Transcript Preview", transcript_data["text"], height=300)

        with open("yt.txt", "rb") as txt_file:
            st.download_button("📥 Download Transcript", txt_file, "yt.txt", mime="text/plain")

        with open("yt.srt", "rb") as srt_file:
            st.download_button("📥 Download Subtitles (.srt)", srt_file, "yt.srt", mime="application/x-subrip")

    except Exception as e:
        st.error(f"❌ Error: {e}")
