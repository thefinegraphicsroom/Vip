import logging
import os
import subprocess
from telethon import TelegramClient, events
from telethon.tl.types import InputPeerChat
import requests
import tempfile

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Your Telegram API credentials
API_ID = '16223706'  # Replace with your own API ID
API_HASH = '2e8a2a9c6f4f46d2d40b7801e5de4e6a'  # Replace with your own API Hash
BOT_TOKEN = '7847570111:AAG9rVQTYwUgLCdpxXR-FHZI8SI8wLPerSA'  # Replace with your own Bot Token

# FFmpeg path (adjust as necessary)
FFMPEG_PATH = "/usr/bin/ffmpeg"  # This should work if FFmpeg is installed

# Telegram Client Setup
client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Your Telegram group chat details (replace with your group chat)
GROUP_ID = -1002342721193  # Replace with your group chat ID

# Function to download a YouTube video using yt-dlp
def download_video_with_ytdlp(video_url):
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        download_path = temp_file.name

        # Run yt-dlp command to download the video
        command = [
            "yt-dlp", 
            "-o", download_path,  # Output file path
            "--format", "bestaudio[ext=webm]",  # Download only the best audio format
            video_url
        ]
        subprocess.run(command, check=True)

        return download_path
    except Exception as e:
        logger.error(f"Error downloading video with yt-dlp: {e}")
        return None

# Command handler for /play <song_name>
@client.on(events.NewMessage(pattern='/play (.+)'))
async def play_song(event):
    query = event.pattern_match.group(1)
    await event.reply(f"Searching for '{query}' on YouTube...")

    # Check if the user is in the group
    user = await event.get_sender()
    is_member = await is_user_in_group(user.id)

    if not is_member:
        await event.reply("Please add me to your group and turn on the voice chat.")
        return

    # Search YouTube manually (replace this with a proper search if needed)
    video_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"

    # Download video with yt-dlp
    file_path = download_video_with_ytdlp(video_url)
    if file_path:
        await event.reply("Video downloaded. Streaming now...")
        await stream_to_voice_chat(file_path, event.chat_id)
        os.remove(file_path)  # Delete the video after streaming
        await event.reply("Video streaming complete, file deleted.")
    else:
        await event.reply("Error occurred while downloading the video.")

# Check if the user is a member of the group
async def is_user_in_group(user_id):
    try:
        group = await client.get_entity(GROUP_ID)
        participants = await client.get_participants(group)
        return any(user.id == user_id for user in participants)
    except Exception as e:
        logger.error(f"Error checking user membership: {e}")
        return False

# Stream the downloaded video/audio to voice chat
async def stream_to_voice_chat(file_path, chat_id):
    try:
        logger.info(f"Streaming {file_path} to the voice chat...")

        # Use FFmpeg to process the video/audio stream
        process = subprocess.Popen(
            [FFMPEG_PATH, "-re", "-i", file_path, "-f", "opus", "-ar", "48000", "-ac", "2", "-"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        # Placeholder: Handle sending the audio to Telegram (not implemented directly)
        logger.info("Audio/video streaming started.")
        # Note: Telethon does not natively support streaming audio to a voice chat.
        # Use Pyrogram or another library if direct streaming is required.

    except Exception as e:
        logger.error(f"Error while streaming to voice chat: {e}")

# Run the bot
client.run_until_disconnected()
