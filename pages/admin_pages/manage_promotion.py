# File: pages/admin_pages/manage_promotion.py
import streamlit as st
import pandas as pd
import datetime  # Cần import datetime hoặc pd.Timestamp
from . import crud_utils
from backend.supabase_client import supabase
# Import các hàm cần thiết từ backend
from backend.data_service import get_current_school_year, run_full_promotion


# --- Helper function for updating configuration (Cần thiết cho phần config) ---
def update_config(key: str, value: str):
    try:
        supabase.table("cau_hinh_chung").update({"value": value, "updated_at": pd.Timestamp.now().isoformat()}).eq(
            "key", key).execute()
        crud_utils.clear_all_cached_data()
        return True
    except Exception as e:
        st.error(f"Lỗi cập nhật cấu hình: {e}")
        return False


def render():
    st.subheader("🎓 Quản lý Năm học & Lên lớp")

    # Load data
    lop_df = crud_utils.load_data("lop_hoc").sort_values(by="khoi")
    current_year = get_current_school_year()

    if not current_year:
        st.warning("⚠️ Vui lòng cấu hình 'current_school_year' trong bảng cau_hinh_chung trước.")
        return

    st.markdown("---")

    # ======================================================
    # PHẦN 1: CẤU HÌNH NĂM HỌC HIỆN TẠI
    # ======================================================

    # Calculate next year
    try:
        start_year = int(current_year.split('-')[0])
        next_year = f"{start_year + 1}-{start_year + 2}"
    except:
        next_year = "Năm học không hợp lệ"

    with st.expander(f"⚙️ Cấu hình Năm học (Hiện tại: {current_year})", expanded=False):
        st.markdown("#### Cập nhật Năm học")

        # Tách năm học để gợi ý năm tiếp theo
        default_new_year = next_year
        if next_year == "Năm học không hợp lệ":
            default_new_year = f"{pd.Timestamp.now().year}-{pd.Timestamp.now().year + 1}"

        with st.form("set_school_year_form"):
            new_year_input = st.text_input("Nhập Năm học mới (Ví dụ: 2026-2027)", value=default_new_year)

            if st.form_submit_button("💾 Lưu Năm học mới", type="primary"):
                if update_config("current_school_year", new_year_input):
                    st.success(f"Năm học đã được cập nhật thành: **{new_year_input}**.")
                    st.rerun()

    st.markdown("---")

    # ======================================================
    # PHẦN 2: THỰC HIỆN LÊN LỚP (PROMOTION)
    # ======================================================

    st.markdown(f"#### ⬆️ Thực hiện Lên lớp (Chuyển khối cho Năm học **{next_year}**)")

    if lop_df.empty:
        st.warning("Chưa có lớp học nào được tạo trong hệ thống.")
        return

    # Lấy dữ liệu học sinh và lớp để tính trạng thái
    all_students_df = crud_utils.load_data("hoc_sinh")

    # Chỉ xem xét Khối 1-5 (tiểu học)
    PROMOTION_STEPS = {1: 2, 2: 3, 3: 4, 4: 5}
    GRADUATING_KHOI = 5
    promotion_status_df = lop_df[lop_df['khoi'].between(1, 5)].copy()

    def get_student_count(khoi):
        # Lấy ID của các lớp thuộc Khối hiện tại
        lop_ids_in_khoi = promotion_status_df[promotion_status_df['khoi'] == khoi]['id'].tolist()
        # Đếm số học sinh thuộc các lớp đó (sử dụng .astype(str) để an toàn với UUID)
        return all_students_df[all_students_df['lop_id'].astype(str).isin(lop_ids_in_khoi)].shape[0]

    with st.expander(f"✨ Trạng thái Khối hiện tại (Sẵn sàng Lên lớp)", expanded=True):
        st.caption("Thao tác này sẽ chuyển học sinh lên khối tiếp theo và cập nhật năm học chung của hệ thống.")

        with st.form("promotion_form"):
            st.warning(
                f"Thao tác này là không thể hoàn tác (UNDO) trên CSDL sản phẩm. Năm học áp dụng: **{next_year}**")

            # --- Promotion Steps Status Table ---
            status_data = []
            eligible_for_promotion = False
            for old_khoi, new_khoi in PROMOTION_STEPS.items():
                student_count = get_student_count(old_khoi)
                status_data.append({
                    "Khối Hiện tại": old_khoi,
                    "Lên Khối": str(new_khoi),  # <--- ĐÃ SỬA (kiểu string)
                    "Số HS": student_count
                })
                if student_count > 0: eligible_for_promotion = True

            # Add graduating class
            k5_count = get_student_count(GRADUATING_KHOI)
            status_data.append({
                "Khối Hiện tại": GRADUATING_KHOI,
                "Lên Khối": "Tốt nghiệp",
                "Số HS": k5_count
            })
            if k5_count > 0: eligible_for_promotion = True

            st.dataframe(pd.DataFrame(status_data), hide_index=True)

            # --- Execution Button ---
            if not eligible_for_promotion:
                st.info("Chưa có học sinh nào để thực hiện thao tác Lên lớp.")
                promote_button = st.form_submit_button("❌ Bắt đầu Lên lớp", disabled=True)
            else:
                st.markdown("---")
                promote_button = st.form_submit_button(f"🚀 XÁC NHẬN LÊN LỚP cho năm học {next_year}")

            if promote_button:

                # Check for existing classes in the next year (Guardrail)
                existing_next_year_classes_res = supabase.table("lop_hoc").select("id").eq("nam_hoc", next_year).limit(
                    1).execute()
                if existing_next_year_classes_res.data:
                    st.error(
                        f"Lỗi: Đã tìm thấy các lớp học đã tồn tại cho năm học {next_year}. Vui lòng xóa chúng trước hoặc kiểm tra lại cấu hình.")
                    st.stop()

                # 1. Run the promotion logic
                try:
                    with st.spinner(f"Đang xử lý lên lớp cho năm học {next_year}..."):

                        # Gọi hàm backend thực sự (Phase 3 logic)
                        promotion_results = run_full_promotion(next_year)

                        # 2. Update the Current School Year in cau_hinh_chung (Nếu thành công)
                        if update_config("current_school_year", next_year):

                            st.success(f"✅ Đã hoàn thành quy trình lên lớp cho năm học {next_year}!")
                            st.caption(
                                f"Tổng số HS chuyển lớp: **{promotion_results['promoted']}** | HS tốt nghiệp: **{promotion_results['graduated']}**")
                            st.caption("Hệ thống đã được cập nhật, vui lòng kiểm tra lại danh sách lớp.")

                            crud_utils.clear_all_cached_data()  # Clear cache for all student/class data
                            st.rerun()
                        else:
                            st.error("Lỗi cập nhật năm học chung. Không thể hoàn tất quy trình.")

                except Exception as e:
                    st.error(f"❌ Lỗi nghiêm trọng trong quá trình lên lớp: {e}")
                    st.caption(
                        "Quá trình chuyển lớp đã bị rollback một phần (hoặc không thành công). Vui lòng kiểm tra log CSDL.")