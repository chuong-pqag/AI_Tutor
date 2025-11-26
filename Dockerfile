# File: Dockerfile trên GitHub
FROM python:3.9

WORKDIR /code

# Copy requirements và cài đặt
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy toàn bộ code vào thư mục làm việc
COPY . .

# Hugging Face Spaces yêu cầu chạy ở port 7860
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0", "--server.port", "7860"]
