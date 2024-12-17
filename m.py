from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler
from googleapiclient.discovery import build
import yt_dlp
import os
import logging

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your Bot Token and API Key
TELEGRAM_BOT_TOKEN = "7503339406:AAFc1wrpNfLVYE6_uj6Kor-7YmGeY4vqcYE"
YOUTUBE_API_KEY = "AIzaSyC4tBjWm_rsa16dW5U_3Fd0jADdgKiuiko"

# Search YouTube for a song or video
def search_youtube(query):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    request = youtube.search().list(
        q=query, part="snippet", type="video", maxResults=1
    )
    response = request.execute()

    if "items" in response and len(response["items"]) > 0:
        video_id = response["items"][0]["id"]["videoId"]
        return f"https://www.youtube.com/watch?v={video_id}"
    else:
        return None

# Download video from YouTube
def download_video(url):
    ydl_opts = {
        "format": "best",
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "cookiefile": "cookies.txt",  # Path to your cookies.txt file
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except yt_dlp.utils.DownloadError as e:
        logger.error(f"Download error: {e}")
        return None

# Download audio from YouTube
def download_audio(url):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "cookiefile": "cookies.txt",  # Path to your cookies.txt file
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".m4a", ".mp3")
    except yt_dlp.utils.DownloadError as e:
        logger.error(f"Download error: {e}")
        return None

# Command: /start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Welcome to the YouTube Bot!\n\n"
        "Use /video <name> to get a video.\n"
        "Use /audio <name> to get an audio.\n"
        "Use /link <YouTube URL> to download directly as audio or video."
    )

# Helper function to send loading animation
async def send_loading_message(update: Update, context: CallbackContext):
    message = await update.message.reply_text("Loading...")
    return message

# Helper function to delete messages
async def delete_messages(context: CallbackContext, messages):
    for msg in messages:
        try:
            await msg.delete()
        except Exception as e:
            logger.error(f"Failed to delete message: {e}")

# Command: /video
async def video(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        await update.message.reply_text("Usage: /video <video name>")
        return

    query = " ".join(context.args)
    loading_message = await send_loading_message(update, context)
    messages_to_delete = [loading_message, update.message]

    url = search_youtube(query)
    if not url:
        not_found_message = await update.message.reply_text("No results found.")
        messages_to_delete.append(not_found_message)
        await delete_messages(context, messages_to_delete)
        return

    try:
        file_path = download_video(url)
        if file_path:
            with open(file_path, "rb") as video_file:
                await update.message.reply_video(video=video_file)
            os.remove(file_path)
        else:
            error_message = await update.message.reply_text("Failed to download video. Please try again.")
            messages_to_delete.append(error_message)
    except Exception as e:
        logger.error(e)
        error_message = await update.message.reply_text("An error occurred while processing your request.")
        messages_to_delete.append(error_message)

    await delete_messages(context, messages_to_delete)

# Command: /audio
async def audio(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        await update.message.reply_text("Usage: /audio <song name>")
        return

    query = " ".join(context.args)
    loading_message = await send_loading_message(update, context)
    messages_to_delete = [loading_message, update.message]

    url = search_youtube(query)
    if not url:
        not_found_message = await update.message.reply_text("No results found.")
        messages_to_delete.append(not_found_message)
        await delete_messages(context, messages_to_delete)
        return

    try:
        file_path = download_audio(url)
        if file_path:
            with open(file_path, "rb") as audio_file:
                await update.message.reply_audio(audio=audio_file)
            os.remove(file_path)
        else:
            error_message = await update.message.reply_text("Failed to download audio. Please try again.")
            messages_to_delete.append(error_message)
    except Exception as e:
        logger.error(e)
        error_message = await update.message.reply_text("An error occurred while processing your request.")
        messages_to_delete.append(error_message)

    await delete_messages(context, messages_to_delete)

# Command: /link
async def link(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        await update.message.reply_text("Usage: /link <YouTube URL>")
        return

    url = context.args[0]
    await update.message.reply_text("You provided a link. Please choose an option below:",
                                     reply_markup=InlineKeyboardMarkup([
                                         [
                                             InlineKeyboardButton("Download Audio", callback_data=f"audio|{url}"),
                                             InlineKeyboardButton("Download Video", callback_data=f"video|{url}"),
                                         ]
                                     ]))

# Callback handler for button press
async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    action, url = query.data.split("|", 1)
    loading_message = await query.message.reply_text("Loading...")

    messages_to_delete = [loading_message, query.message]

    if action == "audio":
        try:
            file_path = download_audio(url)
            if file_path:
                with open(file_path, "rb") as audio_file:
                    await query.message.reply_audio(audio=audio_file)
                os.remove(file_path)
            else:
                error_message = await query.message.reply_text("Failed to download audio. Please try again.")
                messages_to_delete.append(error_message)
        except Exception as e:
            logger.error(e)
            error_message = await query.message.reply_text("An error occurred while processing your request.")
            messages_to_delete.append(error_message)

    elif action == "video":
        try:
            file_path = download_video(url)
            if file_path:
                with open(file_path, "rb") as video_file:
                    await query.message.reply_video(video=video_file)
                os.remove(file_path)
            else:
                error_message = await query.message.reply_text("Failed to download video. Please try again.")
                messages_to_delete.append(error_message)
        except Exception as e:
            logger.error(e)
            error_message = await query.message.reply_text("An error occurred while processing your request.")
            messages_to_delete.append(error_message)

    await delete_messages(context, messages_to_delete)

# Main function
def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("video", video))
    app.add_handler(CommandHandler("audio", audio))
    app.add_handler(CommandHandler("link", link))
    app.add_handler(CallbackQueryHandler(button_handler))

    # Start the Bot
    app.run_polling()

if __name__ == "__main__":
    main()