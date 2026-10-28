"""Du lieu rieng cho kiem thu: tu tao truoc khi chay, tu xoa sau khi xong.

CSDL that khong con du lieu mau, nen test khong duoc dua vao tai khoan/mon co san.
"""

from werkzeug.security import generate_password_hash

from database.connection import get_connection

ADMIN_EMAIL = "pytest-admin@test.local"
ADMIN_MK = "admin123"
NV_EMAIL = "pytest-nhanvien@test.local"
NV_MK = "nhanvien123"

# Duoc dien khi tao: id nhom mon dang co 1 mon (dung de thu "khong xoa duoc").
DANH_MUC_ID = None


def tao():
    global DANH_MUC_ID
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
        cur.execute(
            "INSERT INTO dbo.Mon (DanhMucID, TenMon, GiaBan, TrangThai, NgayTao) "
            "VALUES (?, N'Pytest Mon Co San', 10000, 1, SYSDATETIME())",
            (DANH_MUC_ID,),
        )
        conn.commit()


def xoa_cur(cur):
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
