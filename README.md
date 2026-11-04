# Kho từ

Ứng dụng web nhỏ để quản lý và luyện phát âm từ vựng tiếng Anh, giao diện kiểu VS Code: thư mục bên trái, danh sách từ ở giữa, terminal ở dưới. Audio được tạo tại Vercel bằng Microsoft Edge neural TTS.

## Chạy ứng dụng

```bash
npx vercel dev
```

Hoặc `python3 -m http.server 8000` để xem giao diện tĩnh. Khi đó audio và publish vẫn gọi production trên Vercel (CORS cho phép `localhost:8000`).

## Cách dùng

- **`/` (kho trên máy)**: làm việc trên dữ liệu của trình duyệt, không cần đăng nhập.
  - Gõ `add <từ>` trong terminal, xác nhận `y` để lưu. Từ mới được phát âm ngay.
  - Tạo thư mục để gom từ: `mkdir week1`, `mkdir -p week2/day1`.
  - Bấm **Publish** (hoặc gõ `publish`) để đưa kho lên server. Lần đầu tạo kho mới với số ID tự tăng; trình duyệt nhớ khóa để lần sau publish cập nhật đúng kho đó.
- **`/1`, `/2`, ... (kho đã publish)**: chỉ xem và nghe, các lệnh ghi bị tắt.
- **Phím 1–5**: phát từ gần nhất (1 là từ vừa phát gần nhất). Bấm khi ô nhập đang trống, không cần đưa con trỏ vào đâu.
- **C**: mở Cambridge Dictionary để đối chiếu trọng âm và cách đọc. Cột IPA lấy từ dictionaryapi.dev, theo giọng đang chọn (UK/US).
- **Ctrl+`**: ẩn/hiện terminal.

Các lệnh terminal: `help`, `pwd`, `ls [-l]`, `cd`, `tree`, `mkdir [-p]`, `rmdir`, `rm [-r]`, `mv`, `cat`, `add`, `play`, `publish`, `history`, `clear`. Tab để hoàn thành tên, mũi tên lên/xuống để gọi lại lệnh cũ.

Giới hạn: tối đa 200 từ, 60 thư mục, lồng tối đa 4 cấp; mỗi từ tối đa 80 ký tự; dữ liệu gửi lên tối đa 64KB.

## Backend

- `api/speak.py`: trả audio MP3 từ Edge neural TTS. `?voices=1` trả danh sách giọng; để thêm giọng mới, thêm một mục vào `VOICES`.
- `api/kho.py`: `GET /api/kho?id=N` đọc kho đã publish; `POST /api/kho` với `action: "publish"` tạo hoặc cập nhật kho. Dữ liệu kiểu cũ (danh sách phẳng) được đọc như thư mục `week1`.
- Dữ liệu kho lưu trong Neon Postgres (bảng `kho`), kết nối qua biến môi trường `DATABASE_URL` của Vercel project.
- `vercel.json` rewrite `/:id` về `index.html` để các link `/N` hoạt động.
