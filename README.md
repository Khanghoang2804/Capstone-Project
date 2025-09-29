**1. Capstone Project 1**

📌 **Project Overview**
Đây là một dự án phân tích và xây dựng hệ thống gợi ý khóa học trên nền tảng Udemy. Mục tiêu là vừa phân tích tình hình kinh doanh, xu hướng học tập, vừa áp dụng machine learning để phát triển mô hình gợi ý thông minh hỗ trợ người dùng chọn khóa học phù hợp.

🔍 **Nội dung chính**

**Thu thập & Tiền xử lý dữ liệu**

Cào dữ liệu từ Udemy bằng Selenium và BeautifulSoup.

Xử lý dữ liệu: loại bỏ trùng lặp/null, chuẩn hóa giá, tách chuỗi để tạo trường mới (rating, instructor info).

Lưu trữ dữ liệu thành các file CSV, hợp nhất để phân tích.

**Phân tích dữ liệu & Trực quan hóa**

Sử dụng Tableau để trực quan hóa doanh thu, số học viên, phân khúc giá và danh mục khóa học.

Kết quả:

Development chiếm ~71% doanh thu (127.156 tỷ VND).

Doanh thu tập trung ở phân khúc giá 1.5–2.5 triệu VND.

Các yếu tố ảnh hưởng mạnh đến số học viên: số review, giá, doanh thu, số lượng học viên của giảng viên.

Khóa học dài (>10h) có nhiều học viên hơn gấp 3 lần so với khóa học ngắn.

**Xây dựng hệ thống gợi ý (Machine Learning)**

Sử dụng TF-IDF cho dữ liệu văn bản (mô tả khóa học).

Chuẩn hóa dữ liệu số (price, rating, num_reviews, time, …).

One-hot encoding cho dữ liệu phân loại (category, sub-category, language).

Thử nghiệm các mô hình:

Nearest Neighbors (cosine similarity)

Truncated SVD + Nearest Neighbors (hiệu quả nhất, cosine similarity = 0.95)

K-Means Clustering

Kết quả: SVD + NN vượt trội, loại bỏ nhiễu tốt hơn.

**Ứng dụng Web & LLM**

Xây dựng giao diện web bằng Streamlit.

Cho phép người dùng nhập sở thích → hệ thống gợi ý khóa học tương tự.

Tích hợp Google Gemini để giải thích lý do nên chọn các khóa học.

**Hạn chế**
Dữ liệu bị giới hạn do thời gian crawl lâu (1–2 phút/khóa).

Chưa triển khai được mô hình RAG chatbot do thiếu dữ liệu văn bản mô tả sâu.

Quá trình thực hiện chưa có pipeline tối ưu → mất nhiều thời gian xử lý.
