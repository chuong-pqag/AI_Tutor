# AI Tutor — Scaffold (Streamlit + Supabase)

This scaffold contains a minimal, runnable starting point for the AI Tutor:
- Frontend: Streamlit apps (student and teacher)
- Backend helpers: Supabase client, data service, recommender placeholder
- DB schema SQL and CSV seed data for topics and lessons
- Training script placeholder for ML model

## Quickstart (local)
1. Create a Supabase project and get SUPABASE_URL and SUPABASE_KEY (service role key for server-side operations).
2. Run the SQL schema in `sql/schema.sql` in Supabase SQL editor.
3. Import CSVs in `data/` into the `chu_de` / `lessons` / `question_bank` tables (or use the SQL editor).
4. Create a `.env` file in project root with:
   SUPABASE_URL=your_url
   SUPABASE_KEY=your_key
5. Create a Python virtual env and install requirements:
   pip install -r requirements.txt
6. Run Streamlit apps:
   streamlit run frontend/student_ui.py
   streamlit run frontend/teacher_dashboard.py

## Notes
- The Supabase client uses the `supabase` Python package.
- This scaffold uses placeholders for video links and question bank for demo purposes.
- Train the simple Decision Tree with `backend/train_model.py` when you have `ket_qua_test` data.
