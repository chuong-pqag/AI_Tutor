# File: backend/class_test_service.py
# (BẢN CẬP NHẬT: Hỗ trợ lưu lop_id và tong_so_cau)

import random
from backend.supabase_client import supabase
from datetime import datetime


def generate_class_test(
        lop_id: str, giao_vien_id: str, ten_bai: str, chu_de_id: str,
        so_cau_biet: int, so_cau_hieu: int, so_cau_van_dung: int
):
    """
    Sinh bài KIỂM TRA CHỦ ĐỀ cho lớp.
    Lấy câu hỏi ngẫu nhiên theo cấu trúc 3 mức độ từ ngân hàng câu hỏi của chủ đề.
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
                print(f"Lỗi (KT): Không đủ {so_cau_biet} câu 'biết' (Có: {len(questions_biet)}).")
                return False
            selected_question_ids.extend([q["id"] for q in random.sample(questions_biet, so_cau_biet)])

        # 2. Lấy câu "Hiểu"
        if so_cau_hieu > 0:
            questions_hieu = (supabase.table("cau_hoi").select("id")
                              .eq("chu_de_id", chu_de_id)
                              .eq("muc_do", "hiểu")
                              .execute().data or [])
            if len(questions_hieu) < so_cau_hieu:
                print(f"Lỗi (KT): Không đủ {so_cau_hieu} câu 'hiểu' (Có: {len(questions_hieu)}).")
                return False
            selected_question_ids.extend([q["id"] for q in random.sample(questions_hieu, so_cau_hieu)])

        # 3. Lấy câu "Vận dụng"
        if so_cau_van_dung > 0:
            questions_van_dung = (supabase.table("cau_hoi").select("id")
                                  .eq("chu_de_id", chu_de_id)
                                  .eq("muc_do", "vận dụng")
                                  .execute().data or [])
            if len(questions_van_dung) < so_cau_van_dung:
                print(f"Lỗi (KT): Không đủ {so_cau_van_dung} câu 'vận dụng' (Có: {len(questions_van_dung)}).")
                return False
            selected_question_ids.extend([q["id"] for q in random.sample(questions_van_dung, so_cau_van_dung)])

    except Exception as e:
        print(f"Lỗi khi truy vấn câu hỏi (KT): {e}")
        return False

    # Xáo trộn thứ tự câu hỏi
    random.shuffle(selected_question_ids)

    # Tạo bản ghi bai_tap
    # Lưu ý: Cần đảm bảo bảng 'bai_tap' đã có cột 'lop_id' và 'tong_so_cau'
    try:
        res_bai_tap = supabase.table("bai_tap").insert({
            "chu_de_id": chu_de_id,
            "bai_hoc_id": None,
            "tieu_de": ten_bai,
            "mo_ta": f"Bài kiểm tra do GV giao.",
            "loai_bai_tap": "kiem_tra_chu_de",
            "tong_so_cau": len(selected_question_ids),  # Lưu tổng số câu
            "giao_vien_id": giao_vien_id,
            "lop_id": lop_id  # Lưu ID lớp để hiển thị đúng
        }).execute()

        if not res_bai_tap.data:
            return False

        bai_tap_id = res_bai_tap.data[0]["id"]

        # Liên kết câu hỏi vào bài tập
        links = [{"bai_tap_id": bai_tap_id, "cau_hoi_id": q_id} for q_id in selected_question_ids]
        supabase.table("bai_tap_cau_hoi").insert(links).execute()

        return True

    except Exception as e:
        print(f"Lỗi khi lưu bài kiểm tra: {e}")
        return False


def generate_practice_exercise(
        bai_hoc_id: str, giao_vien_id: str, ten_bai: str,
        so_cau_biet: int, so_cau_hieu: int, so_cau_van_dung: int,
        lop_id: str = None  # Thêm tham số lop_id
):
    """
    Sinh bài LUYỆN TẬP cho một BÀI HỌC cụ thể.
    """
    # Lấy thông tin bài học để biết thuộc chủ đề nào
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

    try:
        # Tạo bản ghi bai_tap
        res_bai_tap = supabase.table("bai_tap").insert({
            "chu_de_id": chu_de_id_of_lesson,
            "bai_hoc_id": bai_hoc_id,
            "tieu_de": ten_bai,
            "mo_ta": f"Bài luyện tập do GV giao. (B:{so_cau_biet}, H:{so_cau_hieu}, VD:{so_cau_van_dung})",
            "loai_bai_tap": "luyen_tap",
            "tong_so_cau": len(selected_question_ids),
            "giao_vien_id": giao_vien_id,
            "lop_id": lop_id  # Lưu ID lớp
        }).execute()

        if not res_bai_tap.data:
            return False

        bai_tap_id = res_bai_tap.data[0]["id"]
        links = [{"bai_tap_id": bai_tap_id, "cau_hoi_id": q_id} for q_id in selected_question_ids]
        supabase.table("bai_tap_cau_hoi").insert(links).execute()
        return True

    except Exception as e:
        print(f"Lỗi khi lưu bài luyện tập: {e}")
        return False