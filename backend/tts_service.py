# File: backend/tts_service.py
import streamlit as st  # st.error, st.warning
import io
import os
from urllib.parse import unquote
from gtts import gTTS
from backend.supabase_client import supabase

# Đặt tên bucket của bạn
QUESTION_AUDIO_BUCKET = "question_audio"


def generate_and_upload_tts(text_content: str, question_id: str):
    """
    Tạo file âm thanh MP3 từ text, upload lên Storage và trả về URL.
    (Đã chuyển từ crud_utils sang đây để worker có thể gọi)
    """
    if not text_content:
        return None

    try:
        # 1. Tạo file MP3 trong bộ nhớ
        tts = gTTS(text=text_content, lang='vi', slow=False)
        mp3_buffer = io.BytesIO()
        tts.write_to_fp(mp3_buffer)
        mp3_buffer.seek(0)  # Đưa con trỏ về đầu file

        file_content = mp3_buffer.getvalue()

        # 2. Upload lên Supabase Storage
        storage_path = f"question_tts_{question_id}.mp3"

        # Xóa file cũ nếu có (upsert=True)
        supabase.storage.from_(QUESTION_AUDIO_BUCKET).upload(
            path=storage_path,
            file=file_content,
            file_options={"content-type": "audio/mpeg", "upsert": "true"}
        )

        # 3. Lấy Public URL
        public_url = supabase.storage.from_(QUESTION_AUDIO_BUCKET).get_public_url(storage_path)
        return public_url

    except Exception as e:
        print(f"Lỗi khi tạo TTS (ID: {question_id}): {e}")
        # Ghi lại lỗi, nhưng không raise để worker tiếp tục
        return None