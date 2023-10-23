from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
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
    return render_template('index.html', transcript_summary='')

@views.route('/process_youtube_url', methods=['POST'])
@login_required
def process_youtube_url():
    flash("Flash test", category='success')
    # Check if the user is logged in
    if not current_user.is_authenticated:
        flash('You must be logged in to summarize a video.', category='error')
        return redirect(url_for('views.index'))

    # Receive the video ID from the form
    video_id = request.form.get('video_id')

    # Get the transcript using YouTubeTranscriptApi
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
    except Exception as e:
        # Handle errors, e.g., if the video doesn't have a transcript
        error_message = str(e)
        return jsonify({'error': error_message})

    # Check if video length exceeds 30 minutes (1800 seconds)
    last_element = transcript[-1]
    video_length_seconds = last_element['start'] + last_element['duration']
    print(video_length_seconds)
    if video_length_seconds > 1800:
        flash('Sorry, videos longer than 30 minutes cannot be summarized for free users.', category='error')
        print("Flash message triggered")
        return redirect(url_for('views.index'))

    # Process the transcript and summarize using OpenAI
    chunk_texts = [chunk['text'] for chunk in transcript]
    summarized = summarize_using_openai(chunk_texts)

    # If the user is not a premium member, increment the summary count
    if not current_user.is_premium:
        current_user.video_summary_count += 1
        db.session.commit()

    # Update the HTML template with the transcript summary
    return jsonify({'transcript_summary': summarized})


def summarize_using_openai(text_chunks):
    #openai.api_key = API_KEY
    max_chunk_length = 4000  # Adjust this as needed
    text_chunks = chunk_text(text_chunks, max_chunk_length)
    
    # Initialize a variable to store the aggregated summaries
    summaries = {}
    
    for counter, chunk in enumerate(text_chunks, start=1):
        prompt = f"Summarize and provide key insights about the following:\n'{chunk}'"
        
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=200  # Adjust max_tokens based on your desired response length
        )
        
        # Extract the summarized text from the response
        summary = response.choices[0].text.strip()
        summaries[f"Summary {counter}"] = summary
    
    return summaries

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
