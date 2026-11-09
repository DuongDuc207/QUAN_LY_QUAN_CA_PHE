# Website Quan Ly Quan Ca Phe - Sprint 1

## Pham vi Sprint 1
- Dang nhap, phan quyen, quan ly tai khoan (11 API - module `auth`)
- Quan ly danh muc va thuc don (10 API - module `menu`)
- 6 bang: VaiTro, Quyen, VaiTroQuyen, TaiKhoan, DanhMuc, Mon

## Cong nghe
- Backend: Python 3.12 + Flask 3.x (to chuc theo Modules)
- Database: SQL Server (`QuanLyCaPhe`)
- Frontend: HTML + CSS + JS (Jinja2), prefix API `/api/v1`

## Chay rieng Sprint 2
Trong thu muc `sprint2`, chay `py app.py` (hoac tu thu muc cha: `py sprint2/app.py`).
Lan dau tu tao `.venv` va cai `requirements.txt` (can ket noi mang).
Cac lan sau tu dung lai moi truong nay; khong can activate hay cai thu vien vao Python chung.
Moi sprint co day du ma nguon va thu vien rieng, co the sao chep thu muc de chay doc lap.

Dia chi mac dinh: http://localhost:5002. Dat `PORT` trong `.env` de doi cong.
Moi sprint doc dung `.env` canh `app.py`, ke ca khi chay tu thu muc khac.
Bien moi truong da dat trong terminal duoc uu tien hon `.env`.
Cau hinh SQL Server trong `.env` va nap schema theo huong dan duoi day neu chua co CSDL.
Neu muon tach du lieu, moi sprint can `DB_NAME` va CSDL da khoi tao tuong ung.

## Cai dat
```bat
cd sprint2
if not exist .env copy .env.example .env
sqlcmd -S "localhost\SQL2022EXP" -E -d QuanLyCaPhe -i database\schema.sql -b
sqlcmd -S "localhost\SQL2022EXP" -E -d QuanLyCaPhe -i database\schema_sprint2.sql -b -f 65001
sqlcmd -S "localhost\SQL2022EXP" -E -d QuanLyCaPhe -i database\seed.sql -b -f 65001
py tao_tai_khoan.py
py app.py
```

Truoc khi khoi dong, dat `FLASK_SECRET_KEY` trong `.env` bang mot khoa rieng tao
boi lenh `py -c "import secrets; print(secrets.token_hex(32))"`. Ung dung tu choi
khoi dong neu khoa bi thieu hoac ngan hon 32 ky tu.

`seed.sql` chi nap vai tro + quyen, khong co tai khoan hay mon mau.
Tai khoan dau tien tao bang terminal (chon vi tri 1 = Quan tri vien), sau do
dang nhap web de them nhan vien, nhom mon va mon.

```bat
py tao_tai_khoan.py              :: tao tai khoan (hoi ho ten, email, vi tri, mat khau)
py tao_tai_khoan.py --danh-sach  :: xem cac tai khoan hien co
```

CSDL da cai ban cu con du lieu mau thi chay 1 lan:
`sqlcmd -S "localhost\SQL2022EXP" -E -d QuanLyCaPhe -i database\xoa_du_lieu_mau.sql -b -f 65001`

Mo trinh duyet: http://localhost:5002 (tu dong ve `/dashboard`, chua login thi ve `/login`).

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
- `tests/test_giao_dien.py` - kiem thu giao dien: menu an theo quyen, khong lo
  thuat ngu ky thuat, va giao dien phu du 21 API
