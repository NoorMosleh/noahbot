from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext
import yt_dlp
import os
import datetime

TOKEN = '7068988594:AAE_hbJjg7oOLc-RdNJEOjIxjpers9ejjVc'

user_state = {}

async def start(update: Update, context: CallbackContext):
    keyboard = [
        [
            InlineKeyboardButton("TikTok", callback_data='source_tiktok'),
            InlineKeyboardButton("YouTube", callback_data='source_youtube'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('مرحبًا! اختر مصدر الفيديو:', reply_markup=reply_markup)

async def source_choice(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_state[query.from_user.id] = {'source': query.data}

    if query.data == 'source_tiktok':
        await query.edit_message_text('أرسل لي رابط فيديو TikTok لتحميله بأعلى جودة.')
    elif query.data == 'source_youtube':
        await query.edit_message_text('أرسل لي رابط فيديو YouTube لعرض الجودات المتاحة.')

async def download_video(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    video_url = update.message.text

    if user_id not in user_state or 'source' not in user_state[user_id]:
        await update.message.reply_text('يرجى اختيار مصدر الفيديو أولاً باستخدام الأمر /start.')
        return

    source = user_state[user_id]['source']

    if source == 'source_tiktok':
        await download_tiktok_video(update, context, video_url)
    elif source == 'source_youtube':
        await list_youtube_qualities(update, context, video_url)

async def download_tiktok_video(update: Update, context: CallbackContext, video_url: str):
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        video_path = f'downloaded_tiktok_{timestamp}.mp4'

        ydl_opts = {
            'format': 'best',
            'outtmpl': video_path,
            'socket_timeout': 60
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        if os.path.exists(video_path):
            with open(video_path, 'rb') as video_file:
                await update.message.reply_video(video=InputFile(video_file))
            os.remove(video_path)
        else:
            await update.message.reply_text('لم أتمكن من تحميل الفيديو. حاول مرة أخرى.')
    except Exception as e:
        await update.message.reply_text(f'حدث خطأ أثناء محاولة تحميل الفيديو: {e}')

async def list_youtube_qualities(update: Update, context: CallbackContext, video_url: str):
    try:
        ydl_opts = {
            'listformats': True,
            'socket_timeout': 60
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(video_url, download=False)

        formats = result.get('formats', [])
        keyboard = []
        for f in formats:
            if f['ext'] == 'mp4':  # حصر التنسيقات إلى MP4 فقط
                keyboard.append([InlineKeyboardButton(f"{f['format']}", callback_data=f"{video_url}|{f['format_id']}")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('اختر جودة الفيديو التي ترغب في تحميلها:', reply_markup=reply_markup)
    except Exception as e:
        await update.message.reply_text(f'حدث خطأ أثناء محاولة جلب الجودات: {e}')

async def download_youtube_video(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    video_url, format_id = query.data.split('|')
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        video_path = f'downloaded_youtube_{timestamp}.mp4'

        ydl_opts = {
            'format': f'{format_id}/bestvideo+bestaudio',  # تحميل أفضل جودة للفيديو مع الصوت
            'outtmpl': video_path,
            'socket_timeout': 60
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        if os.path.exists(video_path):
            with open(video_path, 'rb') as video_file:
                await query.message.reply_video(video=InputFile(video_file))
            os.remove(video_path)
        else:
            await query.message.reply_text('لم أتمكن من تحميل الفيديو. حاول مرة أخرى.')
    except Exception as e:
        await query.message.reply_text(f'حدث خطأ أثناء محاولة تحميل الفيديو: {e}')

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(source_choice, pattern='^source_'))
    application.add_handler(CallbackQueryHandler(download_youtube_video, pattern=r'^https?://.+\|'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    application.run_polling()

if __name__ == '__main__':
    main()
