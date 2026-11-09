# Lịch sử cộng tác với AI

Tài liệu này ghi lại các quyết định và công việc đã thực hiện cùng AI trong phiên
làm việc ngày 09-11-2026. Không ghi lại thông tin xác thực, token hoặc bí mật.

## Mục tiêu

- Rà soát cấu trúc dự án quản lý quán cà phê.
- Tạo nhật ký lỗi, trạng thái và danh sách công việc.
- Chuẩn hóa hướng dẫn dự án và thay schema Sprint 4 bằng hai file cập nhật DB.
- Chuẩn bị đưa mã lên repo GitHub do người dùng cung cấp, không ghi đè nội dung
  đang có trên nhánh `main`.

## Quyết định và kết quả

1. Rà soát cấu trúc cho thấy workspace có bốn ứng dụng độc lập từ `sprint1` đến
   `sprint4`. Repo GitHub được cung cấp hiện chứa ứng dụng Sprint 1 ở thư mục gốc.
2. Theo lựa chọn của người dùng, giữ nguyên nhánh `main` và chọn cách tổ chức bổ
   sung thay vì thay thế nội dung nhánh này.
3. Theo lựa chọn của người dùng, thay `schema_sprint4.sql` bằng hai script cập
   nhật theo chức năng, đồng bộ trong `sprint3/database` và `sprint4/database`:
   - `update_01_promotions.sql`: bảng khuyến mãi và lượt sử dụng.
   - `update_02_staff_schedule.sql`: bảng nhân viên, ca làm việc và lịch làm việc.
4. Cập nhật README gốc, README Sprint 3 và Sprint 4, cùng thông báo trong công cụ
   tạo dữ liệu mẫu để phản ánh thứ tự áp dụng schema và seed.
5. Tạo `.gitignore`, `logbug.md`, `status.md` và `todos.md`.

## Kiểm tra

- `py -m py_compile sprint4\tao_du_lieu_mau.py`: đạt.
- Hai bản sao của mỗi script SQL có cùng SHA-256.
- Không còn tham chiếu đến tên `schema_sprint4.sql` trong nội dung đã rà soát.
- `py -m unittest discover -s tests -v`: 6 kiểm thử đạt khi bật UTF-8 qua
  `PYTHONUTF8=1`. Lần chạy đầu gặp lỗi encoding của console Windows; không cần
  sửa mã nguồn để xử lý.
- Rà soát nhánh trước merge phát hiện khóa ký session mặc định công khai. Đã thay
  cấu hình trong app gốc và bốn sprint bằng yêu cầu khóa ít nhất 32 ký tự, bỏ giá
  trị mẫu có thể dùng, thêm hướng dẫn tạo khóa và test thiếu/ngắn/đủ độ dài.
- `tests.test_bootstrap` và `tests.test_secret_settings`: 8 kiểm thử đạt trên nhánh.
- `compileall` trên cấu hình và kiểm thử Python: đạt. Kiểm thử DB/SQL Server chưa chạy.
- Chưa chạy kiểm thử tích hợp hoặc áp dụng SQL lên SQL Server.
- Rà soát trước merge phát hiện khóa ký session mặc định công khai trong ứng dụng
  gốc và bốn thư mục sprint; việc sửa lỗi đang được triển khai, chưa merge.

## Tình trạng đưa mã lên GitHub

Git for Windows đã được cài và Git Credential Manager xác nhận tài khoản
`DuongDuc207` đã đăng nhập. Worktree riêng được tạo từ `main` trên nhánh
`copilot/project-workspace-sync`. Các commit khởi tạo và tài liệu đã được push;
bản sửa khóa session đang được kiểm thử và chờ push. Nhánh `main` chưa bị thay đổi.

Nhánh: <https://github.com/DuongDuc207/QUAN_LY_QUAN_CA_PHE/tree/copilot/project-workspace-sync>

Tạo pull request: <https://github.com/DuongDuc207/QUAN_LY_QUAN_CA_PHE/compare/main...copilot/project-workspace-sync>

Trong phiên, người dùng đã gửi thông tin xác thực GitHub qua chat. AI khuyến nghị
thu hồi thông tin đó ngay và đăng nhập lại an toàn trên máy bằng Git Credential
Manager hoặc GitHub CLI. Giá trị thông tin xác thực không được lưu trong tài liệu
này.
