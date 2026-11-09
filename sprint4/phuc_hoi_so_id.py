"""Phuc hoi du_lieu_mau_ids.json (so ID de --xoa) khi tep bi mat.

Tep so ID sinh ra luc tao du lieu mau. Neu bi mat, --xoa khong biet xoa ban ghi nao.
Script nay doc lai CSDL, nhan dien ban ghi mau theo dau hieu dac trung, roi ghi lai so.

Dau hieu nhan dien (du lieu mau sinh ra co quy luat ro rang):
- NhanVien/CaLamViec/LichLamViec/KhuyenMai/NguyenLieu/NhaCungCap: ca bang deu la du lieu mau.
- DanhMuc: co MoTa = 'Du lieu mau'. Mon: thuoc cac nhom do.
- PhieuNhap: lui ngay gio ve phut :30 giay :00; phieu ngoai ke hoach lech dau hieu nay.
- DonHang: lui ngay gio ve giay :00 (lech lam tron con :59); ban ghi nguoi dung tao
  that co giay bat ky.
- ThanhToan: thuoc cac don mau.
- TaiKhoan: de trong - 10 tai khoan dang nhap mau duoc dung lai, khong xoa theo (xem .cu).

Chay: py phuc_hoi_so_id.py            (chi xem, khong ghi)
       py phuc_hoi_so_id.py --ghi     (ghi tep so ID)
       py phuc_hoi_so_id.py --thu-xoa (thu chay DELETE trong giao dich roi huy bo)
"""

import argparse
import json
import os
import sys
from contextlib import closing

from bootstrap import ensure_runtime

ensure_runtime(allow_reexec=__name__ == "__main__")

from config.settings import DB_NAME  # noqa: E402
from database.connection import get_connection  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TEP_ID = os.path.join(os.path.dirname(os.path.abspath(__file__)), "du_lieu_mau_ids.json")

# So ban ghi mong doi cua bo du lieu mau dang co (kiem tra cheo, sai thi dung).
MONG_DOI = {
    "TaiKhoan": 0, "NhanVien": 40, "CaLamViec": 4, "LichLamViec": 494,
    "KhuyenMai": 7, "NguyenLieu": 35, "NhaCungCap": 6, "PhieuNhap": 39,
    "DanhMuc": 6, "Mon": 34, "DonHang": 500, "ThanhToan": 480,
}

CAU_HOI = {
    "NhanVien": "SELECT NhanVienID FROM dbo.NhanVien ORDER BY NhanVienID",
    "CaLamViec": "SELECT CaLamViecID FROM dbo.CaLamViec ORDER BY CaLamViecID",
    "LichLamViec": "SELECT LichLamViecID FROM dbo.LichLamViec ORDER BY LichLamViecID",
    "KhuyenMai": "SELECT KhuyenMaiID FROM dbo.KhuyenMai ORDER BY KhuyenMaiID",
    "NguyenLieu": "SELECT NguyenLieuID FROM dbo.NguyenLieu ORDER BY NguyenLieuID",
    "NhaCungCap": "SELECT NhaCungCapID FROM dbo.NhaCungCap ORDER BY NhaCungCapID",
    "DanhMuc": "SELECT DanhMucID FROM dbo.DanhMuc WHERE MoTa = N'Dữ liệu mẫu' ORDER BY DanhMucID",
    "Mon": ("SELECT m.MonID FROM dbo.Mon m JOIN dbo.DanhMuc d ON d.DanhMucID = m.DanhMucID "
            "WHERE d.MoTa = N'Dữ liệu mẫu' ORDER BY m.MonID"),
    "PhieuNhap": ("SELECT PhieuNhapID FROM dbo.PhieuNhap "
                  "WHERE DATEPART(minute, NgayNhap) = 30 AND DATEPART(second, NgayNhap) = 0 "
                  "ORDER BY PhieuNhapID"),
    # Don mau: lui ngay gio ve giay :00, lech lam tron con :59. Don nguoi dung tao that
    # co giay bat ky khac 0/59 (vd :53).
    "DonHang": ("SELECT DonHangID FROM dbo.DonHang "
                "WHERE DATEPART(second, ThoiGianDat) IN (0, 59) ORDER BY DonHangID"),
    "ThanhToan": ("SELECT p.ThanhToanID FROM dbo.ThanhToan p WHERE p.DonHangID IN "
                  "(SELECT DonHangID FROM dbo.DonHang "
                  " WHERE DATEPART(second, ThoiGianDat) IN (0, 59)) ORDER BY p.ThanhToanID"),
}


def doc_id():
    so = {"_CSDL": DB_NAME}
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        for bang, cau in CAU_HOI.items():
            cur.execute(cau)
            so[bang] = [r[0] for r in cur.fetchall()]
        so["TaiKhoan"] = []  # 10 tai khoan mau dung lai, khong xoa theo
    return so


def kiem_tra(so):
    """Doi chieu so luong voi bo du lieu dang co. Tra ve True neu khop."""
    lech = []
    for bang, mong_doi in MONG_DOI.items():
        co = len(so.get(bang, []))
        if co != mong_doi:
            lech.append(f"{bang}: co {co}, mong doi {mong_doi}")
        else:
            print(f"  {bang:14} {co:>5}")
    if lech:
        print("\nSO LUONG KHONG KHOP (co the CSDL da doi, kiem tra lai truoc khi ghi):")
        for d in lech:
            print("  -", d)
        return False
    return True


def thu_xoa(so):
    """Chay dung chuoi DELETE cua --xoa trong 1 giao dich roi huy bo.

    Cho biet so ban ghi se bi xoa, khong thay doi du lieu that.
    """
    def ds(bang):
        gia_tri = so.get(bang) or []
        return ",".join(str(x) for x in gia_tri) if gia_tri else "NULL"

    cau_lenh = (
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
    )
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        tong = 0
        for cau in cau_lenh:
            cur.execute(cau)
            tong += cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0
        conn.rollback()  # khong ghi gi - chi de dem
    print(f"  Thu xoa: se xoa {tong} ban ghi (da huy bo, du lieu khong doi).")

    # Kiem tra khong con sot: sau khi xoa, cac bang mau phai khong con dong nao.
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        sot = []
        for bang in ("NhanVien", "CaLamViec", "LichLamViec", "KhuyenMai", "NguyenLieu",
                     "NhaCungCap", "DonHang"):
            cot = bang + "ID"
            cur.execute(f"SELECT COUNT(*) FROM dbo.{bang} WHERE {cot} NOT IN ({ds(bang)})")
            con_lai = cur.fetchval()
            if con_lai:
                sot.append(f"{bang}: con {con_lai} dong ngoai so (dung, khong phai du lieu mau)")
        for d in sot:
            print(f"  {d}")


def main():
    p = argparse.ArgumentParser(description="Phuc hoi so ID du lieu mau.")
    p.add_argument("--ghi", action="store_true", help="ghi tep so ID")
    p.add_argument("--thu-xoa", action="store_true", help="thu chay DELETE roi huy bo")
    args = p.parse_args()

    if os.path.exists(TEP_ID) and args.ghi:
        print(f"Da co {TEP_ID}. Xoa hoac doi ten truoc khi ghi de.")
        return 2

    print(f"Doc CSDL {DB_NAME} de nhan dien du lieu mau...")
    so = doc_id()
    khop = kiem_tra(so)

    if args.thu_xoa:
        print("\nThu chay xoa (trong giao dich, se huy bo):")
        thu_xoa(so)

    if args.ghi:
        if not khop:
            print("\nKhong ghi: so luong khong khop.")
            return 2
        with open(TEP_ID, "w", encoding="utf-8") as f:
            json.dump(so, f, ensure_ascii=False, indent=1)
        tong = sum(len(v) for k, v in so.items() if k != "_CSDL")
        print(f"\nDa ghi {TEP_ID} cho CSDL {DB_NAME} ({tong} ID).")
    else:
        print("\n(chi xem. Them --ghi de ghi tep so ID.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
