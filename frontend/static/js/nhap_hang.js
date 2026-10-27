/* Trang Nhap hang (phieu nhap). Can main.js nap truoc.
   Ma tinh trang he thong chi di qua ham trong main.js (huyHieuPhieuNhap, phieuNhapChoNhan...). */

/* Cau dien giai loi rieng. Dau hieu = mot doan thong bao he thong viet thuong, khong dau.
   Cau cu the dat truoc cau chung vi tim theo thu tu. */
DIEN_GIAI_LOI_RIENG.push(
  ["danh sach nguyen lieu khong hop le", "Danh sách nguyên liệu chưa hợp lệ. Vui lòng tải lại trang."],
  ["nguyen lieu bi trung trong phieu nhap", "Mỗi nguyên liệu chỉ được xuất hiện một lần trong phiếu. Hãy gộp các dòng trùng lại."],
  ["khong the nhan hang", "Có nguyên liệu trong phiếu đã ngừng sử dụng nên chưa nhận hàng được. Hãy huỷ phiếu và lập phiếu mới."],
  ["da ngung su dung", "Có nguyên liệu trong phiếu đã ngừng sử dụng. Hãy bỏ nguyên liệu đó khỏi phiếu."],
  ["nguyen lieu khong ton tai", "Có nguyên liệu không còn trong hệ thống. Vui lòng tải lại trang."],
  ["nguyen lieu khong hop le", "Vui lòng chọn nguyên liệu cho từng dòng."],
  ["phieu nhap phai co it nhat 1 dong", "Phiếu cần có ít nhất 1 nguyên liệu."],
  ["phieu nhap toi da", "Một phiếu nhập có tối đa 100 nguyên liệu. Hãy tách thành nhiều phiếu."],
  ["so luong phai lon hon 0", "Số lượng phải lớn hơn 0 và không quá 1.000.000."],
  ["don gia nhap phai tu 0", "Đơn giá nhập phải từ 0 đến 1.000.000.000 ₫."],
  ["tong tien phieu nhap qua lon", "Tổng tiền của phiếu quá lớn. Hãy tách thành nhiều phiếu."],
  ["ghi chu khong hop le", "Ghi chú chưa hợp lệ."],
  ["nha cung cap da ngung hop tac", "Nhà cung cấp này đã ngừng hợp tác. Vui lòng chọn nhà cung cấp khác."],
  ["nha cung cap khong ton tai", "Không tìm thấy nhà cung cấp này. Vui lòng tải lại trang."],
  ["nha cung cap khong hop le", "Vui lòng chọn nhà cung cấp."],
  ["phieu nhap khong ton tai", "Không tìm thấy phiếu nhập này. Vui lòng tải lại trang."],
  ["phieu nhap khong co dong nao", "Phiếu này chưa có nguyên liệu nào nên chưa xác nhận được."],
  ["phieu da xac nhan hoac da huy, khong the sua", "Phiếu đã được xác nhận hoặc đã huỷ nên không sửa được. Vui lòng tải lại trang."],
  ["phieu da duoc xac nhan truoc do", "Phiếu này đã được xác nhận nhận hàng trước đó. Vui lòng tải lại trang."],
  ["phieu da huy, khong the xac nhan", "Phiếu này đã huỷ nên không xác nhận được."],
  ["phieu da huy truoc do", "Phiếu này đã được huỷ trước đó."],
  ["ly do huy la bat buoc", "Vui lòng nhập lý do huỷ phiếu."],
  ["khong co quyen huy phieu da xac nhan", "Bạn không có quyền huỷ phiếu đã nhận hàng. Vui lòng nhờ quản lý."],
  ["ton kho khong du", "Không huỷ được vì hàng của phiếu này đã được dùng bớt, tồn kho hiện không đủ để trừ lại."],
  ["he thong dang ban", "Hệ thống đang bận xử lý. Vui lòng thử lại sau vài giây."],
  ["trang thai phieu nhap khong hop le", "Tình trạng lọc chưa hợp lệ. Vui lòng chọn lại."],
  ["du lieu gui len khong hop le", "Thông tin gửi đi chưa hợp lệ. Vui lòng tải lại trang."],
);

(() => {
  const SO_DONG = 20;
  const TOI_DA_DONG = 100;
  const SO_LUONG_TOI_DA = 1000000;
  const DON_GIA_TOI_DA = 1000000000;

  const coQuyen = (q) => (window.QUYEN || []).includes(q);
  const duocLapSua = coQuyen("supplier.manage") && coQuyen("inventory.view");
  const duocHuy = coQuyen("supplier.manage");
  const duocNhan = coQuyen("purchase.confirm");
  const $ = (id) => document.getElementById(id);

  const tbody = document.querySelector("#phieu-table tbody");
  const pageError = $("page-error");
  const phieuForm = $("phieu-form");
  const phieuError = $("phieu-error");
  const dsDong = $("phieu-dong");
  const huyForm = $("huy-form");

  let trang = 1;
  let dsNcc = [];          // moi nha cung cap
  let dsNguyenLieu = [];   // nguyen lieu dung trong form
  let phieuDangSua = null; // null = lap moi
  let phieuDangXem = null; // phieu dang mo chi tiet
  let phieuCho = null;     // phieu dang xac nhan / huy

  function hienLoi(el, text) { el.textContent = text; el.classList.remove("hidden"); }
  function anLoi(el) { el.classList.add("hidden"); }
  const soTien = (n) => Math.round(n * 100) / 100;
  const dangHopTac = (n) => Boolean(n && n.TrangThai);

  /** Tai het cac trang cua mot danh sach (moi trang toi da 100 dong). */
  async function taiTatCa(duongDan, thamSo) {
    const tatCa = [];
    for (let page = 1; page <= 50; page++) {
      const p = new URLSearchParams(Object.assign({}, thamSo, {page: page, per_page: 100}));
      const r = await apiGoi("GET", duongDan + "?" + p.toString());
      if (!r.ok) return r;
      tatCa.push(...r.data.items);
      if (!r.data.items.length || tatCa.length >= r.data.total) break;
    }
    return {ok: true, data: tatCa};
  }

  /* ===================== Bo loc ===================== */
  $("loc-tinh-trang").insertAdjacentHTML("beforeend",
    luaChonTinhTrangPhieuNhap().map((t) => `<option value="${t.ma}">${escapeHtml(t.nhan)}</option>`).join(""));

  const maTuDuongDan = new URLSearchParams(window.location.search).get("q");
  if (maTuDuongDan) $("loc-ma").value = maTuDuongDan;

  async function taiNcc() {
    const r = await taiTatCa("/api/v1/suppliers", {});
    if (!r.ok) return r;
    dsNcc = r.data;
    const loc = $("loc-ncc");
    const dangChon = loc.value;
    loc.innerHTML = `<option value="">Tất cả nhà cung cấp</option>` + dsNcc.map((n) =>
      `<option value="${n.NhaCungCapID}">${escapeHtml(n.TenNhaCungCap)}${dangHopTac(n) ? "" : " (đã ngừng hợp tác)"}</option>`).join("");
    loc.value = dangChon;
    return r;
  }

  /* ===================== Danh sach ===================== */
  function showEmpty(text) {
    tbody.innerHTML = `<tr class="empty-row"><td colspan="7">${escapeHtml(text)}</td></tr>`;
  }

  function dangLoc() {
    return $("loc-ma").value.trim() || $("loc-tinh-trang").value || $("loc-ncc").value
      || $("loc-tu-ngay").value || $("loc-den-ngay").value;
  }

  function ve(rows) {
    if (!rows.length) {
      showEmpty(dangLoc() ? "Không có phiếu nhập nào phù hợp." : "Chưa có phiếu nhập hàng nào.");
      return;
    }
    tbody.innerHTML = rows.map((p) => {
      const nutNhan = phieuNhapChoNhan(p) && duocNhan
        ? `<button type="button" class="btn-icon" data-nhan="${p.PhieuNhapID}">Xác nhận nhận hàng</button>` : "";
      return `<tr>
        <td><div class="cell-name">${escapeHtml(p.MaPhieuNhap)}</div>
          <div class="cell-sub">${Number(p.SoDong || 0).toLocaleString("vi-VN")} nguyên liệu</div></td>
        <td>${escapeHtml(p.TenNhaCungCap)}</td>
        <td>${dinhDangThoiGian(p.NgayNhap)}</td>
        <td class="col-num">${dinhDangGia(p.TongTien)}</td>
        <td>${huyHieuPhieuNhap(p.TrangThai)}</td>
        <td>${p.NguoiLap ? escapeHtml(p.NguoiLap) : `<span class="muted">—</span>`}</td>
        <td class="col-actions"><div class="row-actions">
          ${nutNhan}
          <button type="button" class="btn-icon" data-xem="${p.PhieuNhapID}">Chi tiết</button>
        </div></td>
      </tr>`;
    }).join("");
  }

  function vePhanTrang(total) {
    const soTrang = Math.max(1, Math.ceil(total / SO_DONG));
    const pager = $("pager");
    if (total <= SO_DONG) {
      pager.innerHTML = total ? `<span class="muted">${total.toLocaleString("vi-VN")} phiếu</span>` : "";
      return;
    }
    pager.innerHTML = `
      <span class="muted">Trang ${trang}/${soTrang} · ${total.toLocaleString("vi-VN")} phiếu</span>
      <button type="button" class="btn-outline" data-trang="${trang - 1}" ${trang <= 1 ? "disabled" : ""}>‹ Trước</button>
      <button type="button" class="btn-outline" data-trang="${trang + 1}" ${trang >= soTrang ? "disabled" : ""}>Sau ›</button>`;
  }

  async function tai() {
    anLoi(pageError);
    const tu = $("loc-tu-ngay").value;
    const den = $("loc-den-ngay").value;
    if (tu && den && tu > den) {
      hienLoi(pageError, "Ngày bắt đầu phải trước hoặc cùng ngày kết thúc.");
      showEmpty("Vui lòng chọn lại khoảng ngày.");
      $("pager").innerHTML = "";
      return;
    }
    const p = new URLSearchParams({page: trang, per_page: SO_DONG});
    const q = $("loc-ma").value.trim();
    if (q) p.set("q", q);
    if ($("loc-tinh-trang").value) p.set("status", $("loc-tinh-trang").value);
    if ($("loc-ncc").value) p.set("nha_cung_cap_id", $("loc-ncc").value);
    if (tu) p.set("tu_ngay", tu);
    if (den) p.set("den_ngay", den);
    const r = await apiGoi("GET", "/api/v1/purchase-receipts?" + p.toString());
    if (!r.ok) {
      if (kiemTraHetPhien(r.status)) return;
      hienLoi(pageError, thongBaoLoi(r.status, "danh sách phiếu nhập"));
      showEmpty("Không có dữ liệu để hiển thị.");
      $("pager").innerHTML = "";
      return;
    }
    if (!r.data.items.length && trang > 1 && r.data.total > 0) {
      trang = Math.max(1, Math.ceil(r.data.total / SO_DONG));
      return tai();
    }
    ve(r.data.items);
    vePhanTrang(r.data.total);
  }

  function locLai() { trang = 1; tai(); }

  /* ===================== Chi tiet phieu ===================== */
  async function docPhieu(id) {
    const r = await apiGoi("GET", `/api/v1/purchase-receipts/${id}`);
    if (!r.ok) {
      if (!kiemTraHetPhien(r.status)) hienToast(r.loi);
      return null;
    }
    return r.data;
  }

  function veChiTiet(p) {
    $("phieu-ct-title").textContent = `Phiếu nhập ${p.MaPhieuNhap}`;
    const dong = p.ChiTiet || [];
    const thongTin = [
      ["Tình trạng", huyHieuPhieuNhap(p.TrangThai)],
      ["Nhà cung cấp", escapeHtml(p.TenNhaCungCap)],
      ["Ngày nhập", dinhDangThoiGian(p.NgayNhap)],
      ["Người lập phiếu", p.NguoiLap ? escapeHtml(p.NguoiLap) : "—"],
    ];
    if (phieuNhapDaNhan(p)) {
      thongTin.push(["Đã nhận hàng lúc", dinhDangThoiGian(p.NgayXacNhan)]);
      thongTin.push(["Người xác nhận", p.NguoiXacNhan ? escapeHtml(p.NguoiXacNhan) : "—"]);
    }
    if (phieuNhapDaHuy(p)) {
      thongTin.push(["Lý do huỷ", p.LyDoHuy ? escapeHtml(p.LyDoHuy) : "—"]);
    }
    if (p.GhiChu) thongTin.push(["Ghi chú", escapeHtml(p.GhiChu)]);

    $("phieu-ct-body").innerHTML = `
      <dl class="detail-list">
        ${thongTin.map(([ten, giaTri]) => `<div class="detail-row"><dt>${ten}</dt><dd>${giaTri}</dd></div>`).join("")}
      </dl>
      <h4 class="sub-title">Nguyên liệu trong phiếu</h4>
      <div style="overflow-x:auto">
        <table class="line-table">
          <thead><tr><th>Nguyên liệu</th><th class="col-num">Số lượng</th><th class="col-num">Đơn giá nhập</th><th class="col-num">Thành tiền</th></tr></thead>
          <tbody>${dong.length ? dong.map((c) => `<tr>
            <td><div class="cell-name">${escapeHtml(c.TenNguyenLieu)}</div></td>
            <td class="col-num">${escapeHtml(dinhDangSoLuong(c.SoLuong, c.DonViTinh))}</td>
            <td class="col-num">${dinhDangGia(c.DonGiaNhap)}</td>
            <td class="col-num">${dinhDangGia(c.ThanhTien)}</td>
          </tr>`).join("") : `<tr><td colspan="4" class="muted">Phiếu chưa có nguyên liệu nào.</td></tr>`}</tbody>
        </table>
      </div>
      <div class="sum-box"><div class="sum-row grand"><span>Tổng tiền</span><strong>${dinhDangGia(p.TongTien)}</strong></div></div>
      ${phieuNhapDaNhan(p) ? `<p class="field-hint">Hàng đã được cộng vào tồn kho khi xác nhận nhận hàng.</p>` : ""}
      ${phieuNhapChoNhan(p) ? `<p class="field-hint">Phiếu đang chờ nhận hàng nên tồn kho chưa thay đổi.</p>` : ""}`;

    const nut = [];
    if (phieuNhapChoNhan(p)) {
      if (duocLapSua) nut.push(`<button type="button" class="btn-outline" data-act="sua">Sửa phiếu</button>`);
      if (duocHuy) nut.push(`<button type="button" class="btn-outline nh-nguy-hiem" data-act="huy">Huỷ phiếu</button>`);
    } else if (phieuNhapDaNhan(p) && duocHuy && duocNhan) {
      nut.push(`<button type="button" class="btn-outline nh-nguy-hiem" data-act="huy">Huỷ phiếu đã nhận hàng</button>`);
    }
    nut.push(`<span class="spacer"></span>`);
    nut.push(`<button type="button" class="btn-outline" data-dong-modal="modal-phieu-ct">Đóng</button>`);
    if (phieuNhapChoNhan(p) && duocNhan) nut.push(`<button type="button" data-act="nhan">Xác nhận đã nhận hàng</button>`);
    $("phieu-ct-foot").innerHTML = nut.join("");
  }

  async function xemChiTiet(id) {
    const p = await docPhieu(id);
    if (!p) return;
    phieuDangXem = p;
    veChiTiet(p);
    moModal("modal-phieu-ct");
  }

  $("phieu-ct-foot").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-act]");
    if (!b || !phieuDangXem) return;
    if (b.dataset.act === "sua") moForm(phieuDangXem);
    else if (b.dataset.act === "huy") moHuy(phieuDangXem);
    else if (b.dataset.act === "nhan") moNhan(phieuDangXem);
  });

  /* ===================== Lap / sua phieu ===================== */
  function tuyChonNguyenLieu(chon) {
    return `<option value="">Chọn nguyên liệu</option>` + dsNguyenLieu.map((n) =>
      `<option value="${n.NguyenLieuID}" data-don-vi="${escapeHtml(n.DonViTinh)}"${String(n.NguyenLieuID) === String(chon) ? " selected" : ""}>${escapeHtml(n.TenNguyenLieu)}</option>`).join("");
  }

  function cacDong() { return Array.from(dsDong.querySelectorAll(".nh-dong")); }

  function capNhatDong(row) {
    const sel = row.querySelector("[data-nl]");
    const opt = sel.options[sel.selectedIndex];
    row.querySelector("span[data-dv]").textContent = opt && opt.dataset.donVi ? opt.dataset.donVi : "";
    const sl = Number(row.querySelector("[data-sl]").value);
    const gia = Number(row.querySelector("[data-gia]").value);
    const hopLe = row.querySelector("[data-sl]").value !== "" && row.querySelector("[data-gia]").value !== ""
      && Number.isFinite(sl) && Number.isFinite(gia) && sl >= 0 && gia >= 0;
    row.querySelector("[data-tien]").textContent = hopLe ? dinhDangGia(soTien(sl * gia)) : "—";
  }

  /** Khong cho chon trung: nguyen lieu da chon o dong khac bi vo hieu hoa. */
  function capNhatLuaChon() {
    const rows = cacDong();
    const daChon = new Set(rows.map((r) => r.querySelector("[data-nl]").value).filter(Boolean));
    rows.forEach((r) => {
      const sel = r.querySelector("[data-nl]");
      Array.from(sel.options).forEach((o) => {
        o.disabled = Boolean(o.value) && daChon.has(o.value) && o.value !== sel.value;
      });
    });
  }

  function capNhatTong() {
    let tong = 0;
    cacDong().forEach((r) => {
      const sl = Number(r.querySelector("[data-sl]").value);
      const gia = Number(r.querySelector("[data-gia]").value);
      if (Number.isFinite(sl) && Number.isFinite(gia) && sl > 0 && gia >= 0) tong += soTien(sl * gia);
    });
    $("phieu-tong").textContent = dinhDangGia(soTien(tong));
  }

  function capNhatNut() {
    const rows = cacDong();
    rows.forEach((r) => { r.querySelector("[data-bo]").disabled = rows.length === 1; });
    $("btn-them-dong").disabled = rows.length >= TOI_DA_DONG;
  }

  function themDong(du, lay) {
    const row = document.createElement("div");
    row.className = "nh-dong";
    row.innerHTML = `
      <label class="nh-o-nl"><span class="nh-nhan-nho">Nguyên liệu</span>
        <select data-nl>${tuyChonNguyenLieu(du ? du.nguyenLieuId : "")}</select></label>
      <label><span class="nh-nhan-nho">Số lượng</span>
        <span class="nh-kem-don-vi"><input type="number" data-sl min="0" max="${SO_LUONG_TOI_DA}" step="0.001" inputmode="decimal" value="${du ? du.soLuong : ""}"><span class="nh-don-vi" data-dv></span></span></label>
      <label><span class="nh-nhan-nho">Đơn giá nhập (₫)</span>
        <input type="number" data-gia min="0" max="${DON_GIA_TOI_DA}" step="100" inputmode="numeric" value="${du ? du.donGia : ""}"></label>
      <div class="nh-o-tien" data-tien aria-live="polite">—</div>
      <button type="button" class="btn-icon danger nh-bo-dong" data-bo aria-label="Bỏ dòng nguyên liệu này">Bỏ</button>`;
    dsDong.appendChild(row);
    capNhatDong(row);
    capNhatLuaChon();
    capNhatTong();
    capNhatNut();
    if (lay) row.querySelector("[data-nl]").focus();
  }

  dsDong.addEventListener("input", (e) => {
    const row = e.target.closest(".nh-dong");
    if (!row) return;
    capNhatDong(row);
    capNhatLuaChon();
    capNhatTong();
  });

  dsDong.addEventListener("click", (e) => {
    const b = e.target.closest("[data-bo]");
    if (!b || b.disabled) return;
    b.closest(".nh-dong").remove();
    capNhatLuaChon();
    capNhatTong();
    capNhatNut();
  });

  $("btn-them-dong").addEventListener("click", () => themDong(null, true));

  async function moForm(phieu) {
    anLoi(phieuError);
    const [rNcc, rNl] = await Promise.all([taiNcc(), taiTatCa("/api/v1/ingredients", {status: "active"})]);
    if (!rNcc.ok || !rNl.ok) {
      const loi = !rNcc.ok ? rNcc : rNl;
      if (!kiemTraHetPhien(loi.status)) hienToast(loi.loi);
      return;
    }
    dsNguyenLieu = rNl.data.slice();
    // Phieu cu co the con nguyen lieu da ngung dung: van hien de nguoi dung thay va bo di.
    if (phieu) {
      (phieu.ChiTiet || []).forEach((c) => {
        if (!dsNguyenLieu.some((n) => n.NguyenLieuID === c.NguyenLieuID)) {
          dsNguyenLieu.push({NguyenLieuID: c.NguyenLieuID, TenNguyenLieu: `${c.TenNguyenLieu} (đã ngừng sử dụng)`, DonViTinh: c.DonViTinh});
        }
      });
    }

    phieuDangSua = phieu || null;
    phieuForm.reset();
    dsDong.innerHTML = "";

    const nccChon = dsNcc.filter((n) => dangHopTac(n) || (phieu && n.NhaCungCapID === phieu.NhaCungCapID));
    phieuForm.ncc.innerHTML = `<option value="">Chọn nhà cung cấp</option>` + nccChon.map((n) =>
      `<option value="${n.NhaCungCapID}">${escapeHtml(n.TenNhaCungCap)}${dangHopTac(n) ? "" : " (đã ngừng hợp tác)"}</option>`).join("");

    if (phieu) {
      phieuForm.ncc.value = String(phieu.NhaCungCapID);
      phieuForm.ghi_chu.value = phieu.GhiChu || "";
      (phieu.ChiTiet || []).forEach((c) => themDong({
        nguyenLieuId: c.NguyenLieuID, soLuong: Number(c.SoLuong), donGia: Number(c.DonGiaNhap),
      }, false));
      $("phieu-title").textContent = `Sửa phiếu nhập ${phieu.MaPhieuNhap}`;
      $("btn-luu-phieu").textContent = "Lưu thay đổi";
    } else {
      $("phieu-title").textContent = "Lập phiếu nhập";
      $("btn-luu-phieu").textContent = "Lưu phiếu nhập";
    }
    if (!cacDong().length) themDong(null, false);
    dongModal("modal-phieu-ct");
    moModal("modal-phieu");
  }

  phieuForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    anLoi(phieuError);
    if (!phieuForm.ncc.value) {
      hienLoi(phieuError, "Vui lòng chọn nhà cung cấp.");
      phieuForm.ncc.focus();
      return;
    }
    const items = [];
    for (const row of cacDong()) {
      const sel = row.querySelector("[data-nl]");
      const slEl = row.querySelector("[data-sl]");
      const giaEl = row.querySelector("[data-gia]");
      const sl = slEl.value.trim();
      const gia = giaEl.value.trim();
      if (!sel.value && !sl && !gia) continue; // dong trong: bo qua
      const ten = sel.value ? sel.options[sel.selectedIndex].textContent : "";
      if (!sel.value) {
        hienLoi(phieuError, "Vui lòng chọn nguyên liệu cho dòng đang nhập, hoặc bỏ dòng đó.");
        sel.focus();
        return;
      }
      const slN = Number(sl);
      if (!sl || !Number.isFinite(slN) || slN <= 0 || slN > SO_LUONG_TOI_DA) {
        hienLoi(phieuError, `Số lượng của "${ten}" phải lớn hơn 0 và không quá 1.000.000.`);
        slEl.focus();
        return;
      }
      const giaN = Number(gia);
      if (!gia || !Number.isFinite(giaN) || giaN < 0 || giaN > DON_GIA_TOI_DA) {
        hienLoi(phieuError, `Đơn giá nhập của "${ten}" phải từ 0 đến 1.000.000.000 ₫.`);
        giaEl.focus();
        return;
      }
      items.push({nguyen_lieu_id: Number(sel.value), so_luong: sl, don_gia_nhap: gia});
    }
    if (!items.length) {
      hienLoi(phieuError, "Vui lòng thêm ít nhất 1 nguyên liệu vào phiếu.");
      return;
    }

    const body = {
      nha_cung_cap_id: Number(phieuForm.ncc.value),
      ghi_chu: phieuForm.ghi_chu.value.trim(),
      items: items,
    };
    const btn = $("btn-luu-phieu");
    btn.disabled = true;
    const r = phieuDangSua
      ? await apiGoi("PUT", `/api/v1/purchase-receipts/${phieuDangSua.PhieuNhapID}`, body)
      : await apiGoi("POST", "/api/v1/purchase-receipts", body);
    btn.disabled = false;
    if (!r.ok) {
      if (kiemTraHetPhien(r.status)) return;
      hienLoi(phieuError, r.loi);
      return;
    }
    const daSua = Boolean(phieuDangSua);
    dongModal("modal-phieu");
    hienToast(daSua ? "Đã cập nhật phiếu nhập." : "Đã lập phiếu nhập. Tồn kho chỉ tăng sau khi bạn xác nhận đã nhận hàng.");
    if (!daSua) trang = 1;
    tai();
  });

  /* ===================== Xac nhan da nhan hang ===================== */
  function moNhan(p) {
    phieuCho = p;
    anLoi($("nhan-error"));
    $("nhan-gioi-thieu").innerHTML = `Phiếu <strong>${escapeHtml(p.MaPhieuNhap)}</strong> của <strong>${escapeHtml(p.TenNhaCungCap)}</strong>, tổng tiền <strong>${dinhDangGia(p.TongTien)}</strong>. Bạn đã nhận đủ các nguyên liệu dưới đây?`;
    $("nhan-ds").innerHTML = (p.ChiTiet || []).map((c) =>
      `<div class="sum-row"><span>${escapeHtml(c.TenNguyenLieu)}</span><strong>${escapeHtml(dinhDangSoLuong(c.SoLuong, c.DonViTinh))}</strong></div>`).join("");
    $("btn-nhan").disabled = false;
    moModal("modal-nhan");
    $("btn-chua-nhan").focus();
  }

  $("btn-nhan").addEventListener("click", async () => {
    if (!phieuCho) return;
    const btn = $("btn-nhan");
    anLoi($("nhan-error"));
    btn.disabled = true;
    const r = await apiGoi("POST", `/api/v1/purchase-receipts/${phieuCho.PhieuNhapID}/confirm`, {});
    if (!r.ok) {
      if (kiemTraHetPhien(r.status)) return;
      btn.disabled = false;
      hienLoi($("nhan-error"), r.loi);
      tai();
      return;
    }
    dongModal("modal-nhan");
    dongModal("modal-phieu-ct");
    hienToast("Đã nhận hàng. Tồn kho đã được cập nhật.");
    tai();
  });

  /* ===================== Huy phieu ===================== */
  function moHuy(p) {
    phieuCho = p;
    huyForm.reset();
    anLoi($("huy-error"));
    $("huy-gioi-thieu").innerHTML = `Huỷ phiếu <strong>${escapeHtml(p.MaPhieuNhap)}</strong> của <strong>${escapeHtml(p.TenNhaCungCap)}</strong>. Phiếu đã huỷ không thể mở lại.`;
    const canh = $("huy-canh-bao");
    if (phieuNhapDaNhan(p)) {
      canh.textContent = "Phiếu này đã nhận hàng. Tồn kho sẽ bị trừ lại đúng số lượng đã nhập. Nếu hàng đã được dùng nên không đủ để trừ, hệ thống sẽ không cho huỷ.";
      canh.classList.remove("hidden");
    } else {
      canh.classList.add("hidden");
    }
    $("btn-huy").disabled = false;
    moModal("modal-huy");
  }

  huyForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!phieuCho) return;
    anLoi($("huy-error"));
    const lyDo = huyForm.ly_do.value.trim();
    if (!lyDo) {
      hienLoi($("huy-error"), "Vui lòng nhập lý do huỷ phiếu.");
      huyForm.ly_do.focus();
      return;
    }
    const daNhan = phieuNhapDaNhan(phieuCho);
    const btn = $("btn-huy");
    btn.disabled = true;
    const r = await apiGoi("POST", `/api/v1/purchase-receipts/${phieuCho.PhieuNhapID}/cancel`, {ly_do: lyDo});
    btn.disabled = false;
    if (!r.ok) {
      if (kiemTraHetPhien(r.status)) return;
      hienLoi($("huy-error"), r.loi);
      tai();
      return;
    }
    dongModal("modal-huy");
    dongModal("modal-phieu-ct");
    hienToast(daNhan ? "Đã huỷ phiếu. Tồn kho đã được trừ lại." : "Đã huỷ phiếu nhập.");
    tai();
  });

  /* ===================== Su kien chung ===================== */
  tbody.addEventListener("click", async (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    if (b.dataset.xem) {
      xemChiTiet(b.dataset.xem);
    } else if (b.dataset.nhan) {
      b.disabled = true;
      const p = await docPhieu(b.dataset.nhan);
      b.disabled = false;
      if (p) { phieuDangXem = p; moNhan(p); }
    }
  });

  $("pager").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-trang]");
    if (!b || b.disabled) return;
    trang = Number(b.dataset.trang);
    tai();
  });

  const nutLap = $("btn-lap-phieu");
  if (nutLap) {
    if (!duocLapSua) nutLap.classList.add("hidden");
    nutLap.addEventListener("click", async () => {
      nutLap.disabled = true;
      phieuDangSua = null;
      await moForm(null);
      nutLap.disabled = false;
    });
  }

  let timer;
  $("loc-ma").addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(locLai, 300);
  });
  ["loc-tinh-trang", "loc-ncc", "loc-tu-ngay", "loc-den-ngay"].forEach((id) =>
    $(id).addEventListener("change", locLai));

  taiNcc().then(() => tai());
})();
