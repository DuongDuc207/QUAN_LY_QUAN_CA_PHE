"""Du lieu rieng cho kiem thu: tu tao truoc khi chay, tu xoa sau khi xong.

CSDL that khong con du lieu mau, nen test khong duoc dua vao tai khoan/mon co san.
"""

from werkzeug.security import generate_password_hash

from database.connection import get_connection

ADMIN_EMAIL = "pytest-admin@test.local"
ADMIN_MK = "admin123"
NV_EMAIL = "pytest-nhanvien@test.local"
NV_MK = "nhanvien123"

# Duoc dien khi tao: id nhom mon dang co mon (dung de thu "khong xoa duoc").
DANH_MUC_ID = None
# Mon dung cho Sprint 2: 2 mon dang ban + 1 mon ngung ban.
MON_ID = None        # 10.000
MON2_ID = None       # 25.000
MON_NGUNG_ID = None


def _them_mon(cur, ten, gia, dang_ban=1):
    cur.execute(
        "INSERT INTO dbo.Mon (DanhMucID, TenMon, GiaBan, TrangThai, NgayTao) "
        "OUTPUT INSERTED.MonID VALUES (?, ?, ?, ?, SYSDATETIME())",
        (DANH_MUC_ID, ten, gia, dang_ban),
    )
    return cur.fetchval()


def tao():
    global DANH_MUC_ID, MON_ID, MON2_ID, MON_NGUNG_ID
    with get_connection() as conn:
        cur = conn.cursor()
        xoa_cur(cur)  # lan chay truoc bi ngat giua chung
        for ho_ten, email, mk, vai_tro in (
            ("Pytest Quan Tri", ADMIN_EMAIL, ADMIN_MK, 1),
            ("Pytest Nhan Vien", NV_EMAIL, NV_MK, 3),
        ):
            cur.execute(
                "INSERT INTO dbo.TaiKhoan (VaiTroID, HoTen, Email, MatKhauHash, TrangThai, NgayTao) "
                "VALUES (?, ?, ?, ?, 'HOAT_DONG', SYSDATETIME())",
                (vai_tro, ho_ten, email, generate_password_hash(mk)),
            )
        cur.execute(
            "INSERT INTO dbo.DanhMuc (TenDanhMuc, TrangThai, NgayTao) "
            "OUTPUT INSERTED.DanhMucID VALUES (N'Pytest Nhom', 1, SYSDATETIME())"
        )
        DANH_MUC_ID = cur.fetchval()
        MON_ID = _them_mon(cur, "Pytest Mon Co San", 10000)
        MON2_ID = _them_mon(cur, "Pytest Mon Hai", 25000)
        MON_NGUNG_ID = _them_mon(cur, "Pytest Mon Ngung", 15000, dang_ban=0)
        conn.commit()


def xoa_cur(cur):
    # Don hang cua tai khoan test (Sprint 2) phai xoa truoc vi tro toi TaiKhoan/Mon.
    don_test = (
        "SELECT d.DonHangID FROM dbo.DonHang d LEFT JOIN dbo.TaiKhoan t ON t.TaiKhoanID = d.TaiKhoanID "
        "WHERE t.Email LIKE 'pytest%@test.local' OR EXISTS (SELECT 1 FROM dbo.ChiTietDonHang c "
        "  JOIN dbo.Mon m ON m.MonID = c.MonID WHERE c.DonHangID = d.DonHangID "
        "  AND (m.TenMon LIKE N'Pytest%' OR m.TenMon LIKE N'Mon Pytest%'))"
    )
    cur.execute(
        f"DELETE h FROM dbo.HoanTien h JOIN dbo.ThanhToan p ON p.ThanhToanID = h.ThanhToanID "
        f"WHERE p.DonHangID IN ({don_test})"
    )
    for bang in ("HoaDon", "ThanhToan", "ChiTietDonHang"):
        cur.execute(f"DELETE FROM dbo.{bang} WHERE DonHangID IN ({don_test})")
    cur.execute(f"DELETE FROM dbo.DonHang WHERE DonHangID IN ({don_test})")
    cur.execute(
        "DELETE m FROM dbo.Mon m JOIN dbo.DanhMuc d ON d.DanhMucID = m.DanhMucID "
        "WHERE d.TenDanhMuc LIKE N'Pytest%' OR d.TenDanhMuc LIKE N'DM Pytest%'"
    )
    cur.execute("DELETE FROM dbo.Mon WHERE TenMon LIKE N'Pytest%' OR TenMon = N'Mon Pytest'")
    cur.execute(
        "DELETE FROM dbo.DanhMuc WHERE TenDanhMuc LIKE N'Pytest%' OR TenDanhMuc LIKE N'DM Pytest%'"
    )
    cur.execute(
        "DELETE FROM dbo.TaiKhoan WHERE Email LIKE 'pytest%@test.local' OR Email = 'pytest@caphe.local'"
    )


def xoa():
    with get_connection() as conn:
        xoa_cur(conn.cursor())
        conn.commit()
