from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user, login_required
from . import db
import openai  # Import the OpenAI library
from config import API_KEY
from .models import User
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
import boto3
from functools import wraps
from flask import request, jsonify, redirect, url_for
from flask_login import current_user
import os  
import base64
from botocore.exceptions import BotoCoreError, ClientError
# Configure your Amazon Polly settings
aws_access_key_id = 'AKIAVO6ECS2UOP7HMT3F'
aws_secret_access_key = 'xOCb3DePB0fzDrjcseOAbCuzvmZUMSRXnytwlgkT'
aws_region_name = 'us-east-1'  # Change to your desired region

# Initialize Amazon Polly client
polly = boto3.client('polly', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name=aws_region_name)


def login_required_ajax(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                response = jsonify({
                    'status': 'fail',
                    'message': 'Authentication required.'
                })
                return response, 401
            else:
                return redirect(url_for('auth.login'))  # or wherever your login route is named
        return f(*args, **kwargs)
    return decorated_function

views = Blueprint("views", __name__)
MAX_SUMMARIES_PER_MONTH = 10

@views.route('/signin')
def signin():
    return render_template('signin.html')

@views.route('/')
def index():
    user_data = None
    if current_user.is_authenticated:
        user_data = {
            'video_summary_count': (5-current_user.video_summary_count)
        }

    # Path to your hardcoded audio file within the audio directory
    path_to_audio_file = os.path.join('audio', 'hardcoded_audio.mp3')
    audio_base64 = ""
    try:
        # Read the audio file and encode it to base64
        with open(path_to_audio_file, 'rb') as audio_file:
            audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')
    except IOError as e:
        flash('Error loading audio file.', 'error')

    # Pass the base64 audio data to the template
    return render_template('index.html', user_data=user_data, audio_data=audio_base64)

@""" views.route('/')
def index():
    user_data = None  # Initialize user_data to None

    # Check if the user is authenticated (logged in)
    if current_user.is_authenticated:
        # Fetch user-specific data like video_summary_limit and video_summary_count
        user_data = {
            'video_summary_count': (5-current_user.video_summary_count)
        }
    
    return render_template('index.html', user_data=user_data) """

@views.route('/pricing')
def pricing():
    return render_template('pricing.html')
def synthesize_speech(text):
    # Initialize the Polly client
    polly_client = boto3.client('polly', region_name='us-east-1')  # Replace with your AWS region

    # Use Polly to synthesize text into speech
    response = polly_client.synthesize_speech(
        Text=text,
        OutputFormat='mp3',  # You can choose other formats like 'ogg_vorbis', 'pcm', etc.
        VoiceId='Joanna'  # You can choose different voices
    )

    # Save the speech output to a file or return it as a response
    return response['AudioStream'].read()

# Modify the generate_audio function to accept a filename parameter
def generate_audio(text, filename='output.mp3'):
    try:
        # Assume polly is a properly configured Polly client
        response = polly.synthesize_speech(
            Text=text,
            OutputFormat='mp3',
            VoiceId='Joanna'
        )

        # Check if the response has an audio stream
        if 'AudioStream' in response:
            # Define the path where you want to save the audio file
            audio_file_path = os.path.join('audio', filename)

            # Write the audio stream to the file
            with open(audio_file_path, 'wb') as file:
                file.write(response['AudioStream'].read())
            
            print(f'Audio file {audio_file_path} written successfully.')

            # Return the path to the saved audio file
            return audio_file_path
        else:
            print('No audio stream in response.')
            return None  # Indicate failure

    except (BotoCoreError, ClientError) as e:
        print('Error generating audio:', str(e))
        return None  # Indicate failure


@views.route('/process_youtube_url', methods=['POST'])
@login_required
def process_youtube_url():
    response_data = {
        'messages': [],
        'transcript_summary': '',
        'summaries_left': None,
        'audio_base64': None  # Use base64 audio data string instead of URL
    }

    youtube_url = request.form.get('youtube_url')
    video_id = extract_video_id(youtube_url)
    transcript = fetch_transcript(video_id)

    if not transcript:
        response_data['messages'].append({'text': 'Error fetching transcript.', 'category': 'error'})
        return jsonify(response_data), 400

    if is_video_too_long(transcript):
        response_data['messages'].append(
            {'text': 'Sorry, videos longer than 30 minutes cannot be summarized for free users.', 'category': 'error'})
        return jsonify(response_data), 400

    if has_reached_summary_limit():
        response_data['messages'].append({'text': 'You have reached your monthly limit of summaries.', 'category': 'error'})
        return jsonify(response_data), 400

    summarized = summarize_transcript(transcript)


    if summarized:
        response_data['transcript_summary'] = summarized

        # Path to your hardcoded audio file within the audio directory
        path_to_audio_file = os.path.join('audio', 'hardcoded_audio.mp3')

        try:
            # Read the audio file and encode it to base64
            with open(path_to_audio_file, 'rb') as audio_file:
                audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')

            # Provide the audio data as base64 string to the client
            response_data['audio_base64'] = audio_base64

            # Increment the user's summary count after a successful summary operation
            current_user.video_summary_count += 1
            db.session.commit()

            # Retrieve the updated summary count
            response_data['summaries_left'] = current_user.video_summary_count

        except IOError as e:
            # If the file is not found or cannot be read, send an appropriate error message
            response_data['messages'].append({'text': 'Error loading audio file.', 'category': 'error'})
            return jsonify(response_data), 500

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


# Define the validate_youtube_url and extract_video_id functions
# Define the validate_youtube_url and extract_video_id functions
import re

def is_valid_youtube_url(url):
    # Parse the URL
    parsed_url = urlparse(url)
    
    # Check if the hostname is 'www.youtube.com' or 'youtube.com'
    if parsed_url.netloc == 'www.youtube.com' or parsed_url.netloc == 'youtube.com':
        # Check if the path starts with '/watch'
        if parsed_url.path.startswith('/watch'):
            # Parse the query parameters
            query_params = parse_qs(parsed_url.query)
            
            # Check if 'v' key is present in the query parameters
            if 'v' in query_params:
                return True
    
    return False


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
        
        final_summary = final_summary+summary+"\n\n"
    
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
