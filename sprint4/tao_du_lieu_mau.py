"""Sinh du lieu mau cho quan ca phe: nhan vien, ca lam, lich lam, kho, nhap hang,
thuc don, cong thuc, khuyen mai, don hang va thanh toan.

Chay:  py tao_du_lieu_mau.py --dong-y                    (mac dinh 40 nhan vien, 500 don)
       py tao_du_lieu_mau.py --dong-y --so-nhan-vien 60 --so-don 1200
       py tao_du_lieu_mau.py --xoa                        (xoa dung du lieu da sinh)

AN TOAN: script chi ghi vao CSDL tam ten bat dau bang QLCP_ (xem _qlcp_tools/mkdb.sh).
CSDL that QuanLyCaPhe bi tu choi, tru khi nguoi dung tu them --toi-csdl-that.

Du lieu sinh ra di qua dung cac service cua ung dung (tien do backend tinh, ton kho
qua so cai kho), rieng ngay gio duoc lui ve qua khu bang SQL de bieu do bao cao co du lieu.
Danh sach ID da tao luu o du_lieu_mau_ids.json de --xoa xoa chinh xac.

Chay lai khi CSDL da co du lieu: 10 tai khoan dang nhap mau da co san (do lan chay
truoc bi ngat) duoc dung lai thay vi bao trung email; cac du lieu mau khac con sot
bi phat hien som va chan lai, phai chay --xoa truoc de khong tao ban trung.
"""

import argparse
import datetime
import json
import os
import random
import sys
import time
from contextlib import closing

from bootstrap import ensure_runtime

ensure_runtime(allow_reexec=__name__ == "__main__")

from api.auth import service as auth_service  # noqa: E402
from api.employees import service as nv_service  # noqa: E402
from api.inventory import service as kho_service  # noqa: E402
from api.menu import service as menu_service  # noqa: E402
from api.orders import service as don_service  # noqa: E402
from api.payments import service as tt_service  # noqa: E402
from api.promotions import service as km_service  # noqa: E402
from api.suppliers import service as ncc_service  # noqa: E402
from config.settings import DB_NAME  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CSDL_THAT = "QuanLyCaPhe"
TEP_ID = os.path.join(os.path.dirname(os.path.abspath(__file__)), "du_lieu_mau_ids.json")

SO_NGAY_QUA_KHU = 30
SO_NGAY_LICH_QUA_KHU = 21
SO_NGAY_LICH_SAP_TOI = 7

MK_QUAN_TRI = "admin123"
MK_QUAN_LY = "quanly123"
MK_NHAN_VIEN = "nhanvien123"

# 10 tai khoan dang nhap mau. Neu da co san (lan chay truoc bi ngat giua chung) thi
# dung lai chu khong tao trung; tai khoan dung lai khong vao so ID nen --xoa khong xoa chung.
TAI_KHOAN_MAU = (
    ("Quản trị viên", "admin@caphe.local", MK_QUAN_TRI, 1),
    ("Trần Minh Quản", "quanly@caphe.local", MK_QUAN_LY, 2),
) + tuple(
    (f"Nhân viên {i:02d}", f"nhanvien{i:02d}@caphe.local", MK_NHAN_VIEN, 3) for i in range(1, 9)
)
EMAIL_MAU = tuple(t[1].lower() for t in TAI_KHOAN_MAU)

HO = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng",
      "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý"]
LOT = ["Thị", "Minh", "Thanh", "Quốc", "Hữu", "Ngọc", "Thu", "Hoài", "Kim", "Anh"]
TEN = ["An", "Bình", "Chi", "Dũng", "Duyên", "Giang", "Hà", "Hải", "Hân", "Hiếu", "Hoa",
       "Hùng", "Khánh", "Lan", "Linh", "Long", "Mai", "My", "Nam", "Nga", "Nhung", "Oanh",
       "Phát", "Phương", "Quân", "Quyên", "Sơn", "Tâm", "Thảo", "Thắng", "Trang", "Trâm",
       "Trí", "Trinh", "Tú", "Tuấn", "Vân", "Vy", "Yến", "Bảo", "Cường", "Hạnh"]
CHUC_VU = ["Pha chế", "Pha chế", "Pha chế", "Phục vụ", "Phục vụ", "Thu ngân", "Quản lý ca"]

CA_LAM = [
    ("Ca sáng", "06:00", "12:00", "Mở quán, pha chế và phục vụ buổi sáng"),
    ("Ca chiều", "12:00", "18:00", "Ca chiều, đông khách giờ nghỉ trưa"),
    ("Ca tối", "18:00", "23:00", "Ca tối, dọn quán và kiểm kê cuối ngày"),
    ("Ca đêm", "22:00", "06:00", "Ca đêm qua ngày, giao ca lúc 6 giờ sáng"),
]

# (ten, don vi, muc ton toi thieu, luong dung 1 thang, so don vi mua moi lan)
# Muc ton toi thieu va luong mua tinh theo luong dung thang de ton kho luon du cho 500 don.
NGUYEN_LIEU = [
    ("Cà phê hạt Robusta", "kg", 3, 22, (5, 9)),
    ("Cà phê hạt Arabica", "kg", 2, 12, (3, 6)),
    ("Sữa đặc có đường", "lon", 8, 55, (14, 22)),
    ("Sữa tươi không đường", "lít", 6, 45, (12, 20)),
    ("Kem sữa béo", "lít", 2, 14, (4, 7)),
    ("Đường cát trắng", "kg", 4, 30, (8, 14)),
    ("Đá viên", "kg", 25, 200, (50, 90)),
    ("Trà đen", "kg", 1, 6, (2, 4)),
    ("Trà xanh Thái Nguyên", "kg", 1, 5, (2, 3)),
    ("Bột matcha", "kg", 0.5, 4, (1.5, 2.5)),
    ("Bột cacao", "kg", 0.5, 4, (1.5, 2.5)),
    ("Siro đường", "lít", 2, 16, (5, 8)),
    ("Siro đào", "lít", 1, 8, (2.5, 4)),
    ("Siro vải", "lít", 1, 7, (2.5, 4)),
    ("Siro chanh dây", "lít", 1, 6, (2, 3.5)),
    ("Chanh tươi", "kg", 2, 12, (4, 7)),
    ("Cam tươi", "kg", 6, 42, (14, 22)),
    ("Đào ngâm", "kg", 2, 14, (5, 8)),
    ("Vải ngâm", "kg", 2, 12, (4, 7)),
    ("Trân châu", "kg", 2, 15, (5, 8)),
    ("Hạt é", "kg", 0.5, 4, (1.5, 2.5)),
    ("Thạch trái cây", "kg", 1, 8, (3, 5)),
    ("Sữa chua", "hộp", 10, 90, (30, 45)),
    ("Mật ong", "lít", 0.5, 4, (1.5, 2.5)),
    ("Gừng", "kg", 0.5, 3, (1, 2)),
    ("Sả", "kg", 0.5, 4, (1.5, 2.5)),
    ("Xoài chín", "kg", 3, 18, (6, 10)),
    ("Bơ sáp", "kg", 3, 20, (7, 11)),
    ("Cà rốt", "kg", 2, 12, (4, 7)),
    ("Trứng gà", "quả", 20, 130, (45, 70)),
    ("Muối biển", "kg", 0.5, 2, (1, 1.5)),
    ("Ly nhựa 500ml", "cái", 200, 1400, (450, 700)),
    ("Ống hút giấy", "cái", 250, 1600, (500, 800)),
    ("Túi giấy mang đi", "cái", 150, 800, (250, 400)),
    ("Khăn giấy", "hộp", 4, 26, (8, 12)),
]
# Vài nguyen lieu mua thieu co y de bang "sap het" tren dashboard co du lieu that.
MUA_THIEU = {"Bột matcha", "Hạt é", "Mật ong", "Khăn giấy"}

NHA_CUNG_CAP = [
    ("Công ty Cà phê Tây Nguyên", "0901234567", "lienhe@caphetaynguyen.vn", "Buôn Ma Thuột, Đắk Lắk"),
    ("Đại lý Sữa Việt", "0912345678", "donhang@suaviet.vn", "Quận 12, TP. Hồ Chí Minh"),
    ("Nông trại Trà Thái", "0987654321", None, "Tân Cương, Thái Nguyên"),
    ("Công ty Bao bì Xanh", "0938111222", "kinhdoanh@baobixanh.vn", "Thuận An, Bình Dương"),
    ("Vựa trái cây Miền Tây", "0947222333", None, "Chợ đầu mối Thủ Đức, TP. Hồ Chí Minh"),
    ("Cửa hàng Nguyên liệu Pha chế Sài Gòn", "0956333444", "banhang@nguyenlieusg.vn", "Quận 3, TP. Hồ Chí Minh"),
]

# (ten mon, nhom, gia ban)
THUC_DON = [
    ("Cà phê đen đá", "Cà phê Việt", 25000), ("Cà phê sữa đá", "Cà phê Việt", 29000),
    ("Bạc xỉu", "Cà phê Việt", 32000), ("Cà phê muối", "Cà phê Việt", 35000),
    ("Cà phê trứng", "Cà phê Việt", 39000), ("Sữa chua cà phê", "Cà phê Việt", 35000),
    ("Cold brew cam", "Cà phê Việt", 45000), ("Espresso", "Cà phê Ý", 30000),
    ("Americano", "Cà phê Ý", 35000), ("Latte", "Cà phê Ý", 45000),
    ("Cappuccino", "Cà phê Ý", 45000), ("Mocha", "Cà phê Ý", 50000),
    ("Macchiato", "Cà phê Ý", 42000), ("Trà đào cam sả", "Trà & Trà sữa", 45000),
    ("Trà vải", "Trà & Trà sữa", 45000), ("Trà chanh", "Trà & Trà sữa", 30000),
    ("Trà sen vàng", "Trà & Trà sữa", 40000), ("Trà sữa trân châu", "Trà & Trà sữa", 45000),
    ("Trà xanh matcha latte", "Trà & Trà sữa", 50000), ("Trà gừng mật ong", "Trà & Trà sữa", 35000),
    ("Cà phê đá xay", "Đá xay & Sinh tố", 52000), ("Matcha đá xay", "Đá xay & Sinh tố", 55000),
    ("Socola đá xay", "Đá xay & Sinh tố", 55000), ("Sinh tố xoài", "Đá xay & Sinh tố", 50000),
    ("Sinh tố bơ", "Đá xay & Sinh tố", 52000), ("Nước cam", "Nước ép & Nước ngọt", 40000),
    ("Nước chanh dây", "Nước ép & Nước ngọt", 35000), ("Nước ép cà rốt", "Nước ép & Nước ngọt", 40000),
    ("Soda chanh", "Nước ép & Nước ngọt", 30000), ("Nước suối", "Nước ép & Nước ngọt", 15000),
    ("Bánh flan", "Bánh ngọt", 25000), ("Bánh mì que", "Bánh ngọt", 20000),
    ("Croissant", "Bánh ngọt", 30000), ("Tiramisu", "Bánh ngọt", 45000),
]

# Cong thuc cho 1 phan: ten mon -> [(nguyen lieu, dinh luong)].
# Mon mua san (banh mi que, croissant, nuoc suoi, tiramisu, banh flan) khong co cong thuc.
CONG_THUC = {
    "Cà phê đen đá": [("Cà phê hạt Robusta", 0.02), ("Đường cát trắng", 0.008), ("Đá viên", 0.18), ("Ly nhựa 500ml", 1), ("Ống hút giấy", 1.2)],
    "Cà phê sữa đá": [("Cà phê hạt Robusta", 0.02), ("Sữa đặc có đường", 0.04), ("Đá viên", 0.18), ("Ly nhựa 500ml", 1), ("Ống hút giấy", 1.2)],
    "Bạc xỉu": [("Cà phê hạt Robusta", 0.012), ("Sữa đặc có đường", 0.05), ("Sữa tươi không đường", 0.06), ("Đá viên", 0.18), ("Ly nhựa 500ml", 1)],
    "Cà phê muối": [("Cà phê hạt Robusta", 0.02), ("Sữa đặc có đường", 0.04), ("Muối biển", 0.004), ("Đá viên", 0.18), ("Ly nhựa 500ml", 1)],
    "Cà phê trứng": [("Cà phê hạt Robusta", 0.022), ("Trứng gà", 1), ("Sữa đặc có đường", 0.03), ("Đường cát trắng", 0.01), ("Ly nhựa 500ml", 1)],
    "Sữa chua cà phê": [("Sữa chua", 1), ("Cà phê hạt Robusta", 0.014), ("Sữa đặc có đường", 0.03), ("Đá viên", 0.12), ("Ly nhựa 500ml", 1)],
    "Cold brew cam": [("Cà phê hạt Arabica", 0.024), ("Cam tươi", 0.2), ("Đường cát trắng", 0.012), ("Đá viên", 0.2), ("Ly nhựa 500ml", 1)],
    "Espresso": [("Cà phê hạt Arabica", 0.018), ("Ly nhựa 500ml", 1)],
    "Americano": [("Cà phê hạt Arabica", 0.018), ("Đá viên", 0.2), ("Ly nhựa 500ml", 1)],
    "Latte": [("Cà phê hạt Arabica", 0.018), ("Sữa tươi không đường", 0.15), ("Ly nhựa 500ml", 1)],
    "Cappuccino": [("Cà phê hạt Arabica", 0.018), ("Sữa tươi không đường", 0.12), ("Kem sữa béo", 0.02), ("Ly nhựa 500ml", 1)],
    "Mocha": [("Cà phê hạt Arabica", 0.018), ("Sữa tươi không đường", 0.12), ("Bột cacao", 0.012), ("Siro đường", 0.015), ("Ly nhựa 500ml", 1)],
    "Macchiato": [("Cà phê hạt Arabica", 0.02), ("Sữa tươi không đường", 0.08), ("Kem sữa béo", 0.02), ("Ly nhựa 500ml", 1)],
    "Trà đào cam sả": [("Trà đen", 0.008), ("Đào ngâm", 0.08), ("Cam tươi", 0.08), ("Sả", 0.02), ("Siro đào", 0.02), ("Đá viên", 0.18)],
    "Trà vải": [("Trà đen", 0.008), ("Vải ngâm", 0.08), ("Siro vải", 0.025), ("Đá viên", 0.18), ("Ly nhựa 500ml", 1)],
    "Trà chanh": [("Trà xanh Thái Nguyên", 0.006), ("Chanh tươi", 0.04), ("Đường cát trắng", 0.012), ("Đá viên", 0.18), ("Ly nhựa 500ml", 1)],
    "Trà sen vàng": [("Trà xanh Thái Nguyên", 0.006), ("Hạt é", 0.008), ("Siro đường", 0.02), ("Đá viên", 0.18), ("Ly nhựa 500ml", 1)],
    "Trà sữa trân châu": [("Trà đen", 0.01), ("Sữa đặc có đường", 0.03), ("Sữa tươi không đường", 0.08), ("Trân châu", 0.05), ("Đá viên", 0.15), ("Ly nhựa 500ml", 1)],
    "Trà xanh matcha latte": [("Bột matcha", 0.01), ("Sữa tươi không đường", 0.15), ("Siro đường", 0.015), ("Đá viên", 0.15), ("Ly nhựa 500ml", 1)],
    "Trà gừng mật ong": [("Trà xanh Thái Nguyên", 0.006), ("Gừng", 0.015), ("Mật ong", 0.02), ("Chanh tươi", 0.02), ("Ly nhựa 500ml", 1)],
    "Cà phê đá xay": [("Cà phê hạt Robusta", 0.022), ("Sữa đặc có đường", 0.04), ("Kem sữa béo", 0.03), ("Đá viên", 0.2), ("Ly nhựa 500ml", 1)],
    "Matcha đá xay": [("Bột matcha", 0.014), ("Sữa tươi không đường", 0.12), ("Kem sữa béo", 0.03), ("Đá viên", 0.2), ("Ly nhựa 500ml", 1)],
    "Socola đá xay": [("Bột cacao", 0.018), ("Sữa tươi không đường", 0.12), ("Kem sữa béo", 0.03), ("Đá viên", 0.2), ("Ly nhựa 500ml", 1)],
    "Sinh tố xoài": [("Xoài chín", 0.28), ("Sữa đặc có đường", 0.04), ("Đá viên", 0.15), ("Ly nhựa 500ml", 1)],
    "Sinh tố bơ": [("Bơ sáp", 0.28), ("Sữa đặc có đường", 0.04), ("Đá viên", 0.15), ("Ly nhựa 500ml", 1)],
    "Nước cam": [("Cam tươi", 0.3), ("Đường cát trắng", 0.012), ("Đá viên", 0.12), ("Ly nhựa 500ml", 1)],
    "Nước chanh dây": [("Siro chanh dây", 0.04), ("Chanh tươi", 0.02), ("Đá viên", 0.15), ("Ly nhựa 500ml", 1)],
    "Nước ép cà rốt": [("Cà rốt", 0.3), ("Đường cát trắng", 0.01), ("Đá viên", 0.12), ("Ly nhựa 500ml", 1)],
    "Soda chanh": [("Chanh tươi", 0.05), ("Siro đường", 0.03), ("Đá viên", 0.15), ("Ly nhựa 500ml", 1)],
}

GHI_CHU_DON = ["Bàn 1", "Bàn 2", "Bàn 3", "Bàn 5", "Bàn 7", "Mang đi", "Giao hàng", None, None, None]
GHI_CHU_MON = ["Ít đá", "Ít đường", "Không đường", "Nhiều đá", "Ít sữa", None, None, None, None, None]
LY_DO_HUY = ["Khách đổi ý không lấy nữa", "Khách báo nhầm món", "Hết nguyên liệu pha chế",
             "Nhập nhầm món trên máy", "Khách chờ lâu nên bỏ về"]
LY_DO_HOAN = ["Pha chưa đúng yêu cầu của khách", "Khách phản hồi món bị chua",
              "Đơn giao thiếu món", "Khách phàn nàn về thời gian chờ"]
LY_DO_NHAP = ["Nhập hàng tuần", "Bổ sung hàng sắp hết", "Nhập gấp cho cuối tuần",
              "Đơn hàng định kỳ của nhà cung cấp", "Nhập bù hàng lỗi"]

# Gio trong ngay va ti trong so don (7-9 sang, 12-13 trua, 15-16 xeo, 19-21 toi).
GIO_BAN = [(7, 5), (8, 7), (9, 6), (10, 4), (11, 4), (12, 6), (13, 5), (14, 5),
           (15, 6), (16, 6), (17, 4), (18, 4), (19, 7), (20, 8), (21, 6), (22, 2)]
TI_TRONG_THU = {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.05, 4: 1.2, 5: 1.6, 6: 1.5}  # Thu 2 = 0

KHUYEN_MAI = [
    {"ma": "GIAM10", "ten": "Giảm 10% cho khách quen", "loai": "PHAN_TRAM", "gia_tri": 10,
     "toi_thieu": 0, "toi_da": 20000, "luot": None, "tu": -20, "den": 30, "bat": True},
    {"ma": "SANG20", "ten": "Giờ vàng buổi sáng giảm 20%", "loai": "PHAN_TRAM", "gia_tri": 20,
     "toi_thieu": 50000, "toi_da": 15000, "luot": 200, "tu": -15, "den": 20, "bat": True},
    {"ma": "CUOITUAN", "ten": "Cuối tuần giảm 15%", "loai": "PHAN_TRAM", "gia_tri": 15,
     "toi_thieu": 80000, "toi_da": 25000, "luot": None, "tu": -10, "den": 45, "bat": True},
    {"ma": "GIAM30K", "ten": "Giảm 30.000đ cho đơn từ 150.000đ", "loai": "SO_TIEN", "gia_tri": 30000,
     "toi_thieu": 150000, "toi_da": None, "luot": 100, "tu": -25, "den": 5, "bat": True},
    {"ma": "KHAITRUONG", "ten": "Khuyến mãi khai trương", "loai": "PHAN_TRAM", "gia_tri": 25,
     "toi_thieu": 0, "toi_da": 30000, "luot": 500, "tu": -60, "den": -20, "bat": True},
    {"ma": "SAPMO", "ten": "Sinh nhật quán, giảm 30%", "loai": "PHAN_TRAM", "gia_tri": 30,
     "toi_thieu": 0, "toi_da": 40000, "luot": None, "tu": 20, "den": 40, "bat": True},
    {"ma": "TAMNGUNG", "ten": "Chương trình đang tạm dừng", "loai": "PHAN_TRAM", "gia_tri": 12,
     "toi_thieu": 0, "toi_da": None, "luot": None, "tu": -10, "den": 30, "bat": False},
]


# ---------------------------------------------------------------- tien ich
def _bay_gio():
    return datetime.datetime.now()


def _kq(ket_qua, ten_viec):
    """Kiem tra ket qua service tra ve (data, err); dung ngay neu loi."""
    if isinstance(ket_qua, tuple) and len(ket_qua) == 2 and ket_qua[1]:
        raise RuntimeError(f"{ten_viec}: {ket_qua[1]}")
    return ket_qua[0]


def _chon_mon(rng, ds_chon_mon):
    """ds_chon_mon = [(mon, trong_so)] da chia deu theo nhom."""
    return _chon_theo_trong_so(rng, ds_chon_mon)


def _chon_theo_trong_so(rng, ds):
    """ds = [(gia_tri, trong_so)] -> gia_tri."""
    tong = sum(t for _, t in ds)
    diem = rng.uniform(0, tong)
    for gia_tri, trong_so in ds:
        diem -= trong_so
        if diem <= 0:
            return gia_tri
    return ds[-1][0]


def _ho_ten_day_du(rng, da_dung):
    while True:
        ten = f"{rng.choice(HO)} {rng.choice(LOT)} {rng.choice(TEN)}"
        if ten not in da_dung:
            da_dung.add(ten)
            return ten


class BoDem:
    """Ghi lai ID da tao de --xoa xoa chinh xac, khong dung den du lieu khac.

    So ID ghi kem ten CSDL (khoa "_CSDL") vi ID chi co nghia trong dung CSDL da sinh ra no.
    Khong co khoa nay thi --xoa chay nham CSDL se xoa ban ghi cung ID cua CSDL khac.
    """

    def __init__(self):
        self.id = {k: [] for k in (
            "TaiKhoan", "NhanVien", "CaLamViec", "LichLamViec", "KhuyenMai", "NguyenLieu",
            "NhaCungCap", "PhieuNhap", "DanhMuc", "Mon", "DonHang", "ThanhToan",
        )}
        self.id["_CSDL"] = DB_NAME

    def them(self, bang, gia_tri):
        if gia_tri is not None:
            self.id[bang].append(int(gia_tri))

    def luu(self):
        with open(TEP_ID, "w", encoding="utf-8") as f:
            json.dump(self.id, f, ensure_ascii=False, indent=1)


# ---------------------------------------------------------------- an toan du lieu cu
# Cac bang ma quy trinh sinh du lieu dung tới (Sprint 1-4). Kiem tra truoc khi ghi de
# CSDL thieu schema thi dung ngay, khong tao do dang roi moi bao loi giua chung.
BANG_CAN_CO = (
    "VaiTro", "Quyen", "VaiTroQuyen", "TaiKhoan", "DanhMuc", "Mon",
    "DonHang", "ChiTietDonHang", "ThanhToan", "HoaDon", "HoanTien",
    "NguyenLieu", "CongThuc", "CongThucLichSu", "NhaCungCap", "PhieuNhap",
    "ChiTietPhieuNhap", "LichSuKho",
    "KhuyenMai", "SuDungKhuyenMai", "NhanVien", "CaLamViec", "LichLamViec",
)


def _bang_con_thieu():
    with closing(_ket_noi()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sys.tables")
        co = {r[0] for r in cur.fetchall()}
    return [b for b in BANG_CAN_CO if b not in co]


def _du_lieu_mau_con_sot():
    """Ten cac bang con du lieu mau tu lan chay truoc, nhan biet theo ten dac trung.

    Tai khoan mau khong tinh vi lan chay sau dung lai duoc; cac bang khac khong co dau
    hieu nhan biet tung ban ghi nen phai xoa truoc bang --xoa.
    """
    theo_bang = {
        "DanhMuc": ("TenDanhMuc", sorted({t[1] for t in THUC_DON})),
        "NguyenLieu": ("TenNguyenLieu", sorted(t[0] for t in NGUYEN_LIEU)),
        "NhaCungCap": ("TenNhaCungCap", sorted(t[0] for t in NHA_CUNG_CAP)),
        "CaLamViec": ("TenCa", sorted(t[0] for t in CA_LAM)),
        "KhuyenMai": ("MaKhuyenMai", sorted(t["ma"] for t in KHUYEN_MAI)),
    }
    con_sot = []
    with closing(_ket_noi()) as conn:
        cur = conn.cursor()
        for bang, (cot, gia_tri) in theo_bang.items():
            cho = ",".join("?" * len(gia_tri))
            cur.execute(f"SELECT COUNT(*) FROM dbo.{bang} WHERE {cot} IN ({cho})", gia_tri)
            if cur.fetchval():
                con_sot.append(bang)
    return con_sot


def _xu_ly_tep_id_cu():
    """True neu duoc phep di tiep. Xem tep ID cua lan chay truoc.

    Lan chay truoc chi kip tao tai khoan mau roi dung (cac tai khoan do se duoc dung lai)
    thi luu tep ID cu thanh .cu roi di tiep; con du lieu khac thi chan, phai --xoa truoc.
    """
    if not os.path.exists(TEP_ID):
        return True
    with open(TEP_ID, encoding="utf-8") as f:
        id_cu = json.load(f)

    # So ID chi co nghia trong CSDL da sinh ra no.
    if id_cu.get("_CSDL") and id_cu["_CSDL"] != DB_NAME:
        print(f"So ID {os.path.basename(TEP_ID)} thuoc CSDL {id_cu['_CSDL']}, khong phai {DB_NAME}.")
        print(f"Doi ten tep do di neu muon sinh du lieu vao {DB_NAME}.")
        return False

    if any(v for k, v in id_cu.items() if k not in ("TaiKhoan", "_CSDL")):
        print(f"Da co {TEP_ID} voi du lieu da sinh tu lan chay truoc.")
        print("Chay --xoa truoc khi sinh lai de khong tao ban trung.")
        return False
    email_theo_id = {a["TaiKhoanID"]: (a["Email"] or "").strip().lower()
                     for a in auth_service.danh_sach_tai_khoan()}
    if not all(email_theo_id.get(int(tk)) in EMAIL_MAU for tk in id_cu.get("TaiKhoan", [])):
        print(f"Da co {TEP_ID} tu lan chay truoc. Chay --xoa truoc khi sinh lai.")
        return False
    os.replace(TEP_ID, TEP_ID + ".cu")
    print(f"Lan chay truoc moi tao {len(id_cu.get('TaiKhoan', []))} tai khoan mau roi dung; "
          f"cac tai khoan nay duoc dung lai. Tep ID cu luu o {os.path.basename(TEP_ID)}.cu")
    return True


# ---------------------------------------------------------------- xoa du lieu
def xoa_du_lieu_mau():
    if not os.path.exists(TEP_ID):
        print(f"Khong thay {TEP_ID}. Khong co gi de xoa.")
        return 1
    with open(TEP_ID, encoding="utf-8") as f:
        id_ds = json.load(f)

    # So ID chi co nghia trong CSDL da sinh ra no. Chan xoa nham CSDL khac cung ID.
    csdl_so = id_ds.get("_CSDL")
    if csdl_so and csdl_so != DB_NAME:
        print(f"So ID nay thuoc CSDL {csdl_so}, khong phai {DB_NAME}.")
        print(f"Chay lai voi DB_NAME={csdl_so}, hoac xoa tep {os.path.basename(TEP_ID)} neu chac chan.")
        return 2

    if not any(v for k, v in id_ds.items() if k != "_CSDL"):
        print("Tep ID rong. Khong co gi de xoa.")
        return 1

    def ds(bang):
        gia_tri = id_ds.get(bang) or []
        return ",".join(str(x) for x in gia_tri) if gia_tri else "NULL"

    with closing(_ket_noi()) as conn:
        cur = conn.cursor()
        cur.execute("SET XACT_ABORT ON")
        for cau_lenh in (
            f"DELETE h FROM dbo.HoanTien h JOIN dbo.ThanhToan p ON p.ThanhToanID = h.ThanhToanID "
            f"WHERE p.ThanhToanID IN ({ds('ThanhToan')})",
            f"DELETE FROM dbo.HoaDon WHERE DonHangID IN ({ds('DonHang')})",
            f"DELETE FROM dbo.ThanhToan WHERE ThanhToanID IN ({ds('ThanhToan')})",
            f"DELETE FROM dbo.SuDungKhuyenMai WHERE DonHangID IN ({ds('DonHang')})",
            f"DELETE FROM dbo.ChiTietDonHang WHERE DonHangID IN ({ds('DonHang')})",
            f"DELETE FROM dbo.LichSuKho WHERE DonHangID IN ({ds('DonHang')}) "
            f"OR PhieuNhapID IN ({ds('PhieuNhap')}) OR NguyenLieuID IN ({ds('NguyenLieu')}) "
            f"OR TaiKhoanID IN ({ds('TaiKhoan')})",
            f"DELETE FROM dbo.DonHang WHERE DonHangID IN ({ds('DonHang')})",
            f"DELETE FROM dbo.ChiTietPhieuNhap WHERE PhieuNhapID IN ({ds('PhieuNhap')})",
            f"DELETE FROM dbo.PhieuNhap WHERE PhieuNhapID IN ({ds('PhieuNhap')})",
            f"DELETE FROM dbo.CongThucLichSu WHERE MonID IN ({ds('Mon')}) OR TaiKhoanID IN ({ds('TaiKhoan')})",
            f"DELETE FROM dbo.CongThuc WHERE MonID IN ({ds('Mon')})",
            f"DELETE FROM dbo.Mon WHERE MonID IN ({ds('Mon')})",
            f"DELETE FROM dbo.DanhMuc WHERE DanhMucID IN ({ds('DanhMuc')})",
            f"DELETE FROM dbo.NguyenLieu WHERE NguyenLieuID IN ({ds('NguyenLieu')})",
            f"DELETE FROM dbo.NhaCungCap WHERE NhaCungCapID IN ({ds('NhaCungCap')})",
            f"DELETE FROM dbo.LichLamViec WHERE LichLamViecID IN ({ds('LichLamViec')})",
            f"DELETE FROM dbo.NhanVien WHERE NhanVienID IN ({ds('NhanVien')})",
            f"DELETE FROM dbo.CaLamViec WHERE CaLamViecID IN ({ds('CaLamViec')})",
            f"DELETE FROM dbo.KhuyenMai WHERE KhuyenMaiID IN ({ds('KhuyenMai')})",
            f"DELETE FROM dbo.TaiKhoan WHERE TaiKhoanID IN ({ds('TaiKhoan')})",
        ):
            cur.execute(cau_lenh)
        conn.commit()
    os.remove(TEP_ID)
    tong = sum(len(v) for k, v in id_ds.items() if k != "_CSDL")
    print(f"Da xoa {tong} ban ghi du lieu mau.")
    return 0


def _ket_noi():
    from database.connection import get_connection
    return get_connection()


# ---------------------------------------------------------------- sinh du lieu
def tao_tai_khoan_va_nhan_vien(rng, dem, so_nhan_vien):
    print(f"  Tai khoan quan tri / quan ly / {8} nhan vien dang nhap...")
    da_co = {a["Email"].strip().lower(): a for a in auth_service.danh_sach_tai_khoan()}
    ds_tk = []
    dung_lai = 0
    for ho_ten, email, mk, vai_tro in TAI_KHOAN_MAU:
        cu = da_co.get(email.lower())
        if cu:
            # Con lai tu lan chay bi ngat giua chung: dung lai, khong tao trung email.
            dung_lai += 1
            ds_tk.append(cu)
            continue
        tk = _kq(auth_service.tao_tai_khoan(ho_ten, email, mk, vai_tro), f"tao tai khoan {email}")
        dem.them("TaiKhoan", tk["TaiKhoanID"])
        ds_tk.append(tk)
    if dung_lai:
        print(f"    dung lai {dung_lai} tai khoan mau da co san (khong vao so ID, --xoa khong xoa)")

    print(f"  {so_nhan_vien} ho so nhan vien...")
    da_dung = {t["HoTen"] for t in ds_tk}
    ds_nv = []
    hom_nay = datetime.date.today()
    for i in range(so_nhan_vien):
        ho_ten = _ho_ten_day_du(rng, da_dung)
        # 8 nguoi dau gan tai khoan dang nhap; so con lai chi co ho so.
        tk_id = ds_tk[2 + i]["TaiKhoanID"] if i < 8 else None
        nv = _kq(nv_service.tao_nv({
            "ho_ten": ho_ten,
            "chuc_vu": rng.choice(CHUC_VU),
            "so_dien_thoai": f"0{rng.choice([90, 91, 93, 94, 96, 97, 98])}{rng.randint(1000000, 9999999)}",
            "ngay_vao_lam": (hom_nay - datetime.timedelta(days=rng.randint(20, 900))).isoformat(),
            "tai_khoan_id": tk_id,
        }), f"tao nhan vien {ho_ten}")
        dem.them("NhanVien", nv["NhanVienID"])
        ds_nv.append(nv)
    # Mot nguoi da nghi viec va mot nguoi tam nghi de bo loc co du lieu.
    for nv, trang_thai in ((ds_nv[-1], "NGHI_VIEC"), (ds_nv[-2], "TAM_NGHI")):
        _kq(nv_service.doi_trang_thai_nv(nv["NhanVienID"], trang_thai), "doi trang thai nhan vien")
    return ds_tk, ds_nv


def tao_ca_va_lich(rng, dem, ds_nv):
    print(f"  {len(CA_LAM)} ca lam va lich lam {SO_NGAY_LICH_QUA_KHU + SO_NGAY_LICH_SAP_TOI + 1} ngay...")
    ds_ca = []
    for ten, bat_dau, ket_thuc, mo_ta in CA_LAM:
        ca = _kq(nv_service.tao_ca({"ten_ca": ten, "gio_bat_dau": bat_dau,
                                    "gio_ket_thuc": ket_thuc, "mo_ta": mo_ta}), f"tao ca {ten}")
        dem.them("CaLamViec", ca["CaLamViecID"])
        ds_ca.append(ca)

    # Lich qua khu khong tao duoc qua API (chan ngay da qua) nen ghi thang, da dam bao
    # moi nguoi toi da 1 ca moi ngay nen khong the trung gio.
    dang_lam = [nv for nv in ds_nv if nv["TrangThai"] == "DANG_LAM"]
    dong = []
    hom_nay = datetime.date.today()
    for lech in range(-SO_NGAY_LICH_QUA_KHU, SO_NGAY_LICH_SAP_TOI + 1):
        ngay = hom_nay + datetime.timedelta(days=lech)
        rng.shuffle(dang_lam)
        vi_tri = 0
        for ca in ds_ca:
            # Ca sang / toi dong nguoi, ca dem chi 2 nguoi.
            so_nguoi = 2 if ca["TenCa"] == "Ca đêm" else rng.randint(4, 6)
            for nv in dang_lam[vi_tri:vi_tri + so_nguoi]:
                if ngay < hom_nay:
                    trang_thai = "VANG" if rng.random() < 0.07 else "DA_LAM"
                else:
                    trang_thai = "DA_XEP"
                dong.append((nv["NhanVienID"], ca["CaLamViecID"], ngay, trang_thai))
            vi_tri += so_nguoi
    with closing(_ket_noi()) as conn:
        cur = conn.cursor()
        cur.executemany(
            "INSERT INTO dbo.LichLamViec (NhanVienID, CaLamViecID, NgayLam, TrangThai, NgayTao) "
            "VALUES (?, ?, ?, ?, SYSDATETIME())", dong)
        conn.commit()
        cur.execute("SELECT LichLamViecID FROM dbo.LichLamViec ORDER BY LichLamViecID DESC")
        for (lich_id,) in cur.fetchmany(len(dong)):
            dem.them("LichLamViec", lich_id)
    return ds_ca


def tao_kho(rng, dem, tk_quan_tri, tk_quan_ly):
    print(f"  {len(NGUYEN_LIEU)} nguyen lieu, {len(NHA_CUNG_CAP)} nha cung cap...")
    ds_nl = {}
    for ten, don_vi, muc_toi_thieu, _, _ in NGUYEN_LIEU:
        nl = _kq(kho_service.tao_nguyen_lieu(tk_quan_tri, {
            "ten_nguyen_lieu": ten, "don_vi_tinh": don_vi, "muc_ton_toi_thieu": muc_toi_thieu,
        }), f"tao nguyen lieu {ten}")
        dem.them("NguyenLieu", nl["NguyenLieuID"])
        ds_nl[ten] = nl

    ds_ncc = []
    for ten, sdt, email, dia_chi in NHA_CUNG_CAP:
        body = {"ten_nha_cung_cap": ten, "so_dien_thoai": sdt, "dia_chi": dia_chi}
        if email:
            body["email"] = email
        ncc = _kq(ncc_service.tao_ncc(body), f"tao nha cung cap {ten}")
        dem.them("NhaCungCap", ncc["NhaCungCapID"])
        ds_ncc.append(ncc)

    # Moi nguyen lieu duoc nhap 4 lan trong thang. He so 1.25 de sau khi tru kho cho
    # ~500 don van con du; vai thu nhap thieu (MUA_THIEU) de bang "sap het" co du lieu that.
    dong_ke_hoach = []
    so_luong_moi_lan = {}
    for ten, don_vi, _, luong_thang, (tu, den) in NGUYEN_LIEU:
        he_so = (0.42 if ten in MUA_THIEU else rng.uniform(1.2, 1.45)) * rng.uniform(0.95, 1.05)
        so_luong_moi_lan[ten] = round(luong_thang / 4 * he_so, 3)
        for _ in range(4):
            dong_ke_hoach.append({
                "ten": ten, "nguyen_lieu_id": ds_nl[ten]["NguyenLieuID"],
                "so_luong": so_luong_moi_lan[ten],
            })
    # Xep xen ke theo tung luot nhap: moi nhom 4 dong lien nhau luon la 4 nguyen lieu
    # khac nhau (khong the trung nguyen lieu trong 1 phieu) va trai deu ra cac phieu.
    theo_ten = {}
    for d in dong_ke_hoach:
        theo_ten.setdefault(d["ten"], []).append(d)
    ds_ten = list(theo_ten)
    rng.shuffle(ds_ten)
    xep_lai = []
    for luot in range(4):
        for ten in ds_ten:
            if luot < len(theo_ten[ten]):
                xep_lai.append(theo_ten[ten][luot])
    dong_ke_hoach = xep_lai

    ds_phieu = []
    for i in range(0, len(dong_ke_hoach), 4):
        lo = dong_ke_hoach[i:i + 4]
        items = [{"nguyen_lieu_id": d["nguyen_lieu_id"], "so_luong": d["so_luong"],
                  "don_gia_nhap": _don_gia_nhap(rng, d["ten"])} for d in lo]
        phieu = _kq(ncc_service.tao_phieu(tk_quan_ly, {
            "nha_cung_cap_id": ds_ncc[len(ds_phieu) % len(ds_ncc)]["NhaCungCapID"],
            "ghi_chu": rng.choice(LY_DO_NHAP), "items": items,
        }), "tao phieu nhap")
        dem.them("PhieuNhap", phieu["PhieuNhapID"])
        ds_phieu.append(phieu)
    print(f"  {len(ds_phieu)} phieu nhap hang...")

    # Tat ca phieu ke hoach deu duoc xac nhan: moi nguyen lieu phai nhan du 4 lan nhap
    # thi ton kho moi du cho ~500 don. Phieu cho hang / bi huy tao rieng ben duoi, khong
    # nam trong ke hoach, neu khong nguyen lieu roi vao 4 phieu cuoi se hut 1/4 luong hang.
    for phieu in ds_phieu:
        _kq(ncc_service.xac_nhan_phieu(phieu["PhieuNhapID"], tk_quan_ly), "xac nhan phieu nhap")

    # 4 phieu ngoai ke hoach cho du trang thai tren trang nhap hang: 3 phieu dang cho
    # hang va 1 phieu bi huy. Khong phieu nao cong kho nen khong anh huong ton kho.
    ds_ten_ngoai = list(so_luong_moi_lan)
    for _ in range(4):
        rng.shuffle(ds_ten_ngoai)
        items = [{"nguyen_lieu_id": ds_nl[ten]["NguyenLieuID"],
                  "so_luong": so_luong_moi_lan[ten],
                  "don_gia_nhap": _don_gia_nhap(rng, ten)} for ten in ds_ten_ngoai[:4]]
        phieu = _kq(ncc_service.tao_phieu(tk_quan_ly, {
            "nha_cung_cap_id": ds_ncc[len(ds_phieu) % len(ds_ncc)]["NhaCungCapID"],
            "ghi_chu": rng.choice(LY_DO_NHAP), "items": items,
        }), "tao phieu nhap")
        dem.them("PhieuNhap", phieu["PhieuNhapID"])
        ds_phieu.append(phieu)
    _kq(ncc_service.huy_phieu(ds_phieu[-1]["PhieuNhapID"], tk_quan_ly, "Nhập nhầm nhà cung cấp"),
        "huy phieu nhap")
    return ds_nl, ds_ncc, ds_phieu


def dieu_chinh_sap_het(tk, ds_nl):
    """Kiem ke vai nguyen lieu xuong muc sap het de bang "sap het" co du lieu that.

    MUA_THIEU chi quyet dinh luong nhap, con ton cuoi ky phu thuoc so don sinh ra, nen
    kiem ke lai cho chac chan thay vi doan he so nhap.
    """
    muc_toi_thieu = {ten: muc for ten, _, muc, _, _ in NGUYEN_LIEU}
    for ten in sorted(MUA_THIEU):
        _kq(kho_service.dieu_chinh_ton_kho(tk, {
            "nguyen_lieu_id": ds_nl[ten]["NguyenLieuID"],
            "so_luong_thuc_te": round(muc_toi_thieu[ten] * 0.5, 3) or 0.001,
            "ly_do": "Kiểm kê cuối kỳ: hao hụt và bán chạy hơn dự kiến",
        }), f"kiem ke {ten}")


def _don_gia_nhap(rng, ten):
    """Don gia nhap sat gia thi truong, chi de bao cao chi phi nhap co so that."""
    bang = {
        "Cà phê hạt Robusta": (110000, 145000), "Cà phê hạt Arabica": (165000, 210000),
        "Sữa đặc có đường": (22000, 28000), "Sữa tươi không đường": (28000, 34000),
        "Kem sữa béo": (90000, 120000), "Đường cát trắng": (22000, 27000),
        "Đá viên": (8000, 12000), "Trà đen": (90000, 130000),
        "Trà xanh Thái Nguyên": (180000, 240000), "Bột matcha": (600000, 780000),
        "Bột cacao": (180000, 240000), "Siro đường": (55000, 75000),
        "Siro đào": (95000, 125000), "Siro vải": (95000, 125000), "Siro chanh dây": (95000, 125000),
        "Chanh tươi": (25000, 40000), "Cam tươi": (28000, 42000), "Đào ngâm": (85000, 120000),
        "Vải ngâm": (85000, 120000), "Trân châu": (45000, 65000), "Hạt é": (70000, 95000),
        "Thạch trái cây": (55000, 75000), "Sữa chua": (7000, 9500), "Mật ong": (180000, 260000),
        "Gừng": (45000, 70000), "Sả": (25000, 40000), "Xoài chín": (45000, 65000),
        "Bơ sáp": (55000, 80000), "Cà rốt": (18000, 28000), "Trứng gà": (2800, 3800),
        "Muối biển": (15000, 25000), "Ly nhựa 500ml": (900, 1300), "Ống hút giấy": (400, 700),
        "Túi giấy mang đi": (1200, 1800), "Khăn giấy": (18000, 26000),
    }
    tu, den = bang.get(ten, (20000, 50000))
    return rng.randint(tu, den)


def tao_thuc_don(rng, dem, tk):
    print(f"  {len(THUC_DON)} mon va cong thuc pha che...")
    ds_nhom = {}
    for _, nhom, _ in THUC_DON:
        if nhom not in ds_nhom:
            dm = _kq(menu_service.them_danh_muc(nhom, "Dữ liệu mẫu"), f"tao nhom {nhom}")
            dem.them("DanhMuc", dm["DanhMucID"])
            ds_nhom[nhom] = dm["DanhMucID"]
    with closing(_ket_noi()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT NguyenLieuID, TenNguyenLieu FROM dbo.NguyenLieu")
        id_nl = {ten: nl_id for nl_id, ten in cur.fetchall()}

    ds_mon = []
    for ten, nhom, gia in THUC_DON:
        mon = _kq(menu_service.them_mon(ten, ds_nhom[nhom], gia), f"tao mon {ten}")
        dem.them("Mon", mon["MonID"])
        ds_mon.append(mon)
    for ten, _, _ in THUC_DON:
        cong_thuc = CONG_THUC.get(ten)
        if not cong_thuc:
            continue
        mon = next(m for m in ds_mon if m["TenMon"] == ten)
        items = [{"nguyen_lieu_id": id_nl[t], "so_luong_can": sl} for t, sl in cong_thuc]
        _kq(kho_service.luu_cong_thuc(tk, mon["MonID"], {"items": items, "ly_do": "Công thức chuẩn của quán"}),
            f"luu cong thuc {ten}")
    return ds_mon


def tao_khuyen_mai(rng, dem):
    print(f"  {len(KHUYEN_MAI)} chuong trinh khuyen mai...")
    bay_gio = _bay_gio()
    ds_km = []
    for km in KHUYEN_MAI:
        body = {
            "ma_khuyen_mai": km["ma"], "ten_khuyen_mai": km["ten"], "loai_giam_gia": km["loai"],
            "gia_tri_giam": km["gia_tri"], "don_hang_toi_thieu": km["toi_thieu"],
            "giam_toi_da": km["toi_da"], "so_luong_su_dung": km["luot"],
            "ngay_bat_dau": (bay_gio + datetime.timedelta(days=km["tu"])).strftime("%Y-%m-%dT%H:%M"),
            "ngay_ket_thuc": (bay_gio + datetime.timedelta(days=km["den"])).strftime("%Y-%m-%dT%H:%M"),
        }
        ma = _kq(km_service.tao(body), f"tao khuyen mai {km['ma']}")
        dem.them("KhuyenMai", ma["KhuyenMaiID"])
        if not km["bat"]:
            _kq(km_service.doi_trang_thai(ma["KhuyenMaiID"], False), "tat khuyen mai")
        ds_km.append(ma)
    return [km for km in ds_km if km["TinhTrang"] == "DANG_DIEN_RA"]


def tao_don_hang(rng, dem, ds_tk_ban_hang, ds_mon, ds_km, so_don):
    print(f"  {so_don} don hang (kem thanh toan, tru kho, huy va hoan tien)...")
    hom_nay = datetime.date.today()
    # Chia don theo ngay: cuoi tuan dong khach hon.
    ngay_ds = []
    for lech in range(SO_NGAY_QUA_KHU - 1, -1, -1):
        ngay = hom_nay - datetime.timedelta(days=lech)
        ngay_ds.append((ngay, TI_TRONG_THU[ngay.weekday()]))
    tong_trong_so = sum(t for _, t in ngay_ds)
    so_don_ngay = {ngay: max(1, round(so_don * t / tong_trong_so)) for ngay, t in ngay_ds}

    # Mon ban chay: vai mon quen thuoc chiem phan lon so ly, giong quan that.
    mon_theo_nhom = {}
    for mon in ds_mon:
        mon_theo_nhom.setdefault(mon["TenDanhMuc"], []).append(mon)
    trong_so_nhom = {"Cà phê Việt": 34, "Trà & Trà sữa": 26, "Cà phê Ý": 16,
                     "Đá xay & Sinh tố": 10, "Nước ép & Nước ngọt": 9, "Bánh ngọt": 5}
    ds_chon_mon = [(mon, trong_so_nhom.get(nhom, 3) / len(ds_mon_nhom))
                   for nhom, ds_mon_nhom in mon_theo_nhom.items() for mon in ds_mon_nhom]

    dem_huy = dem_tru_kho_loi = dem_khuyen_mai = 0
    don_can_lui_gio = []

    for ngay, _ in ngay_ds:
        la_hom_nay = ngay == hom_nay
        # Hom nay chi sinh don toi gio hien tai, khong de don roi vao tuong lai.
        gio_toi_da = _bay_gio().hour if la_hom_nay else 23
        ds_gio = [(g, t) for g, t in GIO_BAN if g <= gio_toi_da] or [(max(0, gio_toi_da), 1)]
        for _ in range(so_don_ngay[ngay]):
            tk_id = rng.choice(ds_tk_ban_hang)["TaiKhoanID"]
            gio = _chon_theo_trong_so(rng, ds_gio)
            # Don hom nay: vai don con dang mo (khach dang ngoi) nen chua thu tien.
            con_mo = la_hom_nay and rng.random() < 0.35
            items = []
            for _ in range(_chon_theo_trong_so(rng, [(1, 35), (2, 35), (3, 20), (4, 10)])):
                mon = _chon_mon(rng, ds_chon_mon)
                items.append({"mon_id": mon["MonID"], "so_luong": _chon_theo_trong_so(rng, [(1, 60), (2, 30), (3, 10)]),
                              "ghi_chu": rng.choice(GHI_CHU_MON)})
            ma_km = rng.choice(ds_km)["MaKhuyenMai"] if (ds_km and rng.random() < 0.16) else None
            don, err = don_service.tao_don(tk_id, items, rng.choice(GHI_CHU_DON), ma_km)
            if err and ma_km:  # khong dat don toi thieu -> tao lai khong kem ma
                don, err = don_service.tao_don(tk_id, items, rng.choice(GHI_CHU_DON))
                ma_km = None
            don = _kq((don, err), "tao don")
            dem_khuyen_mai += bool(ma_km)
            dem.them("DonHang", don["DonHangID"])
            don_id = don["DonHangID"]

            if con_mo:
                # Don dang phuc vu: vai don da vao pha che (da tru kho), con lai moi tao.
                if rng.random() < 0.3:
                    _kq(don_service.doi_trang_thai_don(don_id, "CHO_PHA_CHE"), "chuyen trang thai")
                    _kq(don_service.doi_trang_thai_don(don_id, "DANG_PHA_CHE"), "chuyen trang thai")
                    _, loi_tru = kho_service.tru_kho_theo_don(tk_id, {"don_hang_id": don_id})
                    dem_tru_kho_loi += bool(loi_tru)
                don_can_lui_gio.append((don_id, ngay, gio, rng.randint(0, 59)))
                continue

            _kq(don_service.doi_trang_thai_don(don_id, "CHO_PHA_CHE"), "chuyen trang thai")
            _kq(don_service.doi_trang_thai_don(don_id, "DANG_PHA_CHE"), "chuyen trang thai")
            _, loi_tru = kho_service.tru_kho_theo_don(tk_id, {"don_hang_id": don_id})
            dem_tru_kho_loi += bool(loi_tru)

            if rng.random() < 0.075:
                dem_huy += 1
                ly_do = rng.choice(LY_DO_HUY)
                # Don giam het tien thi khong co gi de thu/hoan.
                if float(don["ThanhTien"]) > 0 and rng.random() < 0.5:  # da thu tien roi moi huy
                    _thu_tien(rng, dem, don)
                    _kq(don_service.huy_don(don_id, ly_do, hoan_tien=True, duoc_hoan_tien=True),
                        "huy don da thu tien")
                else:
                    _kq(don_service.huy_don(don_id, ly_do), "huy don")
                don_can_lui_gio.append((don_id, ngay, gio, rng.randint(0, 59)))
                continue

            _kq(don_service.doi_trang_thai_don(don_id, "HOAN_THANH"), "chuyen trang thai")
            tt = _thu_tien(rng, dem, don) if float(don["ThanhTien"]) > 0 else None

            # Vai don bi hoan mot phan hoac hoan het vi khach phan nan.
            if tt and rng.random() < 0.012:
                so_tien = float(don["ThanhTien"])
                if rng.random() < 0.6:
                    so_tien = round(so_tien * rng.uniform(0.2, 0.6), 2)
                if so_tien > 0:
                    _kq(tt_service.hoan_tien(tt["ThanhToanID"], so_tien, rng.choice(LY_DO_HOAN),
                                             "RF" + str(tt["ThanhToanID"]).zfill(6)), "hoan tien")
            don_can_lui_gio.append((don_id, ngay, gio, rng.randint(0, 59)))

    print(f"    da huy {dem_huy} don, {dem_khuyen_mai} don dung ma khuyen mai, "
          f"{dem_tru_kho_loi} don khong tru duoc kho (thieu nguyen lieu)")
    return don_can_lui_gio


def _thu_tien(rng, dem, don):
    phuong_thuc = _chon_theo_trong_so(rng, [("TIEN_MAT", 65), ("CHUYEN_KHOAN", 25), ("THE", 10)])
    ma_giao_dich = None
    if phuong_thuc != "TIEN_MAT":
        ma_giao_dich = ("CK" if phuong_thuc == "CHUYEN_KHOAN" else "THE") + str(rng.randint(10**7, 10**8))
    tt = _kq(tt_service.tao_thanh_toan(don["DonHangID"], phuong_thuc, float(don["ThanhTien"]), ma_giao_dich),
             "tao thanh toan")
    dem.them("ThanhToan", tt["ThanhToanID"])
    _kq(tt_service.xac_nhan_thanh_toan(tt["ThanhToanID"], True, ma_giao_dich), "xac nhan thanh toan")
    return tt


def lui_thoi_gian(don_can_lui_gio, ds_phieu):
    """Lui ngay gio cua don va phieu nhap ve qua khu de bao cao co du lieu nhieu ngay.

    Cac bang lien quan lui cung mot khoang de thu tu (dat -> pha che -> thu tien -> hoan)
    khong bi dao lon.
    """
    print("  Lui ngay gio don hang va phieu nhap ve qua khu...")
    with closing(_ket_noi()) as conn:
        cur = conn.cursor()
        for don_id, ngay, gio, phut in don_can_lui_gio:
            cur.execute("SELECT ThoiGianDat FROM dbo.DonHang WHERE DonHangID = ?", (don_id,))
            hien_tai = cur.fetchone()[0]
            dich = datetime.datetime.combine(ngay, datetime.time(gio, phut, 0))
            giay = int((dich - hien_tai).total_seconds())
            for cau_lenh, tham_so in (
                ("UPDATE dbo.DonHang SET ThoiGianDat = DATEADD(second, ?, ThoiGianDat), "
                 "NgayCapNhat = DATEADD(second, ?, NgayCapNhat) WHERE DonHangID = ?", (giay, giay, don_id)),
                ("UPDATE dbo.ThanhToan SET NgayTao = DATEADD(second, ?, NgayTao), "
                 "ThoiGianThanhToan = DATEADD(second, ?, ThoiGianThanhToan) WHERE DonHangID = ?",
                 (giay, giay, don_id)),
                ("UPDATE dbo.HoaDon SET NgayLap = DATEADD(second, ?, NgayLap) WHERE DonHangID = ?", (giay, don_id)),
                ("UPDATE dbo.SuDungKhuyenMai SET NgaySuDung = DATEADD(second, ?, NgaySuDung) WHERE DonHangID = ?",
                 (giay, don_id)),
                ("UPDATE dbo.LichSuKho SET NgayGiaoDich = DATEADD(second, ?, NgayGiaoDich) WHERE DonHangID = ?",
                 (giay, don_id)),
                ("UPDATE h SET h.NgayYeuCau = DATEADD(second, ?, h.NgayYeuCau), "
                 "h.NgayHoanTien = DATEADD(second, ?, h.NgayHoanTien) "
                 "FROM dbo.HoanTien h JOIN dbo.ThanhToan p ON p.ThanhToanID = h.ThanhToanID "
                 "WHERE p.DonHangID = ?", (giay, giay, don_id)),
            ):
                cur.execute(cau_lenh, tham_so)

        hom_nay = datetime.date.today()
        so_ngay = SO_NGAY_QUA_KHU
        for i, phieu in enumerate(ds_phieu):
            ngay = hom_nay - datetime.timedelta(days=max(0, so_ngay - 1 - round(i * (so_ngay - 1) / max(1, len(ds_phieu) - 1))))
            cur.execute("SELECT NgayNhap FROM dbo.PhieuNhap WHERE PhieuNhapID = ?", (phieu["PhieuNhapID"],))
            hien_tai = cur.fetchone()[0]
            dich = datetime.datetime.combine(ngay, datetime.time(rng_gio_nhap(i), 30))
            giay = int((dich - hien_tai).total_seconds())
            for cau_lenh, tham_so in (
                ("UPDATE dbo.PhieuNhap SET NgayNhap = DATEADD(second, ?, NgayNhap), "
                 "NgayXacNhan = DATEADD(second, ?, NgayXacNhan), NgayCapNhat = DATEADD(second, ?, NgayCapNhat) "
                 "WHERE PhieuNhapID = ?", (giay, giay, giay, phieu["PhieuNhapID"])),
                ("UPDATE dbo.LichSuKho SET NgayGiaoDich = DATEADD(second, ?, NgayGiaoDich) WHERE PhieuNhapID = ?",
                 (giay, phieu["PhieuNhapID"])),
            ):
                cur.execute(cau_lenh, tham_so)
        conn.commit()


def rng_gio_nhap(i):
    return [8, 9, 10, 14, 15, 16][i % 6]


def bao_cao_tong_ket():
    with closing(_ket_noi()) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT (SELECT COUNT(*) FROM dbo.NhanVien) AS NhanVien, "
            "(SELECT COUNT(*) FROM dbo.LichLamViec) AS Lich, "
            "(SELECT COUNT(*) FROM dbo.DonHang) AS DonHang, "
            "(SELECT COUNT(*) FROM dbo.DonHang WHERE TrangThai = 'DA_HUY') AS DonHuy, "
            "(SELECT COUNT(*) FROM dbo.ThanhToan WHERE TrangThai IN ('THANH_CONG','HOAN_MOT_PHAN','DA_HOAN_TIEN')) AS DaThu, "
            "(SELECT COALESCE(SUM(SoTien), 0) FROM dbo.ThanhToan WHERE TrangThai IN ('THANH_CONG','HOAN_MOT_PHAN','DA_HOAN_TIEN')) AS DoanhThu, "
            "(SELECT COUNT(*) FROM dbo.HoanTien) AS LanHoan, "
            "(SELECT COUNT(*) FROM dbo.PhieuNhap WHERE TrangThai = 'DA_NHAN') AS PhieuNhap, "
            "(SELECT COUNT(*) FROM dbo.LichSuKho) AS GiaoDichKho, "
            "(SELECT COUNT(*) FROM dbo.NguyenLieu WHERE TrangThai = 1 AND SoLuongTon <= MucTonToiThieu) AS SapHet"
        )
        r = cur.fetchone()
    print("\nTong ket du lieu mau:")
    print(f"  Nhan vien {r.NhanVien} | lich lam {r.Lich} | don hang {r.DonHang} (huy {r.DonHuy})")
    print(f"  Da thu tien {r.DaThu} don, doanh thu {float(r.DoanhThu):,.0f} d, {r.LanHoan} lan hoan tien")
    print(f"  Phieu nhap da nhan {r.PhieuNhap} | giao dich kho {r.GiaoDichKho} | nguyen lieu sap het {r.SapHet}")
    print("\nDang nhap thu: admin@caphe.local / admin123  |  quanly@caphe.local / quanly123"
          "  |  nhanvien01@caphe.local / nhanvien123")


def main():
    parser = argparse.ArgumentParser(description="Sinh du lieu mau cho quan ca phe.")
    parser.add_argument("--dong-y", action="store_true", help="xac nhan ghi du lieu")
    parser.add_argument("--xoa", action="store_true", help="xoa du lieu mau da sinh truoc do")
    parser.add_argument("--so-nhan-vien", type=int, default=40, help="so ho so nhan vien (mac dinh 40)")
    parser.add_argument("--so-don", type=int, default=500, help="so don hang (mac dinh 500)")
    parser.add_argument("--seed", type=int, default=None, help="seed ngau nhien de chay lai giong nhau")
    parser.add_argument("--toi-csdl-that", action="store_true",
                        help=f"cho phep ghi vao {CSDL_THAT} (mac dinh tu choi)")
    args = parser.parse_args()

    if args.xoa:
        return xoa_du_lieu_mau()

    if DB_NAME == CSDL_THAT and not args.toi_csdl_that:
        print(f"Tu choi: DB_NAME dang la CSDL that ({DB_NAME}).")
        print("Hay tro sang CSDL tam QLCP_ (vi du: DB_NAME=QLCP_mau) hoac them --toi-csdl-that neu ban that su muon.")
        return 2
    if not args.dong_y:
        print(f"Script se ghi du lieu mau vao CSDL: {DB_NAME}")
        print("Chay lai kem --dong-y de xac nhan.")
        return 2

    thieu = _bang_con_thieu()
    if thieu:
        print(f"CSDL {DB_NAME} thieu bang: {', '.join(thieu)}.")
        print("Nap du schema truoc: schema.sql, schema_sprint2.sql, schema_sprint3.sql, "
              "update_01_promotions.sql, update_02_staff_schedule.sql, roi seed.sql "
              "(thu muc database/).")
        return 2

    con_sot = _du_lieu_mau_con_sot()
    if con_sot:
        print(f"CSDL {DB_NAME} con du lieu mau tu lan chay truoc: {', '.join(con_sot)}.")
        print("Chay --xoa truoc khi sinh lai de khong tao ban trung.")
        return 2
    if not _xu_ly_tep_id_cu():
        return 2

    rng = random.Random(args.seed)
    dem = BoDem()
    bat_dau = time.time()
    print(f"Sinh du lieu mau vao CSDL {DB_NAME} ({args.so_nhan_vien} nhan vien, {args.so_don} don)...")
    try:
        ds_tk, ds_nv = tao_tai_khoan_va_nhan_vien(rng, dem, args.so_nhan_vien)
        tao_ca_va_lich(rng, dem, ds_nv)
        ds_nl, _, ds_phieu = tao_kho(rng, dem, ds_tk[0]["TaiKhoanID"], ds_tk[1]["TaiKhoanID"])
        ds_mon = tao_thuc_don(rng, dem, ds_tk[0]["TaiKhoanID"])
        ds_km = tao_khuyen_mai(rng, dem)
        # Don hang gan cho 8 tai khoan nhan vien ban hang (va quan ly).
        tk_ban_hang = ds_tk[1:10]
        lui_don = tao_don_hang(rng, dem, tk_ban_hang, ds_mon, ds_km, args.so_don)
        dieu_chinh_sap_het(ds_tk[0]["TaiKhoanID"], ds_nl)
        lui_thoi_gian(lui_don, ds_phieu)
    except BaseException:
        # Loi giua chung: van luu ID da tao de --xoa don sach duoc.
        dem.luu()
        print(f"\nGap loi giua chung. Da luu ID vao {TEP_ID}; chay --xoa de don sach.")
        raise
    dem.luu()
    bao_cao_tong_ket()
    print(f"\nXong sau {time.time() - bat_dau:.0f} giay. Xoa du lieu mau: --xoa")
    return 0


if __name__ == "__main__":
    sys.exit(main())
