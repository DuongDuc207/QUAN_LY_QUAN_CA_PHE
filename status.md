# Trạng thái dự án

**Cập nhật:** 2026-11-09

**Phạm vi rà soát:** workspace gồm các ứng dụng độc lập `sprint1` đến `sprint4`.

## Hoàn thành

- Đọc cấu trúc dự án, hướng dẫn cấp gốc và hướng dẫn Sprint 3–4.
- Thay schema bổ sung theo sprint bằng hai script cập nhật theo chức năng; đồng bộ
  bản trong `sprint3/database` và `sprint4/database`.
- Cập nhật hướng dẫn khởi tạo DB và thông báo của công cụ dữ liệu mẫu.
- Thêm hướng dẫn dự án và các file theo dõi công việc.
- Kiểm tra cú pháp Python, tham chiếu schema cũ, checksum hai bản cập nhật và chạy
  thành công 8 kiểm thử bootstrap và cấu hình khóa session.
- Sửa khóa ký session mặc định ở ứng dụng gốc và bốn ứng dụng sprint; thêm `.env`
  mẫu an toàn, hướng dẫn tạo khóa và kiểm thử từ chối khóa thiếu/quá ngắn.

## Đang chờ

- Kiểm thử tích hợp với SQL Server riêng chưa chạy; hiện chỉ xác nhận tính nhất
  quán của các script SQL và không kết nối CSDL vận hành.

## Kết quả push

- Các thay đổi đã push lên nhánh `copilot/project-workspace-sync`; commit mới nhất
  `ed64ab8f52e057cad7f468138303b74cb13c5343` bao gồm bản sửa khóa session và
  cập nhật trạng thái rà soát.
- Các file `.env`, môi trường ảo, cache kiểm thử, ZIP và file rỗng bất thường đã
  được loại khỏi nội dung chuẩn bị commit.

- Nhánh: <https://github.com/DuongDuc207/QUAN_LY_QUAN_CA_PHE/tree/copilot/project-workspace-sync>
- Đã fast-forward `main` tới cùng commit `ed64ab8f52e057cad7f468138303b74cb13c5343`.
- Nhánh `main`: <https://github.com/DuongDuc207/QUAN_LY_QUAN_CA_PHE/tree/main>

## Rà soát trước merge

- Khóa session yếu/mặc định đã được loại bỏ ở ứng dụng gốc và bốn sprint.
- 8 kiểm thử bootstrap và cấu hình khóa đạt; compile Python đạt.
- Code review lại nhánh không phát hiện vấn đề nghiêm trọng.
- Đã merge fast-forward vào `main`; kiểm thử tích hợp SQL Server chưa chạy.
