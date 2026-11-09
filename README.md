# Quản lý quán cà phê

Ứng dụng quản lý hoạt động quán cà phê, gồm đăng nhập và phân quyền, thực đơn,
bán hàng, kho, nhà cung cấp, khuyến mãi, báo cáo, nhân viên và lịch làm việc.

## Các phiên bản ứng dụng

Mỗi thư mục `sprint1` đến `sprint4` là một ứng dụng Flask độc lập, có môi trường
Python, cấu hình và bộ kiểm thử riêng. Có thể chạy từng phiên bản mà không cần
cài đặt hay khởi động phiên bản trước.

| Thư mục | Chức năng chính | Cổng mặc định |
| --- | --- | --- |
| `sprint1` | Đăng nhập, phân quyền, tài khoản, danh mục và thực đơn | 5001 |
| `sprint2` | Đơn hàng, thanh toán và hóa đơn | 5002 |
| `sprint3` | Kho, công thức pha chế, nhà cung cấp và nhập hàng | 5003 |
| `sprint4` | Khuyến mãi, báo cáo, nhân viên, ca và lịch làm việc | 5004 |

`sprint4` là phiên bản đầy đủ tính năng nhất. README trong từng thư mục có hướng
dẫn chi tiết cho ứng dụng tương ứng.

## Công nghệ

- Python 3.12
- Flask 3.x, Jinja2, HTML, CSS và JavaScript
- Microsoft SQL Server, `pyodbc` và Microsoft ODBC Driver for SQL Server
- API có tiền tố `/api/v1`

## Yêu cầu

- Windows và Python 3.12 có lệnh `py`.
- SQL Server đã khởi động, có thể kết nối từ máy chạy ứng dụng.
- ODBC Driver tương ứng với cấu hình `DB_DRIVER`; cài `sqlcmd` nếu cần khởi tạo
  cơ sở dữ liệu bằng các lệnh bên dưới.
- Kết nối Internet ở lần chạy đầu để cài các gói Python vào môi trường riêng của
  phiên bản đang chạy.

## Cài đặt và chạy Sprint 4

Từ thư mục gốc dự án, mở PowerShell:

```powershell
cd sprint4
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Chỉnh `.env` theo SQL Server của bạn (`DB_SERVER`, `DB_NAME`, `DB_DRIVER`, và
thông tin đăng nhập nếu không dùng Windows Authentication). Đặt
`FLASK_SECRET_KEY` thành giá trị bí mật riêng trước khi triển khai.

Nếu cần tạo cơ sở dữ liệu mới, chạy lần lượt các script sau trong thư mục `sprint4`:

```powershell
sqlcmd -S "localhost\SQL2022EXP" -E -d QuanLyCaPhe -i database\schema.sql -b
sqlcmd -S "localhost\SQL2022EXP" -E -d QuanLyCaPhe -i database\schema_sprint2.sql -b -f 65001
sqlcmd -S "localhost\SQL2022EXP" -E -d QuanLyCaPhe -i database\schema_sprint3.sql -b -f 65001
sqlcmd -S "localhost\SQL2022EXP" -E -d QuanLyCaPhe -i database\update_01_promotions.sql -b -f 65001
sqlcmd -S "localhost\SQL2022EXP" -E -d QuanLyCaPhe -i database\update_02_staff_schedule.sql -b -f 65001
sqlcmd -S "localhost\SQL2022EXP" -E -d QuanLyCaPhe -i database\seed.sql -b -f 65001
py tao_tai_khoan.py
py app.py
```

`seed.sql` tạo các vai trò và quyền mặc định, không tạo tài khoản hay dữ liệu món
mẫu. Tạo tài khoản quản trị đầu tiên bằng `py tao_tai_khoan.py`, sau đó mở
<http://localhost:5004>. Ứng dụng tự tạo `.venv` và cài `requirements.txt` trong
lần chạy đầu.

Để chạy phiên bản khác, vào thư mục tương ứng rồi dùng `py app.py`; xem README
riêng của phiên bản đó để biết schema cần thiết. Đặt `PORT` trong `.env` để đổi
cổng mặc định.

## Cập nhật cơ sở dữ liệu

Các script `schema.sql`, `schema_sprint2.sql` và `schema_sprint3.sql` là các phần
schema nền hiện có. Phần khuyến mãi và nhân sự được cung cấp dưới dạng hai cập
nhật tăng dần, không phụ thuộc tên sprint:

1. `database\update_01_promotions.sql` tạo bảng khuyến mãi và lượt sử dụng.
2. `database\update_02_staff_schedule.sql` tạo bảng nhân viên, ca làm việc và lịch
   làm việc.

Chạy hai cập nhật sau schema nền, theo đúng thứ tự ở trên. Chúng bỏ qua bảng đã
tồn tại và không xóa dữ liệu. Sau khi cập nhật schema, chạy lại `seed.sql` để nạp
quyền mới. Các script này được lưu đồng nhất trong thư mục `database` của cả
`sprint3` và `sprint4`.

## Kiểm thử

Kiểm tra cơ chế khởi động độc lập của bốn phiên bản:

```powershell
py -m unittest discover -s tests -v
```

Các bộ kiểm thử tích hợp nằm trong `sprintN\tests`. Cài dependencies phát triển
vào môi trường của phiên bản cần kiểm thử rồi chạy:

```powershell
cd sprint4
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest tests\ -v
```

Kiểm thử tích hợp cần SQL Server và dữ liệu thử nghiệm. Không chạy kiểm thử trên
cơ sở dữ liệu vận hành; xem README của phiên bản để cấu hình cơ sở dữ liệu thử
nghiệm trước khi chạy.

## Cấu trúc thư mục

```text
sprint1/ ... sprint4/   Ứng dụng, cấu hình, schema và tests độc lập
tests/                  Kiểm thử dùng chung ở cấp dự án
README.md               Hướng dẫn tổng quan
AI_COLLABORATION.md     Lịch sử cộng tác và các quyết định trong phiên làm việc
logbug.md               Nhật ký lỗi và vấn đề đã xác nhận
status.md               Trạng thái công việc
todos.md                Danh sách việc cần làm
```

## Cấu hình và dữ liệu nhạy cảm

Không commit `.env`, mật khẩu, khóa ứng dụng, môi trường ảo, cache kiểm thử hay
dữ liệu ID sinh tự động. Dùng `.env.example` làm mẫu và lưu giá trị bí mật trong
môi trường triển khai phù hợp.
