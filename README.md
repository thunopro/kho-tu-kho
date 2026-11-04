# Kho từ

Ứng dụng web đơn giản để lưu và luyện từ vựng tiếng Anh. Dữ liệu lưu trên trình duyệt của bạn.

## Cách dùng

- **Thư mục / File**: bấm “Thư mục mới” hoặc “File mới”. Bấm vào thư mục để mở, dùng “Quay lại” để trở về.
- **Thêm từ**: mở một file, nhập từ rồi bấm “Thêm”, xác nhận “Lưu”. Từ mới được đọc to ngay.
- **Nghe**: bấm “Nghe” để nghe từ hai lần.
- **Phiên âm (IPA)**: hiện dưới mỗi từ, theo giọng đang chọn (UK/US).
- **Cambridge**: mở từ điển Cambridge để đối chiếu.
- **Phím 1–5**: đọc lại từ vừa nghe gần nhất (1 là từ gần nhất). Bấm khi không gõ gì.
- **Đổi tên / Di chuyển / Xóa**: nằm bên phải mỗi thư mục hoặc file.

Giới hạn: tối đa 1000 từ, 100 file, 60 thư mục, lồng tối đa 4 cấp; mỗi từ tối đa 80 ký tự, tên tối đa 40 ký tự.

## Chạy

Mở `index.html` trong trình duyệt, hoặc chạy `python3 -m http.server 8000` rồi mở `http://localhost:8000`.

Audio lấy từ `api/speak.py` (Edge neural TTS), chạy trên Vercel.
