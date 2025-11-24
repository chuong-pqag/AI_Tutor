# File: backend/class_test_service.py
# (BẢN FINAL: Tự động thêm suffix mức độ vào tiêu đề bài tập)

import random
from backend.supabase_client import supabase
from datetime import datetime


def generate_class_test(
        lop_id: str, giao_vien_id: str, ten_bai: str, chu_de_id: str,
        so_cau_biet: int, so_cau_hieu: int, so_cau_van_dung: int
):
    """
    Sinh bài KIỂM TRA CHỦ ĐỀ cho lớp.
    """
    selected_question_ids = []

    try:
        # 1. Lấy câu "Biết"
        if so_cau_biet > 0:
            questions_biet = (supabase.table("cau_hoi").select("id")
                              .eq("chu_de_id", chu_de_id)
                              .eq("muc_do", "biết")
                              .execute().data or [])
            if len(questions_biet) < so_cau_biet:
                print(f"Lỗi (KT): Không đủ {so_cau_biet} câu 'biết'.")
                return False
            selected_question_ids.extend([q["id"] for q in random.sample(questions_biet, so_cau_biet)])

        # 2. Lấy câu "Hiểu"
        if so_cau_hieu > 0:
            questions_hieu = (supabase.table("cau_hoi").select("id")
                              .eq("chu_de_id", chu_de_id)
                              .eq("muc_do", "hiểu")
                              .execute().data or [])
            if len(questions_hieu) < so_cau_hieu:
                print(f"Lỗi (KT): Không đủ {so_cau_hieu} câu 'hiểu'.")
                return False
            selected_question_ids.extend([q["id"] for q in random.sample(questions_hieu, so_cau_hieu)])

        # 3. Lấy câu "Vận dụng"
        if so_cau_van_dung > 0:
            questions_van_dung = (supabase.table("cau_hoi").select("id")
                                  .eq("chu_de_id", chu_de_id)
                                  .eq("muc_do", "vận dụng")
                                  .execute().data or [])
            if len(questions_van_dung) < so_cau_van_dung:
                print(f"Lỗi (KT): Không đủ {so_cau_van_dung} câu 'vận dụng'.")
                return False
            selected_question_ids.extend([q["id"] for q in random.sample(questions_van_dung, so_cau_van_dung)])

    except Exception as e:
        print(f"Lỗi khi truy vấn câu hỏi (KT): {e}")
        return False

    # Xáo trộn thứ tự câu hỏi
    random.shuffle(selected_question_ids)

    try:
        # Lưu bài tập
        res_bai_tap = supabase.table("bai_tap").insert({
            "chu_de_id": chu_de_id,
            "bai_hoc_id": None,
            "tieu_de": ten_bai,
            "mo_ta": f"Bài kiểm tra do GV giao.",
            "loai_bai_tap": "kiem_tra_chu_de",
            "tong_so_cau": len(selected_question_ids),
            "giao_vien_id": giao_vien_id,
            "lop_id": lop_id
        }).execute()

        if not res_bai_tap.data: return False

        bai_tap_id = res_bai_tap.data[0]["id"]

        # Liên kết câu hỏi
        links = [{"bai_tap_id": bai_tap_id, "cau_hoi_id": q_id} for q_id in selected_question_ids]
        supabase.table("bai_tap_cau_hoi").insert(links).execute()

        return True

    except Exception as e:
        print(f"Lỗi khi lưu bài kiểm tra: {e}")
        return False


def generate_practice_exercise(
        bai_hoc_id: str, giao_vien_id: str, ten_bai: str,
        so_cau_biet: int, so_cau_hieu: int, so_cau_van_dung: int,
        lop_id: str = None
):
    """
    Sinh bài LUYỆN TẬP cho một BÀI HỌC cụ thể.
    (ĐÃ CẬP NHẬT: Tự động thêm hậu tố mức độ vào tên bài)
    """
    try:
        lesson_info = supabase.table("bai_hoc").select("chu_de_id").eq("id", bai_hoc_id).maybe_single().execute().data
        if not lesson_info or not lesson_info.get("chu_de_id"):
            return False
        chu_de_id_of_lesson = lesson_info["chu_de_id"]
    except Exception as e:
        print(f"Lỗi lấy thông tin bài học: {e}")
        return False

    selected_question_ids = []

    try:
        # 1. Biết
        if so_cau_biet > 0:
            questions_biet = (supabase.table("cau_hoi").select("id")
                              .eq("bai_hoc_id", bai_hoc_id)
                              .eq("muc_do", "biết")
                              .execute().data or [])
            if len(questions_biet) < so_cau_biet: return False
            selected_question_ids.extend([q["id"] for q in random.sample(questions_biet, so_cau_biet)])

        # 2. Hiểu
        if so_cau_hieu > 0:
            questions_hieu = (supabase.table("cau_hoi").select("id")
                              .eq("bai_hoc_id", bai_hoc_id)
                              .eq("muc_do", "hiểu")
                              .execute().data or [])
            if len(questions_hieu) < so_cau_hieu: return False
            selected_question_ids.extend([q["id"] for q in random.sample(questions_hieu, so_cau_hieu)])

        # 3. Vận dụng
        if so_cau_van_dung > 0:
            questions_van_dung = (supabase.table("cau_hoi").select("id")
                                  .eq("bai_hoc_id", bai_hoc_id)
                                  .eq("muc_do", "vận dụng")
                                  .execute().data or [])
            if len(questions_van_dung) < so_cau_van_dung: return False
            selected_question_ids.extend([q["id"] for q in random.sample(questions_van_dung, so_cau_van_dung)])

    except Exception as e:
        print(f"Lỗi khi truy vấn câu hỏi (LT): {e}")
        return False

    random.shuffle(selected_question_ids)

    # --- LOGIC MỚI: TỰ ĐỘNG TẠO SUFFIX MỨC ĐỘ ---
    level_labels = []
    if so_cau_biet > 0: level_labels.append("Biết")
    if so_cau_hieu > 0: level_labels.append("Hiểu")
    if so_cau_van_dung > 0: level_labels.append("Vận dụng")

    final_title = ten_bai
    if level_labels:
        suffix = " - ".join(level_labels)
        # Chỉ thêm nếu người dùng chưa tự tay gõ vào tiêu đề
        if f"Mức độ: {suffix}" not in ten_bai:
            final_title = f"{ten_bai} (Mức độ: {suffix})"
    # --------------------------------------------

    try:
        res_bai_tap = supabase.table("bai_tap").insert({
            "chu_de_id": chu_de_id_of_lesson,
            "bai_hoc_id": bai_hoc_id,
            "tieu_de": final_title,  # Sử dụng tên đã xử lý
            "mo_ta": f"Bài luyện tập tự động. (B:{so_cau_biet}, H:{so_cau_hieu}, VD:{so_cau_van_dung})",
            "loai_bai_tap": "luyen_tap",
            "tong_so_cau": len(selected_question_ids),
            "giao_vien_id": giao_vien_id,
            "lop_id": lop_id
        }).execute()

        if not res_bai_tap.data: return False

        bai_tap_id = res_bai_tap.data[0]["id"]
        links = [{"bai_tap_id": bai_tap_id, "cau_hoi_id": q_id} for q_id in selected_question_ids]
        supabase.table("bai_tap_cau_hoi").insert(links).execute()
        return True

    except Exception as e:
        print(f"Lỗi khi lưu bài luyện tập: {e}")
        return False