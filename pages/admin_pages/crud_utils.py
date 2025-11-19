# pages/admin_pages/crud_utils.py
import streamlit as st
import pandas as pd
import datetime
import uuid
from backend.supabase_client import supabase
import xlsxwriter
import os
import io
from urllib.parse import unquote
from gtts import gTTS
from backend.tts_service import generate_and_upload_tts

@st.cache_data(ttl=60)
def load_data(table_name):
    """Tải toàn bộ dữ liệu từ bảng và trả về DataFrame."""
    try:
        # Thử order theo created_at hoặc cột có ý nghĩa khác nếu có
        order_col = "created_at" # Mặc định thử created_at
        try:
             # Cố gắng lấy tên cột đầu tiên làm fallback nếu created_at không có
             res_cols = supabase.table(table_name).select('*', count='exact', head=True).execute()
             fallback_col = res_cols.data[0]['columns'][0]['name'] if res_cols.data and res_cols.data[0]['columns'] else 'id'
             order_col = fallback_col # Sử dụng cột đầu tiên nếu created_at lỗi
             res = supabase.table(table_name).select("*").order(order_col, desc=True).execute() # Sửa lỗi, dùng order_col
        except:
             order_col = 'id' # Fallback cuối cùng là id
             res = supabase.table(table_name).select("*").order(order_col, desc=True).execute()

        return pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"Lỗi tải dữ liệu bảng {table_name}: {e}")
        return pd.DataFrame()

# ---- HÀM MỚI ----
def clear_all_cached_data():
    """Chỉ xóa cache dữ liệu của Streamlit."""
    st.cache_data.clear()
    # st.toast("Cache cleared!") # Có thể thêm thông báo nhỏ nếu muốn
# ---- KẾT THÚC HÀM MỚI ----

def clear_cache_and_rerun():
    """Xóa cache, lựa chọn hiện tại và chạy lại trang (dùng khi Sửa/Xóa)."""
    clear_all_cached_data() # Gọi hàm xóa cache mới
    # Xóa các key session liên quan đến item đang chọn (nếu có)
    keys_to_delete = [key for key in st.session_state if key.endswith('_selected_item_id')]
    for key in keys_to_delete:
        try:
            del st.session_state[key]
        except KeyError:
            pass # Bỏ qua nếu key đã bị xóa
    st.rerun() # Chỉ rerun khi cần thiết (sau khi sửa/xóa hoặc hủy chọn)

def is_valid_uuid(val):
    """Kiểm tra xem giá trị có phải là UUID hợp lệ không."""
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False

def create_excel_download(df_sample, filename, sheet_name='Sheet1'):
    """Tạo nút tải file Excel mẫu từ DataFrame."""
    output = io.BytesIO()
    try:
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_sample.to_excel(writer, index=False, sheet_name=sheet_name)
        excel_data = output.getvalue()
        st.download_button(
            label="📥 Tải file mẫu Excel",
            data=excel_data,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.error(f"Lỗi tạo file Excel mẫu: {e}")


# ===============================================
# 🔊 HÀM HELPER MỚI CHO TTS (TEXT-TO-SPEECH)
# ===============================================

# Đặt tên bucket của bạn (bạn phải tạo bucket này trong Supabase Storage)
QUESTION_AUDIO_BUCKET = "question_audio"


