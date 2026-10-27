/* Hop thoai don hang dung chung cho trang Ban hang va trang Don hang:
   chi tiet don, thu tien, huy don, hoan tien, xem / in hoa don.
   Can main.js nap truoc va templates/orders/_modals.html co trong trang. */
const DonHang = (() => {
  const coQuyen = (q) => (window.QUYEN || []).includes(q);
  const $ = (id) => document.getElementById(id);

  let don = null;           // don dang mo
  let thanhToans = [];      // lich su thanh toan cua don dang mo
  let monBan = null;        // mon dang ban (them nhanh vao don)
  let khiThayDoi = () => {};
  let thanhToanCho = null;  // giao dich dang cho xac nhan (khi xac nhan lai)
  let hoanTienCho = null;   // giao dich dang hoan tien
  let hoaDonDangXem = null;

  function baoLoi(el, text) { el.textContent = text; el.classList.remove("hidden"); }
  function anLoi(el) { el.classList.add("hidden"); }

  async function taiMonBan() {
    if (monBan) return monBan;
    const r = await apiGoi("GET", "/api/v1/menu?dang_ban=1&per_page=100");
    monBan = r.ok ? (r.data.items || []) : [];
    return monBan;
  }

  /* ===================== Chi tiet don ===================== */
  async function moChiTiet(id, onChange) {
    if (onChange) khiThayDoi = onChange;
    if (await taiLaiDon(id)) moModal("modal-order");
  }

  async function taiLaiDon(id) {
    const [rDon, rMon, rTT] = await Promise.all([
      apiGoi("GET", `/api/v1/orders/${id}`),
      apiGoi("GET", `/api/v1/orders/${id}/items`),
      apiGoi("GET", `/api/v1/orders/${id}/payments`),
    ]);
    if (!rDon.ok) {
      if (!kiemTraHetPhien(rDon.status)) hienToast(rDon.loi);
      return false;
    }
    don = rDon.data;
    don.ChiTiet = rMon.ok ? rMon.data : (don.ChiTiet || []);
    thanhToans = rTT.ok ? rTT.data : [];
    if (don.DuocSuaMon && coQuyen("order.manage")) await taiMonBan();
    veChiTiet();
    return true;
  }

  /** Sau moi thao tac: bao ket qua, tai lai don, bao trang ngoai cap nhat. */
  async function sauThayDoi(r, thongBao) {
    if (!r.ok) {
      if (kiemTraHetPhien(r.status)) return false;
      hienToast(r.loi);
      await taiLaiDon(don.DonHangID);
      return false;
    }
    if (thongBao) hienToast(thongBao);
    await taiLaiDon(don.DonHangID);
    khiThayDoi();
    return true;
  }

  function veDongMon(c, suaDuoc) {
    const ten = escapeHtml(c.TenMon);
    const soLuong = suaDuoc ? `
      <span class="stepper">
        <button type="button" data-giam="${c.ChiTietDonHangID}" aria-label="Bớt 1 ${ten}">−</button>
        <span class="qty">${c.SoLuong}</span>
        <button type="button" data-tang="${c.ChiTietDonHangID}" aria-label="Thêm 1 ${ten}">+</button>
      </span>` : c.SoLuong;
    const nutBo = suaDuoc
      ? `<td class="col-num"><button type="button" class="btn-icon danger" data-xoa-dong="${c.ChiTietDonHangID}" aria-label="Bỏ ${ten} khỏi đơn">Bỏ</button></td>`
      : "";
    return `<tr>
      <td><div class="cell-name">${ten}</div>
        <div class="cell-sub">${dinhDangGia(c.DonGia)} / phần</div>
        ${c.GhiChu ? `<div class="cell-sub">Ghi chú: ${escapeHtml(c.GhiChu)}</div>` : ""}</td>
      <td class="col-num">${soLuong}</td>
      <td class="col-num">${dinhDangGia(c.ThanhTien)}</td>
      ${nutBo}
    </tr>`;
  }

  function veThanhToan(p) {
    let nut = "";
    if (thanhToanDangCho(p) && coQuyen("payment.manage")) {
      nut = `<div class="row-actions" style="justify-content:flex-start;margin-top:8px">
        <button type="button" class="btn-icon" data-xac-nhan-tt="${p.ThanhToanID}">Xác nhận đã nhận tiền</button>
        <button type="button" class="btn-icon danger" data-that-bai-tt="${p.ThanhToanID}">Báo không thành công</button>
      </div>`;
    } else if (thanhToanHoanDuoc(p) && coQuyen("payment.refund")) {
      nut = `<div class="row-actions" style="justify-content:flex-start;margin-top:8px">
        <button type="button" class="btn-icon danger" data-hoan-tt="${p.ThanhToanID}">Hoàn tiền</button>
      </div>`;
    }
    const phu = [dinhDangThoiGian(p.ThoiGianThanhToan || p.NgayTao)];
    if (p.MaGiaoDich) phu.push("Mã giao dịch: " + escapeHtml(p.MaGiaoDich));
    if (Number(p.SoTienDaHoan) > 0) phu.push("Đã hoàn " + dinhDangGia(p.SoTienDaHoan));
    return `<div class="pay-item">
      <div class="pay-top">
        <span><strong>${dinhDangGia(p.SoTien)}</strong> · ${escapeHtml(nhanHinhThuc(p.PhuongThuc))}</span>
        ${huyHieuThuTien(p.TrangThai)}
      </div>
      <div class="pay-sub">${phu.join(" · ")}</div>
      ${nut}
    </div>`;
  }

  function veChiTiet() {
    const suaDuoc = don.DuocSuaMon && coQuyen("order.manage");
    $("order-title").textContent = "Đơn " + don.MaDonHang;

    let html = `<div class="order-meta">
      ${huyHieuDon(don.TrangThai)} ${huyHieuThuTien(don.TrangThaiThanhToan)}
      <span class="muted small">${dinhDangThoiGian(don.ThoiGianDat)}${don.NguoiTao ? " · " + escapeHtml(don.NguoiTao) : ""}</span>
    </div>`;
    if (don.LyDoHuy) html += `<div class="note-box danger">Lý do huỷ: ${escapeHtml(don.LyDoHuy)}</div>`;
    if (don.GhiChu) html += `<div class="note-box">Ghi chú: ${escapeHtml(don.GhiChu)}</div>`;

    html += `<table class="line-table">
      <thead><tr><th>Món</th><th class="col-num">SL</th><th class="col-num">Thành tiền</th>${suaDuoc ? "<th></th>" : ""}</tr></thead>
      <tbody>${don.ChiTiet.map((c) => veDongMon(c, suaDuoc)).join("")}</tbody>
    </table>`;

    if (suaDuoc && monBan && monBan.length) {
      html += `<div class="quick-add">
        <select id="quick-mon" aria-label="Chọn món để thêm vào đơn">
          ${monBan.map((m) => `<option value="${m.MonID}">${escapeHtml(m.TenMon)} · ${dinhDangGia(m.GiaBan)}</option>`).join("")}
        </select>
        <input id="quick-sl" type="number" min="1" max="999" value="1" aria-label="Số lượng">
        <button type="button" data-them-nhanh="1">Thêm</button>
      </div>`;
    } else if (!suaDuoc && donConMo(don) && coQuyen("order.manage")) {
      html += `<p class="muted small" style="margin:6px 0 0">${chuaThuTien(don)
        ? "Đơn đã bắt đầu pha chế nên không sửa món được nữa."
        : "Đơn đã thu tiền (hoặc đang chờ xác nhận) nên không sửa món được nữa."}</p>`;
    }

    const giam = Number(don.GiamGia) > 0
      ? `<div class="sum-row"><span>Giảm giá</span><span>−${dinhDangGia(don.GiamGia)}</span></div>` : "";
    html += `<div class="sum-box">
      <div class="sum-row"><span>Tạm tính (${Number(don.SoMon || 0)} món)</span><span>${dinhDangGia(don.TongTien)}</span></div>
      ${giam}
      <div class="sum-row grand"><span>Cần thu</span><span>${dinhDangGia(don.ThanhTien)}</span></div>
    </div>`;

    if (thanhToans.length) {
      html += `<h4 class="sub-title">Thanh toán</h4>${thanhToans.map(veThanhToan).join("")}`;
    }
    $("order-body").innerHTML = html;

    // Nut cuoi hop thoai
    const coThuTien = coQuyen("payment.manage") && chuaThuTien(don) && !donDaHuy(don) && Number(don.ThanhTien) > 0;
    const nut = [];
    if (coQuyen("order.cancel") && donConMo(don)) {
      nut.push(`<button type="button" class="btn-outline" data-hanh-dong="huy">Huỷ đơn</button>`);
    }
    nut.push(`<span class="spacer"></span>`);
    if (daCoHoaDon(don)) {
      nut.push(`<button type="button" class="btn-outline" data-hanh-dong="hoa-don">Xem hoá đơn</button>`);
    }
    const buoc = buocTiepDon(don.TrangThai);
    if (buoc && coQuyen("order.manage")) {
      nut.push(`<button type="button" class="${coThuTien ? "btn-outline" : ""}" data-hanh-dong="buoc">${escapeHtml(buoc.nut)}</button>`);
    }
    if (coThuTien) {
      nut.push(`<button type="button" data-hanh-dong="thu-tien">Thu tiền ${dinhDangGia(don.ThanhTien)}</button>`);
    }
    $("order-foot").innerHTML = nut.join("");
  }

  async function chuyenBuoc(donHang) {
    const buoc = buocTiepDon(donHang.TrangThai);
    if (!buoc) return null;
    const laBuocCuoi = !buocTiepDon(buoc.ma);
    if (laBuocCuoi && chuaThuTien(donHang)
        && !xacNhan(`Đơn ${donHang.MaDonHang} chưa thu tiền. Vẫn đánh dấu hoàn thành?`)) return null;
    const r = await apiGoi("PATCH", `/api/v1/orders/${donHang.DonHangID}/status`, {trang_thai: buoc.ma});
    if (r.ok) hienToast(`Đơn ${donHang.MaDonHang}: ${nhanTinhTrangDon(buoc.ma)}.`);
    return r;
  }

  async function xoaDong(c) {
    if (don.ChiTiet.length <= 1) {
      hienToast("Đơn cần còn ít nhất 1 món. Nếu khách không lấy nữa, hãy huỷ đơn.");
      return;
    }
    if (!xacNhan(`Bỏ "${c.TenMon}" khỏi đơn?`)) return;
    await sauThayDoi(
      await apiGoi("DELETE", `/api/v1/orders/${don.DonHangID}/items/${c.ChiTietDonHangID}`),
      `Đã bỏ ${c.TenMon} khỏi đơn.`);
  }

  async function xuLyClickDon(e) {
    const b = e.target.closest("button");
    if (!b || !don) return;
    const ds = b.dataset;

    if (ds.tang || ds.giam) {
      const c = don.ChiTiet.find((x) => String(x.ChiTietDonHangID) === (ds.tang || ds.giam));
      if (!c) return;
      const moi = c.SoLuong + (ds.tang ? 1 : -1);
      if (moi < 1) { await xoaDong(c); return; }
      const items = don.ChiTiet.map((x) => ({
        chi_tiet_id: x.ChiTietDonHangID,
        mon_id: x.MonID,
        so_luong: x === c ? moi : x.SoLuong,
        ghi_chu: x.GhiChu || "",
      }));
      b.disabled = true;
      await sauThayDoi(await apiGoi("PUT", `/api/v1/orders/${don.DonHangID}/items`, {items}));
      return;
    }
    if (ds.xoaDong) {
      const c = don.ChiTiet.find((x) => String(x.ChiTietDonHangID) === ds.xoaDong);
      if (c) await xoaDong(c);
      return;
    }
    if (ds.themNhanh) {
      const soLuong = Number($("quick-sl").value);
      if (!Number.isInteger(soLuong) || soLuong < 1 || soLuong > 999) {
        hienToast("Số lượng phải là số nguyên từ 1 đến 999.");
        return;
      }
      b.disabled = true;
      await sauThayDoi(
        await apiGoi("POST", `/api/v1/orders/${don.DonHangID}/items`,
          {mon_id: Number($("quick-mon").value), so_luong: soLuong}),
        "Đã thêm món vào đơn.");
      return;
    }
    if (ds.xacNhanTt) {
      moThuTien(thanhToans.find((p) => String(p.ThanhToanID) === ds.xacNhanTt));
      return;
    }
    if (ds.thatBaiTt) {
      if (!xacNhan("Đánh dấu lần thu tiền này là không thành công? Bạn có thể thu lại sau.")) return;
      await sauThayDoi(
        await apiGoi("POST", `/api/v1/payments/${ds.thatBaiTt}/confirm`, {thanh_cong: false}),
        "Đã ghi nhận thu tiền không thành công.");
      return;
    }
    if (ds.hoanTt) { moHoanTien(ds.hoanTt); return; }

    switch (ds.hanhDong) {
      case "buoc": {
        b.disabled = true;
        const r = await chuyenBuoc(don);
        b.disabled = false;
        if (r) await sauThayDoi(r);
        break;
      }
      case "thu-tien": moThuTien(null); break;
      case "huy": moHuyDon(); break;
      case "hoa-don": xemHoaDonCuaDon(don.DonHangID); break;
    }
  }

  /* ===================== Thu tien ===================== */
  const payForm = $("pay-form");
  const payError = $("pay-error");

  $("pay-methods").insertAdjacentHTML("beforeend", luaChonHinhThuc().map((h) => `
    <label class="method-option"><input type="radio" name="phuong_thuc" value="${h.ma}"> ${escapeHtml(h.nhan)}</label>`).join(""));

  function goiYTienMat(can) {
    const s = new Set([can]);
    for (const buoc of [10000, 50000, 100000, 200000, 500000]) s.add(Math.ceil(can / buoc) * buoc);
    return [...s].filter((x) => x >= can).sort((a, b) => a - b).slice(0, 5);
  }

  function capNhatHinhThuc() {
    const pt = payForm.phuong_thuc.value;
    const tienMat = !canMaGiaoDich(pt);
    $("pay-cash").classList.toggle("hidden", !tienMat);
    $("pay-code").classList.toggle("hidden", tienMat);
  }

  function capNhatTienThoi() {
    const can = Number(don.ThanhTien);
    const raw = payForm.tien_khach_dua.value;
    const dua = Number(raw || 0);
    const row = $("pay-change");
    const thieu = raw !== "" && dua < can;
    row.classList.toggle("thieu", thieu);
    row.querySelector("span").textContent = thieu ? "Còn thiếu" : "Tiền thối lại";
    row.querySelector("strong").textContent = dinhDangGia(raw === "" ? 0 : Math.abs(dua - can));
  }

  /** pending: giao dich dang cho xac nhan (null = thu tien moi). */
  function moThuTien(pending) {
    thanhToanCho = pending || null;
    payForm.reset();
    anLoi(payError);
    const can = Number(don.ThanhTien);
    $("pay-title").textContent = pending ? "Xác nhận thu tiền" : "Thu tiền";
    $("pay-order").textContent = "Cần thu · Đơn " + don.MaDonHang;
    $("pay-amount").textContent = dinhDangGia(can);
    payForm.querySelectorAll('input[name="phuong_thuc"]').forEach((r, i) => {
      r.checked = pending ? r.value === pending.PhuongThuc : i === 0;
      r.disabled = Boolean(pending);
    });
    if (pending && pending.MaGiaoDich) payForm.ma_giao_dich.value = pending.MaGiaoDich;
    $("pay-quick").innerHTML = goiYTienMat(can).map((x) =>
      `<button type="button" class="btn-icon" data-tien="${x}">${dinhDangGia(x)}</button>`).join("");
    capNhatHinhThuc();
    capNhatTienThoi();
    moModal("modal-pay");
  }

  payForm.addEventListener("change", (e) => {
    if (e.target.name === "phuong_thuc") capNhatHinhThuc();
  });
  payForm.tien_khach_dua.addEventListener("input", capNhatTienThoi);
  $("pay-quick").addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    payForm.tien_khach_dua.value = b.dataset.tien;
    capNhatTienThoi();
  });

  payForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    anLoi(payError);
    const pt = payForm.phuong_thuc.value;
    const ma = payForm.ma_giao_dich.value.trim();
    const can = Number(don.ThanhTien);
    if (!pt) { baoLoi(payError, "Vui lòng chọn hình thức thanh toán."); return; }
    if (canMaGiaoDich(pt) && !ma) {
      baoLoi(payError, "Vui lòng nhập mã giao dịch ngân hàng để đối soát.");
      payForm.ma_giao_dich.focus();
      return;
    }
    const dua = payForm.tien_khach_dua.value;
    if (!canMaGiaoDich(pt) && dua !== "" && Number(dua) < can) {
      baoLoi(payError, "Khách đưa chưa đủ tiền.");
      return;
    }

    const btn = $("btn-pay");
    btn.disabled = true;
    let thanhToanId = thanhToanCho && thanhToanCho.ThanhToanID;
    if (!thanhToanId) {
      const r1 = await apiGoi("POST", "/api/v1/payments",
        {don_hang_id: don.DonHangID, phuong_thuc: pt, so_tien: can});
      if (!r1.ok) {
        btn.disabled = false;
        if (kiemTraHetPhien(r1.status)) return;
        baoLoi(payError, r1.loi);
        return;
      }
      thanhToanId = r1.data.ThanhToanID;
    }
    const r2 = await apiGoi("POST", `/api/v1/payments/${thanhToanId}/confirm`,
      {thanh_cong: true, ma_giao_dich: ma || undefined});
    btn.disabled = false;
    if (!r2.ok) {
      if (kiemTraHetPhien(r2.status)) return;
      baoLoi(payError, r2.loi);
      // Giao dich da tao nhung chua xac nhan duoc -> hien o lich su de xac nhan lai.
      await taiLaiDon(don.DonHangID);
      thanhToanCho = thanhToans.find((p) => p.ThanhToanID === thanhToanId) || null;
      return;
    }
    dongModal("modal-pay");
    hienToast("Đã thu tiền. Hoá đơn đã được lập.");
    await taiLaiDon(don.DonHangID);
    khiThayDoi();
    if (r2.data.HoaDon) xemHoaDon(r2.data.HoaDon.HoaDonID);
  });

  /* ===================== Huy don ===================== */
  const cancelForm = $("cancel-form");
  const cancelError = $("cancel-error");
  const LY_DO_NHANH = ["Khách đổi ý", "Hết nguyên liệu", "Nhập nhầm đơn", "Khách chờ lâu quá"];

  $("cancel-reasons").innerHTML = LY_DO_NHANH.map((t) =>
    `<button type="button" class="btn-icon" data-ly-do="${escapeHtml(t)}">${escapeHtml(t)}</button>`).join("");
  $("cancel-reasons").addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (b) { cancelForm.ly_do.value = b.dataset.lyDo; cancelForm.ly_do.focus(); }
  });

  function soTienConHoan() {
    return thanhToans.filter(thanhToanHoanDuoc)
      .reduce((s, p) => s + Number(p.SoTien) - Number(p.SoTienDaHoan || 0), 0);
  }

  function moHuyDon() {
    cancelForm.reset();
    anLoi(cancelError);
    $("cancel-title").textContent = "Huỷ đơn " + don.MaDonHang;
    const box = $("cancel-refund");
    const btn = $("btn-cancel");
    btn.disabled = false;
    btn.textContent = "Huỷ đơn";
    box.className = "note-box hidden";
    if (donConGiuTien(don)) {
      const conLai = soTienConHoan();
      if (coQuyen("payment.refund")) {
        box.className = "note-box";
        box.textContent = `Đơn đã thu tiền. Khi huỷ, hệ thống sẽ ghi nhận hoàn lại ${dinhDangGia(conLai)} cho khách.`;
        btn.textContent = "Huỷ đơn và hoàn tiền";
      } else {
        box.className = "note-box danger";
        box.textContent = "Đơn đã thu tiền nên cần hoàn tiền cho khách khi huỷ. Vui lòng nhờ quản lý huỷ đơn này.";
        btn.disabled = true;
      }
    }
    moModal("modal-cancel");
  }

  cancelForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    anLoi(cancelError);
    const lyDo = cancelForm.ly_do.value.trim();
    if (!lyDo) { baoLoi(cancelError, "Vui lòng nhập lý do huỷ đơn."); return; }
    const btn = $("btn-cancel");
    btn.disabled = true;
    const r = await apiGoi("POST", `/api/v1/orders/${don.DonHangID}/cancel`,
      {ly_do: lyDo, hoan_tien: donConGiuTien(don)});
    btn.disabled = false;
    if (!r.ok) {
      if (kiemTraHetPhien(r.status)) return;
      baoLoi(cancelError, r.loi);
      return;
    }
    dongModal("modal-cancel");
    await sauThayDoi(r, `Đã huỷ đơn ${don.MaDonHang}.`);
  });

  /* ===================== Hoan tien ===================== */
  const refundForm = $("refund-form");
  const refundError = $("refund-error");

  async function moHoanTien(thanhToanId) {
    const r = await apiGoi("GET", `/api/v1/payments/${thanhToanId}`);
    if (!r.ok) { if (!kiemTraHetPhien(r.status)) hienToast(r.loi); return; }
    hoanTienCho = r.data;
    const daThu = Number(hoanTienCho.SoTien);
    const daHoan = Number(hoanTienCho.SoTienDaHoan || 0);
    const conLai = daThu - daHoan;
    refundForm.reset();
    anLoi(refundError);
    $("refund-info").innerHTML = `
      <div class="sum-row"><span>Đã thu (${escapeHtml(nhanHinhThuc(hoanTienCho.PhuongThuc))})</span><span>${dinhDangGia(daThu)}</span></div>
      <div class="sum-row"><span>Đã hoàn trước đó</span><span>${dinhDangGia(daHoan)}</span></div>
      <div class="sum-row grand"><span>Còn có thể hoàn</span><span>${dinhDangGia(conLai)}</span></div>`;
    refundForm.so_tien.value = conLai;
    refundForm.so_tien.max = conLai;
    $("refund-code-wrap").classList.toggle("hidden", !canMaGiaoDich(hoanTienCho.PhuongThuc));
    moModal("modal-refund");
  }

  refundForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    anLoi(refundError);
    const conLai = Number(hoanTienCho.SoTien) - Number(hoanTienCho.SoTienDaHoan || 0);
    const soTien = Number(refundForm.so_tien.value);
    const lyDo = refundForm.ly_do.value.trim();
    if (!(soTien > 0)) { baoLoi(refundError, "Số tiền hoàn phải lớn hơn 0."); return; }
    if (soTien > conLai) { baoLoi(refundError, `Chỉ hoàn được tối đa ${dinhDangGia(conLai)}.`); return; }
    if (!lyDo) { baoLoi(refundError, "Vui lòng nhập lý do hoàn tiền."); return; }
    if (!xacNhan(`Hoàn ${dinhDangGia(soTien)} cho khách?`)) return;

    const btn = $("btn-refund");
    btn.disabled = true;
    const r = await apiGoi("POST", `/api/v1/payments/${hoanTienCho.ThanhToanID}/refund`, {
      so_tien: soTien,
      ly_do: lyDo,
      ma_giao_dich_hoan: refundForm.ma_giao_dich_hoan.value.trim() || undefined,
    });
    btn.disabled = false;
    if (!r.ok) {
      if (kiemTraHetPhien(r.status)) return;
      baoLoi(refundError, r.loi);
      return;
    }
    dongModal("modal-refund");
    await sauThayDoi(r, `Đã hoàn ${dinhDangGia(soTien)} cho khách.`);
  });

  /* ===================== Hoa don ===================== */
  function veHoaDon(hd) {
    const dong = (hd.ChiTiet || []).map((c) => `
      <div>${escapeHtml(c.TenMon)}</div>
      ${c.GhiChu ? `<div class="r-item-sub">(${escapeHtml(c.GhiChu)})</div>` : ""}
      <div class="r-row r-item-sub"><span>${c.SoLuong} x ${dinhDangGia(c.DonGia)}</span><span>${dinhDangGia(c.ThanhTien)}</span></div>`).join("");
    const tt = hd.ThanhToan;
    const hoan = Number(hd.SoTienDaHoan || 0);
    return `
      <div class="r-center r-shop">Cà Phê Việt</div>
      <div class="r-center">HOÁ ĐƠN THANH TOÁN</div>
      <div class="r-line"></div>
      <div class="r-row"><span>Số hoá đơn</span><span>${escapeHtml(hd.MaHoaDon)}</span></div>
      <div class="r-row"><span>Đơn hàng</span><span>${escapeHtml(hd.MaDonHang)}</span></div>
      <div class="r-row"><span>Thời gian</span><span>${dinhDangThoiGian(hd.NgayLap)}</span></div>
      ${hd.NguoiTao ? `<div class="r-row"><span>Thu ngân</span><span>${escapeHtml(hd.NguoiTao)}</span></div>` : ""}
      <div class="r-line"></div>
      ${dong}
      <div class="r-line"></div>
      <div class="r-row"><span>Tạm tính</span><span>${dinhDangGia(hd.TongTien)}</span></div>
      ${Number(hd.GiamGia) > 0 ? `<div class="r-row"><span>Giảm giá</span><span>−${dinhDangGia(hd.GiamGia)}</span></div>` : ""}
      <div class="r-row r-grand"><span>TỔNG CỘNG</span><span>${dinhDangGia(hd.ThanhTien)}</span></div>
      ${tt ? `<div class="r-row"><span>Hình thức</span><span>${escapeHtml(nhanHinhThuc(tt.PhuongThuc))}</span></div>` : ""}
      ${hoan > 0 ? `<div class="r-row"><span>Đã hoàn lại</span><span>${dinhDangGia(hoan)}</span></div>` : ""}
      <div class="r-row"><span>Tình trạng</span><span>${escapeHtml(nhanHoaDon(hd.TrangThai))}</span></div>
      <div class="r-line"></div>
      <div class="r-center">Cảm ơn quý khách. Hẹn gặp lại!</div>`;
  }

  function hienHoaDon(r) {
    if (!r.ok) { if (!kiemTraHetPhien(r.status)) hienToast(r.loi); return; }
    hoaDonDangXem = r.data;
    $("invoice-title").textContent = "Hoá đơn " + hoaDonDangXem.MaHoaDon;
    $("invoice-body").innerHTML = veHoaDon(hoaDonDangXem);
    moModal("modal-invoice");
  }

  async function xemHoaDon(hoaDonId) {
    hienHoaDon(await apiGoi("GET", `/api/v1/invoices/${hoaDonId}`));
  }

  async function xemHoaDonCuaDon(donHangId) {
    hienHoaDon(await apiGoi("GET", `/api/v1/orders/${donHangId}/invoice`));
  }

  /** In qua khung an trong trang: khong mo tab moi, khong lo duong dan he thong. */
  function inHoaDon(hoaDonId) {
    let f = $("print-frame");
    if (!f) {
      f = document.createElement("iframe");
      f.id = "print-frame";
      f.title = "Bản in hoá đơn";
      f.setAttribute("aria-hidden", "true");
      f.tabIndex = -1;
      f.style.cssText = "position:fixed;right:0;bottom:0;width:0;height:0;border:0;";
      document.body.appendChild(f);
    }
    f.onload = () => {
      try {
        f.contentWindow.focus();
        f.contentWindow.print();
      } catch (e) {
        hienToast("Chưa in được hoá đơn. Vui lòng thử lại.");
      }
    };
    f.src = `/api/v1/invoices/${hoaDonId}/print?t=${Date.now()}`;
  }

  $("btn-print").addEventListener("click", () => {
    if (hoaDonDangXem) inHoaDon(hoaDonDangXem.HoaDonID);
  });

  /* ===================== Gan su kien ===================== */
  $("modal-order").addEventListener("click", xuLyClickDon);

  return {
    coQuyen,
    moChiTiet,
    chuyenBuoc,
    xemHoaDon,
    /** Mo don roi mo luon hop thoai thu tien (dung sau khi tao don). */
    async moVaThuTien(id, onChange) {
      await moChiTiet(id, onChange);
      if (don && chuaThuTien(don) && coQuyen("payment.manage")) moThuTien(null);
    },
  };
})();
