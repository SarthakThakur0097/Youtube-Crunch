from flask import Flask, request, render_template, jsonify
import openai  # Import the OpenAI library
from scrape import YouTubeTranscriptScraper
from config import API_KEY
app = Flask(__name__)

# Create an instance of the YouTubeTranscriptScraper
scraper = YouTubeTranscriptScraper()
@app.route('/signin')
def signin():
    return render_template('signin.html')

@app.route('/register')
def register():
    return render_template('register.html')

# Define an endpoint to serve the HTML page
@app.route('/')
def index():
    return render_template('index.html', transcript_summary='')

# Define an endpoint to receive YouTube URLs and process them
@app.route('/process_youtube_url', methods=['POST'])
def process_youtube_url():
    # Receive the YouTube URL from the form
    youtube_url = request.form.get('youtube_url')

    # Scrape the transcript using the scraper
    transcript = scraper.scrape_youtube_transcript(youtube_url)
    chunk_texts = chunk_text(transcript, 4000)
    summarized = summarize(chunk_texts)
    
    # Update the HTML template with the transcript summary
    return jsonify({'transcript_summary': summarized})
def summarize(text_chunks):
    openai.api_key = API_KEY
    # Initialize a variable to store the aggregated summaries
    summaries = {}
    # Process each text chunk sequentially
    for counter, chunk in enumerate(text_chunks, start=1):
        # Create the prompt for the current chunk
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
    while len(text) > max_chunk_length:
        split_index = text.rfind("\n", 0, max_chunk_length)
        if split_index == -1:
            split_index = max_chunk_length
        text_chunks.append(text[:split_index])
        text = text[split_index:].strip()
    text_chunks.append(text)
    return text_chunks

if __name__ == '__main__':
    app.run(debug=True)
