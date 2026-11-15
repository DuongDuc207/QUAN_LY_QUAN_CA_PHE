/* Du lieu va noi dung the mon dung chung cho Thuc don va Ban hang. */
const ThucDon = (() => {
  async function taiTatCa(dangBan = false) {
    const items = [];
    let page = 1;
    while (true) {
      const params = new URLSearchParams({page, per_page: 100});
      if (dangBan) params.set("dang_ban", "1");
      const r = await apiGoi("GET", "/api/v1/menu?" + params);
      if (!r.ok) return r;
      items.push(...r.data.items);
      if (items.length >= r.data.total || !r.data.items.length) break;
      page++;
    }
    return {ok: true, data: sapXep(items)};
  }

  function sapXep(items) {
    return items.slice().sort((a, b) =>
      String(a.TenDanhMuc || "").localeCompare(String(b.TenDanhMuc || ""), "vi") ||
      String(a.TenMon).localeCompare(String(b.TenMon), "vi") || Number(a.MonID) - Number(b.MonID));
  }

  function dangBan(mon) {
    return Boolean(mon.TrangThai) && mon.DanhMucHienThi !== false && mon.DanhMucHienThi !== 0;
  }

  function loc(items, tuKhoa = "", nhom = "", tinhTrang = "tat-ca") {
    const q = boDau(tuKhoa.trim());
    return items.filter(m =>
      (!nhom || String(m.DanhMucID) === String(nhom)) &&
      (!q || boDau([m.TenMon, m.TenDanhMuc, m.MoTa].join(" ")).includes(q)) &&
      (tinhTrang === "tat-ca" || (tinhTrang === "dang-ban" ? dangBan(m) : !dangBan(m))));
  }

  function noiDungThe(mon) {
    const anh = String(mon.HinhAnh || "").trim();
    const anhHopLe = /^(https?:\/\/|\/(?!\/))/i.test(anh);
    return `${anhHopLe ? `<img class="catalog-image" src="${escapeHtml(anh)}" alt="" loading="lazy">` : ""}
      <span class="catalog-info">
        <span class="tile-group">${escapeHtml(mon.TenDanhMuc || "Chưa phân nhóm")}</span>
        <span class="tile-name">${escapeHtml(mon.TenMon)}</span>
        ${mon.MoTa ? `<span class="catalog-description">${escapeHtml(mon.MoTa)}</span>` : ""}
      </span>
      <span class="catalog-meta">
        <span class="tile-price">${dinhDangGia(mon.GiaBan)}</span>
        <span class="badge ${dangBan(mon) ? "badge-on" : "badge-off"}">${dangBan(mon) ? "Đang bán" : (mon.TrangThai ? "Nhóm đang ẩn" : "Ngừng bán")}</span>
      </span>`;
  }

  function baoThayDoi() {
    try { localStorage.setItem("qlcp-thuc-don", String(Date.now())); } catch (_) {}
  }

  function theoDoiThayDoi(taiLai) {
    window.addEventListener("focus", taiLai);
    window.addEventListener("storage", e => {
      if (e.key === "qlcp-thuc-don") taiLai();
    });
  }

  return {taiTatCa, sapXep, dangBan, loc, noiDungThe, baoThayDoi, theoDoiThayDoi};
})();
