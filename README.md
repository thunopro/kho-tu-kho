# Word Cabinet — Kho từ khó

Ứng dụng web nhỏ để nhập, xác nhận, lưu và luyện phát âm từ vựng tiếng Anh. Danh sách được lưu trong `localStorage` của trình duyệt trên thiết bị hiện tại. Audio được tạo tại Vercel bằng Microsoft Edge neural TTS (giọng Sonia UK hoặc Aria US), không phụ thuộc voice cài trong máy người dùng.

## Chạy ứng dụng

Trong thư mục dự án, chạy:

```bash
npx vercel dev
```

Sau đó mở URL local do Vercel CLI in ra. Có thể dùng `python3 -m http.server 8000` để xem giao diện tĩnh; trong trường hợp đó audio vẫn gọi API production trên Vercel.

## Cách dùng

1. Nhập một từ hoặc cụm từ rồi bấm **Thêm vào kho**.
2. Chọn **Xác nhận lưu** để đưa từ vào danh sách.
3. Bấm vào từ hoặc biểu tượng loa để nghe audio giọng người hai lần.
4. Chọn giọng Anh-Anh/Anh-Mỹ; bấm **C** cạnh từ để nghe/đối chiếu trực tiếp trên Cambridge Dictionary.

Endpoint `/api/speak` trả audio MP3 từ Microsoft Edge neural TTS, có cache CDN một ngày và cho phép gọi từ Vercel/GitHub Pages. Không dùng giọng tổng hợp cài cục bộ trong trình duyệt nữa. Cambridge vẫn có liên kết riêng để đối chiếu từ điển, trọng âm và nghĩa theo ngữ cảnh. Danh sách từ được lưu cục bộ trên thiết bị, không tải lên máy chủ.
