# Website Quan Ly Quan Ca Phe

## Pham vi Sprint 1
- Dang nhap, phan quyen, quan ly tai khoan (11 API - module `auth`)
- Quan ly danh muc va thuc don (10 API - module `menu`)
- 6 bang: VaiTro, Quyen, VaiTroQuyen, TaiKhoan, DanhMuc, Mon

## Cong nghe
- Backend: Python 3.12 + Flask 3.x (to chuc theo Modules)
- Database: SQL Server (`QuanLyCaPhe`)
- Frontend: HTML + CSS + JS (Jinja2), prefix API `/api/v1`

## Chay rieng Sprint 3
Trong thu muc `sprint3`, chay `py app.py` (hoac tu thu muc cha: `py sprint3/app.py`).
Lan dau tu tao `.venv` va cai `requirements.txt` (can ket noi mang).
Cac lan sau tu dung lai moi truong nay; khong can activate hay cai thu vien vao Python chung.
Moi sprint co day du ma nguon va thu vien rieng, co the sao chep thu muc de chay doc lap.

Dia chi mac dinh: http://localhost:5003. Dat `PORT` trong `.env` de doi cong.
Moi sprint doc dung `.env` canh `app.py`, ke ca khi chay tu thu muc khac.
Bien moi truong da dat trong terminal duoc uu tien hon `.env`.
Cau hinh SQL Server trong `.env` va nap schema theo huong dan duoi day neu chua co CSDL.
Neu muon tach du lieu, moi sprint can `DB_NAME` va CSDL da khoi tao tuong ung.

## Cai dat
```bat
cd sprint3
if not exist .env copy .env.example .env
sqlcmd -S "localhost\SQL2022EXP" -E -d QuanLyCaPhe -i database\schema.sql -b
sqlcmd -S "localhost\SQL2022EXP" -E -d QuanLyCaPhe -i database\schema_sprint2.sql -b -f 65001
sqlcmd -S "localhost\SQL2022EXP" -E -d QuanLyCaPhe -i database\schema_sprint3.sql -b -f 65001
sqlcmd -S "localhost\SQL2022EXP" -E -d QuanLyCaPhe -i database\seed.sql -b -f 65001
py tao_tai_khoan.py
py app.py
```

Truoc khi khoi dong, dat `FLASK_SECRET_KEY` trong `.env` bang mot khoa rieng tao
boi lenh `py -c "import secrets; print(secrets.token_hex(32))"`. Ung dung tu choi
khoi dong neu khoa bi thieu hoac ngan hon 32 ky tu.

## Cập nhật cơ sở dữ liệu tùy chọn

Ứng dụng Sprint 3 không cần các bảng khuyến mãi và lịch nhân sự. Nếu cùng cơ sở dữ
liệu sẽ được dùng cho các chức năng mở rộng, sau khi đã cài schema Sprint 1–3,
có thể chạy lần lượt:

```bat
sqlcmd -S "localhost\SQL2022EXP" -E -d QuanLyCaPhe -i database\update_01_promotions.sql -b -f 65001
sqlcmd -S "localhost\SQL2022EXP" -E -d QuanLyCaPhe -i database\update_02_staff_schedule.sql -b -f 65001
```

Hai script cập nhật chỉ bổ sung bảng còn thiếu, không xóa dữ liệu. Chạy lại
`database\seed.sql` để thêm quyền tương ứng.

`seed.sql` chi nap vai tro + quyen, khong co tai khoan hay mon mau.
Tai khoan dau tien tao bang terminal (chon vi tri 1 = Quan tri vien), sau do
dang nhap web de them nhan vien, nhom mon va mon.

```bat
py tao_tai_khoan.py              :: tao tai khoan (hoi ho ten, email, vi tri, mat khau)
py tao_tai_khoan.py --danh-sach  :: xem cac tai khoan hien co
```

CSDL da cai ban cu con du lieu mau thi chay 1 lan:
`sqlcmd -S "localhost\SQL2022EXP" -E -d QuanLyCaPhe -i database\xoa_du_lieu_mau.sql -b -f 65001`

Mo trinh duyet: http://localhost:5003 (tu dong ve `/dashboard`, chua login thi ve `/login`).

## Dữ liệu mẫu Sprint 3 (tùy chọn)

Sau khi đã có schema Sprint 1–3 và `database/seed.sql`, chạy trong thư mục `sprint3`:

```bat
py tao_du_lieu_mau.py --xem-truoc
py tao_du_lieu_mau.py
```

Công cụ đọc kết nối từ `.env` của Sprint 3 và **thêm vào CSDL đang cấu hình**.
Không cần chạy lại các file schema trên CSDL đã có dữ liệu.

Bộ mẫu gồm:

- 6 nhân sự thuộc ba vị trí, có một nhân sự tạm khóa.
- 8 nhóm, 40 món, đầy đủ định lượng và 80 bản ghi lịch sử công thức; có 2 món ngừng bán.
- 48 nguyên liệu: 6 hết hàng, 8 sắp hết, 32 đủ hàng đang dùng và 2 nguyên liệu ngừng dùng.
- 14 nhà cung cấp, gồm 12 đang hợp tác và 2 ngừng hợp tác.
- 120 phiếu nhập: 80 đã nhận, 20 nháp, 20 đã hủy (10 phiếu hủy sau khi nhận).
- 120 đơn hàng đủ năm trạng thái, kèm 72 thanh toán/hóa đơn bằng tiền mặt, chuyển khoản hoặc thẻ.
- Lịch sử tồn đầu kỳ, nhập hàng, hoàn nhập, tiêu hao theo công thức, kiểm kê và xuất kho.
  Các giao dịch trải dài khoảng 2 tháng để thử tìm kiếm, phân trang và lọc theo ngày.

Tên dữ liệu mẫu bắt đầu bằng `Mẫu - `; mã phiếu/đơn bắt đầu bằng `PN-MAU3-` / `DH-MAU3-`.
Mật khẩu chung cho các tài khoản mẫu là `DemoS3@2026`:

| Vị trí | Email |
|---|---|
| Quản trị viên | `demo.s3.admin@example.com` |
| Quản lý | `demo.s3.quanly@example.com` |
| Nhân viên thu ngân | `demo.s3.thungan@example.com` |
| Nhân viên pha chế | `demo.s3.phache@example.com` |
| Nhân viên phục vụ | `demo.s3.phucvu@example.com` |
| Nhân viên tạm khóa | `demo.s3.tamnghi@example.com` |

Chạy lại bỏ qua dữ liệu mẫu đã có, giữ nguyên mật khẩu/trạng thái/định lượng đã sửa
và không cộng tồn kho lần nữa. Công cụ không xóa dữ liệu hiện có, không đổi quyền
các vị trí; mọi thay đổi tồn kho đều qua sổ cái kho. Toàn bộ lần nạp dùng một
giao dịch: có lỗi thì hoàn tác toàn bộ phần thêm mới.

## Giao dien nguoi dung
Ten hien thi voi khach hang: **Ca Phe Viet**. Giao dien phu du 21 API Sprint 1
(`/auth/me` dung ngam de xac thuc phien, khong co nut rieng).

| Trang | Chuc nang |
|---|---|
| `/login` | Dang nhap |
| `/dashboard` | O so lieu (mon dang ban, nhom, nhan su) + loi tat |
| `/accounts` | Nhan su: xem, tim, loc, them, chi tiet, sua, tam ngung/mo lai |
| `/menu` tab Mon | Xem, tim, loc theo nhom, them, chi tiet, sua gia, ngung/ban lai |
| `/menu` tab Nhom mon | Xem, them, sua, an/hien, xoa |
| `/roles` | Phan quyen theo vi tri cong viec |
| `/pos` | Ban hang: chon mon, ghi chu, tao don, thu tien (tien mat / chuyen khoan / the) |
| `/orders` | Don hang: loc theo ngay/tinh trang, chuyen buoc pha che, sua mon, huy, hoan tien, xem/in hoa don |

## Sprint 2 - Don hang & thanh toan (17 API)
- Module `api/orders/` (API 22-30) va `api/payments/` (API 31-38), 5 bang moi trong
  `database/schema_sprint2.sql`. CSDL da co Sprint 1: chi can chay `schema_sprint2.sql`
  roi chay lai `seed.sql` (them 5 quyen moi; gan quyen cac vi tri ve mac dinh).
- Tien tinh o backend tu gia trong CSDL; gia duoc chot vao don luc them mon.
- Trang thai don (`MOI -> CHO_PHA_CHE -> DANG_PHA_CHE -> HOAN_THANH`, hoac `DA_HUY`)
  tach rieng trang thai thanh toan. Chi sua mon khi don chua pha che va chua thu tien.
- Chong thanh toan trung: khoa dong don khi ghi + index loc
  `UQ_ThanhToan_DonHang_HieuLuc` (moi don toi da 1 giao dich chua that bai).
- Xac nhan thanh toan thanh cong moi lap hoa don. Chuyen khoan / the phai co ma giao dich.
- Huy don da thu tien: phai hoan tien (quyen `payment.refund`) trong cung thao tac.
- Quyen moi: `order.view`, `order.manage`, `order.cancel`, `payment.manage`, `payment.refund`.
  Nhan vien mac dinh duoc ban hang + thu tien, KHONG duoc hoan tien.

## Sprint 3 - Kho nguyen lieu, cong thuc, nhap hang (25 API)
- Module `api/inventory/` (API 39-53: nguyen lieu, ton kho, cong thuc pha che) va
  `api/suppliers/` (API 54-63: nha cung cap, phieu nhap), 7 bang moi trong
  `database/schema_sprint3.sql`. CSDL da co Sprint 2: chi chay `schema_sprint3.sql`
  roi chay lai `seed.sql` (them 5 quyen moi). Ca hai file chay lai nhieu lan an toan.
- Moi thay doi ton kho chi di qua `api/inventory/ledger.py` (khoa dong nguyen lieu,
  chan ton am, ghi `LichSuKho`). Khong module nao duoc UPDATE `SoLuongTon` truc tiep.
- Phieu nhap: `NHAP -> DA_NHAN` (xac nhan moi cong kho) hoac `DA_HUY`. Huy phieu da nhan
  thi tru lai kho, can quyen `purchase.confirm`, khong cho huy neu ton khong du de tru.
- Tien phieu nhap tinh o backend: ThanhTien = SoLuong x DonGiaNhap, TongTien = tong dong.
- Quyen moi: `inventory.view`, `inventory.manage`, `supplier.view`, `supplier.manage`,
  `purchase.confirm`. Nhan vien mac dinh chi xem kho va cong thuc.

| Trang | Chuc nang |
|---|---|
| `/inventory` | Nguyen lieu, ton kho, sap het, lich su kho, kiem ke, xuat kho |
| `/recipes` | Cong thuc pha che cua mon va lich su thay doi |
| `/suppliers` | Nha cung cap: tim, loc, them, sua, chi tiet + phieu gan nhat |
| `/purchases` | Phieu nhap: loc, lap, sua, xac nhan nhan hang, huy |

Nguyen tac khi sua frontend:
- Khong de lo thuat ngu ky thuat (ten bang/cot, endpoint API, ma trang thai, "Sprint").
- Khong in truc tiep `data.message` tu API. Dung `apiGoi()` trong
  `frontend/static/js/main.js` - no tu doi thong bao qua tieng Viet than thien
  (bang `DIEN_GIAI_LOI`). Them tinh huong moi thi bo sung vao bang nay.
- Ma trang thai he thong (`HOAT_DONG`/`KHOA`) chi nam trong `main.js`, khong viet
  rai rac trong template.
- Thuat ngu doi sang ngon ngu nguoi dung: tai khoan -> nhan su, vai tro -> vi tri,
  danh muc -> nhom, quyen ky thuat -> cau viec lam duoc (bang `NHAN_QUYEN`).
- Khong hien ID khoa chinh tren bang danh sach.
- Muc menu/the/nut an theo quyen (`account.view`, `menu.manage`, `role.manage`...)
  de nguoi dung khong gap loi tu choi truy cap.
- Mau sac dat chuan tuong phan WCAG AA (toi thieu 4.5:1 cho chu thuong).

## Nhanh lam viec (2 nguoi - 2 module API)
- `sprint1/member1-auth` - Nguoi 1: module `api/auth/` (tai khoan, phan quyen)
- `sprint1/member2-menu` - Nguoi 2: module `api/menu/` (danh muc, thuc don)

## Chay kiem thu
```bat
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest tests/ -v
```
- Test tu tao tai khoan/mon rieng (`tests/du_lieu_test.py`, ten bat dau bang
  `pytest`) va tu xoa khi xong - khong dung den du lieu that cua ban.
- `tests/test_sprint1.py` - kiem thu 21 API (auth + menu)
- `tests/test_sprint2.py` - kiem thu 17 API va quy trinh ban hang (tinh tien, chot gia,
  trang thai, huy, thanh toan trung, hoan tien, hoa don, phan quyen)
- `tests/test_sprint3_kho.py`, `tests/test_sprint3_nhap_hang.py` - kiem thu 25 API kho,
  cong thuc, nha cung cap, phieu nhap (so cai kho, chong ton am, xac nhan / huy phieu)
- `tests/test_du_lieu_mau.py` - kiểm tra hoàn tác khi nạp lỗi, số dư/lịch sử kho,
  tổng tiền, tiêu hao theo công thức và chạy lại không tạo trùng hay ghi đè chỉnh sửa.
- `tests/test_giao_dien.py` - kiem thu giao dien: menu an theo quyen, khong lo
  thuat ngu ky thuat, ma trang thai chi nam trong `main.js`, va giao dien phu du 63 API

Chay test tren CSDL tam (khong dung CSDL that):
`set DB_NAME=QLCP_ten` roi `.venv\Scripts\python.exe -m pytest tests/ -q`.
