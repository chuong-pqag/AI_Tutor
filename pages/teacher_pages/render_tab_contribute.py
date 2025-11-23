# ===============================================
# ✍️ Module Đóng góp Câu hỏi - render_tab_contribute.py
# (ĐÃ CẬP NHẬT: LỌC ĐA CẤP CHỦ ĐỀ/BÀI HỌC)
# ===============================================
import streamlit as st
import uuid
from backend.supabase_client import supabase


def render(giao_vien_id):
    st.subheader("✍️ Đóng góp Ngân hàng đề")
    st.info("Câu hỏi bạn tạo sẽ ở trạng thái **'Chờ duyệt'**. Admin sẽ kiểm tra trước khi đưa vào ngân hàng chung.")

    # --- 1. TẢI DỮ LIỆU CẦN THIẾT ---
    # Lấy danh sách Môn học
    try:
        mon_hoc_res = supabase.table("mon_hoc").select("*").execute()
        mon_hoc_df = mon_hoc_res.data or []

        # Lấy danh sách Chủ đề (để lọc)
        chu_de_res = supabase.table("chu_de").select("id, ten_chu_de, mon_hoc, lop, tuan").execute()
        chu_de_data = chu_de_res.data or []

        # Lấy danh sách Bài học (để lọc)
        bai_hoc_res = supabase.table("bai_hoc").select("id, ten_bai_hoc, chu_de_id, thu_tu").execute()
        bai_hoc_data = bai_hoc_res.data or []

    except Exception as e:
        st.error(f"Lỗi tải dữ liệu: {e}")
        return

    # --- 2. FORM NHẬP LIỆU VỚI BỘ LỌC ĐA CẤP ---
    with st.form("contribute_question_form", clear_on_submit=True):

        # BỐ CỤC: CHỌN VỊ TRÍ CÂU HỎI
        st.markdown("##### 📍 Vị trí câu hỏi")
        c1, c2, c3 = st.columns(3)

        # BƯỚC 1: CHỌN KHỐI
        with c1:
            lop = st.selectbox("1. Khối lớp *", [1, 2, 3, 4, 5])

        # BƯỚC 2: CHỌN MÔN HỌC (Lọc theo Khối)
        with c2:
            # Lọc môn học áp dụng cho khối này
            valid_mon_hocs = [
                m['ten_mon'] for m in mon_hoc_df
                if not m.get('khoi_ap_dung') or lop in m.get('khoi_ap_dung', [])
            ]
            mon_hoc_ten = st.selectbox("2. Môn học *", valid_mon_hocs if valid_mon_hocs else ["Toán",
                                                                                              "Tiếng Việt"])  # Fallback nếu data rỗng

        # BƯỚC 3: CHỌN CHỦ ĐỀ (Lọc theo Khối & Môn)
        with c3:
            valid_chu_des = [
                cd for cd in chu_de_data
                if cd['lop'] == lop and cd['mon_hoc'] == mon_hoc_ten
            ]
            # Sort theo tuần
            valid_chu_des.sort(key=lambda x: x['tuan'])

            chu_de_opts = {f"Tuần {cd['tuan']}: {cd['ten_chu_de']}": cd['id'] for cd in valid_chu_des}

            if not chu_de_opts:
                st.warning(f"Chưa có chủ đề nào cho {mon_hoc_ten} - Khối {lop}.")
                chu_de_ten_display = None
                selected_chu_de_id = None
            else:
                chu_de_ten_display = st.selectbox("3. Chủ đề *", list(chu_de_opts.keys()))
                selected_chu_de_id = chu_de_opts[chu_de_ten_display]

        # BƯỚC 4: CHỌN BÀI HỌC (Tùy chọn - Lọc theo Chủ đề)
        selected_bai_hoc_id = None
        if selected_chu_de_id:
            valid_bai_hocs = [
                bh for bh in bai_hoc_data
                if bh['chu_de_id'] == selected_chu_de_id
            ]
            valid_bai_hocs.sort(key=lambda x: x.get('thu_tu', 0))

            bai_hoc_opts = {f"{bh.get('thu_tu', 0)}. {bh['ten_bai_hoc']}": bh['id'] for bh in valid_bai_hocs}
            bai_hoc_opts_with_none = {"(Câu hỏi chung của chủ đề)": None}
            bai_hoc_opts_with_none.update(bai_hoc_opts)

            bai_hoc_display = st.selectbox("4. Bài học (Tùy chọn)", list(bai_hoc_opts_with_none.keys()))
            selected_bai_hoc_id = bai_hoc_opts_with_none[bai_hoc_display]

        st.markdown("---")

        # BỐ CỤC: NỘI DUNG CÂU HỎI
        st.markdown("##### 📝 Nội dung câu hỏi")

        col_type, col_level = st.columns(2)
        with col_type:
            loai = st.selectbox("Loại câu hỏi", ["mot_lua_chon", "nhieu_lua_chon", "dien_khuyet"])
        with col_level:
            muc_do = st.selectbox("Mức độ", ["biết", "hiểu", "vận dụng"])

        noi_dung = st.text_area("Nội dung (Chữ) *", height=100)
        hinh_anh_url = st.text_input("Link Ảnh minh họa (nếu có)",
                                     help="Dán URL ảnh công khai (ví dụ từ Supabase Storage)")

        st.markdown("**Đáp án:**")
        dap_an_dung_raw = st.text_area("Đáp án ĐÚNG * (Mỗi dòng 1 đáp án / hoặc Link ảnh)", height=80,
                                       help="Nếu là trắc nghiệm 1 lựa chọn, chỉ nhập 1 dòng.")

        dap_an_khac_raw = ""
        if loai != "dien_khuyet":
            dap_an_khac_raw = st.text_area("Đáp án SAI (Mỗi dòng 1 đáp án / hoặc Link ảnh)", height=80)

        st.markdown("---")
        submitted = st.form_submit_button("🚀 Gửi câu hỏi duyệt", width='stretch')

        if submitted:
            # VALIDATION
            if not selected_chu_de_id:
                st.error("Bắt buộc phải chọn Chủ đề.")
            elif not noi_dung and not hinh_anh_url:
                st.error("Phải nhập Nội dung hoặc Link ảnh.")
            elif not dap_an_dung_raw:
                st.error("Phải có ít nhất 1 đáp án đúng.")
            else:
                try:
                    # Xử lý dữ liệu
                    dap_an_dung = [s.strip() for s in dap_an_dung_raw.split('\n') if s.strip()]
                    dap_an_khac = [s.strip() for s in dap_an_khac_raw.split('\n') if s.strip()]

                    # Tạo ID
                    new_id = str(uuid.uuid4())

                    insert_data = {
                        "id": new_id,
                        "chu_de_id": selected_chu_de_id,  # Đã có ID chính xác
                        "bai_hoc_id": selected_bai_hoc_id,  # Có thể là None
                        "loai_cau_hoi": loai,
                        "noi_dung": noi_dung,
                        "hinh_anh_url": hinh_anh_url if hinh_anh_url else None,
                        "dap_an_dung": dap_an_dung,
                        "dap_an_khac": dap_an_khac,
                        "muc_do": muc_do,
                        "nguoi_tao_id": giao_vien_id,
                        "trang_thai_duyet": "pending"
                    }

                    # Insert vào CSDL
                    supabase.table("cau_hoi").insert(insert_data).execute()

                    # Xếp hàng tạo TTS (nếu có nội dung chữ)
                    if noi_dung:
                        supabase.table("task_queue").insert({
                            "task_type": "tts_generation",
                            "status": "pending",
                            "payload": {"question_id": new_id, "noi_dung": noi_dung}
                        }).execute()

                    st.success("✅ Đã gửi câu hỏi thành công! Cảm ơn đóng góp của bạn.")

                except Exception as e:
                    st.error(f"Lỗi khi gửi: {e}")

    # --- Danh sách câu hỏi đã gửi ---
    st.markdown("---")
    st.subheader("🗃️ Lịch sử đóng góp của bạn")
    try:
        my_questions = supabase.table("cau_hoi").select(
            "noi_dung, muc_do, trang_thai_duyet, created_at, chu_de(ten_chu_de)"
        ).eq("nguoi_tao_id", giao_vien_id).order("created_at", desc=True).limit(10).execute().data

        if my_questions:
            for q in my_questions:
                status_icon = "⏳" if q['trang_thai_duyet'] == 'pending' else (
                    "✅" if q['trang_thai_duyet'] == 'approved' else "❌")
                chu_de_ten = q.get('chu_de', {}).get('ten_chu_de', 'N/A') if q.get('chu_de') else 'N/A'

                with st.expander(f"{status_icon} [{q['muc_do']}] {q['noi_dung'][:50]}..."):
                    st.write(f"**Chủ đề:** {chu_de_ten}")
                    st.write(f"**Trạng thái:** {q['trang_thai_duyet']}")
                    st.write(f"**Nội dung đầy đủ:** {q['noi_dung']}")
        else:
            st.caption("Bạn chưa đóng góp câu hỏi nào.")
    except Exception as e:
        st.error("Không thể tải lịch sử đóng góp.")