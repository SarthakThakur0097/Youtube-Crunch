from youtube_transcript_api import YouTubeTranscriptApi

def fetch_youtube_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return transcript
    except Exception as e:
        # Handle any errors, e.g., video not found
        print(f"Error: {str(e)}")
        return None

def chunk_text(text, max_chunk_length):
    text_chunks = []
    current_chunk = ""

    for item in text:
        item_text = item['text']
        if len(current_chunk) + len(item_text) <= max_chunk_length:
            current_chunk += item_text + " "
        else:
            text_chunks.append(current_chunk.strip())
            current_chunk = item_text + " "

    if current_chunk:
        text_chunks.append(current_chunk.strip())

    return text_chunks

if __name__ == "__main__":
    # Replace with the actual video ID for testing
    video_id = "gViODEWrT0g"

    transcript_data = fetch_youtube_transcript(video_id)

    if transcript_data:
        max_chunk_length = 4000  # Adjust this as needed

        text_chunks = chunk_text(transcript_data, max_chunk_length)

        # You can print or further process the text chunks here
        for i, chunk in enumerate(text_chunks, start=1):
            print(f"Chunk {i}:\n{chunk}")
    else:
        print("Failed to retrieve the transcript data.")
