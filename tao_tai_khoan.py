"""Tao tai khoan tu terminal (dung cho lan dau khi CSDL chua co tai khoan nao).

Chay:  py tao_tai_khoan.py
       py tao_tai_khoan.py --danh-sach      (xem cac tai khoan hien co)
"""

import argparse
import getpass
import os
import re
import sys

from bootstrap import ensure_runtime

ensure_runtime(allow_reexec=__name__ == "__main__")

from api.auth import service  # noqa: E402

# Terminal Windows mac dinh khong phai UTF-8 -> tieng Viet bi loi font.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")

EMAIL_HOP_LE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SDT_HOP_LE = re.compile(r"^[0-9+\s.-]{8,15}$")


def hoi(cau, bat_buoc=True, kiem_tra=None, loi=""):
    """Hoi lai cho toi khi nhap dung."""
    while True:
        gia_tri = input(cau).strip()
        if not gia_tri and not bat_buoc:
            return ""
        if not gia_tri:
            print("  -> Khong duoc de trong.")
            continue
        if kiem_tra and not kiem_tra(gia_tri):
            print(f"  -> {loi}")
            continue
        return gia_tri


def hoi_mat_khau():
    while True:
        mk = getpass.getpass("Mat khau (it nhat 6 ky tu, go se khong hien): ")
        if len(mk) < 6:
            print("  -> Mat khau can it nhat 6 ky tu.")
            continue
        if getpass.getpass("Nhap lai mat khau: ") != mk:
            print("  -> Hai lan nhap khong khop, nhap lai.")
            continue
        return mk


def chon_vi_tri(ds):
    print("\nVi tri cong viec:")
    for v in ds:
        print(f"  {v['VaiTroID']}. {v['TenVaiTro']}")
    ids = {str(v["VaiTroID"]) for v in ds}
    return int(hoi("Chon so: ", kiem_tra=lambda x: x in ids, loi="Chon mot so trong danh sach."))


def in_danh_sach():
    ds = service.danh_sach_tai_khoan()
    if not ds:
        print("Chua co tai khoan nao.")
        return
    for a in ds:
        tinh_trang = "dang lam" if a["TrangThai"] == "HOAT_DONG" else "tam ngung"
        print(f"  {a['Email']:<32} {a['HoTen']:<28} {a['TenVaiTro']:<16} {tinh_trang}")


def tao():
    vi_tri = service.danh_sach_vai_tro()
    if not vi_tri:
        print("CSDL chua co vi tri cong viec. Hay chay database\\seed.sql truoc.")
        return 1

    print("=== Tao tai khoan moi ===")
    if not service.danh_sach_tai_khoan():
        print("(CSDL chua co tai khoan nao - nen tao tai khoan Quan tri vien truoc.)")

    ho_ten = hoi("Ho va ten: ")
    email = hoi("Email: ", kiem_tra=EMAIL_HOP_LE.match, loi="Email chua dung dinh dang.").lower()
    sdt = hoi("So dien thoai (Enter de bo qua): ", bat_buoc=False,
              kiem_tra=SDT_HOP_LE.match, loi="So dien thoai chua hop le.")
    vai_tro_id = chon_vi_tri(vi_tri)
    mat_khau = hoi_mat_khau()

    tk, loi = service.tao_tai_khoan(ho_ten, email, mat_khau, vai_tro_id, sdt or None)
    if loi:
        print(f"\nKhong tao duoc: {loi}")
        return 1
    print(f"\nDa tao: {tk['HoTen']} <{tk['Email']}> - {tk['TenVaiTro']}")
    port = int(os.getenv("PORT", "5001"))
    print(f"Dang nhap tai http://localhost:{port}/login")
    return 0


def main():
    p = argparse.ArgumentParser(description="Tao tai khoan dang nhap cho quan ca phe.")
    p.add_argument("--danh-sach", action="store_true", help="Xem cac tai khoan hien co")
    args = p.parse_args()
    try:
        if args.danh_sach:
            in_danh_sach()
            return 0
        return tao()
    except KeyboardInterrupt:
        print("\nDa huy.")
        return 1
    except Exception as e:  # loi ket noi CSDL...
        print(f"\nLoi: {e}")
        print("Kiem tra SQL Server dang chay va file .env dung thong tin ket noi.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
