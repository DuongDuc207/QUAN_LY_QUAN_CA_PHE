# Website Quan Ly Quan Ca Phe - Sprint 1

## Pham vi Sprint 1
- Dang nhap, phan quyen, quan ly tai khoan (11 API - module `auth`)
- Quan ly danh muc va thuc don (10 API - module `menu`)
- 6 bang: VaiTro, Quyen, VaiTroQuyen, TaiKhoan, DanhMuc, Mon

## Cong nghe
- Backend: Python 3.12 + Flask 3.x (to chuc theo Modules)
- Database: SQL Server (`QuanLyCaPhe`)
- Frontend: HTML + CSS + JS (Jinja2), prefix API `/api/v1`

## Chay rieng Sprint 1
Trong thu muc `sprint1`, chay `py app.py` (hoac tu thu muc cha: `py sprint1/app.py`).
Lan dau tu tao `.venv` va cai `requirements.txt` (can ket noi mang).
Cac lan sau tu dung lai moi truong nay; khong can activate hay cai thu vien vao Python chung.
Moi sprint co day du ma nguon va thu vien rieng, co the sao chep thu muc de chay doc lap.

Dia chi mac dinh: http://localhost:5001. Dat `PORT` trong `.env` de doi cong.
Moi sprint doc dung `.env` canh `app.py`, ke ca khi chay tu thu muc khac.
Bien moi truong da dat trong terminal duoc uu tien hon `.env`.
Cau hinh SQL Server trong `.env` va nap schema theo huong dan duoi day neu chua co CSDL.
Neu muon tach du lieu, moi sprint can `DB_NAME` va CSDL da khoi tao tuong ung.

## Cai dat
```bat
cd sprint1
if not exist .env copy .env.example .env
sqlcmd -S "localhost\SQL2022EXP" -E -d QuanLyCaPhe -i database\schema.sql -b
sqlcmd -S "localhost\SQL2022EXP" -E -d QuanLyCaPhe -i database\seed.sql -b -f 65001
py tao_tai_khoan.py
py app.py
```

`seed.sql` chi nap vai tro + quyen, khong co tai khoan hay mon mau.
Tai khoan dau tien tao bang terminal (chon vi tri 1 = Quan tri vien), sau do
dang nhap web de them nhan vien, nhom mon va mon.

```bat
py tao_tai_khoan.py              :: tao tai khoan (hoi ho ten, email, vi tri, mat khau)
py tao_tai_khoan.py --danh-sach  :: xem cac tai khoan hien co
```

CSDL da cai ban cu con du lieu mau thi chay 1 lan:
`sqlcmd -S "localhost\SQL2022EXP" -E -d QuanLyCaPhe -i database\xoa_du_lieu_mau.sql -b -f 65001`

Mo trinh duyet: http://localhost:5001 (tu dong ve `/dashboard`, chua login thi ve `/login`).

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
- `tests/test_giao_dien.py` - kiem thu giao dien: menu an theo quyen, khong lo
  thuat ngu ky thuat, va giao dien phu du 21 API
