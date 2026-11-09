"""Kiem thu Sprint 3 - module inventory (API 39-53): nguyen lieu, ton kho, cong thuc, tru kho.

Chay: py -3.12 -m pytest tests/test_sprint3_kho.py -q
Du lieu test deu bat dau bang "Pytest" de du_lieu_test.xoa_cur don dep.
"""

import datetime
import threading
import uuid
from decimal import Decimal

import pytest

from app import create_app
from database.connection import get_connection
from tests import du_lieu_test as dl

API = "/api/v1"
D = Decimal


# ---------- Ha tang test ----------
@pytest.fixture()
def client():
    app = create_app()
    app.config.update(TESTING=True)
    with app.test_client() as c:
        yield c


def _xoa_cong_thuc_mon_test():
    with get_connection() as conn:
        cur = conn.cursor()
        for mon_id in (dl.MON_ID, dl.MON2_ID, dl.MON_NGUNG_ID):
            cur.execute("DELETE FROM dbo.CongThucLichSu WHERE MonID = ?", (mon_id,))
            cur.execute("DELETE FROM dbo.CongThuc WHERE MonID = ?", (mon_id,))
        conn.commit()


@pytest.fixture(autouse=True)
def cong_thuc_sach():
    """Mon test dung chung giua cac test -> moi test bat dau/ket thuc voi cong thuc trong."""
    _xoa_cong_thuc_mon_test()
    yield
    _xoa_cong_thuc_mon_test()


def login(c, email=dl.ADMIN_EMAIL, password=dl.ADMIN_MK):
    r = c.post(f"{API}/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.get_json()
    return c


def admin():
    return login(create_app().test_client())


def staff():
    return login(create_app().test_client(), dl.NV_EMAIL, dl.NV_MK)


def ten(nhan="NL"):
    return f"Pytest {nhan} {uuid.uuid4().hex[:8]}"


def data(r):
    return r.get_json()["data"]


def msg(r):
    return r.get_json()["message"]


def tao_nl(c, ten_nl=None, don_vi="g", muc=0, ton=0):
    r = c.post(f"{API}/ingredients", json={
        "ten_nguyen_lieu": ten_nl or ten(), "don_vi_tinh": don_vi,
        "muc_ton_toi_thieu": muc, "so_luong_ton_ban_dau": ton})
    assert r.status_code == 201, r.get_json()
    return data(r)


def ton_db(nl_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT SoLuongTon FROM dbo.NguyenLieu WHERE NguyenLieuID = ?", (nl_id,))
        return D(cur.fetchval())


def so_cai(nl_id=None, don_hang_id=None, loai=None):
    where, params = "WHERE 1=1", []
    if nl_id is not None:
        where += " AND NguyenLieuID = ?"
        params.append(nl_id)
    if don_hang_id is not None:
        where += " AND DonHangID = ?"
        params.append(don_hang_id)
    if loai:
        where += " AND LoaiGiaoDich = ?"
        params.append(loai)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM dbo.LichSuKho {where} ORDER BY LichSuKhoID", params)
        cot = [c[0] for c in cur.description]
        return [dict(zip(cot, r)) for r in cur.fetchall()]


def kiem_so_cai(nl_id):
    """Moi bien dong phai co dong so cai noi tiep nhau: Truoc -> Sau, khong am, dong cuoi = ton hien tai."""
    truoc = D(0)
    for r in so_cai(nl_id):
        assert r["SoLuongTruoc"] == truoc, r
        assert r["SoLuongSau"] == r["SoLuongTruoc"] + r["SoLuongThayDoi"], r
        assert r["SoLuongSau"] >= 0, r
        truoc = r["SoLuongSau"]
    assert truoc == ton_db(nl_id)


def dat_cong_thuc(c, mon_id, items, ly_do=None):
    body = {"items": [{"nguyen_lieu_id": i, "so_luong_can": q} for i, q in items]}
    if ly_do:
        body["ly_do"] = ly_do
    r = c.put(f"{API}/recipes/{mon_id}", json=body)
    assert r.status_code == 200, r.get_json()
    return data(r)


def tao_don(c, items):
    r = c.post(f"{API}/orders", json={"items": items})
    assert r.status_code == 201, r.get_json()
    return data(r)


def don_pha_che(c, items=None, den="DANG_PHA_CHE"):
    don = tao_don(c, items or [{"mon_id": dl.MON_ID, "so_luong": 1}])
    buoc = ["CHO_PHA_CHE", "DANG_PHA_CHE", "HOAN_THANH"]
    for tt in buoc[: buoc.index(den) + 1]:
        r = c.patch(f"{API}/orders/{don['DonHangID']}/status", json={"trang_thai": tt})
        assert r.status_code == 200, r.get_json()
    return don


def tru_kho(c, don_hang_id):
    return c.post(f"{API}/inventory/consumptions", json={"don_hang_id": don_hang_id})


def song_song(viec):
    """Chay cac ham cung luc (barrier). Tra ve danh sach (status, json) theo thu tu."""
    barrier = threading.Barrier(len(viec))
    ket_qua = [None] * len(viec)

    def chay(i, ham):
        try:
            barrier.wait(timeout=30)
            r = ham()
            ket_qua[i] = (r.status_code, r.get_json())
        except Exception as e:  # noqa: BLE001 - dua loi thread ve luong chinh
            ket_qua[i] = e

    ts = [threading.Thread(target=chay, args=(i, h)) for i, h in enumerate(viec)]
    for t in ts:
        t.start()
    for t in ts:
        t.join(timeout=60)
    for kq in ket_qua:
        assert not isinstance(kq, Exception), kq
        assert kq is not None, "thread khong ket thuc"
    return ket_qua


# ---------- API 40: them nguyen lieu ----------
def test_tao_nguyen_lieu_va_ton_ban_dau_qua_so_cai(client):
    login(client)
    nl_ten = ten("Ca phe")
    r = client.post(f"{API}/ingredients", json={
        "ten_nguyen_lieu": f"  {nl_ten}  ", "don_vi_tinh": " g ",
        "muc_ton_toi_thieu": 100, "so_luong_ton_ban_dau": 12.345,
        "so_luong_ton": 99999, "trang_thai": 0})  # truong la -> bo qua
    assert r.status_code == 201, r.get_json()
    nl = data(r)
    assert nl["TenNguyenLieu"] == nl_ten and nl["DonViTinh"] == "g"
    assert D(nl["SoLuongTon"]) == D("12.345") and D(nl["MucTonToiThieu"]) == 100
    assert nl["TrangThai"] is True and nl["TinhTrangKho"] == "SAP_HET"
    assert nl["SoMonDungNguyenLieu"] == 0

    # QD06: ton ban dau di qua so cai bang DIEU_CHINH + ly do
    rows = so_cai(nl["NguyenLieuID"])
    assert len(rows) == 1
    assert rows[0]["LoaiGiaoDich"] == "DIEU_CHINH" and rows[0]["LyDo"] == "Ton kho ban dau"
    assert rows[0]["SoLuongTruoc"] == 0 and rows[0]["SoLuongSau"] == D("12.345")
    kiem_so_cai(nl["NguyenLieuID"])


def test_tao_nguyen_lieu_mac_dinh_ton_0_khong_ghi_so_cai(client):
    login(client)
    nl = data(client.post(f"{API}/ingredients", json={"ten_nguyen_lieu": ten(), "don_vi_tinh": "ml"}))
    assert D(nl["SoLuongTon"]) == 0 and D(nl["MucTonToiThieu"]) == 0
    assert nl["TinhTrangKho"] == "HET"
    assert so_cai(nl["NguyenLieuID"]) == []


@pytest.mark.parametrize("body", [
    {},
    {"don_vi_tinh": "g"},                                              # thieu ten
    {"ten_nguyen_lieu": "Pytest thieu don vi"},                        # thieu don vi
    {"ten_nguyen_lieu": "   ", "don_vi_tinh": "g"},
    {"ten_nguyen_lieu": 123, "don_vi_tinh": "g"},
    {"ten_nguyen_lieu": "Pytest sai", "don_vi_tinh": ""},
    {"ten_nguyen_lieu": "Pytest sai", "don_vi_tinh": ["g"]},
    {"ten_nguyen_lieu": "Pytest sai", "don_vi_tinh": "g", "muc_ton_toi_thieu": -1},
    {"ten_nguyen_lieu": "Pytest sai", "don_vi_tinh": "g", "muc_ton_toi_thieu": "abc"},
    {"ten_nguyen_lieu": "Pytest sai", "don_vi_tinh": "g", "muc_ton_toi_thieu": "NaN"},
    {"ten_nguyen_lieu": "Pytest sai", "don_vi_tinh": "g", "muc_ton_toi_thieu": "Infinity"},
    {"ten_nguyen_lieu": "Pytest sai", "don_vi_tinh": "g", "muc_ton_toi_thieu": True},
    {"ten_nguyen_lieu": "Pytest sai", "don_vi_tinh": "g", "muc_ton_toi_thieu": ""},
    {"ten_nguyen_lieu": "Pytest sai", "don_vi_tinh": "g", "so_luong_ton_ban_dau": -5},
    {"ten_nguyen_lieu": "Pytest sai", "don_vi_tinh": "g", "so_luong_ton_ban_dau": "abc"},
    {"ten_nguyen_lieu": "Pytest sai", "don_vi_tinh": "g", "so_luong_ton_ban_dau": "NaN"},
    {"ten_nguyen_lieu": "Pytest sai", "don_vi_tinh": "g", "so_luong_ton_ban_dau": "-Infinity"},
    {"ten_nguyen_lieu": "Pytest sai", "don_vi_tinh": "g", "so_luong_ton_ban_dau": False},
    {"ten_nguyen_lieu": "Pytest sai", "don_vi_tinh": "g", "so_luong_ton_ban_dau": [1]},
    {"ten_nguyen_lieu": "Pytest sai", "don_vi_tinh": "g", "so_luong_ton_ban_dau": 1e12},
    {"ten_nguyen_lieu": "Pytest sai", "don_vi_tinh": "g", "so_luong_ton_ban_dau": "9" * 400},
])
def test_tao_nguyen_lieu_du_lieu_sai(client, body):
    login(client)
    r = client.post(f"{API}/ingredients", json=body)
    assert r.status_code == 400, r.get_json()
    assert r.get_json()["success"] is False
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM dbo.NguyenLieu WHERE TenNguyenLieu IN (N'Pytest sai', N'Pytest thieu don vi')")
        assert cur.fetchval() == 0


def test_tao_nguyen_lieu_nan_json_that_su(client):
    login(client)
    r = client.post(f"{API}/ingredients", content_type="application/json",
                    data='{"ten_nguyen_lieu": "Pytest NaN json", "don_vi_tinh": "g", "so_luong_ton_ban_dau": NaN}')
    assert r.status_code == 400, r.get_json()


def test_tao_nguyen_lieu_than_json_khong_hop_le(client):
    login(client)
    assert client.post(f"{API}/ingredients", json=[1, 2]).status_code == 400
    assert client.post(f"{API}/ingredients", data="khong phai json", content_type="application/json").status_code == 400
    assert client.post(f"{API}/ingredients").status_code == 400


def test_ten_va_don_vi_qua_dai_bi_cat_theo_cot(client):
    login(client)
    nl = tao_nl(client, ten_nl=f"Pytest {uuid.uuid4().hex[:8]} " + "A" * 300, don_vi="d" * 50)
    assert len(nl["TenNguyenLieu"]) == 150 and len(nl["DonViTinh"]) == 30


def test_nguyen_lieu_trung_ten_khong_phan_biet_hoa_thuong(client):
    login(client)
    nl = tao_nl(client, ten_nl=ten("Sua tuoi"))
    for biến_the in (nl["TenNguyenLieu"], nl["TenNguyenLieu"].upper(), f"  {nl['TenNguyenLieu'].lower()}  "):
        r = client.post(f"{API}/ingredients", json={"ten_nguyen_lieu": biến_the, "don_vi_tinh": "ml"})
        assert r.status_code == 409, r.get_json()
        assert msg(r) == "Ten nguyen lieu da ton tai"


def test_ten_tieng_viet_co_dau_va_chuoi_nguy_hiem_luu_nguyen_ban(client):
    login(client)
    tag = uuid.uuid4().hex[:8]
    ten_viet = f"Pytest Sữa tươi đặc {tag}"
    ten_xau = f"Pytest x'; DROP TABLE dbo.NguyenLieu;-- {tag}"
    a, b = tao_nl(client, ten_nl=ten_viet), tao_nl(client, ten_nl=ten_xau)
    assert a["TenNguyenLieu"] == ten_viet and b["TenNguyenLieu"] == ten_xau
    r = client.get(f"{API}/ingredients", query_string={"q": f"Sữa tươi đặc {tag}"})
    assert [i["NguyenLieuID"] for i in data(r)["items"]] == [a["NguyenLieuID"]]
    r = client.get(f"{API}/ingredients", query_string={"q": "x'; DROP"})
    assert r.status_code == 200 and data(r)["total"] >= 1


def test_tao_trung_ten_dong_thoi_chi_1_thanh_cong_khong_500():
    ten_chung = ten("Dong thoi")
    cs = [admin() for _ in range(4)]
    kq = song_song([
        (lambda c=c: c.post(f"{API}/ingredients", json={"ten_nguyen_lieu": ten_chung, "don_vi_tinh": "g"}))
        for c in cs
    ])
    codes = sorted(k[0] for k in kq)
    assert codes == [201, 409, 409, 409], kq
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM dbo.NguyenLieu WHERE TenNguyenLieu = ?", (ten_chung,))
        assert cur.fetchval() == 1


# ---------- API 39: danh sach nguyen lieu ----------
def test_danh_sach_nguyen_lieu_tim_loc_phan_trang(client):
    login(client)
    tag = uuid.uuid4().hex[:8]
    ids = [tao_nl(client, ten_nl=f"Pytest Ds{i} {tag}", ton=i * 10, muc=15)["NguyenLieuID"] for i in range(3)]
    r = client.get(f"{API}/ingredients", query_string={"q": tag})
    d = data(r)
    assert d["total"] == 3 and d["page"] == 1 and d["per_page"] == 20
    assert [i["NguyenLieuID"] for i in d["items"]] == ids          # xep theo ten
    assert [i["TinhTrangKho"] for i in d["items"]] == ["HET", "SAP_HET", "DU"]

    d = data(client.get(f"{API}/ingredients", query_string={"q": tag, "per_page": 2, "page": 2}))
    assert d["total"] == 3 and len(d["items"]) == 1 and d["page"] == 2 and d["per_page"] == 2

    # Ngung dung 1 cai -> loc theo status
    assert client.patch(f"{API}/ingredients/{ids[0]}/status", json={"dang_dung": False}).status_code == 200
    q = {"q": tag}
    assert data(client.get(f"{API}/ingredients", query_string=q))["total"] == 3
    assert data(client.get(f"{API}/ingredients", query_string={**q, "status": "active"}))["total"] == 2
    d = data(client.get(f"{API}/ingredients", query_string={**q, "status": "inactive"}))
    assert [i["NguyenLieuID"] for i in d["items"]] == [ids[0]]
    assert client.get(f"{API}/ingredients", query_string={"status": "xyz"}).status_code == 400


def test_tim_kiem_khong_hieu_nham_ky_tu_dac_biet_cua_like(client):
    login(client)
    tag = uuid.uuid4().hex[:8]
    a = tao_nl(client, ten_nl=f"Pytest a_b {tag}")
    tao_nl(client, ten_nl=f"Pytest axb {tag}")
    d = data(client.get(f"{API}/ingredients", query_string={"q": f"a_b {tag}"}))
    assert [i["NguyenLieuID"] for i in d["items"]] == [a["NguyenLieuID"]]
    assert data(client.get(f"{API}/ingredients", query_string={"q": f"%{tag}"}))["total"] == 0
    assert data(client.get(f"{API}/ingredients", query_string={"q": "[a-z]"}))["total"] == 0


def test_phan_trang_tham_so_rac_khong_gay_loi(client):
    login(client)
    d = data(client.get(f"{API}/ingredients", query_string={"per_page": 1000, "page": -5}))
    assert d["per_page"] == 100 and d["page"] == 1
    d = data(client.get(f"{API}/ingredients", query_string={"per_page": "abc", "page": "xyz"}))
    assert d["per_page"] == 20 and d["page"] == 1
    assert client.get(f"{API}/ingredients", query_string={"page": 10 ** 12}).status_code == 200


# ---------- API 41: chi tiet ----------
def test_chi_tiet_nguyen_lieu_dem_so_mon_dung(client):
    login(client)
    nl = tao_nl(client, ton=50, muc=10)
    d = data(client.get(f"{API}/ingredients/{nl['NguyenLieuID']}"))
    assert d["TinhTrangKho"] == "DU" and d["SoMonDungNguyenLieu"] == 0
    dat_cong_thuc(client, dl.MON_ID, [(nl["NguyenLieuID"], 5)])
    dat_cong_thuc(client, dl.MON2_ID, [(nl["NguyenLieuID"], 7)])
    d = data(client.get(f"{API}/ingredients/{nl['NguyenLieuID']}"))
    assert d["SoMonDungNguyenLieu"] == 2
    for bad in (999999, 2147483648, 10 ** 15):
        assert client.get(f"{API}/ingredients/{bad}").status_code == 404


# ---------- API 42: cap nhat ----------
def test_cap_nhat_nguyen_lieu_khong_doi_duoc_ton(client):
    login(client)
    nl = tao_nl(client, ton=100, muc=0)
    nl_id = nl["NguyenLieuID"]
    ten_moi = ten("Moi")
    r = client.put(f"{API}/ingredients/{nl_id}", json={
        "ten_nguyen_lieu": ten_moi, "muc_ton_toi_thieu": "100", "so_luong_ton": 5, "SoLuongTon": 5})
    assert r.status_code == 200, r.get_json()
    d = data(r)
    assert d["TenNguyenLieu"] == ten_moi and D(d["MucTonToiThieu"]) == 100
    assert D(d["SoLuongTon"]) == 100 and d["TinhTrangKho"] == "SAP_HET"      # ton khong doi, trang thai tinh lai
    assert d["NgayCapNhat"]
    assert ton_db(nl_id) == 100 and len(so_cai(nl_id)) == 1

    # Chi gui truong ton -> khong co gi hop le de cap nhat
    for body in ({}, {"so_luong_ton": 5}, {"TrangThai": 0}):
        r = client.put(f"{API}/ingredients/{nl_id}", json=body)
        assert r.status_code == 400 and msg(r) == "Khong co gi de cap nhat", body
    assert ton_db(nl_id) == 100

    d = data(client.put(f"{API}/ingredients/{nl_id}", json={"muc_ton_toi_thieu": 5}))
    assert d["TinhTrangKho"] == "DU"


@pytest.mark.parametrize("body", [
    {"ten_nguyen_lieu": ""}, {"ten_nguyen_lieu": "   "}, {"ten_nguyen_lieu": None}, {"ten_nguyen_lieu": 5},
    {"don_vi_tinh": " "}, {"don_vi_tinh": None},
    {"muc_ton_toi_thieu": -1}, {"muc_ton_toi_thieu": "abc"}, {"muc_ton_toi_thieu": "NaN"},
    {"muc_ton_toi_thieu": None}, {"muc_ton_toi_thieu": True}, {"muc_ton_toi_thieu": 1e12},
])
def test_cap_nhat_nguyen_lieu_du_lieu_sai(client, body):
    login(client)
    nl = tao_nl(client, ton=10, muc=3)
    r = client.put(f"{API}/ingredients/{nl['NguyenLieuID']}", json=body)
    assert r.status_code == 400, r.get_json()
    d = data(client.get(f"{API}/ingredients/{nl['NguyenLieuID']}"))
    assert d["TenNguyenLieu"] == nl["TenNguyenLieu"] and D(d["MucTonToiThieu"]) == 3


def test_cap_nhat_nguyen_lieu_trung_ten_va_404(client):
    login(client)
    a, b = tao_nl(client), tao_nl(client)
    r = client.put(f"{API}/ingredients/{b['NguyenLieuID']}", json={"ten_nguyen_lieu": a["TenNguyenLieu"].upper()})
    assert r.status_code == 409 and msg(r) == "Ten nguyen lieu da ton tai"
    # Doi hoa/thuong ten cua chinh no thi duoc
    r = client.put(f"{API}/ingredients/{a['NguyenLieuID']}", json={"ten_nguyen_lieu": a["TenNguyenLieu"].upper()})
    assert r.status_code == 200
    assert client.put(f"{API}/ingredients/999999", json={"ten_nguyen_lieu": ten()}).status_code == 404
    assert client.put(f"{API}/ingredients/2147483648", json={"ten_nguyen_lieu": ten()}).status_code == 404


def test_khong_doi_don_vi_khi_da_co_lich_su_hoac_nam_trong_cong_thuc(client):
    login(client)
    # Moi tao, chua phat sinh gi -> doi duoc
    sach = tao_nl(client, don_vi="g", ton=0)
    r = client.put(f"{API}/ingredients/{sach['NguyenLieuID']}", json={"don_vi_tinh": "kg"})
    assert r.status_code == 200 and data(r)["DonViTinh"] == "kg"

    # Da co lich su kho
    co_ls = tao_nl(client, don_vi="g", ton=100)
    r = client.put(f"{API}/ingredients/{co_ls['NguyenLieuID']}", json={"don_vi_tinh": "kg"})
    assert r.status_code == 409, r.get_json()
    assert data(client.get(f"{API}/ingredients/{co_ls['NguyenLieuID']}"))["DonViTinh"] == "g"
    # Gui lai dung don vi cu thi khong phai doi -> van cap nhat ten duoc
    r = client.put(f"{API}/ingredients/{co_ls['NguyenLieuID']}", json={"don_vi_tinh": "g", "ten_nguyen_lieu": ten()})
    assert r.status_code == 200

    # Nam trong cong thuc (ton 0, chua co lich su)
    trong_ct = tao_nl(client, don_vi="g", ton=0)
    dat_cong_thuc(client, dl.MON_ID, [(trong_ct["NguyenLieuID"], 3)])
    r = client.put(f"{API}/ingredients/{trong_ct['NguyenLieuID']}", json={"don_vi_tinh": "ml"})
    assert r.status_code == 409
    # Doi ten van duoc
    assert client.put(f"{API}/ingredients/{trong_ct['NguyenLieuID']}", json={"ten_nguyen_lieu": ten()}).status_code == 200


# ---------- API 43: bat/ngung su dung ----------
def test_ngung_dung_khong_xoa_du_lieu(client):
    login(client)
    nl = tao_nl(client, ton=40)
    nl_id = nl["NguyenLieuID"]
    url = f"{API}/ingredients/{nl_id}/status"
    for body in ({}, {"dang_dung": None}, {"trang_thai": False}, {"dang_dung": "abc"}, {"dang_dung": "false"}, {"dang_dung": 0}):
        assert client.patch(url, json=body).status_code == 400, body
    assert data(client.get(f"{API}/ingredients/{nl_id}"))["TrangThai"] is True

    r = client.patch(url, json={"dang_dung": False})
    assert r.status_code == 200 and data(r)["TrangThai"] is False
    d = data(client.get(f"{API}/ingredients/{nl_id}"))
    assert D(d["SoLuongTon"]) == 40 and len(so_cai(nl_id)) == 1     # du lieu con nguyen
    r = client.patch(url, json={"dang_dung": True})
    assert data(r)["TrangThai"] is True
    assert client.patch(f"{API}/ingredients/999999/status", json={"dang_dung": False}).status_code == 404


# ---------- API 44, 45: ton kho, sap het ----------
def test_danh_sach_ton_kho_loc_tinh_trang_va_trang_thai(client):
    login(client)
    tag = uuid.uuid4().hex[:8]
    het = tao_nl(client, ten_nl=f"Pytest Het {tag}", muc=5, ton=0)
    bien = tao_nl(client, ten_nl=f"Pytest Bien {tag}", muc=5, ton=5)        # = muc -> SAP_HET
    du = tao_nl(client, ten_nl=f"Pytest Du {tag}", muc=5, ton=5.001)
    khong_muc = tao_nl(client, ten_nl=f"Pytest KhongMuc {tag}", muc=0, ton=0)  # ton 0 -> HET du muc 0
    assert (het["TinhTrangKho"], bien["TinhTrangKho"], du["TinhTrangKho"], khong_muc["TinhTrangKho"]) == \
        ("HET", "SAP_HET", "DU", "HET")

    def ids(**q):
        d = data(client.get(f"{API}/inventory", query_string={"q": tag, "per_page": 100, **q}))
        return {i["NguyenLieuID"] for i in d["items"]}

    assert ids() == {het["NguyenLieuID"], bien["NguyenLieuID"], du["NguyenLieuID"], khong_muc["NguyenLieuID"]}
    assert ids(tinh_trang="HET") == {het["NguyenLieuID"], khong_muc["NguyenLieuID"]}
    assert ids(tinh_trang="SAP_HET") == {bien["NguyenLieuID"]}
    assert ids(tinh_trang="du") == {du["NguyenLieuID"]}
    assert client.get(f"{API}/inventory", query_string={"tinh_trang": "XYZ"}).status_code == 400
    assert client.get(f"{API}/inventory", query_string={"status": "xyz"}).status_code == 400

    # Mac dinh chi nguyen lieu dang dung
    client.patch(f"{API}/ingredients/{du['NguyenLieuID']}/status", json={"dang_dung": False})
    assert du["NguyenLieuID"] not in ids()
    assert du["NguyenLieuID"] in ids(status="all")
    assert ids(status="inactive") == {du["NguyenLieuID"]}
    d = data(client.get(f"{API}/inventory", query_string={"q": tag}))
    assert {"items", "total", "page", "per_page"} <= set(d)
    assert all("TinhTrangKho" in i for i in d["items"])


def test_low_stock_dung_thu_tu_va_can_nhap_them(client):
    login(client)
    c_het = tao_nl(client, muc=100, ton=0)       # het, can 100
    d_het = tao_nl(client, muc=20, ton=0)        # het, can 20
    a = tao_nl(client, muc=100, ton=10)          # 10% -> can 90
    b = tao_nl(client, muc=100, ton=50)          # 50% -> can 50
    e = tao_nl(client, muc=10, ton=10)           # bang muc -> can 0
    du = tao_nl(client, muc=10, ton=10.5)        # du -> khong co mat
    ngung = tao_nl(client, muc=10, ton=0)        # het nhung ngung dung -> khong co mat
    client.patch(f"{API}/ingredients/{ngung['NguyenLieuID']}/status", json={"dang_dung": False})

    r = client.get(f"{API}/inventory/low-stock")
    assert r.status_code == 200
    lst = data(r)
    assert isinstance(lst, list)                                    # khong phan trang
    mine = {x["NguyenLieuID"]: x for x in lst}
    assert du["NguyenLieuID"] not in mine and ngung["NguyenLieuID"] not in mine
    thu_tu = [x["NguyenLieuID"] for x in lst if x["NguyenLieuID"] in
              {c_het["NguyenLieuID"], d_het["NguyenLieuID"], a["NguyenLieuID"], b["NguyenLieuID"], e["NguyenLieuID"]}]
    assert thu_tu == [c_het["NguyenLieuID"], d_het["NguyenLieuID"], a["NguyenLieuID"],
                      b["NguyenLieuID"], e["NguyenLieuID"]]
    assert [D(mine[x["NguyenLieuID"]]["CanNhapThem"]) for x in (c_het, d_het, a, b, e)] == [100, 20, 90, 50, 0]
    assert all(D(x["CanNhapThem"]) >= 0 and x["TinhTrangKho"] in ("HET", "SAP_HET") and x["TrangThai"] for x in lst)
    # Moi HET dung truoc moi SAP_HET
    tt = [x["TinhTrangKho"] for x in lst]
    assert tt == sorted(tt, key=lambda v: 0 if v == "HET" else 1)

    # Nhap them -> roi khoi danh sach
    client.post(f"{API}/inventory/adjustments", json={"nguyen_lieu_id": a["NguyenLieuID"], "so_luong_thuc_te": 500, "ly_do": "Kiem ke"})
    assert a["NguyenLieuID"] not in {x["NguyenLieuID"] for x in data(client.get(f"{API}/inventory/low-stock"))}


# ---------- API 47: kiem ke ----------
def test_kiem_ke_dieu_chinh_tang_giam_ve_0(client):
    login(client)
    nl = tao_nl(client, ton=100)
    nl_id = nl["NguyenLieuID"]
    url = f"{API}/inventory/adjustments"

    r = client.post(url, json={"nguyen_lieu_id": nl_id, "so_luong_thuc_te": "80.5", "ly_do": "  Kiem ke cuoi thang  "})
    assert r.status_code == 201, r.get_json()
    d = data(r)
    ls = d["LichSuKho"]
    assert ls["LoaiGiaoDich"] == "DIEU_CHINH" and D(ls["SoLuongThayDoi"]) == D("-19.5")
    assert D(ls["SoLuongTruoc"]) == 100 and D(ls["SoLuongSau"]) == D("80.5") and ls["LyDo"] == "Kiem ke cuoi thang"
    assert D(d["NguyenLieu"]["SoLuongTon"]) == D("80.5") and ton_db(nl_id) == D("80.5")

    d = data(client.post(url, json={"nguyen_lieu_id": nl_id, "so_luong_thuc_te": 130, "ly_do": "Dem lai"}))
    assert D(d["LichSuKho"]["SoLuongThayDoi"]) == D("49.5")

    d = data(client.post(url, json={"nguyen_lieu_id": nl_id, "so_luong_thuc_te": 0, "ly_do": "Hong het"}))
    assert D(d["NguyenLieu"]["SoLuongTon"]) == 0 and d["NguyenLieu"]["TinhTrangKho"] == "HET"

    # Chenh lech 0 -> 400, khong ghi them dong
    truoc = len(so_cai(nl_id))
    r = client.post(url, json={"nguyen_lieu_id": nl_id, "so_luong_thuc_te": 0, "ly_do": "Y nhu cu"})
    assert r.status_code == 400 and msg(r) == "Ton kho khong thay doi"
    assert len(so_cai(nl_id)) == truoc
    kiem_so_cai(nl_id)


def test_kiem_ke_ly_do_dai_bi_cat(client):
    login(client)
    nl = tao_nl(client, ton=1)
    d = data(client.post(f"{API}/inventory/adjustments", json={
        "nguyen_lieu_id": nl["NguyenLieuID"], "so_luong_thuc_te": 2, "ly_do": "x" * 600}))
    assert len(d["LichSuKho"]["LyDo"]) == 500


@pytest.mark.parametrize("sua, ma", [
    ({"so_luong_thuc_te": -1}, 400), ({"so_luong_thuc_te": "abc"}, 400), ({"so_luong_thuc_te": "NaN"}, 400),
    ({"so_luong_thuc_te": "Infinity"}, 400), ({"so_luong_thuc_te": True}, 400), ({"so_luong_thuc_te": None}, 400),
    ({"so_luong_thuc_te": 1e12}, 400), ({"so_luong_thuc_te": ""}, 400),
    ({"ly_do": ""}, 400), ({"ly_do": "   "}, 400), ({"ly_do": None}, 400), ({"ly_do": 123}, 400),
    ({"nguyen_lieu_id": None}, 400), ({"nguyen_lieu_id": "abc"}, 400), ({"nguyen_lieu_id": 0}, 400),
    ({"nguyen_lieu_id": -3}, 400), ({"nguyen_lieu_id": True}, 400), ({"nguyen_lieu_id": 1.5}, 400),
    ({"nguyen_lieu_id": 999999}, 404),
])
def test_kiem_ke_du_lieu_sai(client, sua, ma):
    login(client)
    nl = tao_nl(client, ton=100)
    body = {"nguyen_lieu_id": nl["NguyenLieuID"], "so_luong_thuc_te": 50, "ly_do": "Kiem ke"}
    body.update(sua)
    r = client.post(f"{API}/inventory/adjustments", json=body)
    assert r.status_code == ma, r.get_json()
    assert ton_db(nl["NguyenLieuID"]) == 100 and len(so_cai(nl["NguyenLieuID"])) == 1


# ---------- API 48: xuat kho ----------
def test_xuat_kho_vuot_ton_va_ton_khong_am(client):
    login(client)
    nl = tao_nl(client, ton=100)
    nl_id = nl["NguyenLieuID"]
    url = f"{API}/inventory/issues"

    r = client.post(url, json={"nguyen_lieu_id": nl_id, "so_luong": "30.25", "ly_do": "Do vo"})
    assert r.status_code == 201, r.get_json()
    ls = data(r)["LichSuKho"]
    assert ls["LoaiGiaoDich"] == "XUAT_KHO" and D(ls["SoLuongThayDoi"]) == D("-30.25")
    assert D(ls["SoLuongTruoc"]) == 100 and D(ls["SoLuongSau"]) == D("69.75") and ls["LyDo"] == "Do vo"
    assert D(data(r)["NguyenLieu"]["SoLuongTon"]) == D("69.75")

    # Vuot ton 0.001 -> 409, khong doi gi
    truoc = len(so_cai(nl_id))
    r = client.post(url, json={"nguyen_lieu_id": nl_id, "so_luong": "69.751", "ly_do": "Qua tay"})
    assert r.status_code == 409 and "Ton kho khong du" in msg(r)
    assert ton_db(nl_id) == D("69.75") and len(so_cai(nl_id)) == truoc

    # Xuat dung bang ton -> ve 0, khong am
    r = client.post(url, json={"nguyen_lieu_id": nl_id, "so_luong": "69.75", "ly_do": "Het"})
    assert r.status_code == 201 and data(r)["NguyenLieu"]["TinhTrangKho"] == "HET"
    assert client.post(url, json={"nguyen_lieu_id": nl_id, "so_luong": "0.001", "ly_do": "x"}).status_code == 409
    assert ton_db(nl_id) == 0
    kiem_so_cai(nl_id)


@pytest.mark.parametrize("sua, ma", [
    ({"so_luong": 0}, 400), ({"so_luong": -5}, 400), ({"so_luong": "abc"}, 400), ({"so_luong": "NaN"}, 400),
    ({"so_luong": "Infinity"}, 400), ({"so_luong": True}, 400), ({"so_luong": None}, 400), ({"so_luong": ""}, 400),
    ({"so_luong": "0.0004"}, 400), ({"so_luong": 1e12}, 400), ({"so_luong": [5]}, 400),
    ({"ly_do": ""}, 400), ({"ly_do": "  "}, 400), ({"ly_do": None}, 400),
    ({"nguyen_lieu_id": None}, 400), ({"nguyen_lieu_id": "x"}, 400), ({"nguyen_lieu_id": 999999}, 404),
])
def test_xuat_kho_du_lieu_sai(client, sua, ma):
    login(client)
    nl = tao_nl(client, ton=100)
    body = {"nguyen_lieu_id": nl["NguyenLieuID"], "so_luong": 10, "ly_do": "Hao hut"}
    body.update(sua)
    r = client.post(f"{API}/inventory/issues", json=body)
    assert r.status_code == ma, r.get_json()
    assert ton_db(nl["NguyenLieuID"]) == 100 and len(so_cai(nl["NguyenLieuID"])) == 1


def test_xuat_kho_dong_thoi_khong_bao_gio_am():
    nl = tao_nl(admin(), ton=100)
    cs = [admin() for _ in range(6)]
    kq = song_song([
        (lambda c=c: c.post(f"{API}/inventory/issues", json={
            "nguyen_lieu_id": nl["NguyenLieuID"], "so_luong": 30, "ly_do": "Dong thoi"}))
        for c in cs
    ])
    codes = sorted(k[0] for k in kq)
    assert codes == [201, 201, 201, 409, 409, 409], kq
    assert ton_db(nl["NguyenLieuID"]) == 10
    assert len(so_cai(nl["NguyenLieuID"], loai="XUAT_KHO")) == 3
    kiem_so_cai(nl["NguyenLieuID"])


# ---------- API 46: lich su giao dich kho ----------
def test_lich_su_kho_loc_phan_trang_moi_nhat_truoc(client):
    login(client)
    nl = tao_nl(client, ton=100, don_vi="kg")
    nl_id = nl["NguyenLieuID"]
    client.post(f"{API}/inventory/issues", json={"nguyen_lieu_id": nl_id, "so_luong": 10, "ly_do": "Hu"})
    client.post(f"{API}/inventory/adjustments", json={"nguyen_lieu_id": nl_id, "so_luong_thuc_te": 50, "ly_do": "Kiem ke"})
    url = f"{API}/inventory/transactions"

    d = data(client.get(url, query_string={"nguyen_lieu_id": nl_id}))
    assert d["total"] == 3 and d["page"] == 1
    assert [i["LoaiGiaoDich"] for i in d["items"]] == ["DIEU_CHINH", "XUAT_KHO", "DIEU_CHINH"]
    assert [D(i["SoLuongThayDoi"]) for i in d["items"]] == [-40, -10, 100]
    top = d["items"][0]
    assert top["TenNguyenLieu"] == nl["TenNguyenLieu"] and top["DonViTinh"] == "kg"
    assert top["NguoiThucHien"] == "Pytest Quan Tri" and top["MaDonHang"] is None and top["MaPhieuNhap"] is None
    assert D(top["SoLuongTruoc"]) == 90 and D(top["SoLuongSau"]) == 50

    d = data(client.get(url, query_string={"nguyen_lieu_id": nl_id, "loai": "xuat_kho"}))
    assert d["total"] == 1 and d["items"][0]["LyDo"] == "Hu"
    d = data(client.get(url, query_string={"nguyen_lieu_id": nl_id, "per_page": 2, "page": 2}))
    assert d["total"] == 3 and len(d["items"]) == 1

    homnay = datetime.date.today()
    chuoi = lambda ngay: ngay.isoformat()  # noqa: E731
    q = {"nguyen_lieu_id": nl_id}
    assert data(client.get(url, query_string={**q, "tu_ngay": chuoi(homnay), "den_ngay": chuoi(homnay)}))["total"] == 3
    assert data(client.get(url, query_string={**q, "den_ngay": chuoi(homnay + datetime.timedelta(days=1))}))["total"] == 3
    assert data(client.get(url, query_string={**q, "tu_ngay": chuoi(homnay + datetime.timedelta(days=2))}))["total"] == 0
    assert data(client.get(url, query_string={**q, "den_ngay": chuoi(homnay - datetime.timedelta(days=1))}))["total"] == 0


@pytest.mark.parametrize("q", [
    {"tu_ngay": "abc"}, {"den_ngay": "2025-13-45"}, {"tu_ngay": "2025/01/01"}, {"den_ngay": "01-01-2025"},
    {"tu_ngay": "2025-02-30"}, {"tu_ngay": "9999-12-31", "den_ngay": "9999-12-31"},
])
def test_lich_su_kho_ngay_sai(client, q):
    login(client)
    r = client.get(f"{API}/inventory/transactions", query_string=q)
    assert r.status_code == 400, r.get_json()
    assert msg(r) == "Ngay khong hop le"


def test_lich_su_kho_tham_so_sai_khac(client):
    login(client)
    url = f"{API}/inventory/transactions"
    assert client.get(url, query_string={"loai": "XYZ"}).status_code == 400
    assert client.get(url, query_string={"nguyen_lieu_id": "abc"}).status_code == 400
    assert client.get(url, query_string={"nguyen_lieu_id": "-1"}).status_code == 400
    assert client.get(url, query_string={"tu_ngay": "2025-05-02", "den_ngay": "2025-05-01"}).status_code == 400
    assert client.get(url, query_string={"nguyen_lieu_id": "999999"}).status_code == 200


# ---------- API 49: ton kho 1 nguyen lieu ----------
def test_ton_kho_mot_nguyen_lieu_20_giao_dich_gan_nhat(client):
    login(client)
    nl = tao_nl(client, ton=100, muc=10)
    nl_id = nl["NguyenLieuID"]
    for i in range(22):
        assert client.post(f"{API}/inventory/issues", json={"nguyen_lieu_id": nl_id, "so_luong": 1, "ly_do": f"Lan {i}"}).status_code == 201
    r = client.get(f"{API}/inventory/ingredients/{nl_id}")
    assert r.status_code == 200
    d = data(r)
    assert d["TenNguyenLieu"] == nl["TenNguyenLieu"] and D(d["SoLuongTon"]) == 78 and d["TinhTrangKho"] == "DU"
    gd = d["GiaoDichGanNhat"]
    assert len(gd) == 20
    assert gd[0]["LyDo"] == "Lan 21" and gd[-1]["LyDo"] == "Lan 2"        # moi nhat truoc, bo 2 dong cu nhat
    assert [g["LichSuKhoID"] for g in gd] == sorted((g["LichSuKhoID"] for g in gd), reverse=True)
    assert D(gd[0]["SoLuongSau"]) == 78 and gd[0]["NguoiThucHien"] == "Pytest Quan Tri"
    assert client.get(f"{API}/inventory/ingredients/999999").status_code == 404
    kiem_so_cai(nl_id)


# ---------- API 50-52: cong thuc ----------
def test_xem_cong_thuc_mon_chua_co_va_mon_khong_ton_tai(client):
    login(client)
    r = client.get(f"{API}/recipes/{dl.MON_ID}")
    assert r.status_code == 200
    d = data(r)
    assert d["MonID"] == dl.MON_ID and d["TenMon"] == "Pytest Mon Co San" and D(d["GiaBan"]) == 10000
    assert d["items"] == [] and d["SoPhanLamDuoc"] is None
    assert client.get(f"{API}/recipes/999999").status_code == 404
    assert client.get(f"{API}/recipes/999999/history").status_code == 404
    assert client.put(f"{API}/recipes/999999", json={"items": []}).status_code == 404
    d = data(client.get(f"{API}/recipes/{dl.MON_ID}/history"))
    assert d["items"] == [] and d["total"] == 0


def test_luu_cong_thuc_thay_the_va_lich_su_truoc_sau(client):
    login(client)
    a = tao_nl(client, ton=1000, don_vi="g")
    b = tao_nl(client, ton=10, don_vi="ml")
    c = tao_nl(client, ton=50, don_vi="g")
    mon = dl.MON_ID

    # Tao moi: 2 dong -> SoPhanLamDuoc = min(floor(1000/18), floor(10/3)) = 3
    d = dat_cong_thuc(client, mon, [(b["NguyenLieuID"], "3"), (a["NguyenLieuID"], 18)], ly_do="Cong thuc dau")
    assert [i["NguyenLieuID"] for i in d["items"]] == sorted([a["NguyenLieuID"], b["NguyenLieuID"]])
    ia = next(i for i in d["items"] if i["NguyenLieuID"] == a["NguyenLieuID"])
    assert set(ia) >= {"NguyenLieuID", "TenNguyenLieu", "DonViTinh", "SoLuongCan", "SoLuongTon", "NguyenLieuDangDung"}
    assert ia["DonViTinh"] == "g" and D(ia["SoLuongCan"]) == 18 and D(ia["SoLuongTon"]) == 1000 and ia["NguyenLieuDangDung"] is True
    assert d["SoPhanLamDuoc"] == 3 and d["MonID"] == mon and d["TenMon"] == "Pytest Mon Co San"
    assert data(client.get(f"{API}/recipes/{mon}"))["SoPhanLamDuoc"] == 3

    lich_su = data(client.get(f"{API}/recipes/{mon}/history"))
    assert lich_su["total"] == 1
    h1 = lich_su["items"][0]
    assert set(h1) >= {"CongThucLichSuID", "NgayThayDoi", "NguoiThayDoi", "LyDo", "Truoc", "Sau"}
    assert h1["NguoiThayDoi"] == "Pytest Quan Tri" and h1["LyDo"] == "Cong thuc dau"
    assert h1["Truoc"] == [] and len(h1["Sau"]) == 2
    s_a = next(x for x in h1["Sau"] if x["NguyenLieuID"] == a["NguyenLieuID"])
    assert set(s_a) == {"NguyenLieuID", "TenNguyenLieu", "DonViTinh", "SoLuongCan"}
    assert s_a["TenNguyenLieu"] == a["TenNguyenLieu"] and D(s_a["SoLuongCan"]) == 18

    # Thay the: bo b, doi a thanh 20, them c
    d = dat_cong_thuc(client, mon, [(a["NguyenLieuID"], 20), (c["NguyenLieuID"], 5)])
    assert {i["NguyenLieuID"] for i in d["items"]} == {a["NguyenLieuID"], c["NguyenLieuID"]}
    assert d["SoPhanLamDuoc"] == min(1000 // 20, 50 // 5)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM dbo.CongThuc WHERE MonID = ?", (mon,))
        assert cur.fetchval() == 2
    lich_su = data(client.get(f"{API}/recipes/{mon}/history"))
    assert lich_su["total"] == 2
    moi_nhat = lich_su["items"][0]                                    # moi nhat truoc
    assert {x["NguyenLieuID"]: D(x["SoLuongCan"]) for x in moi_nhat["Truoc"]} == {a["NguyenLieuID"]: 18, b["NguyenLieuID"]: 3}
    assert {x["NguyenLieuID"]: D(x["SoLuongCan"]) for x in moi_nhat["Sau"]} == {a["NguyenLieuID"]: 20, c["NguyenLieuID"]: 5}
    assert lich_su["items"][1]["CongThucLichSuID"] == h1["CongThucLichSuID"]
    p = data(client.get(f"{API}/recipes/{mon}/history", query_string={"per_page": 1, "page": 2}))
    assert p["total"] == 2 and [x["CongThucLichSuID"] for x in p["items"]] == [h1["CongThucLichSuID"]]

    # Cong thuc cua mon khac khong bi anh huong
    assert data(client.get(f"{API}/recipes/{dl.MON2_ID}"))["items"] == []


def test_luu_cong_thuc_khong_doi_thi_400_va_khong_ghi_lich_su(client):
    login(client)
    a, b = tao_nl(client, ton=100), tao_nl(client, ton=100)
    mon = dl.MON_ID
    dat_cong_thuc(client, mon, [(a["NguyenLieuID"], 10), (b["NguyenLieuID"], "2.5")])
    tong = data(client.get(f"{API}/recipes/{mon}/history"))["total"]
    # Cung noi dung, khac thu tu / dinh dang so
    r = client.put(f"{API}/recipes/{mon}", json={"items": [
        {"nguyen_lieu_id": str(b["NguyenLieuID"]), "so_luong_can": 2.5},
        {"nguyen_lieu_id": a["NguyenLieuID"], "so_luong_can": "10.000"}], "ly_do": "Khong doi"})
    assert r.status_code == 400 and msg(r) == "Khong co gi de cap nhat"
    assert data(client.get(f"{API}/recipes/{mon}/history"))["total"] == tong
    # Doi dinh luong rat nho thi la thay doi
    dat_cong_thuc(client, mon, [(a["NguyenLieuID"], 10), (b["NguyenLieuID"], "2.501")])
    assert data(client.get(f"{API}/recipes/{mon}/history"))["total"] == tong + 1


def test_xoa_cong_thuc_bang_items_rong(client):
    login(client)
    a = tao_nl(client, ton=100)
    mon = dl.MON_ID
    # Mon chua co cong thuc ma gui [] -> khong co gi doi
    r = client.put(f"{API}/recipes/{mon}", json={"items": []})
    assert r.status_code == 400 and msg(r) == "Khong co gi de cap nhat"
    dat_cong_thuc(client, mon, [(a["NguyenLieuID"], 4)])
    d = dat_cong_thuc(client, mon, [], ly_do="Bo cong thuc")
    assert d["items"] == [] and d["SoPhanLamDuoc"] is None
    lich_su = data(client.get(f"{API}/recipes/{mon}/history"))
    assert lich_su["total"] == 2
    assert lich_su["items"][0]["Sau"] == [] and len(lich_su["items"][0]["Truoc"]) == 1
    assert lich_su["items"][0]["LyDo"] == "Bo cong thuc"
    assert data(client.get(f"{API}/ingredients/{a['NguyenLieuID']}"))["SoMonDungNguyenLieu"] == 0


def test_luu_cong_thuc_trung_dong_va_du_lieu_sai(client):
    login(client)
    a, b = tao_nl(client, ton=100), tao_nl(client, ton=100)
    mon = dl.MON_ID
    dat_cong_thuc(client, mon, [(a["NguyenLieuID"], 10)])
    tong = data(client.get(f"{API}/recipes/{mon}/history"))["total"]
    ida, idb = a["NguyenLieuID"], b["NguyenLieuID"]

    def dong(i=ida, q=5):
        return {"nguyen_lieu_id": i, "so_luong_can": q}

    xau = [
        ({"items": [dong(ida, 1), dong(idb, 2), dong(ida, 3)]}, 400),     # trung nguyen lieu
        ({"items": [dong(ida, 1), dong(str(ida), 2)]}, 400),              # trung (id dang chuoi)
        ({"items": [dong(q=0)]}, 400), ({"items": [dong(q=-1)]}, 400), ({"items": [dong(q="abc")]}, 400),
        ({"items": [dong(q="NaN")]}, 400), ({"items": [dong(q="Infinity")]}, 400), ({"items": [dong(q=True)]}, 400),
        ({"items": [dong(q=None)]}, 400), ({"items": [dong(q="0.0004")]}, 400), ({"items": [dong(q=1000000.001)]}, 400),
        ({"items": [{"nguyen_lieu_id": ida}]}, 400), ({"items": [{"so_luong_can": 1}]}, 400),
        ({"items": [dong(i="abc")]}, 400), ({"items": [dong(i=0)]}, 400), ({"items": [dong(i=None)]}, 400),
        ({"items": [dong(i=True)]}, 400), ({"items": ["abc"]}, 400), ({"items": [None]}, 400),
        ({"items": "abc"}, 400), ({"items": None}, 400), ({}, 400), ({"items": {"a": 1}}, 400),
        ({"items": [dong(ida, 1), dong(999999, 1)]}, 404),                # nguyen lieu khong ton tai
    ]
    for body, ma in xau:
        r = client.put(f"{API}/recipes/{mon}", json=body)
        assert r.status_code == ma, (body, r.get_json())
    # Khong dong nao ghi thanh cong: cong thuc va lich su y nguyen (khong ghi dang do)
    d = data(client.get(f"{API}/recipes/{mon}"))
    assert [(i["NguyenLieuID"], D(i["SoLuongCan"])) for i in d["items"]] == [(ida, 10)]
    assert data(client.get(f"{API}/recipes/{mon}/history"))["total"] == tong

    # Bien hop le: dung 1.000.000 duoc, 101 dong khong duoc
    assert client.put(f"{API}/recipes/{mon}", json={"items": [dong(ida, 1000000)]}).status_code == 200
    r = client.put(f"{API}/recipes/{mon}", json={"items": [dong(ida, 1)] * 101})
    assert r.status_code == 400 and "toi da" in msg(r)
    assert client.put(f"{API}/recipes/{mon}", data="rac", content_type="application/json").status_code == 400
    assert client.put(f"{API}/recipes/{mon}", json="chuoi").status_code == 400


def test_luu_cong_thuc_100_dong_hop_le(client):
    login(client)
    ids = [tao_nl(client, ton=1)["NguyenLieuID"] for _ in range(100)]
    d = dat_cong_thuc(client, dl.MON_ID, [(i, 1) for i in ids])
    assert len(d["items"]) == 100 and d["SoPhanLamDuoc"] == 1


def test_cong_thuc_nguyen_lieu_ngung_dung(client):
    login(client)
    cu, moi = tao_nl(client, ton=100), tao_nl(client, ton=100)
    mon = dl.MON_ID
    dat_cong_thuc(client, mon, [(cu["NguyenLieuID"], 5)])
    for nl in (cu, moi):
        client.patch(f"{API}/ingredients/{nl['NguyenLieuID']}/status", json={"dang_dung": False})

    # Nguyen lieu moi them phai dang dung
    r = client.put(f"{API}/recipes/{mon}", json={"items": [
        {"nguyen_lieu_id": cu["NguyenLieuID"], "so_luong_can": 5}, {"nguyen_lieu_id": moi["NguyenLieuID"], "so_luong_can": 1}]})
    assert r.status_code == 400, r.get_json()
    # Dong cu giu nguyen (du nguyen lieu da ngung dung) thi khong can dang dung
    d = dat_cong_thuc(client, mon, [(cu["NguyenLieuID"], 7)])
    assert D(d["items"][0]["SoLuongCan"]) == 7 and d["items"][0]["NguyenLieuDangDung"] is False
    assert data(client.get(f"{API}/recipes/{mon}"))["items"][0]["NguyenLieuDangDung"] is False


def test_lich_su_cong_thuc_phan_trang_tham_so_sai(client):
    login(client)
    a = tao_nl(client, ton=100)
    for q in (1, 2, 3):
        dat_cong_thuc(client, dl.MON_ID, [(a["NguyenLieuID"], q)])
    d = data(client.get(f"{API}/recipes/{dl.MON_ID}/history", query_string={"per_page": 2}))
    assert d["total"] == 3 and len(d["items"]) == 2 and d["per_page"] == 2
    assert [D(x["Sau"][0]["SoLuongCan"]) for x in d["items"]] == [3, 2]
    d = data(client.get(f"{API}/recipes/{dl.MON_ID}/history", query_string={"page": "abc", "per_page": "-3"}))
    assert d["page"] == 1 and d["per_page"] == 1


# ---------- API 53: tru kho theo don ----------
def chuan_bi_kho():
    """a (1000 g), b (100 ml); MON_ID can a 18 + b 5; MON2_ID can a 10."""
    c = admin()
    a, b = tao_nl(c, ton=1000, don_vi="g"), tao_nl(c, ton=100, don_vi="ml")
    dat_cong_thuc(c, dl.MON_ID, [(a["NguyenLieuID"], 18), (b["NguyenLieuID"], 5)])
    dat_cong_thuc(c, dl.MON2_ID, [(a["NguyenLieuID"], 10)])
    return c, a, b


def test_tru_kho_theo_don_nhan_so_luong_va_gop_theo_nguyen_lieu():
    c, a, b = chuan_bi_kho()
    don = don_pha_che(c, [
        {"mon_id": dl.MON_ID, "so_luong": 2},
        {"mon_id": dl.MON_ID, "so_luong": 1, "ghi_chu": "size L"},      # dong rieng cung mon -> van gop
        {"mon_id": dl.MON2_ID, "so_luong": 3},
    ])
    did = don["DonHangID"]
    r = tru_kho(c, did)
    assert r.status_code == 201, r.get_json()
    d = data(r)
    assert d["DonHangID"] == did and d["MaDonHang"] == don["MaDonHang"] and d["MonChuaCoCongThuc"] == []
    # a: 3*18 + 3*10 = 84 ; b: 3*5 = 15  -> gop thanh dung 2 dong, tang dan theo ID
    assert [x["NguyenLieuID"] for x in d["ChiTiet"]] == [a["NguyenLieuID"], b["NguyenLieuID"]]
    ca, cb = d["ChiTiet"]
    assert ca["LoaiGiaoDich"] == "TIEU_HAO" and ca["DonHangID"] == did
    assert (D(ca["SoLuongThayDoi"]), D(ca["SoLuongTruoc"]), D(ca["SoLuongSau"])) == (-84, 1000, 916)
    assert (D(cb["SoLuongThayDoi"]), D(cb["SoLuongTruoc"]), D(cb["SoLuongSau"])) == (-15, 100, 85)
    assert ton_db(a["NguyenLieuID"]) == 916 and ton_db(b["NguyenLieuID"]) == 85
    assert len(so_cai(don_hang_id=did, loai="TIEU_HAO")) == 2
    kiem_so_cai(a["NguyenLieuID"])
    kiem_so_cai(b["NguyenLieuID"])

    # Lich su kho hien ma don
    h = data(c.get(f"{API}/inventory/transactions", query_string={"nguyen_lieu_id": a["NguyenLieuID"], "loai": "TIEU_HAO"}))
    assert h["total"] == 1 and h["items"][0]["MaDonHang"] == don["MaDonHang"]

    # Tru lan 2 -> 409, khong doi ton
    r = tru_kho(c, did)
    assert r.status_code == 409 and msg(r) == "Don nay da duoc tru kho"
    assert ton_db(a["NguyenLieuID"]) == 916 and ton_db(b["NguyenLieuID"]) == 85
    assert len(so_cai(don_hang_id=did, loai="TIEU_HAO")) == 2


def test_tru_kho_don_hoan_thanh_van_duoc():
    c, a, _ = chuan_bi_kho()
    don = don_pha_che(c, den="HOAN_THANH")
    assert tru_kho(c, don["DonHangID"]).status_code == 201
    assert ton_db(a["NguyenLieuID"]) == 982


def test_tru_kho_don_chua_pha_che_hoac_da_huy_bi_chan():
    c, a, b = chuan_bi_kho()
    moi = tao_don(c, [{"mon_id": dl.MON_ID, "so_luong": 1}])
    r = tru_kho(c, moi["DonHangID"])
    assert r.status_code == 409, r.get_json()
    c.patch(f"{API}/orders/{moi['DonHangID']}/status", json={"trang_thai": "CHO_PHA_CHE"})
    assert tru_kho(c, moi["DonHangID"]).status_code == 409

    huy = tao_don(c, [{"mon_id": dl.MON_ID, "so_luong": 1}])
    c.patch(f"{API}/orders/{huy['DonHangID']}/status", json={"trang_thai": "CHO_PHA_CHE"})
    c.patch(f"{API}/orders/{huy['DonHangID']}/status", json={"trang_thai": "DANG_PHA_CHE"})
    assert c.post(f"{API}/orders/{huy['DonHangID']}/cancel", json={"ly_do": "Khach bo"}).status_code == 200
    assert tru_kho(c, huy["DonHangID"]).status_code == 409

    assert ton_db(a["NguyenLieuID"]) == 1000 and ton_db(b["NguyenLieuID"]) == 100
    assert so_cai(don_hang_id=moi["DonHangID"]) == [] and so_cai(don_hang_id=huy["DonHangID"]) == []


@pytest.mark.parametrize("body, ma", [
    ({}, 400), ({"don_hang_id": None}, 400), ({"don_hang_id": "abc"}, 400), ({"don_hang_id": 0}, 400),
    ({"don_hang_id": -1}, 400), ({"don_hang_id": True}, 400), ({"don_hang_id": 1.5}, 400),
    ({"don_hang_id": 999999}, 404), ({"don_hang_id": 2147483648}, 400),
])
def test_tru_kho_don_khong_hop_le(client, body, ma):
    login(client)
    assert client.post(f"{API}/inventory/consumptions", json=body).status_code == ma


def test_tru_kho_thieu_ton_mot_nguyen_lieu_thi_rollback_het():
    c = admin()
    a = tao_nl(c, ton=1000)
    thieu = tao_nl(c, ton=5, don_vi="ml")                   # ID lon hon a -> a bi tru truoc roi moi gap loi
    dat_cong_thuc(c, dl.MON_ID, [(a["NguyenLieuID"], 18), (thieu["NguyenLieuID"], 10)])
    don = don_pha_che(c, [{"mon_id": dl.MON_ID, "so_luong": 1}])
    r = tru_kho(c, don["DonHangID"])
    assert r.status_code == 409, r.get_json()
    assert thieu["TenNguyenLieu"] in msg(r)
    assert ton_db(a["NguyenLieuID"]) == 1000 and ton_db(thieu["NguyenLieuID"]) == 5
    assert so_cai(don_hang_id=don["DonHangID"]) == []
    kiem_so_cai(a["NguyenLieuID"])

    # Bo sung ton roi tru lai -> thanh cong (lan that bai khong bi tinh la da tru)
    assert c.post(f"{API}/inventory/adjustments", json={
        "nguyen_lieu_id": thieu["NguyenLieuID"], "so_luong_thuc_te": 10, "ly_do": "Nhap bo sung"}).status_code == 201
    r = tru_kho(c, don["DonHangID"])
    assert r.status_code == 201, r.get_json()
    assert ton_db(a["NguyenLieuID"]) == 982 and ton_db(thieu["NguyenLieuID"]) == 0


def test_tru_kho_mon_chua_co_cong_thuc_duoc_bao_lai():
    c = admin()
    a = tao_nl(c, ton=100)
    dat_cong_thuc(c, dl.MON_ID, [(a["NguyenLieuID"], 4)])        # MON2_ID khong co cong thuc
    don = don_pha_che(c, [{"mon_id": dl.MON_ID, "so_luong": 2}, {"mon_id": dl.MON2_ID, "so_luong": 1}])
    r = tru_kho(c, don["DonHangID"])
    assert r.status_code == 201, r.get_json()
    d = data(r)
    assert d["MonChuaCoCongThuc"] == ["Pytest Mon Hai"] and len(d["ChiTiet"]) == 1
    assert ton_db(a["NguyenLieuID"]) == 92


def test_tru_kho_don_khong_mon_nao_co_cong_thuc_la_400():
    c = admin()
    don = don_pha_che(c, [{"mon_id": dl.MON_ID, "so_luong": 1}])   # chua dat cong thuc nao
    r = tru_kho(c, don["DonHangID"])
    assert r.status_code == 400, r.get_json()
    assert so_cai(don_hang_id=don["DonHangID"]) == []


def test_tru_kho_don_dong_thoi_chi_1_yeu_cau_thanh_cong():
    c, a, b = chuan_bi_kho()
    don = don_pha_che(c, [{"mon_id": dl.MON_ID, "so_luong": 2}])
    cs = [admin() for _ in range(4)]
    kq = song_song([(lambda x=x: tru_kho(x, don["DonHangID"])) for x in cs])
    codes = sorted(k[0] for k in kq)
    assert codes == [201, 409, 409, 409], kq
    assert ton_db(a["NguyenLieuID"]) == 964 and ton_db(b["NguyenLieuID"]) == 90     # chi tru 1 lan
    assert len(so_cai(don_hang_id=don["DonHangID"], loai="TIEU_HAO")) == 2
    kiem_so_cai(a["NguyenLieuID"])
    kiem_so_cai(b["NguyenLieuID"])


def test_tru_kho_nhieu_don_khac_nhau_dong_thoi_khong_deadlock():
    c, a, b = chuan_bi_kho()
    dons = [don_pha_che(c, [{"mon_id": dl.MON_ID, "so_luong": 1}]) for _ in range(6)]
    cs = [admin() for _ in dons]
    kq = song_song([(lambda x=x, d=d: tru_kho(x, d["DonHangID"])) for x, d in zip(cs, dons)])
    assert [k[0] for k in kq] == [201] * 6, kq
    assert ton_db(a["NguyenLieuID"]) == 1000 - 6 * 18 and ton_db(b["NguyenLieuID"]) == 100 - 6 * 5
    kiem_so_cai(a["NguyenLieuID"])
    kiem_so_cai(b["NguyenLieuID"])


def test_tru_kho_nhieu_don_dong_thoi_het_ton_thi_409_khong_am():
    c = admin()
    a = tao_nl(c, ton=40)                                   # du cho 2 don (18 x 2 = 36), don thu 3 thieu
    dat_cong_thuc(c, dl.MON_ID, [(a["NguyenLieuID"], 18)])
    dons = [don_pha_che(c, [{"mon_id": dl.MON_ID, "so_luong": 1}]) for _ in range(4)]
    cs = [admin() for _ in dons]
    kq = song_song([(lambda x=x, d=d: tru_kho(x, d["DonHangID"])) for x, d in zip(cs, dons)])
    assert sorted(k[0] for k in kq) == [201, 201, 409, 409], kq
    assert ton_db(a["NguyenLieuID"]) == 4
    kiem_so_cai(a["NguyenLieuID"])


# ---------- Phan quyen ----------
TAT_CA_API = [
    ("get", "/ingredients", None), ("post", "/ingredients", {}), ("get", "/ingredients/1", None),
    ("put", "/ingredients/1", {}), ("patch", "/ingredients/1/status", {}), ("get", "/inventory", None),
    ("get", "/inventory/low-stock", None), ("get", "/inventory/transactions", None),
    ("post", "/inventory/adjustments", {}), ("post", "/inventory/issues", {}),
    ("get", "/inventory/ingredients/1", None), ("get", "/recipes/1", None), ("put", "/recipes/1", {}),
    ("get", "/recipes/1/history", None), ("post", "/inventory/consumptions", {}),
]


@pytest.mark.parametrize("method, url, body", TAT_CA_API)
def test_chua_dang_nhap_thi_401(method, url, body):
    anon = create_app().test_client()
    r = getattr(anon, method)(f"{API}{url}", json=body)
    assert r.status_code == 401, (method, url)


def test_dang_ky_du_15_route_kho():
    app = create_app()
    rules = {(m, r.rule) for r in app.url_map.iter_rules() if r.endpoint.startswith("inventory.")
             for m in r.methods if m not in ("HEAD", "OPTIONS")}
    assert len(rules) == 15, sorted(rules)


def test_nhan_vien_chi_xem_duoc_khong_sua_kiem_ke_xuat_kho():
    ad = admin()
    nl = tao_nl(ad, ton=100, muc=10)
    nl_id = nl["NguyenLieuID"]
    dat_cong_thuc(ad, dl.MON_ID, [(nl_id, 5)])
    nv = staff()

    # Xem duoc
    for url in (f"/ingredients", f"/ingredients/{nl_id}", "/inventory", "/inventory/low-stock",
                "/inventory/transactions", f"/inventory/ingredients/{nl_id}", f"/recipes/{dl.MON_ID}",
                f"/recipes/{dl.MON_ID}/history"):
        r = nv.get(f"{API}{url}")
        assert r.status_code == 200, (url, r.get_json())
    assert data(nv.get(f"{API}/recipes/{dl.MON_ID}"))["items"][0]["NguyenLieuID"] == nl_id

    # Sua / kiem ke / xuat kho / cong thuc -> 403, va khong co gi thay doi
    tong_ls = len(so_cai(nl_id))
    cac_lenh = [
        nv.post(f"{API}/ingredients", json={"ten_nguyen_lieu": ten("NV"), "don_vi_tinh": "g"}),
        nv.put(f"{API}/ingredients/{nl_id}", json={"ten_nguyen_lieu": ten("NV")}),
        nv.patch(f"{API}/ingredients/{nl_id}/status", json={"dang_dung": False}),
        nv.post(f"{API}/inventory/adjustments", json={"nguyen_lieu_id": nl_id, "so_luong_thuc_te": 1, "ly_do": "x"}),
        nv.post(f"{API}/inventory/issues", json={"nguyen_lieu_id": nl_id, "so_luong": 1, "ly_do": "x"}),
        nv.put(f"{API}/recipes/{dl.MON_ID}", json={"items": []}),
    ]
    assert [r.status_code for r in cac_lenh] == [403] * 6
    d = data(ad.get(f"{API}/ingredients/{nl_id}"))
    assert d["TenNguyenLieu"] == nl["TenNguyenLieu"] and d["TrangThai"] is True and D(d["SoLuongTon"]) == 100
    assert len(so_cai(nl_id)) == tong_ls
    assert len(data(ad.get(f"{API}/recipes/{dl.MON_ID}"))["items"]) == 1
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM dbo.NguyenLieu WHERE TenNguyenLieu LIKE N'Pytest NV %'")
        assert cur.fetchval() == 0


def test_nhan_vien_van_tru_kho_duoc():
    c, a, _ = chuan_bi_kho()
    don = don_pha_che(c, [{"mon_id": dl.MON_ID, "so_luong": 1}])
    r = tru_kho(staff(), don["DonHangID"])
    assert r.status_code == 201, r.get_json()
    assert ton_db(a["NguyenLieuID"]) == 982
    rows = so_cai(don_hang_id=don["DonHangID"])
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT HoTen FROM dbo.TaiKhoan WHERE TaiKhoanID = ?", (rows[0]["TaiKhoanID"],))
        assert cur.fetchval() == "Pytest Nhan Vien"             # ghi dung nguoi thuc hien


def test_ton_kho_luon_khop_so_cai_sau_chuoi_thao_tac(client):
    login(client)
    nl = tao_nl(client, ton=200, muc=50)
    i = nl["NguyenLieuID"]
    dat_cong_thuc(client, dl.MON_ID, [(i, 12.5)])
    for body in ({"so_luong": 33.333}, {"so_luong": 0.001}, {"so_luong": 500}):
        client.post(f"{API}/inventory/issues", json={"nguyen_lieu_id": i, "ly_do": "Thu", **body})
    client.post(f"{API}/inventory/adjustments", json={"nguyen_lieu_id": i, "so_luong_thuc_te": 77.7, "ly_do": "Dem"})
    don = don_pha_che(client, [{"mon_id": dl.MON_ID, "so_luong": 3}])
    assert tru_kho(client, don["DonHangID"]).status_code == 201
    assert ton_db(i) == D("77.7") - D("37.5")
    kiem_so_cai(i)
    assert D(data(client.get(f"{API}/ingredients/{i}"))["SoLuongTon"]) == ton_db(i)
