from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from googleapiclient.discovery import build
import youtube_dl
import os
import logging

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your YouTube API Key
YOUTUBE_API_KEY = 'AIzaSyC4tBjWm_rsa16dW5U_3Fd0jADdgKiuiko'

# YouTube Search Function
def search_youtube(query):
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    request = youtube.search().list(
        q=query,
        part='snippet',
        type='video',
        maxResults=1
    )
    response = request.execute()
    if 'items' in response and len(response['items']) > 0:
        video_id = response['items'][0]['id']['videoId']
        return f'https://www.youtube.com/watch?v={video_id}'
    else:
        return None

# Download Function
def download_audio(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info).replace('.webm', '.mp3')

# Play Command
def play(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if len(context.args) == 0:
        update.message.reply_text('Usage: /play <song name>')
        return

    query = ' '.join(context.args)
    update.message.reply_text(f'Searching for "{query}" on YouTube...')
    url = search_youtube(query)

    if not url:
        update.message.reply_text('No results found for your query.')
        return

    update.message.reply_text('Downloading audio...')
    try:
        file_path = download_audio(url)
        update.message.reply_audio(audio=open(file_path, 'rb'))
        os.remove(file_path)
    except Exception as e:
        logger.error(e)
        update.message.reply_text('An error occurred while processing your request.')

# Start Command
def start(update: Update, context: CallbackContext):
    update.message.reply_text('Hi! Send /play <song name> to search and play music.')

# Main Function
def main():
    TOKEN = '7847570111:AAG9rVQTYwUgLCdpxXR-FHZI8SI8wLPerSA'
    updater = Updater(TOKEN)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('play', play))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
    