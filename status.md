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
  thành công 6 kiểm thử cấp gốc.

## Đang chờ

- Kiểm thử tích hợp với SQL Server riêng chưa chạy; hiện chỉ xác nhận tính nhất
  quán của các script SQL và không kết nối CSDL vận hành.
- Cài Git for Windows, xác nhận Git Credential Manager đăng nhập tài khoản
  `DuongDuc207`, và tạo worktree riêng từ repo GitHub để chuẩn bị push an toàn.
- Repo đích hiện có ứng dụng Sprint 1 ở thư mục gốc; đã chọn giữ nguyên `main`,
  không thay thế nội dung hiện có.

## Kết quả push

- Đã push commit `ca0dac71c3f0d97b3d358147d18834ebab4a735d` lên nhánh
  `copilot/project-workspace-sync`.
- Các file `.env`, môi trường ảo, cache kiểm thử, ZIP và file rỗng bất thường đã
  được loại khỏi nội dung chuẩn bị commit.

- Nhánh: <https://github.com/DuongDuc207/QUAN_LY_QUAN_CA_PHE/tree/copilot/project-workspace-sync>
- Nhánh `main` được giữ nguyên.
- Có thể mở pull request tại:
  <https://github.com/DuongDuc207/QUAN_LY_QUAN_CA_PHE/compare/main...copilot/project-workspace-sync>
