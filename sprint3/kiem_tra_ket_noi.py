"""Kiem tra moi truong va ket noi, khong doc mat khau hay sua du lieu."""

from bootstrap import ensure_runtime

ensure_runtime(allow_reexec=__name__ == "__main__")

from config import settings  # noqa: E402
from database.connection import get_connection  # noqa: E402


def main():
    print(f"SQL Server: {settings.DB_SERVER}")
    print(f"Database: {settings.DB_NAME}")
    try:
        conn = get_connection()
        try:
            cur = conn.cursor()
            print("Ket noi:", cur.execute("SELECT DB_NAME(), @@SERVERNAME").fetchone())
            tables = {r[0] for r in cur.execute("SELECT name FROM sys.tables").fetchall()}
            required = {"TaiKhoan", "VaiTro", "Quyen", "VaiTroQuyen", "Mon", "DanhMuc",
                        "DonHang", "ChiTietDonHang", "ThanhToan", "HoanTien", "HoaDon",
                        "NguyenLieu", "LichSuKho", "CongThuc", "CongThucLichSu",
                        "NhaCungCap", "PhieuNhap", "ChiTietPhieuNhap"}
            missing = required - tables
            if missing:
                print("Thieu bang:", ", ".join(sorted(missing)))
                print("Xem README.md de nap schema con thieu; khong chay lai schema.sql tren du lieu dang dung.")
                return 1
            count = cur.execute("SELECT COUNT(*) FROM dbo.TaiKhoan").fetchval()
            print("So tai khoan:", count)
            if not count:
                print("Chua co tai khoan. Chay: py tao_tai_khoan.py")
            return 0
        finally:
            conn.close()
    except Exception as exc:
        print("Khong ket noi duoc:", exc)
        print("Kiem tra SQL Server dang chay va DB_SERVER / DB_NAME / DB_DRIVER trong .env.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
