# Word Cabinet — Kho từ khó

Ứng dụng web nhỏ để nhập, xác nhận, lưu và luyện phát âm từ vựng tiếng Anh. Danh sách được lưu trong `localStorage` của trình duyệt trên thiết bị hiện tại.

## Chạy ứng dụng

Trong thư mục dự án, chạy:

```bash
python3 -m http.server 8000
```

Sau đó mở <http://localhost:8000>.

## Cách dùng

1. Nhập một từ hoặc cụm từ rồi bấm **Thêm vào kho**.
2. Chọn **Xác nhận lưu** để đưa từ vào danh sách.
3. Bấm vào từ hoặc biểu tượng loa để nghe audio giọng người hai lần.
4. Chọn giọng Anh-Anh/Anh-Mỹ; bấm **C** cạnh từ để tra trực tiếp trên Cambridge Dictionary.

Audio ưu tiên bản ghi giọng người do Free Dictionary API cung cấp. Nếu API chưa có audio cho một từ, ứng dụng dùng giọng đọc tiếng Anh UK/US có sẵn trong trình duyệt; nút Cambridge cạnh từ đó mở mục từ để đối chiếu phát âm. Danh sách từ được lưu cục bộ trên thiết bị, không tải lên máy chủ.
