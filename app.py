from flask import Flask, request, render_template, jsonify
import subprocess

app = Flask(__name__)

# Define an endpoint to serve the HTML page
@app.route('/')
def index():
    return render_template('index.html', embedded_video='', video_description='')

# Define an endpoint to receive YouTube URLs and process them
@app.route('/process_youtube_url', methods=['POST'])

# Define an endpoint to receive YouTube URLs and process them
@app.route('/process_youtube_url', methods=['POST'])
def process_youtube_url():
    # Receive the YouTube URL from the form
    youtube_url = request.form.get('youtube_url')

    # Print the YouTube URL (for debugging purposes)
    print(f"Received YouTube URL: {youtube_url}")

    try:
        # Execute the Jupyter Notebook script with the URL as an argument
        result = subprocess.run(['jupyter', 'nbconvert', '--to', 'script', 'your_notebook.ipynb'])
        result = subprocess.run(['python', 'API.ipynb', youtube_url], capture_output=True, text=True, timeout=120)
        
        # Extract the embedded video and video description from the result
        result_lines = result.stdout.strip().split('\n')
        embedded_video = result_lines[0]
        video_description = result_lines[1]

        # Return the embedded video, video description, and YouTube URL as JSON
        return jsonify({'youtube_url': youtube_url, 'embedded_video': embedded_video, 'video_description': video_description})
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Processing the URL took too long.'}), 500


if __name__ == '__main__':
    app.run(debug=True)
