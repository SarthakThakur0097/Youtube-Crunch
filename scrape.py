import os
import time
import sys
from selenium import webdriver

class YouTubeTranscriptScraper:
    def __init__(self):
        # Add the Chromedriver executable to the PATH (separate with a semicolon)
        os.environ['PATH'] += r";C:\Users\Sarthak\Drivers\Selenium Drivers"
        self.driver = webdriver.Chrome()

    def scrape_youtube_transcript(self, youtube_url):
        self.driver.get(youtube_url)

        # Wait for the page to load (you may adjust the wait time as needed)
        self.driver.implicitly_wait(20)

        # Find the "Dismiss" button by its ID
        dismiss_button = self.driver.find_element_by_id('dismiss-button')

        # Click the "Dismiss" button
        dismiss_button.click()

        # Find the ellipsis button (three dots) by CSS selector
        ellipsis_button = self.driver.find_element_by_css_selector('button[aria-label="More actions"]')

        time.sleep(2)

        # Use JavaScript to click the ellipsis button
        self.driver.execute_script("arguments[0].click();", ellipsis_button)

        # Wait for a moment to ensure the menu options appear (you can adjust the wait time)
        time.sleep(2)

        # Find and click the "Show transcript" button by XPath
        transcript_button = self.driver.find_element_by_xpath("//yt-formatted-string[text()='Show transcript']")
        transcript_button.click()

        # Wait for a moment (you can adjust the wait time)
        time.sleep(2)

        transcript_button_2 = self.driver.find_element_by_css_selector('button[aria-label="Show transcript"][title=""]')
        transcript_button_2.click()

        # Wait for a moment (you can adjust the wait time)
        time.sleep(2)

        # Find the container element for the transcript section
        transcript_section_container = self.driver.find_element_by_css_selector('ytd-transcript-segment-list-renderer')

        # Find all the transcript segments
        transcript_segments = transcript_section_container.find_elements_by_css_selector('ytd-transcript-segment-renderer')

        # Initialize a list to store timestamp-text pairs
        timestamp_text_pairs = []

        # Iterate through the transcript segments and extract timestamp and text
        for segment in transcript_segments:
            timestamp = segment.find_element_by_css_selector('div.segment-timestamp').text.strip()
            text = segment.find_element_by_css_selector('yt-formatted-string.segment-text').text.strip()
            timestamp_text_pairs.append((timestamp, text))

        # Scroll down to load more transcript segments
        self.driver.execute_script("arguments[0].scrollIntoView();", transcript_segments[-1])

        # Add a delay to allow time for the additional segments to load
        time.sleep(2)  # You can adjust the sleep duration as needed

        # Extract the newly loaded transcript segments
        new_transcript_segments = transcript_section_container.find_elements_by_css_selector('ytd-transcript-segment-renderer')

        # Get the transcript with timestamps
        transcript = self.transcript_without_timestamps(new_transcript_segments)
        print(transcript)
        return transcript

    def transcript_with_timestamps(self, new_transcript_segments):
        # Initialize a list to store timestamp-text pairs
        timestamp_text_pairs = []

        # Iterate through the new transcript segments and extract timestamp and text
        for segment in new_transcript_segments:
            timestamp = segment.find_element_by_css_selector('div.segment-timestamp').text.strip()
            text = segment.find_element_by_css_selector('yt-formatted-string.segment-text').text.strip()
            timestamp_text_pairs.append((timestamp, text))

        # Process and return the transcript with timestamps
        formatted_transcript = ""
        for timestamp, text in timestamp_text_pairs:
            formatted_transcript += f"{timestamp} {text}\n"

        return formatted_transcript

    def transcript_without_timestamps(self, transcript_segments):
        # Initialize a list to store text without timestamps
        text_without_timestamps = []

        # Iterate through the transcript segments and extract text only
        for segment in transcript_segments:
            text = segment.find_element_by_css_selector('yt-formatted-string.segment-text').text.strip()
            text_without_timestamps.append(text)

        # Join the text without timestamps into a single string
        transcript_text = "\n".join(text_without_timestamps)

        return transcript_text

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python scrape.py <YouTube_URL>")
        sys.exit(1)

    youtube_url = sys.argv[1]
    
    # Create an instance of the scraper
    scraper = YouTubeTranscriptScraper()
    
    # Scrape the transcript
    transcript = scraper.scrape_youtube_transcript(youtube_url)
    
    # Print the transcript
    print(transcript)
    
    # Quit the WebDriver
    scraper.driver.quit()
