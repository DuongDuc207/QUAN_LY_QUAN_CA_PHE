"""Kiểm tra nạp mẫu trên CSDL tạm: rollback, sổ cái và chạy lại an toàn."""

from contextlib import closing

import pytest
from werkzeug.security import check_password_hash

from database.connection import get_connection
import tao_du_lieu_mau as mau


def _anh_chup(cur):
    ket_qua = {}
    for bang, cot in (
        ("TaiKhoan", "TaiKhoanID"), ("DanhMuc", "DanhMucID"), ("Mon", "MonID"),
        ("NguyenLieu", "NguyenLieuID"), ("NhaCungCap", "NhaCungCapID"),
        ("CongThuc", "CongThucID"), ("CongThucLichSu", "CongThucLichSuID"),
        ("PhieuNhap", "PhieuNhapID"), ("ChiTietPhieuNhap", "ChiTietPhieuNhapID"),
        ("DonHang", "DonHangID"), ("ChiTietDonHang", "ChiTietDonHangID"),
        ("LichSuKho", "LichSuKhoID"), ("ThanhToan", "ThanhToanID"), ("HoaDon", "HoaDonID"),
    ):
        cur.execute(f"SELECT * FROM dbo.{bang} ORDER BY {cot}")
        ket_qua[bang] = [tuple(r) for r in cur.fetchall()]
    return ket_qua


def test_nap_mau_rollback_so_cai_va_khong_trung(monkeypatch):
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        truoc = _anh_chup(cur)
        with monkeypatch.context() as m:
            def loi_giua_chung(*args):
                raise ValueError("Lỗi giả lập sau khi tạo tài khoản, nguyên liệu, công thức")
            m.setattr(mau, "_phieu_nhap", loi_giua_chung)
            with pytest.raises(ValueError, match="Lỗi giả lập"):
                mau.tao_du_lieu(conn)
        assert _anh_chup(cur) == truoc

        dem = mau.tao_du_lieu(conn)
        assert dem["Nguyên liệu"] == 48
        assert dem["Món"] == 40
        assert dem["Phiếu nhập"] == dem["Đơn hàng"] == 120
        assert dem["Lịch sử công thức"] == 80
        assert dem["Thanh toán và hóa đơn"] == 72

        cur.execute("SELECT MatKhauHash FROM dbo.TaiKhoan WHERE Email = 'demo.s3.admin@example.com'")
        assert check_password_hash(cur.fetchval(), mau.MAT_KHAU)
        # Tổng phát sinh khớp số dư, từng giao dịch nối tiếp đúng số dư giao dịch trước.
        cur.execute(
            "SELECT n.NguyenLieuID FROM dbo.NguyenLieu n LEFT JOIN dbo.LichSuKho l "
            "ON l.NguyenLieuID = n.NguyenLieuID WHERE n.TenNguyenLieu LIKE N'Mẫu - %' "
            "GROUP BY n.NguyenLieuID, n.SoLuongTon "
            "HAVING n.SoLuongTon <> COALESCE(SUM(l.SoLuongThayDoi), 0)")
        assert not cur.fetchall()
        cur.execute(
            "WITH h AS (SELECT l.*, LAG(SoLuongSau, 1, CAST(0 AS decimal(18,3))) OVER "
            "(PARTITION BY l.NguyenLieuID ORDER BY NgayGiaoDich, LichSuKhoID) AS TonTruoc "
            "FROM dbo.LichSuKho l JOIN dbo.NguyenLieu n ON n.NguyenLieuID = l.NguyenLieuID "
            "WHERE n.TenNguyenLieu LIKE N'Mẫu - %') "
            "SELECT LichSuKhoID FROM h WHERE SoLuongTruoc <> TonTruoc OR SoLuongSau < 0")
        assert not cur.fetchall()
        cur.execute("SELECT DISTINCT LoaiGiaoDich FROM dbo.LichSuKho WHERE LyDo LIKE N'Mẫu:%'")
        assert {r[0] for r in cur.fetchall()} == {"DIEU_CHINH", "NHAP_HANG", "HUY_NHAP", "TIEU_HAO", "XUAT_KHO"}
        cur.execute(
            "SELECT COUNT(*), SUM(CASE WHEN SoLuongTon = 0 THEN 1 ELSE 0 END), "
            "SUM(CASE WHEN SoLuongTon > 0 AND SoLuongTon <= MucTonToiThieu THEN 1 ELSE 0 END) "
            "FROM dbo.NguyenLieu WHERE TenNguyenLieu LIKE N'Mẫu - %' AND TrangThai = 1")
        assert tuple(cur.fetchone()) == (46, 6, 8)
        cur.execute(
            "SELECT p.PhieuNhapID FROM dbo.PhieuNhap p JOIN dbo.ChiTietPhieuNhap c "
            "ON c.PhieuNhapID = p.PhieuNhapID WHERE p.MaPhieuNhap LIKE 'PN-MAU3-%' "
            "GROUP BY p.PhieuNhapID, p.TongTien HAVING p.TongTien <> SUM(c.ThanhTien) "
            "OR MIN(c.ThanhTien - ROUND(c.SoLuong * c.DonGiaNhap, 2)) <> 0 "
            "OR MAX(c.ThanhTien - ROUND(c.SoLuong * c.DonGiaNhap, 2)) <> 0")
        assert not cur.fetchall()
        cur.execute(
            "SELECT p.PhieuNhapID FROM dbo.PhieuNhap p JOIN dbo.LichSuKho l "
            "ON l.PhieuNhapID = p.PhieuNhapID WHERE p.MaPhieuNhap LIKE 'PN-MAU3-%' "
            "AND p.TrangThai = 'DA_HUY' GROUP BY p.PhieuNhapID, l.NguyenLieuID "
            "HAVING SUM(l.SoLuongThayDoi) <> 0")
        assert not cur.fetchall()
        cur.execute(
            "SELECT l.DonHangID, l.NguyenLieuID FROM dbo.LichSuKho l JOIN "
            "(SELECT ct.DonHangID, c.NguyenLieuID, SUM(ct.SoLuong * c.SoLuongCan) AS Can "
            "FROM dbo.ChiTietDonHang ct JOIN dbo.CongThuc c ON c.MonID = ct.MonID "
            "GROUP BY ct.DonHangID, c.NguyenLieuID) x ON x.DonHangID = l.DonHangID "
            "AND x.NguyenLieuID = l.NguyenLieuID WHERE l.LoaiGiaoDich = 'TIEU_HAO' "
            "AND l.LyDo LIKE N'Mẫu:%' AND l.SoLuongThayDoi <> -x.Can")
        assert not cur.fetchall()

        # Sau khi sửa dữ liệu mẫu trên web, chạy lại vẫn giữ nguyên mọi bản ghi.
        cur.execute("UPDATE dbo.TaiKhoan SET HoTen = N'Đã sửa tên', TrangThai = 'KHOA' "
                    "WHERE Email = 'demo.s3.admin@example.com'")
        cur.execute("UPDATE dbo.NguyenLieu SET TrangThai = 1 "
                    "WHERE TenNguyenLieu = N'Mẫu - Syrup hoa hồng cũ'")
        conn.commit()
        da_sua = _anh_chup(cur)
        assert not any(mau.tao_du_lieu(conn).values())
        assert _anh_chup(cur) == da_sua
