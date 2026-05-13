# ========================
# Base image từ Airflow chính thức
# ========================
FROM apache/airflow:2.10.3

# ========================
# Chạy với quyền root để cài package hệ thống (nếu cần)
# ========================
USER root

# Cài thêm một số thư viện hệ thống hữu ích
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

    USER airflow
# ========================
# Copy và cài Python dependencies
# ========================
COPY requirements.txt /requirements.txt

# Cài packages với pip (tối ưu cache)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
       -r /requirements.txt \
       --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.3/constraints-3.12.txt"
# ========================
# (Tùy chọn) Pre-download embedding model để nhanh hơn
# ========================
# Uncomment 2 dòng dưới nếu muốn model được tải sẵn khi build (tăng kích thước image nhưng nhanh khi chạy)
# RUN python -c "from sentence_transformers import SentenceTransformer; \
#     SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# ========================
# Trở lại user airflow (bắt buộc của Airflow Docker)
# ========================
USER airflow

# ========================
# Set working directory mặc định là project của bạn
# ========================
WORKDIR /opt/airflow/project