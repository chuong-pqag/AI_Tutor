# ===============================================
# 💾 Backend Data Service Layer (Sửa lỗi đếm cuối cùng)
# ===============================================
from backend.supabase_client import supabase
from datetime import datetime
import json
import pandas as pd


# =========================================================
# 1️⃣ HỌC SINH (Giữ nguyên)
# =========================================================
def get_student(student_id: str):
    try:
        res = supabase.table("hoc_sinh").select("*").eq("id", student_id).maybe_single().execute()
        return res.data
    except Exception as e:
        print(f"Lỗi khi lấy thông tin học sinh {student_id}: {e}"); return None


def get_all_students(lop_id: str = None):
    try:
        query = supabase.table("hoc_sinh").select("*")
        if lop_id: query = query.eq("lop_id", lop_id)
        res = query.order("ho_ten").execute()
        return res.data
    except Exception as e:
        print(f"Lỗi khi lấy danh sách học sinh: {e}"); return []


def insert_student(ho_ten: str, lop_id: str, ma_hoc_sinh: str, mat_khau: str, email: str = None, gioi_tinh: str = None,
                   ngay_sinh: str = None):
    data = {"ho_ten": ho_ten, "lop_id": lop_id, "ma_hoc_sinh": ma_hoc_sinh, "mat_khau": mat_khau, "email": email,
            "gioi_tinh": gioi_tinh, "ngay_sinh": ngay_sinh}
    data = {k: v for k, v in data.items() if v is not None}
    try:
        return supabase.table("hoc_sinh").insert(data).execute()
    except Exception as e:
        print(f"Lỗi khi thêm học sinh {ma_hoc_sinh}: {e}"); raise e


# =========================================================
# 2️⃣ MÔN HỌC & CHỦ ĐỀ (Giữ nguyên)
# =========================================================
def get_subjects_by_grade(lop: int):
    if lop is None: return []
    try:
        lop_int = int(lop)
    except (ValueError, TypeError):
        return []
    try:
        filter_value = f'[{lop_int}]'
        query = supabase.table("mon_hoc").select("id, ten_mon").filter("khoi_ap_dung", "cs", filter_value)
        res = query.execute()
        if hasattr(res, 'data'):
            if res.data is None: return []
            return res.data
        else:
            return []
    except Exception as e:
        print(f"Lỗi Exception khi truy vấn Supabase (get_subjects_by_grade): {e}"); return []


def get_topics_by_subject_and_class(mon_hoc_ten: str, lop: int):
    if lop is None or not mon_hoc_ten: return []
    try:
        res = supabase.table("chu_de").select("id, ten_chu_de, tuan, mon_hoc").eq("mon_hoc", mon_hoc_ten).eq("lop",
                                                                                                             lop).order(
            "tuan", desc=False).execute()
        return res.data
    except Exception as e:
        print(f"Lỗi khi lấy chủ đề theo môn '{mon_hoc_ten}', lớp {lop}: {e}"); return []


def get_all_topics(mon_hoc: str, lop: int):
    return get_topics_by_subject_and_class(mon_hoc, lop)


def get_topic_by_id(chu_de_id: str):
    try:
        res = supabase.table("chu_de").select("*").eq("id", chu_de_id).maybe_single().execute()
        return res.data
    except Exception as e:
        print(f"Lỗi khi lấy chủ đề ID {chu_de_id}: {e}"); return None


# =========================================================
# 📝 BÀI HỌC (Giữ nguyên)
# =========================================================
def get_lessons_by_topic(chu_de_id: str):
    try:
        res = supabase.table("bai_hoc").select("*").eq("chu_de_id", chu_de_id).order("thu_tu", desc=False).execute()
        return res.data
    except Exception as e:
        print(f"Lỗi khi lấy bài học cho chủ đề {chu_de_id}: {e}"); return []


def get_lesson_by_id(bai_hoc_id: str):
    try:
        res = supabase.table("bai_hoc").select("*").eq("id", bai_hoc_id).maybe_single().execute()
        return res.data
    except Exception as e:
        print(f"Lỗi khi lấy bài học ID {bai_hoc_id}: {e}"); return None


def insert_lesson(chu_de_id: str, ten_bai_hoc: str, thu_tu: int = 0, mo_ta: str = None, noi_dung_pdf_url: str = None):
    data = {"chu_de_id": chu_de_id, "ten_bai_hoc": ten_bai_hoc, "thu_tu": thu_tu, "mo_ta": mo_ta,
            "noi_dung_pdf_url": noi_dung_pdf_url}
    data = {k: v for k, v in data.items() if v is not None};
    try:
        return supabase.table("bai_hoc").insert(data).execute()
    except Exception as e:
        print(f"Lỗi thêm bài học: {e}"); raise e


def update_lesson(bai_hoc_id: str, update_data: dict):
    allowed_keys = {"chu_de_id", "ten_bai_hoc", "thu_tu", "mo_ta", "noi_dung_pdf_url"};
    data_to_update = {k: v for k, v in update_data.items() if k in allowed_keys}
    if not data_to_update: return None;
    try:
        return supabase.table("bai_hoc").update(data_to_update).eq("id", bai_hoc_id).execute()
    except Exception as e:
        print(f"Lỗi cập nhật bài học: {e}"); raise e


def delete_lesson(bai_hoc_id: str):
    try:
        return supabase.table("bai_hoc").delete().eq("id", bai_hoc_id).execute()
    except Exception as e:
        print(f"Lỗi xóa bài học: {e}"); raise e


# =========================================================
# 🎥 VIDEO BÀI GIẢNG (Giữ nguyên)
# =========================================================
def get_videos_by_lesson(bai_hoc_id: str):
    try:
        res = supabase.table("video_bai_giang").select("*").eq("bai_hoc_id", bai_hoc_id).execute()
        return res.data
    except Exception as e:
        print(f"Lỗi khi lấy video cho bài học {bai_hoc_id}: {e}"); return []


def insert_video(bai_hoc_id: str, tieu_de: str, url: str, mo_ta: str = None):
    data = {"bai_hoc_id": bai_hoc_id, "tieu_de": tieu_de, "url": url, "mo_ta": mo_ta};
    data = {k: v for k, v in data.items() if v is not None}
    try:
        return supabase.table("video_bai_giang").insert(data).execute()
    except Exception as e:
        print(f"Lỗi thêm video: {e}"); raise e


def update_video(video_id: str, update_data: dict):
    allowed_keys = {"bai_hoc_id", "tieu_de", "url", "mo_ta"};
    data_to_update = {k: v for k, v in update_data.items() if k in allowed_keys}
    if not data_to_update: return None;
    try:
        return supabase.table("video_bai_giang").update(data_to_update).eq("id", video_id).execute()
    except Exception as e:
        print(f"Lỗi cập nhật video: {e}"); raise e


def delete_video(video_id: str):
    try:
        return supabase.table("video_bai_giang").delete().eq("id", video_id).execute()
    except Exception as e:
        print(f"Lỗi xóa video: {e}"); raise e


# =========================================================
# 🧩 BÀI TẬP (Giữ nguyên)
# =========================================================
def get_practice_exercises_by_lesson(bai_hoc_id: str):
    try:
        res = supabase.table("bai_tap").select("*").eq("bai_hoc_id", bai_hoc_id).eq("loai_bai_tap", "luyen_tap").order(
            "created_at", desc=False).execute()
        return res.data
    except Exception as e:
        print(f"Lỗi khi lấy bài luyện tập cho bài học {bai_hoc_id}: {e}"); return []


def get_topic_test_by_topic(chu_de_id: str, lop_id: str = None):  # <--- Thêm tham số lop_id
    try:
        query = supabase.table("bai_tap").select("*") \
            .eq("chu_de_id", chu_de_id) \
            .eq("loai_bai_tap", "kiem_tra_chu_de")

        # CHỈNH SỬA QUAN TRỌNG: Nếu có lop_id, bắt buộc phải khớp
        if lop_id:
            query = query.eq("lop_id", lop_id)

        res = query.limit(1).maybe_single().execute()

        if res and res.data:
            return res.data
        else:
            return None
    except Exception as e:
        print(f"Lỗi khi lấy bài kiểm tra chủ đề {chu_de_id}: {e}")
        return None


def get_exercise_by_id(bai_tap_id: str):
    try:
        res = supabase.table("bai_tap").select("*").eq("id", bai_tap_id).maybe_single().execute(); return res.data
    except Exception as e:
        print(f"Lỗi lấy bài tập ID {bai_tap_id}: {e}"); return None


def insert_exercise(tieu_de: str, loai_bai_tap: str, chu_de_id: str = None, bai_hoc_id: str = None, mo_ta: str = None,
                    muc_do: str = 'biết'):
    if loai_bai_tap == 'luyen_tap' and not bai_hoc_id: raise ValueError("Bài luyện tập phải có bai_hoc_id.");
    if loai_bai_tap == 'kiem_tra_chu_de' and not chu_de_id: raise ValueError("Bài kiểm tra chủ đề phải có chu_de_id.");
    data = {"tieu_de": tieu_de, "loai_bai_tap": loai_bai_tap, "chu_de_id": chu_de_id, "bai_hoc_id": bai_hoc_id,
            "mo_ta": mo_ta, "muc_do": muc_do};
    data = {k: v for k, v in data.items() if v is not None}
    try:
        return supabase.table("bai_tap").insert(data).execute()
    except Exception as e:
        print(f"Lỗi thêm bài tập: {e}"); raise e


def add_questions_to_exercise(bai_tap_id: str, cau_hoi_ids: list):
    if not cau_hoi_ids: return None; links = [{"bai_tap_id": bai_tap_id, "cau_hoi_id": q_id} for q_id in cau_hoi_ids];
    try:
        return supabase.table("bai_tap_cau_hoi").insert(links, upsert=False).execute()
    except Exception as e:
        print(f"Lỗi thêm câu hỏi vào bài tập: {e}"); raise e


# =========================================================
# ❓ CÂU HỎI (ĐÃ CẬP NHẬT)
# =========================================================
def get_questions_by_topic_for_admin(chu_de_id: str):
    try:
        res = supabase.table("cau_hoi").select("*").eq("chu_de_id", chu_de_id).execute()
        return res.data
    except Exception as e:
        print(f"Lỗi khi lấy câu hỏi cho chủ đề {chu_de_id}: {e}"); return []


# ===============================================
# ---- HÀM get_question_counts (ĐÃ SỬA LỖI) ----
# ===============================================
# ===============================================
# ---- HÀM get_question_counts (ĐÃ SỬA LỖI) ----
# ===============================================
def get_question_counts(chu_de_id: str = None, bai_hoc_id: str = None):
    """
    Đếm số lượng câu hỏi theo từng mức độ (biết, hiểu, vận dụng)
    cho một chủ đề hoặc một bài học cụ thể.
    SỬ DỤNG 3 TRUY VẤN RIÊNG BIỆT ĐỂ ĐẢM BẢO ĐỘ CHÍNH XÁC.
    """
    counts = {'biết': 0, 'hiểu': 0, 'vận dụng': 0}  # Khởi tạo dict đếm

    if not chu_de_id and not bai_hoc_id:
        print("DEBUG (get_question_counts): Không có ID, trả về 0")
        return counts  # Trả về 0 nếu không có ID

    # Xác định cột và giá trị để lọc
    filter_col = "bai_hoc_id" if bai_hoc_id else "chu_de_id"
    filter_val = bai_hoc_id if bai_hoc_id else chu_de_id

    try:
        # ---- SỬA LỖI LOGIC: Xây dựng 3 truy vấn đầy đủ ----

        # 1. Đếm 'biết'
        res_biet = supabase.table("cau_hoi") \
            .select("id", count="exact") \
            .eq(filter_col, filter_val) \
            .eq("muc_do", "biết") \
            .execute()
        counts['biết'] = res_biet.count

        # 2. Đếm 'hiểu'
        res_hieu = supabase.table("cau_hoi") \
            .select("id", count="exact") \
            .eq(filter_col, filter_val) \
            .eq("muc_do", "hiểu") \
            .execute()
        counts['hiểu'] = res_hieu.count

        # 3. Đếm 'vận dụng'
        res_van_dung = supabase.table("cau_hoi") \
            .select("id", count="exact") \
            .eq(filter_col, filter_val) \
            .eq("muc_do", "vận dụng") \
            .execute()
        counts['vận dụng'] = res_van_dung.count

        print(f"DEBUG (get_question_counts): Lọc theo {filter_col}={filter_val}. Counts={counts}")
        return counts

    except Exception as e:
        print(f"Lỗi khi đếm câu hỏi (get_question_counts): {e}")
        return counts  # Trả về 0 nếu có lỗi


# ===============================================
# ---- KẾT THÚC HÀM get_question_counts ----
# ===============================================

def get_questions_for_exercise(bai_tap_id: str):
    """Lấy danh sách câu hỏi cho một BÀI TẬP cụ thể."""
    try:
        res_links = supabase.table("bai_tap_cau_hoi").select("cau_hoi_id").eq("bai_tap_id", bai_tap_id).execute()
        if not res_links.data: return []
        question_ids = [link['cau_hoi_id'] for link in res_links.data]
        if not question_ids: return []

        # --- CẬP NHẬT: Thêm 'audio_url' và 'hinh_anh_url' vào select ---
        res_questions = supabase.table("cau_hoi").select(
            "id, noi_dung, dap_an_dung, dap_an_khac, muc_do, diem_so, loai_cau_hoi, audio_url, hinh_anh_url"
        ).in_("id", question_ids).execute()
        # ----------------------------------------------------------------

        if not res_questions.data: return []

        questions_data = res_questions.data
        questions = []
        for q in questions_data:
            lua_chon_raw = q.get("dap_an_khac") or []
            lua_chon = [str(opt) for opt in lua_chon_raw]
            dap_an_dung_raw = q.get("dap_an_dung") if isinstance(q.get("dap_an_dung"), list) else []
            dap_an_dung = [str(ans) for ans in dap_an_dung_raw]
            loai_cau_hoi = q.get("loai_cau_hoi", "mot_lua_chon")

            questions.append({
                "id": str(q["id"]),
                "noi_dung": q["noi_dung"],
                "loai_cau_hoi": loai_cau_hoi,
                "lua_chon": lua_chon,
                "dap_an_dung": dap_an_dung,
                "muc_do": q.get("muc_do", "biết"),
                "diem_so": q.get("diem_so", 1),
                "audio_url": q.get("audio_url"),  # <-- Lấy Audio URL
                "hinh_anh_url": q.get("hinh_anh_url")  # <-- Lấy Ảnh minh họa
            })
        return questions
    except Exception as e:
        print(f"Lỗi khi lấy câu hỏi cho bài tập {bai_tap_id}: {e}")
        return []


def insert_question(chu_de_id: str, loai_cau_hoi: str, noi_dung: str, dap_an_dung: list, dap_an_khac: list = None,
                    muc_do: str = 'biết', diem_so: int = 1, bai_hoc_id: str = None):
    data = {"chu_de_id": chu_de_id, "bai_hoc_id": bai_hoc_id, "loai_cau_hoi": loai_cau_hoi, "noi_dung": noi_dung,
            "dap_an_dung": dap_an_dung, "dap_an_khac": dap_an_khac or [], "muc_do": muc_do, "diem_so": diem_so}
    data = {k: v for k, v in data.items() if v is not None}
    try:
        return supabase.table("cau_hoi").insert(data).execute()
    except Exception as e:
        print(f"Lỗi thêm câu hỏi: {e}")
        raise e


# ... (Giữ nguyên tất cả các hàm còn lại: save_test_result, get_student_results_by_topic, v.v...)
def save_test_result(hoc_sinh_id: str, bai_tap_id: str, chu_de_id: str, diem: float, so_cau_dung: int, tong_cau: int,
                     tuan_kiem_tra: int, lop: int,
                     diem_biet: float = 0, diem_hieu: float = 0, diem_van_dung: float = 0,
                     tong_diem_biet: float = 0, tong_diem_hieu: float = 0,
                     tong_diem_van_dung: float = 0):  # <-- 3 THAM SỐ MỚI
    """
    (ĐÃ NÂNG CẤP LẦN 2) Lưu kết quả test, bao gồm 6 cột điểm chi tiết.
    """
    data = {"hoc_sinh_id": hoc_sinh_id, "bai_tap_id": bai_tap_id, "chu_de_id": chu_de_id, "diem": diem,
            "so_cau_dung": so_cau_dung, "tong_cau": tong_cau, "tuan_kiem_tra": tuan_kiem_tra, "lop": lop,
            "ngay_kiem_tra": datetime.now().isoformat(),

            "diem_biet": diem_biet,
            "diem_hieu": diem_hieu,
            "diem_van_dung": diem_van_dung,

            # (THÊM MỚI) Thêm 3 cột tổng điểm tối đa
            "tong_diem_biet": tong_diem_biet,
            "tong_diem_hieu": tong_diem_hieu,
            "tong_diem_van_dung": tong_diem_van_dung
            }
    try:
        return supabase.table("ket_qua_test").insert(data).execute()
    except Exception as e:
        print(f"Lỗi lưu kết quả test: {e}");
        return None


def get_student_results_by_topic(hoc_sinh_id: str, chu_de_id: str):
    test_exercise = get_topic_test_by_topic(chu_de_id)
    if not test_exercise: return []
    try:
        res = supabase.table("ket_qua_test").select("*").eq("hoc_sinh_id", hoc_sinh_id).eq("bai_tap_id",
                                                                                           test_exercise['id']).order(
            "ngay_kiem_tra", desc=True).execute()
        return res.data
    except Exception as e:
        print(f"Lỗi lấy KQ theo chủ đề: {e}"); return []


def get_student_all_results(hoc_sinh_id: str):
    try:
        res = supabase.table("ket_qua_test").select("*, bai_tap(tieu_de, loai_bai_tap), chu_de(ten_chu_de)").eq(
            "hoc_sinh_id", hoc_sinh_id).order("ngay_kiem_tra", desc=True).execute()
        return res.data
    except Exception as e:
        print(f"Lỗi lấy tất cả KQ: {e}"); return []


def insert_learning_path(hoc_sinh_id: str, loai_goi_y: str, chu_de_id: str = None, bai_hoc_id: str = None,
                         muc_do_de_xuat: str = "biết", diem_truoc_goi_y: float = None):
    # ... (data setup giữ nguyên) ...
    data = {
        "hoc_sinh_id": hoc_sinh_id,
        "loai_goi_y": loai_goi_y,
        "chu_de_id": chu_de_id,
        "bai_hoc_id": bai_hoc_id,
        "muc_do_de_xuat": muc_do_de_xuat,
        "diem_truoc_goi_y": diem_truoc_goi_y,
        "trang_thai": "Chưa thực hiện"
    }
    data = {k: v for k, v in data.items() if v is not None}
    try:
        return supabase.table("lo_trinh_hoc").insert(data).execute()
    except Exception as e:
        print(f"Lỗi thêm lộ trình: {e}")
        return None # <-- KHÔNG RAISE E NỮA, TRẢ VỀ NONE AN TOÀN


def update_learning_status(lo_trinh_id: str, trang_thai: str):
    try:
        return supabase.table("lo_trinh_hoc").update({"trang_thai": trang_thai}).eq("id", lo_trinh_id).execute()
    except Exception as e:
        print(f"Lỗi cập nhật trạng thái lộ trình: {e}"); raise e


def get_learning_paths(hoc_sinh_id: str):
    try:
        res = supabase.table("lo_trinh_hoc").select(
            "*, suggested_lesson:bai_hoc_id(ten_bai_hoc), suggested_topic:chu_de_id(ten_chu_de)").eq("hoc_sinh_id",
                                                                                                     hoc_sinh_id).order(
            "ngay_goi_y", desc=True).execute()
        return res.data
    except Exception as e:
        print(f"Lỗi lấy lộ trình: {e}"); return []


def log_learning_activity(hoc_sinh_id: str, hanh_dong: str, noi_dung: str, chu_de_id: str = None,
                          bai_hoc_id: str = None):
    data = {"hoc_sinh_id": hoc_sinh_id, "chu_de_id": chu_de_id, "bai_hoc_id": bai_hoc_id, "hanh_dong": hanh_dong,
            "noi_dung": noi_dung, "thoi_gian": datetime.now().isoformat()}
    data = {k: v for k, v in data.items() if v is not None}
    try:
        return supabase.table("lich_su_hoc").insert(data).execute()
    except Exception as e:
        print(f"Lỗi ghi lịch sử học: {e}")


def get_learning_history(hoc_sinh_id: str):
    try:
        res = supabase.table("lich_su_hoc").select("*, lesson:bai_hoc_id(ten_bai_hoc), topic:chu_de_id(ten_chu_de)").eq(
            "hoc_sinh_id", hoc_sinh_id).order("thoi_gian", desc=True).execute()
        return res.data
    except Exception as e:
        print(f"Lỗi lấy lịch sử học: {e}"); return []


def log_ai_recommendation(hoc_sinh_id: str, input_features: dict, action: str, chu_de_nguon: str,
                          chu_de_de_xuat: str = None, bai_hoc_de_xuat: str = None, model_version: str = "rule-based",
                          confidence: float = None):
    data = {"hoc_sinh_id": hoc_sinh_id, "input_features": input_features, "action": action,
            "chu_de_nguon": chu_de_nguon, "chu_de_de_xuat": chu_de_de_xuat, "bai_hoc_de_xuat": bai_hoc_de_xuat,
            "model_version": model_version, "confidence": confidence}
    data = {k: v for k, v in data.items() if v is not None}
    try:
        return supabase.table("ai_recommendation_log").insert(data).execute()
    except Exception as e:
        print(f"Lỗi ghi log AI: {e}"); return None


def get_ai_logs(hoc_sinh_id: str):
    try:
        res = supabase.table("ai_recommendation_log").select(
            "*, suggested_lesson:bai_hoc_de_xuat(ten_bai_hoc), suggested_topic:chu_de_de_xuat(ten_chu_de)").eq(
            "hoc_sinh_id", hoc_sinh_id).order("created_at", desc=True).execute()
        return res.data
    except Exception as e:
        print(f"Lỗi lấy log AI: {e}"); return []

def get_teacher_exercises(giao_vien_id: str):
    """Lấy danh sách bài tập (luyện tập & kiểm tra) do GV này tạo."""
    try:
        # LƯU Ý: Nếu chưa có cột giao_vien_id trong bai_tap, bạn phải thêm nó vào CSDL và code
        # Giả định cột giao_vien_id đã được thêm vào bảng bai_tap.
        res = supabase.table("bai_tap").select(
            "*, chu_de(ten_chu_de, mon_hoc), bai_hoc(ten_bai_hoc)"
        ).eq("giao_vien_id", giao_vien_id).order("created_at", desc=True).execute()
        return res.data
    except Exception as e:
        print(f"Lỗi khi lấy danh sách bài tập của GV: {e}"); return []

def can_delete_exercise(bai_tap_id: str):
    """Kiểm tra xem đã có học sinh nào làm bài tập này chưa."""
    try:
        res = supabase.table("ket_qua_test").select("id", count="exact").eq("bai_tap_id", bai_tap_id).limit(1).execute()
        # Trả về True nếu count == 0 (chưa có ai làm)
        return res.count == 0
    except Exception as e:
        print(f"Lỗi khi kiểm tra xóa bài tập: {e}"); return False

def update_exercise_title(bai_tap_id: str, new_title: str):
    """Cập nhật tiêu đề bài tập."""
    try:
        return supabase.table("bai_tap").update({"tieu_de": new_title}).eq("id", bai_tap_id).execute()
    except Exception as e:
        print(f"Lỗi cập nhật tiêu đề bài tập: {e}"); raise e

def delete_exercise_and_links(bai_tap_id: str):
    """Xóa bài tập và các liên kết câu hỏi khỏi bai_tap_cau_hoi."""
    try:
        # Xóa liên kết trước
        supabase.table("bai_tap_cau_hoi").delete().eq("bai_tap_id", bai_tap_id).execute()
        # Xóa bài tập
        return supabase.table("bai_tap").delete().eq("id", bai_tap_id).execute()
    except Exception as e:
        print(f"Lỗi xóa bài tập và liên kết: {e}");
        raise e


# =========================================================
# 🆕 3️⃣ HÀM MỚI CHO DASHBOARD HỌC SINH
# =========================================================
import pandas as pd


# Đảm bảo bạn đã import pandas ở đầu file nếu chưa có

def get_student_overall_progress(hoc_sinh_id: str):
    """
    1.1. Tính Điểm trung bình Topic Test và đếm số Chủ đề đã kiểm tra.
    """
    try:
        # Truy vấn tất cả kết quả test của học sinh, join với bai_tap để lấy loai_bai_tap
        res = supabase.table("ket_qua_test").select(
            "diem, chu_de_id, bai_tap(loai_bai_tap)"
        ).eq("hoc_sinh_id", hoc_sinh_id).order("ngay_kiem_tra", desc=True).execute()

        data = res.data or []
        df = pd.DataFrame(data)

        if df.empty:
            return {"avg_score": 0.0, "completed_topics_count": 0, "total_topics_available": 0, "latest_score": 0.0}

        # 1. Lọc chỉ lấy Bài kiểm tra Chủ đề
        df['loai_bai_tap'] = df['bai_tap'].apply(lambda x: x.get('loai_bai_tap') if isinstance(x, dict) else None)
        df_topic_test = df[df['loai_bai_tap'] == 'kiem_tra_chu_de'].copy()

        if df_topic_test.empty:
            return {"avg_score": 0.0, "completed_topics_count": 0, "total_topics_available": 0, "latest_score": 0.0}

        # 2. Tính Điểm trung bình (chỉ trên Topic Test)
        df_topic_test['diem'] = pd.to_numeric(df_topic_test['diem'], errors='coerce')
        avg_score = round(df_topic_test['diem'].mean(), 2) if not df_topic_test['diem'].empty else 0.0

        # 3. Đếm số chủ đề đã được kiểm tra (unique ID)
        completed_topics_count = df_topic_test['chu_de_id'].nunique()

        # 4. Lấy điểm gần nhất
        latest_score = round(df_topic_test.iloc[0]['diem'], 2)

        # 5. Tổng số chủ đề (tạm thời không tính)
        total_topics_available = 0

        return {
            "avg_score": avg_score,
            "completed_topics_count": completed_topics_count,
            "total_topics_available": total_topics_available,
            "latest_score": latest_score
        }
    except Exception as e:
        print(f"Lỗi khi tính progress: {e}")
        return {"avg_score": 0.0, "completed_topics_count": 0, "total_topics_available": 0, "latest_score": 0.0}


def get_latest_ai_recommendation(hoc_sinh_id: str, mon_hoc: str = None, lop: int = None):
    """
    Lấy gợi ý AI MỚI NHẤT cho đúng môn học (nếu có).
    - Chỉ lấy bản ghi 'Chưa thực hiện' hoặc 'Đang thực hiện' (bỏ NULL)
    - Nếu không tìm thấy bản ghi cho môn đó, fallback: chọn topic tiếp theo chưa HT từ get_topics_status()
    - Trả về dict chuẩn hoặc None
    """
    try:
        # 1) Lấy tất cả gợi ý hiện có cho học sinh (trạng thái hợp lệ)
        res = supabase.table("lo_trinh_hoc").select(
            "*, suggested_topic:chu_de_id(ten_chu_de, mon_hoc, lop), suggested_lesson:bai_hoc_id(ten_bai_hoc)"
        ).eq("hoc_sinh_id", hoc_sinh_id) \
         .or_("trang_thai.eq.'Chưa thực hiện', trang_thai.eq.'Đang thực hiện'") \
         .order("ngay_goi_y", desc=True).execute()

        rows = res.data or []

        # 2) Nếu có truyền mon_hoc thì lọc theo môn
        if mon_hoc:
            rows = [r for r in rows if r.get("suggested_topic", {}).get("mon_hoc") == mon_hoc]

        # 3) Nếu có row → lấy row đầu (mới nhất)
        if rows:
            latest = rows[0]
            rec = {
                "id": latest.get("id"),
                "action": latest.get("loai_goi_y"),
                "diem_truoc_goi_y": latest.get("diem_truoc_goi_y"),
                "chu_de_id": latest.get("chu_de_id"),
                "bai_hoc_id": latest.get("bai_hoc_id"),
                "mon_hoc": latest.get("suggested_topic", {}).get("mon_hoc"),
                "lop": latest.get("suggested_topic", {}).get("lop"),
                "ten_chu_de": latest.get("suggested_topic", {}).get("ten_chu_de"),
                "ten_bai_hoc": latest.get("suggested_lesson", {}).get("ten_bai_hoc"),
                "ngay_goi_y": latest.get("ngay_goi_y")
            }
            return rec

        # 4) FALLBACK: nếu không có gợi ý trong lo_trinh_hoc cho môn đó, tự tạo gợi ý "topic tiếp theo chưa HT"
        if mon_hoc and lop is not None:
            topics = get_topics_status(hoc_sinh_id, mon_hoc, lop)
            if topics:
                # chọn topic đầu tiên chưa hoàn thành (theo tuần tăng dần)
                next_topic = next((t for t in topics if not t.get("completed")), None)
                if next_topic:
                    return {
                        "id": None,
                        "action": "advance",
                        "diem_truoc_goi_y": None,
                        "chu_de_id": next_topic["id"],
                        "bai_hoc_id": None,
                        "mon_hoc": mon_hoc,
                        "lop": lop,
                        "ten_chu_de": next_topic["ten_chu_de"],
                        "ten_bai_hoc": None,
                        "ngay_goi_y": None
                    }

        # Nếu vẫn không tìm được, trả về None
        return None

    except Exception as e:
        print(f"Lỗi get_latest_ai_recommendation: {e}")
        return None

def get_topics_status(hoc_sinh_id: str, mon_hoc_name: str, lop: int):
    """
    1.3. Lấy tất cả chủ đề cho môn học/lớp và đánh dấu trạng thái Đã/Chưa hoàn thành kiểm tra.
    Sửa lỗi kiểu ID: chuẩn hóa tất cả về str để so sánh chính xác.
    """
    if lop is None or not mon_hoc_name:
        return []

    try:
        # 1. Lấy TẤT CẢ chủ đề cho môn học/lớp này
        all_topics_res = supabase.table("chu_de").select("id, ten_chu_de, tuan, prerequisite_id").eq("lop", lop).eq(
            "mon_hoc", mon_hoc_name).order("tuan", desc=False).execute()
        all_topics = all_topics_res.data or []

        if not all_topics:
            return []

        # 2. Lấy tất cả bai_tap_id là 'kiem_tra_chu_de' cho các chu_de trong all_topics
        topic_ids = [t['id'] for t in all_topics]

        topic_test_res = supabase.table("bai_tap").select("id, chu_de_id").in_("chu_de_id", topic_ids).eq("loai_bai_tap",
                                                                                               "kiem_tra_chu_de").execute()
        topic_test_ids = [b['id'] for b in topic_test_res.data or []]
        test_map = {str(b['id']): str(b['chu_de_id']) for b in (topic_test_res.data or [])}

        # 3. Lấy ket_qua_test cho các bài kiểm tra này (và chuẩn hóa kiểu chu_de_id về str)
        if not topic_test_ids:
            completed_topic_ids = set()
        else:
            completed_res = supabase.table("ket_qua_test").select("chu_de_id").eq("hoc_sinh_id", hoc_sinh_id).in_(
                "bai_tap_id", topic_test_ids).execute()
            # CHUẨN HÓA: ép tất cả về str để so sánh đúng
            completed_topic_ids = {str(r['chu_de_id']) for r in (completed_res.data or [])}

        # 4. Kết hợp và gán trạng thái (chuẩn hóa id thành str)
        topics_status = []
        for topic in all_topics:
            topic_id = str(topic['id'])
            topics_status.append({
                "id": topic_id,
                "ten_chu_de": topic.get('ten_chu_de'),
                "tuan": topic.get('tuan'),
                "completed": topic_id in completed_topic_ids,
                "prerequisite_id": topic.get('prerequisite_id')
            })

        return topics_status
    except Exception as e:
        print(f"Lỗi khi lấy topic status: {e}")
        return []


# =========================================================
# 🆕 4️⃣ HÀM MỚI CHO TÍNH NĂNG THÔNG BÁO (ANNOUNCEMENT)
# =========================================================

def create_announcement(giao_vien_id: str, lop_id: str, tieu_de: str, noi_dung: str):
    """
    2.1. Giáo viên tạo một thông báo mới cho một lớp.
    """
    if not giao_vien_id or not lop_id or not tieu_de:
        raise ValueError("Thiếu thông tin bắt buộc (GV, Lớp, Tiêu đề) để tạo thông báo.")

    try:
        data = {
            "giao_vien_id": giao_vien_id,
            "lop_id": lop_id,
            "tieu_de": tieu_de,
            "noi_dung": noi_dung
        }
        res = supabase.table("thong_bao").insert(data).execute()
        return res.data
    except Exception as e:
        print(f"Lỗi khi tạo thông báo: {e}")
        raise e


def get_announcements_for_student(lop_id: str, limit: int = 5):
    """
    2.2. Lấy các thông báo mới nhất cho học sinh (dựa trên lop_id).
    """
    if not lop_id:
        return []
    try:
        res = supabase.table("thong_bao").select(
            "tieu_de, noi_dung, created_at, giao_vien(ho_ten)"
        ).eq("lop_id", lop_id).order("created_at", desc=True).limit(limit).execute()

        return res.data or []
    except Exception as e:
        print(f"Lỗi khi lấy thông báo cho học sinh: {e}")
        return []


def get_announcements_for_teacher(giao_vien_id: str):
    """
    2.3. Lấy tất cả thông báo đã gửi của một giáo viên.
    """
    if not giao_vien_id:
        return []
    try:
        res = supabase.table("thong_bao").select(
            "id, tieu_de, noi_dung, created_at, lop_id, lop_hoc(ten_lop)"
        ).eq("giao_vien_id", giao_vien_id).order("created_at", desc=True).execute()

        return res.data or []
    except Exception as e:
        print(f"Lỗi khi lấy thông báo cho giáo viên: {e}")
        return []


def delete_announcement(thong_bao_id: str, giao_vien_id: str):
    """
    (Hàm bổ sung) Xóa một thông báo (chỉ chủ sở hữu mới được xóa).
    """
    try:
        res = supabase.table("thong_bao").delete().eq("id", thong_bao_id).eq("giao_vien_id", giao_vien_id).execute()
        return res
    except Exception as e:
        print(f"Lỗi khi xóa thông báo: {e}")
        raise e

# =========================================================
# 🆕 5️⃣ HÀM MỚI CHO QUẢN LÝ NĂM HỌC
# =========================================================

def get_current_school_year():
    """
    1.2. Lấy năm học hiện tại đang được cấu hình trong bảng cau_hinh_chung.
    """
    try:
        res = supabase.table("cau_hinh_chung").select("value").eq("key", "current_school_year").maybe_single().execute()
        return res.data.get("value") if res.data else None
    except Exception as e:
        print(f"Lỗi khi lấy năm học hiện tại: {e}")
        return None


# =========================================================
# 🆕 6️⃣ HÀM MỚI CHO QUẢN LÝ LÊN LỚP
# =========================================================

def run_full_promotion(next_year: str):
    """
    Implements the full promotion logic: K1->K2, K2->K3, K3->K4, K4->K5, K5->Alumni.
    1. Finds active classes (K1-K5) in the current school year.
    2. Creates new classes (K2-K5) for the next_year.
    3. Reassigns students to the new classes.
    4. Gradates K5 students.
    """
    import uuid

    # 1. Determine the current school year being promoted FROM
    # We use a direct query since get_current_school_year() might be using cached data.
    current_year_res = supabase.table("cau_hinh_chung").select("value").eq("key",
                                                                           "current_school_year").maybe_single().execute()
    current_year_from = current_year_res.data.get("value") if current_year_res.data else None

    if not current_year_from:
        # Nếu không có năm học để chuyển đi, ta dừng lại.
        raise Exception("Không thể xác định Năm học hiện tại để bắt đầu quá trình Lên lớp.")

    # 2. Get all active classes (lop_hoc) in the current school year (K1-K5)
    # Chỉ chuyển những lớp thuộc năm học hiện tại.
    active_classes_res = supabase.table("lop_hoc").select("id, ten_lop, khoi").eq("nam_hoc", current_year_from).in_(
        "khoi", [1, 2, 3, 4, 5]).execute()
    active_classes = active_classes_res.data or []

    if not active_classes:
        return {"promoted": 0, "graduated": 0, "message": "Không tìm thấy lớp học nào để chuyển."}

    # Data structure to hold mappings for promotion
    class_promotion_map = {}  # { old_lop_id: { new_lop_id, old_khoi, new_khoi } }
    new_classes_to_insert = []

    # 3. Process promotion structure and generate new class IDs
    for old_class in active_classes:
        old_khoi = old_class['khoi']

        if old_khoi == 5:
            # Graduation case
            continue

        new_khoi = old_khoi + 1  # K1->K2, K2->K3, K3->K4, K4->K5

        # Create a new lop_hoc record
        new_lop_id = str(uuid.uuid4())
        new_classes_to_insert.append({
            "id": new_lop_id,
            "ten_lop": old_class['ten_lop'],
            "khoi": new_khoi,
            "nam_hoc": next_year
        })

        # Store mapping
        class_promotion_map[old_class['id']] = {
            "new_lop_id": new_lop_id,
            "old_khoi": old_khoi,
            "new_khoi": new_khoi
        }

    # --- PHASE 1: INSERT NEW CLASSES ---
    if new_classes_to_insert:
        try:
            supabase.table("lop_hoc").insert(new_classes_to_insert).execute()
        except Exception as e:
            # Nếu insert thất bại (ví dụ: lớp đã tồn tại), ta dừng lại.
            raise Exception(f"Lỗi khi tạo lớp học mới: {e}")

    # --- PHASE 2: REASSIGN STUDENTS ---
    promoted_students_count = 0

    for old_lop_id, mapping in class_promotion_map.items():
        new_lop_id = mapping['new_lop_id']

        # 2a. Find student count for logging
        count_res = supabase.table("hoc_sinh").select("id", count="exact").eq("lop_id", old_lop_id).execute()
        student_count = count_res.count

        if student_count > 0:
            # 2b. Update lop_id for all students in the old class to the new class ID
            supabase.table("hoc_sinh").update({"lop_id": new_lop_id}).eq("lop_id", old_lop_id).execute()
            promoted_students_count += student_count

    # --- PHASE 3: GRADUATION (K5) ---
    graduated_count = 0

    k5_classes_ids = [c['id'] for c in active_classes if c['khoi'] == 5]

    if k5_classes_ids:
        # Find student count for logging
        k5_count_res = supabase.table("hoc_sinh").select("id", count="exact").in_("lop_id", k5_classes_ids).execute()
        k5_student_count = k5_count_res.count

        if k5_student_count > 0:
            # Update their lop_id to NULL (Graduated/Alumni)
            supabase.table("hoc_sinh").update({"lop_id": None}).in_("lop_id", k5_classes_ids).execute()
            graduated_count = k5_student_count

    return {
        "promoted": promoted_students_count,
        "graduated": graduated_count,
        "message": "Quá trình lên lớp đã hoàn tất."
    }


def get_all_school_years():
    """
    Lấy tất cả các năm học độc nhất từ bảng lop_hoc (và thêm năm học hiện tại).
    """
    try:
        # 1. Lấy tất cả năm học từ các lớp đã tạo
        res = supabase.table("lop_hoc").select("nam_hoc").order("nam_hoc", desc=True).execute()

        # Lấy các giá trị độc nhất (unique) và loại bỏ NULL
        years = {r['nam_hoc'] for r in res.data if r.get('nam_hoc')}

        # 2. Thêm năm học hiện tại (từ cấu hình chung) nếu nó chưa có
        current_year = get_current_school_year()
        if current_year:
            years.add(current_year)

        # 3. Trả về danh sách đã sắp xếp (năm mới nhất ở trên)
        return sorted(list(years), reverse=True)
    except Exception as e:
        print(f"Lỗi khi lấy danh sách năm học: {e}")
        return []