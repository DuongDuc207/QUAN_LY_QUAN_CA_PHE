"""Tạo dữ liệu demo Sprint 3, không xóa dữ liệu đang có.

Chạy: py tao_du_lieu_mau.py [--xem-truoc]
Mọi thay đổi tồn kho dùng ledger; toàn bộ lần nạp nằm trong một transaction.
"""

import argparse
from collections import Counter, defaultdict
from contextlib import closing
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import sys

from bootstrap import ensure_runtime

ensure_runtime(allow_reexec=__name__ == "__main__")

from api.inventory.ledger import ghi_bien_dong  # noqa: E402
from database.connection import get_connection  # noqa: E402
from database.du_lieu_mau_sprint3 import (  # noqa: E402
    NGUYEN_LIEU, NHA_CUNG_CAP, NHAN_SU, THUC_DON,
)
from werkzeug.security import generate_password_hash  # noqa: E402

TIEN_TO = "Mẫu - "
MAT_KHAU = "DemoS3@2026"
SO_PHIEU = 120
SO_DON = 120


def _id_moi(cur, sql, params):
    cur.execute(sql, params)
    return cur.fetchval()


def _bien_dong(cur, nl_id, tk_id, loai, sl, ly_do, ngay, **lien_ket):
    dong, loi = ghi_bien_dong(cur, nl_id, tk_id, loai, sl, ly_do, **lien_ket)
    if loi:
        raise ValueError(loi[0])
    cur.execute("UPDATE dbo.LichSuKho SET NgayGiaoDich = ? WHERE LichSuKhoID = ?",
                (ngay, dong["LichSuKhoID"]))


def _tai_khoan(cur, dem):
    ids = []
    for i, (ma, ten, vai_tro) in enumerate(NHAN_SU):
        email = f"demo.s3.{ma}@example.com"
        cur.execute("SELECT TaiKhoanID FROM dbo.TaiKhoan WHERE Email = ?", (email,))
        tk_id = cur.fetchval()
        if tk_id is None:
            tk_id = _id_moi(cur,
                "INSERT INTO dbo.TaiKhoan "
                "(VaiTroID, HoTen, Email, MatKhauHash, SoDienThoai, TrangThai) "
                "OUTPUT INSERTED.TaiKhoanID VALUES (?, ?, ?, ?, ?, ?)",
                (vai_tro, TIEN_TO + ten, email, generate_password_hash(MAT_KHAU),
                 f"090900{i:04d}", "KHOA" if ma == "tamnghi" else "HOAT_DONG"))
            dem["Nhân sự"] += 1
        ids.append(tk_id)
    return ids


def _nguyen_lieu(cur, tk_id, ngay, dem):
    ids = {}
    for ten, dv, muc, _ in NGUYEN_LIEU:
        cur.execute("SELECT NguyenLieuID FROM dbo.NguyenLieu WHERE TenNguyenLieu = ?",
                    (TIEN_TO + ten,))
        nl_id = cur.fetchval()
        if nl_id is None:
            nl_id = _id_moi(cur,
                "INSERT INTO dbo.NguyenLieu (TenNguyenLieu, DonViTinh, MucTonToiThieu, NgayTao) "
                "OUTPUT INSERTED.NguyenLieuID VALUES (?, ?, ?, ?)",
                (TIEN_TO + ten, dv, muc, ngay))
            # Tồn đầu kỳ cũng phải có lịch sử, không gán trực tiếp SoLuongTon.
            _bien_dong(cur, nl_id, tk_id, "DIEU_CHINH", Decimal(muc) * 20,
                       "Mẫu: ghi nhận tồn đầu kỳ", ngay)
            dem["Nguyên liệu"] += 1
        ids[ten] = nl_id
    return ids


def _thuc_don(cur, nl_ids, tk_id, ngay, dem):
    mon = []
    for ten_nhom, cac_mon in THUC_DON:
        cur.execute("SELECT DanhMucID FROM dbo.DanhMuc WHERE TenDanhMuc = ? ORDER BY DanhMucID",
                    (TIEN_TO + ten_nhom,))
        nhom_id = cur.fetchval()
        if nhom_id is None:
            nhom_id = _id_moi(cur,
                "INSERT INTO dbo.DanhMuc (TenDanhMuc, MoTa, NgayTao) "
                "OUTPUT INSERTED.DanhMucID VALUES (?, ?, ?)",
                (TIEN_TO + ten_nhom, "Nhóm món mẫu để trải nghiệm thực đơn và công thức", ngay))
            dem["Nhóm món"] += 1
        for ten, gia, cong_thuc in cac_mon:
            cur.execute("SELECT MonID FROM dbo.Mon WHERE TenMon = ? AND DanhMucID = ? ORDER BY MonID",
                        (TIEN_TO + ten, nhom_id))
            mon_id = cur.fetchval()
            if mon_id is None:
                mon_id = _id_moi(cur,
                    "INSERT INTO dbo.Mon (DanhMucID, TenMon, GiaBan, MoTa, NgayTao) "
                    "OUTPUT INSERTED.MonID VALUES (?, ?, ?, ?, ?)",
                    (nhom_id, TIEN_TO + ten, gia, "Món mẫu có sẵn định lượng pha chế", ngay))
                dem["Món"] += 1
                sau = [{"NguyenLieuID": nl_ids[nl], "TenNguyenLieu": TIEN_TO + nl,
                        "DonViTinh": next(r[1] for r in NGUYEN_LIEU if r[0] == nl),
                        "SoLuongCan": str(sl)} for nl, sl in cong_thuc.items()]
                # Có cả lịch sử tạo và chỉnh định lượng để xem đối chiếu trước/sau.
                truoc = [dict(r) for r in sau]
                truoc[0]["SoLuongCan"] = str(Decimal(truoc[0]["SoLuongCan"]) + 1)
                for cu, moi, ly_do, moc in (
                    ([], truoc, "Mẫu: tạo công thức ban đầu", ngay),
                    (truoc, sau, "Mẫu: cân chỉnh định lượng sau thử món", ngay + timedelta(days=1)),
                ):
                    cur.execute(
                        "INSERT INTO dbo.CongThucLichSu "
                        "(MonID, TaiKhoanID, TruocJson, SauJson, LyDo, NgayThayDoi) VALUES (?, ?, ?, ?, ?, ?)",
                        (mon_id, tk_id, json.dumps(cu, ensure_ascii=False),
                         json.dumps(moi, ensure_ascii=False), ly_do, moc))
                for nl, sl in cong_thuc.items():
                    cur.execute(
                        "INSERT INTO dbo.CongThuc (MonID, NguyenLieuID, SoLuongCan, NgayCapNhat) "
                        "VALUES (?, ?, ?, ?)", (mon_id, nl_ids[nl], sl, ngay + timedelta(days=1)))
                    dem["Dòng công thức"] += 1
                dem["Lịch sử công thức"] += 2
            mon.append((mon_id, TIEN_TO + ten, Decimal(gia), cong_thuc))
    return mon


def _nha_cung_cap(cur, dem):
    ids = []
    for i, ten in enumerate(NHA_CUNG_CAP):
        cur.execute("SELECT NhaCungCapID FROM dbo.NhaCungCap WHERE TenNhaCungCap = ?",
                    (TIEN_TO + ten,))
        ncc_id = cur.fetchval()
        if ncc_id is None:
            ncc_id = _id_moi(cur,
                "INSERT INTO dbo.NhaCungCap (TenNhaCungCap, SoDienThoai, Email, DiaChi, TrangThai) "
                "OUTPUT INSERTED.NhaCungCapID VALUES (?, ?, ?, ?, ?)",
                (TIEN_TO + ten, f"0287000{i:04d}", f"demo.s3.ncc{i+1:02d}@example.com",
                 f"{10 + i * 7} đường Hoa Mai, TP. Hồ Chí Minh (địa chỉ mẫu)",
                 0 if i >= 12 else 1))
            dem["Nhà cung cấp"] += 1
        ids.append(ncc_id)
    return ids


def _phieu_nhap(cur, nl_ids, ncc_ids, tk_ids, bay_gio, dem):
    for i in range(1, SO_PHIEU + 1):
        ma = f"PN-MAU3-{i:05d}"
        cur.execute("SELECT PhieuNhapID FROM dbo.PhieuNhap WHERE MaPhieuNhap = ?", (ma,))
        if cur.fetchval() is not None:
            continue
        ngay = bay_gio - timedelta(days=59 - (i - 1) * 51 / (SO_PHIEU - 1))
        # 80 đã nhận, 20 nháp, 20 đã hủy (10 hủy sau khi nhận).
        trang_thai = "DA_NHAN" if i % 6 < 4 else ("NHAP" if i % 6 == 4 else "DA_HUY")
        da_nhan = trang_thai == "DA_NHAN" or (trang_thai == "DA_HUY" and i % 12 == 5)
        ly_do = "Nhà cung cấp giao sai quy cách, đổi lịch giao" if trang_thai == "DA_HUY" else None
        dong = []
        for j in range(3 + i % 4):
            ten, dv, muc, gia = NGUYEN_LIEU[(i * 7 + j * 5) % 46]
            sl = (Decimal(muc) * Decimal(str(1 + (i + j) % 5)) / 2).quantize(Decimal("0.001"))
            gia = (Decimal(gia) * (1000 if dv in ("g", "ml") else 1)).quantize(Decimal("0.01"))
            dong.append((nl_ids[ten], sl, gia, (sl * gia).quantize(Decimal("0.01"))))
        tk_id = tk_ids[i % 2]
        phieu_id = _id_moi(cur,
            "INSERT INTO dbo.PhieuNhap (NhaCungCapID, TaiKhoanID, MaPhieuNhap, NgayNhap, "
            "TongTien, TrangThai, GhiChu, NgayXacNhan, TaiKhoanXacNhanID, LyDoHuy, NgayCapNhat) "
            "OUTPUT INSERTED.PhieuNhapID VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (ncc_ids[(i - 1) % 12], tk_id, ma, ngay, sum(r[3] for r in dong), trang_thai,
             f"Dữ liệu mẫu: đợt nhập {i:03d}, kiểm tra quy cách trước khi nhận",
             ngay if da_nhan else None, tk_id if da_nhan else None, ly_do,
             ngay + timedelta(seconds=1) if trang_thai == "DA_HUY" else ngay))
        for nl_id, sl, gia, tien in sorted(dong):
            cur.execute(
                "INSERT INTO dbo.ChiTietPhieuNhap "
                "(PhieuNhapID, NguyenLieuID, SoLuong, DonGiaNhap, ThanhTien) VALUES (?, ?, ?, ?, ?)",
                (phieu_id, nl_id, sl, gia, tien))
            dem["Dòng phiếu nhập"] += 1
            if da_nhan:
                _bien_dong(cur, nl_id, tk_id, "NHAP_HANG", sl, f"Mẫu: nhập theo phiếu {ma}",
                           ngay, phieu_nhap_id=phieu_id)
                if trang_thai == "DA_HUY":
                    _bien_dong(cur, nl_id, tk_id, "HUY_NHAP", -sl, f"Mẫu: trả hàng phiếu {ma}",
                               ngay + timedelta(seconds=1), phieu_nhap_id=phieu_id)
        dem["Phiếu nhập"] += 1


def _don_hang(cur, cac_mon, nl_ids, tk_ids, bay_gio, dem):
    for i in range(1, SO_DON + 1):
        ma = f"DH-MAU3-{i:05d}"
        cur.execute("SELECT DonHangID FROM dbo.DonHang WHERE MaDonHang = ?", (ma,))
        if cur.fetchval() is not None:
            continue
        ngay = bay_gio - timedelta(days=7 - (i - 1) * 6.9 / (SO_DON - 1))
        trang_thai = ("HOAN_THANH",) * 6 + ("MOI", "CHO_PHA_CHE", "DANG_PHA_CHE", "DA_HUY")
        trang_thai = trang_thai[(i - 1) % 10]
        dong = [(cac_mon[(i * 3 + j * 7) % len(cac_mon)], 1 + (i + j) % 3)
                for j in range(1 + i % 3)]
        tong = sum(m[2] * sl for m, sl in dong)
        giam = Decimal(5000 if i % 5 == 0 else 0)
        tk_id = tk_ids[2 + i % 3]
        don_id = _id_moi(cur,
            "INSERT INTO dbo.DonHang (TaiKhoanID, MaDonHang, ThoiGianDat, TongTien, GiamGia, "
            "ThanhTien, TrangThai, GhiChu, LyDoHuy, NgayCapNhat) "
            "OUTPUT INSERTED.DonHangID VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (tk_id, ma, ngay, tong, giam, tong - giam, trang_thai,
             "Đơn mẫu mang đi" if i % 2 else f"Đơn mẫu tại bàn {i % 15 + 1:02d}",
             "Khách đổi ý trước khi pha chế" if trang_thai == "DA_HUY" else None, ngay))
        tieu_hao = defaultdict(Decimal)
        for (mon_id, ten, gia, cong_thuc), sl in dong:
            cur.execute(
                "INSERT INTO dbo.ChiTietDonHang (DonHangID, MonID, TenMon, DonGia, SoLuong, ThanhTien, GhiChu) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (don_id, mon_id, ten, gia, sl, gia * sl, ("Ít đá", "Ít đường", "Bình thường")[i % 3]))
            for nl, can in cong_thuc.items():
                tieu_hao[nl_ids[nl]] += Decimal(can) * sl
        if trang_thai in ("DANG_PHA_CHE", "HOAN_THANH"):
            for nl_id, sl in sorted(tieu_hao.items()):
                _bien_dong(cur, nl_id, tk_id, "TIEU_HAO", -sl,
                           f"Mẫu: pha chế đơn {ma}", ngay, don_hang_id=don_id)
        if trang_thai == "HOAN_THANH":
            phuong_thuc = ("TIEN_MAT", "CHUYEN_KHOAN", "THE")[i % 3]
            cur.execute(
                "INSERT INTO dbo.ThanhToan (DonHangID, MaGiaoDich, PhuongThuc, SoTien, TrangThai, "
                "ThoiGianThanhToan, NgayTao) VALUES (?, ?, ?, ?, 'THANH_CONG', ?, ?)",
                (don_id, None if phuong_thuc == "TIEN_MAT" else f"GD-MAU3-{i:05d}",
                 phuong_thuc, tong - giam, ngay, ngay))
            cur.execute(
                "INSERT INTO dbo.HoaDon (DonHangID, MaHoaDon, NgayLap, TongTien, GiamGia, ThanhTien) "
                "VALUES (?, ?, ?, ?, ?, ?)", (don_id, f"HD-MAU3-{i:05d}", ngay, tong, giam, tong - giam))
            dem["Thanh toán và hóa đơn"] += 1
        dem["Đơn hàng"] += 1


def _tinh_huong_kho(cur, nl_ids, tk_id, bay_gio, dem):
    # Thực hiện sau nhập và pha chế: tạo các tình huống thực tế cho bộ lọc kho.
    for i, (ten, _, muc, _) in enumerate(NGUYEN_LIEU):
        nl_id = nl_ids[ten]
        ly_do = f"Mẫu: kiểm kê cuối kỳ - {ten}"
        cur.execute("SELECT 1 FROM dbo.LichSuKho WHERE NguyenLieuID = ? AND LyDo = ?", (nl_id, ly_do))
        if cur.fetchval():
            continue
        cur.execute("SELECT SoLuongTon FROM dbo.NguyenLieu WHERE NguyenLieuID = ?", (nl_id,))
        ton = Decimal(cur.fetchval())
        if i < 6:
            dich = Decimal(0)  # Hết hàng.
        elif i < 14:
            dich = Decimal(muc) / 2  # Sắp hết.
        else:
            dich = ton - Decimal(1)  # Xuất hủy/hao hụt nhỏ, vẫn đủ hàng.
        if dich != ton:
            _bien_dong(cur, nl_id, tk_id, "DIEU_CHINH" if i < 14 else "XUAT_KHO",
                       dich - ton, ly_do, bay_gio)
            dem["Kiểm kê / xuất kho"] += 1
    # Hai nguyên liệu cũ không có trong công thức, hai món ngừng bán.
    # Chỉ đổi trạng thái trong lần đầu tạo mẫu, không ghi đè chỉnh sửa khi chạy lại.
    if dem["Nguyên liệu"]:
        for ten, *_ in NGUYEN_LIEU[-2:]:
            cur.execute("UPDATE dbo.NguyenLieu SET TrangThai = 0, NgayCapNhat = ? WHERE NguyenLieuID = ?",
                        (bay_gio, nl_ids[ten]))
    if dem["Món"]:
        for ten in ("Mocha hazelnut", "Sữa chua chanh dây"):
            cur.execute("UPDATE dbo.Mon SET TrangThai = 0, NgayCapNhat = ? WHERE TenMon = ?",
                        (bay_gio, TIEN_TO + ten))


def tao_du_lieu(conn):
    """Nạp toàn bộ hoặc rollback; gọi lại giữ nguyên dữ liệu đã nạp và đã chỉnh sửa."""
    dem = Counter()
    bay_gio = datetime.now(timezone(timedelta(hours=7))).replace(tzinfo=None, microsecond=0)
    try:
        cur = conn.cursor()
        cur.execute("SET XACT_ABORT ON; SET QUOTED_IDENTIFIER ON; SET ANSI_NULLS ON; "
                    "IF @@TRANCOUNT = 0 BEGIN TRANSACTION")
        # Ngăn hai lần chạy công cụ cùng lúc tạo bản ghi trùng nhau.
        cur.execute(
            "DECLARE @r int; EXEC @r = sys.sp_getapplock @Resource = N'demo_sprint3', "
            "@LockMode = 'Exclusive', @LockOwner = 'Transaction', @LockTimeout = 5000; SELECT @r")
        if cur.fetchval() < 0:
            raise ValueError("Một tiến trình khác đang nạp dữ liệu mẫu. Hãy thử lại sau.")
        cur.execute("SELECT COUNT(*) FROM dbo.VaiTro WHERE VaiTroID IN (1, 2, 3)")
        if cur.fetchval() != 3:
            raise ValueError("Cần nạp database/seed.sql để có đủ ba vị trí công việc trước.")
        tk_ids = _tai_khoan(cur, dem)
        nl_ids = _nguyen_lieu(cur, tk_ids[1], bay_gio - timedelta(days=61), dem)
        cac_mon = _thuc_don(cur, nl_ids, tk_ids[1], bay_gio - timedelta(days=61), dem)
        ncc_ids = _nha_cung_cap(cur, dem)
        _phieu_nhap(cur, nl_ids, ncc_ids, tk_ids, bay_gio, dem)
        _don_hang(cur, cac_mon, nl_ids, tk_ids, bay_gio, dem)
        _tinh_huong_kho(cur, nl_ids, tk_ids[1], bay_gio, dem)
        conn.commit()
        return dem
    except BaseException:
        conn.rollback()
        raise


def main():
    p = argparse.ArgumentParser(description="Tạo nhiều dữ liệu mẫu cho kho, công thức và nhập hàng.")
    p.add_argument("--xem-truoc", action="store_true", help="Xem quy mô bộ mẫu, không kết nối hay ghi CSDL")
    args = p.parse_args()
    if args.xem_truoc:
        print(f"Bộ mẫu: {len(NHAN_SU)} nhân sự, {len(THUC_DON)} nhóm, "
              f"{sum(len(r[1]) for r in THUC_DON)} món, {len(NGUYEN_LIEU)} nguyên liệu, "
              f"{len(NHA_CUNG_CAP)} nhà cung cấp, {SO_PHIEU} phiếu nhập, {SO_DON} đơn hàng.")
        print("Có lịch sử công thức, nhập/hoàn nhập, tiêu hao, kiểm kê, xuất kho, thanh toán và hóa đơn.")
        return 0
    try:
        with closing(get_connection()) as conn:
            dem = tao_du_lieu(conn)
        if not any(dem.values()):
            print("Bộ dữ liệu mẫu đã có. Không thêm trùng hoặc thay đổi dữ liệu đã chỉnh sửa.")
            return 0
        print("Đã nạp dữ liệu mẫu:")
        for ten, sl in dem.items():
            if sl:
                print(f"  {ten}: {sl}")
        print(f"Đăng nhập quản trị: demo.s3.admin@example.com / {MAT_KHAU}")
        print(f"Quản lý: demo.s3.quanly@example.com / {MAT_KHAU}")
        print(f"Nhân viên: demo.s3.thungan@example.com / {MAT_KHAU}")
        print("Các tài khoản mẫu dùng chung mật khẩu trên; tài khoản tamnghi bị khóa.")
        return 0
    except Exception as e:
        print(f"Không thể nạp dữ liệu mẫu, đã hoàn tác lần nạp: {e}", file=sys.stderr)
        print("Kiểm tra .env và các bảng Sprint 1–3; không chạy lại schema.sql trên CSDL đang dùng.",
              file=sys.stderr)
        return 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
