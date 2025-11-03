import os
from dotenv import load_dotenv
from supabase import create_client, Client

# 🔹 Nạp biến môi trường từ file .env
load_dotenv()

# 🔹 Lấy giá trị từ tên biến môi trường
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Please set SUPABASE_URL and SUPABASE_KEY in .env")

# 🔹 Tạo kết nối Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# 🔸 Các hàm truy xuất dữ liệu
# =========================
def get_chu_de_by_class_week(lop, tuan):
    return supabase.table("chu_de").select("*").eq("lop", lop).lte("tuan", tuan).execute()

def get_lessons_by_chu_de(chu_de_id):
    return supabase.table("lessons").select("*").eq("chu_de_id", chu_de_id).execute()

def insert_ket_qua(hoc_sinh_id, chu_de_id, mon, lop, tuan, diem, ngay_test):
    return supabase.table("ket_qua_test").insert({
        "hoc_sinh_id": hoc_sinh_id,
        "chu_de_id": chu_de_id,
        "mon": mon,
        "lop": lop,
        "tuan": tuan,
        "diem": diem,
        "ngay_test": ngay_test
    }).execute()
