from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user, login_required
from . import db
import openai  # Import the OpenAI library
from config import API_KEY
from .models import User
from youtube_transcript_api import YouTubeTranscriptApi

views = Blueprint("views", __name__)

@views.route('/signin')
def signin():
    return render_template('signin.html')

@views.route('/')
def index():
    user_data = None  # Initialize user_data to None

    # Check if the user is authenticated (logged in)
    if current_user.is_authenticated:
        # Fetch user-specific data like video_summary_limit and video_summary_count
        user_data = {
            'video_summary_count': (5-current_user.video_summary_count)
        }
    
    return render_template('index.html', user_data=user_data)


@views.route('/pricing')
def pricing():
    return render_template('pricing.html')

@views.route('/test_flash', methods=['POST'])
def test_flash():
    print("Inside test flash")
    flash('This is a test flash message.', category='success')
    return render_template('pricing.html') 


from datetime import datetime

@views.route('/process_youtube_url', methods=['POST'])
@login_required
def process_youtube_url():
    response_data = {'messages': [], 'transcript_summary': '', 'summaries_left': None}

    youtube_url = request.form.get('youtube_url')

    if not validate_youtube_url(youtube_url):
        response_data['messages'].append({'text': 'Invalid YouTube URL. Please enter a valid YouTube video URL.', 'category': 'error'})
        return jsonify(response_data), 400  # Bad request status

    video_id = extract_video_id(youtube_url)

    transcript = fetch_transcript(video_id)

    if not transcript:
        response_data['messages'].append({'text': 'Error fetching transcript.', 'category': 'error'})
        return jsonify(response_data), 400

    # Assuming this is a function you've defined to check the video length.
    if is_video_too_long(transcript):  
        response_data['messages'].append({'text': 'Sorry, videos longer than 30 minutes cannot be summarized for free users.', 'category': 'error'})
        return jsonify(response_data), 400

    # Assuming you have a method to check if the user has reached their summary limit.
    if has_reached_summary_limit():  
        response_data['messages'].append({'text': 'You have reached your monthly limit of summaries.', 'category': 'error'})
        return jsonify(response_data), 400

    summarized = summarize_transcript(transcript)
    if summarized:
        response_data['transcript_summary'] = summarized

        # Increment the user's summary count after a successful summary operation
        current_user.video_summary_count += 1
        db.session.commit()

        # Retrieve the updated summary count
        response_data['summaries_left'] = current_user.video_summary_count
    else:
        response_data['messages'].append({'text': 'Error summarizing the video.', 'category': 'error'})
        return jsonify(response_data), 500  # Internal server error status

    return jsonify(response_data)

def get_updated_summary_count():
    # Make sure the user is authenticated before trying to access their information
    if current_user.is_authenticated:
        return current_user.video_summary_count
    else:
        # Handle the case for non-authenticated users if necessary
        return None  # Or you could redirect them to login, raise an error, etc.

def increment_summary_count():
    if current_user.is_authenticated:
        # Increment the summary count
        current_user.video_summary_count += 1
        # Commit changes to the database
        db.session.commit()

def fetch_transcript(video_id):
    try:
        return YouTubeTranscriptApi.get_transcript(video_id)
    except Exception as e:
        flash('Error fetching transcript: ' + str(e), category='error')
        return None

def is_video_too_long(transcript):
    last_element = transcript[-1]
    video_length_seconds = last_element['start'] + last_element['duration']
    return video_length_seconds > 1800

def has_reached_summary_limit():
    return not current_user.is_premium and current_user.video_summary_count >= 5

def summarize_transcript(transcript):
    chunk_texts = [chunk['text'] for chunk in transcript]
    return summarize(chunk_texts)

def increment_summary_count():
    if not current_user.is_premium:
        current_user.video_summary_count += 1
        db.session.commit()


# Define the validate_youtube_url and extract_video_id functions
# Define the validate_youtube_url and extract_video_id functions
import re

def validate_youtube_url(url):
    # Regular expression for a YouTube URL
    youtube_url_regex = r'^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+$'
    return bool(re.match(youtube_url_regex, url, re.IGNORECASE))

def extract_video_id(url):
    video_id_regex = r'(?:\/|v=)([a-zA-Z0-9_-]{11})(?:\?|&|$)'
    match = re.search(video_id_regex, url)
    return match.group(1) if match else None

def summarize(text_chunks):
    openai.api_key = API_KEY
    max_chunk_length = 4000  # Adjust this as needed
    text_chunks = chunk_text(text_chunks, max_chunk_length)
    
    # Initialize a variable to store the aggregated summaries
    summaries = {}
    final_summary = ""
    for counter, chunk in enumerate(text_chunks, start=1):
        prompt = f"Summarize and provide key insights about the following:\n'{chunk}'"
        
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=200  # Adjust max_tokens based on your desired response length
        )
        
        # Extract the summarized text from the response
        summary = response.choices[0].text.strip()
        
        final_summary = final_summary+"\n\n"+summary
    
    return final_summary

def chunk_text(text, max_chunk_length):
    text_chunks = []
    current_chunk = ""

    for item in text:
        item_text = item
        if len(current_chunk) + len(item_text) <= max_chunk_length:
            current_chunk += item_text + " "
        else:
            text_chunks.append(current_chunk.strip())
            current_chunk = item_text + " "

    if current_chunk:
        text_chunks.append(current_chunk.strip())

    return text_chunks
