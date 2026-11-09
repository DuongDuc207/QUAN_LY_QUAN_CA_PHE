# Website Quan Ly Quan Ca Phe

## Pham vi Sprint 1
- Dang nhap, phan quyen, quan ly tai khoan (11 API - module `auth`)
- Quan ly danh muc va thuc don (10 API - module `menu`)
- 6 bang: VaiTro, Quyen, VaiTroQuyen, TaiKhoan, DanhMuc, Mon

## Cong nghe
- Backend: Python 3.12 + Flask 3.x (to chuc theo Modules)
- Database: SQL Server (`QuanLyCaPhe`)
- Frontend: HTML + CSS + JS (Jinja2), prefix API `/api/v1`

## Chay rieng Sprint 4
Trong thu muc `sprint4`, chay `py app.py` (hoac tu thu muc cha: `py sprint4/app.py`).
Lan dau tu tao `.venv` va cai `requirements.txt` (can ket noi mang).
Cac lan sau tu dung lai moi truong nay; khong can activate hay cai thu vien vao Python chung.
Moi sprint co day du ma nguon va thu vien rieng, co the sao chep thu muc de chay doc lap.

Dia chi mac dinh: http://localhost:5004. Dat `PORT` trong `.env` de doi cong.
Moi sprint doc dung `.env` canh `app.py`, ke ca khi chay tu thu muc khac.
Bien moi truong da dat trong terminal duoc uu tien hon `.env`.
Cau hinh SQL Server trong `.env` va nap schema theo huong dan duoi day neu chua co CSDL.
Neu muon tach du lieu, moi sprint can `DB_NAME` va CSDL da khoi tao tuong ung.

## Cai dat
```bat
cd sprint4
if not exist .env copy .env.example .env
sqlcmd -S "localhost\SQL2022EXP" -E -d QuanLyCaPhe -i database\schema.sql -b
sqlcmd -S "localhost\SQL2022EXP" -E -d QuanLyCaPhe -i database\schema_sprint2.sql -b -f 65001
sqlcmd -S "localhost\SQL2022EXP" -E -d QuanLyCaPhe -i database\schema_sprint3.sql -b -f 65001
sqlcmd -S "localhost\SQL2022EXP" -E -d QuanLyCaPhe -i database\update_01_promotions.sql -b -f 65001
sqlcmd -S "localhost\SQL2022EXP" -E -d QuanLyCaPhe -i database\update_02_staff_schedule.sql -b -f 65001
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

Mo trinh duyet: http://localhost:5004 (tu dong ve `/dashboard`, chua login thi ve `/login`).

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

## Sprint 4 - Khuyen mai, bao cao, nhan vien (27 API)
- Module `api/promotions/` (API 64-70), `api/reports/` (API 71-79),
  `api/employees/` (API 80-90), 5 bang moi trong hai script cap nhat:
  `database/update_01_promotions.sql` (KhuyenMai, SuDungKhuyenMai) va
  `database/update_02_staff_schedule.sql` (NhanVien, CaLamViec, LichLamViec).
  CSDL da co schema Sprint 3: chay lan luot hai script tren, roi chay lai `seed.sql`
  (them 6 quyen moi). Cac script bo qua bang da co, khong xoa du lieu cu.
- Khuyen mai ap vao don ngay khi tao don: gui `ma_khuyen_mai` trong `POST /orders`
  hoac `PUT /orders/{id}/items` (gui chuoi rong = go ma, khong gui = giu ma dang gan).
  So tien giam luon tinh o backend tu tong tien trong CSDL, lam tron toi dong,
  khong bao gio giam qua tong tien va khong qua `GiamToiDa`.
- Doi mon lam tong tien doi -> so giam tinh lai; don tut xuong duoi muc toi thieu thi
  tu go khuyen mai. Moi don toi da 1 khuyen mai; luot da dung dem theo don chua huy.
- Bao cao chi doc du lieu, mac dinh 7 ngay gan nhat, toi da 366 ngay/lan xem:
  doanh thu (thu - hoan), don hang, mon ban chay, thanh toan, huy & hoan tien, ton kho,
  chi phi nhap hang, hieu qua khuyen mai, tong quan.
- Nhan vien: ho so gan toi da 1 tai khoan dang nhap; ca lam cho phep qua dem;
  xep lich chan trung ca, trung gio va nhan vien da nghi. Nghi viec thi tu huy lich sap toi.
- Quyen moi: `promotion.view`, `promotion.manage`, `report.view`, `employee.view`,
  `employee.manage`, `schedule.view`. Nhan vien mac dinh duoc ap ma khuyen mai khi ban
  hang va xem lich lam cua chinh minh.

| Trang | Chuc nang |
|---|---|
| `/promotions` | Chuong trinh khuyen mai: tao, sua, bat/tat, chi tiet + luot dung |
| `/reports` | 9 nhom bao cao, chon khoang ngay, xem nhanh 7/30 ngay |
| `/employees` | Ho so nhan vien: tim, loc, them, sua, chi tiet + lich sap toi |
| `/schedules` | Lich tuan: xep lich, doi ca, cham cong, huy lich, quan ly ca lam |
| `/pos` | Them o nhap ma khuyen mai (kiem tra ma truoc khi tao don) |

Nguyen tac khi sua frontend:
- Khong de lo thuat ngu ky thuat (ten bang/cot, endpoint API, ma trang thai, "Sprint").
- Khong in truc tiep `data.message` tu API. Dung `apiGoi()` trong
  `frontend/static/js/main.js` - no tu doi thong bao qua tieng Viet than thien
  (bang `DIEN_GIAI_LOI`). Them tinh huong moi thi bo sung vao bang nay.
- Khong dung `confirm()` / `alert()` cua trinh duyet (hop thoai xau, khong doi ten nut
  duoc). Dung `await xacNhan(text, {nhanDongY, nhanHuy, nguyHiem})` trong `main.js`;
  no tra ve Promise<boolean>. Ham goi phai la `async`. Dat `nguyHiem: true` khi thao tac
  khong the hoan tac (xoa, huy, hoan tien) de nut dong y mau do.
- Ma trang thai he thong (`HOAT_DONG`/`KHOA`) chi nam trong `main.js`, khong viet
  rai rac trong template.
- `{% set %}` trong block `content` KHONG nhin thay duoc tu block `scripts` (Jinja tach
  pham vi tung block). Template nao dung co quyen trong JS phai khai bao lai o `scripts`
  (xem `test_bien_jinja_dung_trong_scripts_phai_khai_bao_trong_scripts`).
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
- `tests/test_sprint4.py` - kiem thu 27 API khuyen mai, bao cao, nhan vien, ca, lich
  (tinh tien giam, het luot, trung gio, cham cong)
- `tests/test_giao_dien.py` - kiem thu giao dien: menu an theo quyen, khong lo
  thuat ngu ky thuat, ma trang thai chi nam trong `main.js`, va giao dien phu du 90 API

Chay test tren CSDL tam (khong dung CSDL that):
`set DB_NAME=QLCP_ten` roi `.venv\Scripts\python.exe -m pytest tests/ -q`.

## Du lieu mau de xem giao dien va bao cao
```bat
py tao_du_lieu_mau.py --dong-y                       :: 40 nhan vien, 500 don trong 30 ngay
py tao_du_lieu_mau.py --dong-y --so-nhan-vien 60 --so-don 1200
py tao_du_lieu_mau.py --xoa                          :: xoa dung du lieu da sinh
```
- Chi ghi vao CSDL tam ten bat dau bang `QLCP_` (tao bang `_qlcp_tools/mkdb.sh`).
  CSDL that `QuanLyCaPhe` bi tu choi, tru khi them `--toi-csdl-that` (chi khi CSDL that
  da nap du 4 file schema, neu thieu bang script dung ngay chu khong ghi do dang).
- Du lieu di qua dung cac service cua ung dung, nen tien, ton kho va trang thai deu
  theo luat nghiep vu (ton kho chi doi qua so cai kho). Ngay gio duoc lui ve qua khu
  de bieu do bao cao co du lieu nhieu ngay.
- Sinh ra: tai khoan dang nhap, 4 ca lam, lich lam 29 ngay, nguyen lieu + nha cung cap +
  phieu nhap, thuc don 34 mon kem cong thuc, 7 chuong trinh khuyen mai, don hang kem
  thanh toan (co don huy, don hoan tien, don dung ma khuyen mai, vai don dang phuc vu).
  Cuoi ky kiem ke 4 nguyen lieu xuong duoi muc toi thieu de bang "sap het" co du lieu.
- `--xoa` doc `du_lieu_mau_ids.json` (sinh ra khi tao) nen chi xoa dung ban ghi da sinh.
  Neu lan chay truoc moi tao duoc tai khoan mau roi dung, chay lai se dung lai chinh cac
  tai khoan do (khong tao trung); cac bang khac con sot thi bao va chan, phai `--xoa` truoc.
- Tai khoan dang nhap: `admin@caphe.local / admin123`, `quanly@caphe.local / quanly123`,
  `nhanvien01@caphe.local / nhanvien123` (den `nhanvien08`).
- Them `--seed 7` de chay lai ra dung bo du lieu nhu lan truoc.
