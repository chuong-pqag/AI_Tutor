import streamlit as st
import pandas as pd
from backend.supabase_client import supabase

st.set_page_config(page_title='AI Tutor - Teacher', layout='wide')
st.title('📊 Teacher Dashboard (Demo)')

lop = st.selectbox('Chọn lớp', [2,3,'Tất cả'])
tuan = st.number_input('Tuần', 1, 35, 1)

query = supabase.table('ket_qua_test').select('*')
if lop != 'Tất cả':
    hs = supabase.table('hoc_sinh').select('id').eq('lop', lop).execute().data
    hs_ids = [h['id'] for h in hs]
    query = query.in_('hoc_sinh_id', hs_ids)
query = query.eq('tuan', tuan)
res = query.execute()
data = res.data if res.data else []
if data:
    df = pd.DataFrame(data)
    st.dataframe(df)
    st.metric('Điểm TB', f"{df['diem'].astype(float).mean():.2f}")
    st.download_button('Tải CSV', df.to_csv(index=False).encode('utf-8'), file_name=f'report_week_{tuan}.csv')
else:
    st.info('Chưa có dữ liệu cho bộ lọc này.')