/* Tien ich dung chung cho cac trang kho + trang "Nguyen lieu va ton kho".
   Can main.js nap truoc. Trang "Cong thuc pha che" (cong_thuc.js) cung dung doi tuong Kho o day.
   Khong viet truc tiep ma he thong: tinh trang kho / don hang lay qua ham trong main.js. */

/* Cau dien giai loi rieng cua phan kho (dau hieu = doan thong bao khong dau viet thuong).
   Dat cu the truoc, chung sau; main.js xet bang rieng truoc bang chung. */
DIEN_GIAI_LOI_RIENG.push(
  ["ten nguyen lieu da ton tai", "Tên nguyên liệu này đã có trong kho. Vui lòng dùng tên khác."],
  ["ten nguyen lieu la bat buoc", "Vui lòng nhập tên nguyên liệu."],
  ["ten nguyen lieu khong hop le", "Tên nguyên liệu chưa hợp lệ."],
  ["don vi tinh la bat buoc", "Vui lòng nhập đơn vị tính, ví dụ g, ml hoặc cái."],
  ["khong the doi don vi tinh", "Nguyên liệu đã có lịch sử kho hoặc nằm trong công thức nên không đổi được đơn vị tính."],
  ["don vi tinh khong hop le", "Đơn vị tính chưa hợp lệ."],
  ["muc ton toi thieu khong hop le", "Mức tồn tối thiểu chưa hợp lệ. Vui lòng nhập số từ 0 trở lên."],
  ["so luong ton ban dau khong hop le", "Số lượng tồn ban đầu chưa hợp lệ. Vui lòng nhập số từ 0 trở lên."],
  ["du lieu nguyen lieu khong hop le", "Thông tin nguyên liệu chưa hợp lệ."],
  ["nguyen lieu khong ton tai", "Không tìm thấy nguyên liệu này. Vui lòng tải lại trang."],
  ["nguyen lieu khong hop le", "Vui lòng chọn nguyên liệu."],
  ["da ngung dung", "Có nguyên liệu đã ngừng dùng nên không thêm mới vào công thức được."],
  ["thieu truong dang_dung", "Chưa lưu được tình trạng sử dụng. Vui lòng thử lại."],
  ["dang_dung phai la", "Chưa lưu được tình trạng sử dụng. Vui lòng thử lại."],
  ["tinh trang kho khong hop le", "Bộ lọc chưa hợp lệ. Vui lòng tải lại trang."],
  ["trang thai khong hop le", "Bộ lọc chưa hợp lệ. Vui lòng tải lại trang."],
  ["loai giao dich kho khong hop le", "Loại thay đổi kho chưa hợp lệ."],
  ["loai giao dich khong hop le", "Loại thay đổi kho chưa hợp lệ."],
  ["khoang ngay khong hop le", "Ngày bắt đầu phải trước hoặc cùng ngày kết thúc."],
  ["so luong thuc te khong hop le", "Số lượng đếm được chưa hợp lệ. Vui lòng nhập số từ 0 trở lên."],
  ["ly do la bat buoc", "Vui lòng nhập lý do."],
  ["ton kho khong thay doi", "Số đếm bằng với tồn kho hiện tại nên không cần điều chỉnh."],
  ["so luong xuat phai lon hon 0", "Số lượng xuất phải lớn hơn 0."],
  ["ton kho khong du", "Tồn kho không đủ cho thao tác này. Vui lòng kiểm tra lại số lượng tồn."],
  ["so luong thay doi phai khac 0", "Số lượng thay đổi phải khác 0."],
  ["chieu thay doi khong khop", "Chiều thay đổi không khớp với loại thao tác."],
  ["danh sach nguyen lieu khong hop le", "Danh sách nguyên liệu chưa hợp lệ. Vui lòng tải lại trang."],
  ["cong thuc toi da", "Một công thức có tối đa 100 nguyên liệu."],
  ["so luong can phai lon hon 0", "Định lượng mỗi nguyên liệu phải lớn hơn 0 và không quá 1.000.000."],
  ["nguyen lieu bi trung", "Mỗi nguyên liệu chỉ được xuất hiện một lần trong công thức."],
  ["he thong dang ban", "Hệ thống đang bận. Vui lòng thử lại sau ít giây."],
  ["don hang khong hop le", "Vui lòng chọn đơn cần trừ kho."],
  ["don hang da huy, khong the tru kho", "Đơn đã huỷ nên không trừ kho được."],
  ["don hang chua o buoc pha che", "Đơn chưa bắt đầu pha chế nên chưa trừ kho được."],
  ["don nay da duoc tru kho", "Đơn này đã được trừ kho trước đó."],
  ["khong co mon nao co cong thuc", "Các món trong đơn chưa có công thức nên không có gì để trừ. Hãy bổ sung công thức trước."],
);

const Kho = (() => {
  const $ = (id) => document.getElementById(id);
  const coQuyen = (q) => (window.QUYEN || []).includes(q);

  function hienLoi(el, text) { el.textContent = text; el.classList.remove("hidden"); }
  function anLoi(el) { el.textContent = ""; el.classList.add("hidden"); }

  /** Mo hop thoai; neu khong co o nhap thi dua tieu diem vao nut Dong. */
  function mo(id) {
    moModal(id);
    const m = $(id);
    if (m && !m.querySelector("input, select, textarea")) {
      setTimeout(() => { const n = m.querySelector(".modal-close"); if (n) n.focus(); }, 40);
    }
  }

  /** Doc o nhap so luong: toi da 3 so le. Tra {chuoi, so} hoac {loi}. */
  function docSo(text, opt) {
    const o = Object.assign({nhan: "Số lượng", toiDa: 1000000000, lonHonKhong: false}, opt || {});
    const s = String(text == null ? "" : text).trim();
    if (!s) return {loi: `Vui lòng nhập ${o.nhan.toLowerCase()}.`};
    if (s.startsWith("-")) return {loi: `${o.nhan} không được là số âm.`};
    if (!/^\d+(\.\d{1,3})?$/.test(s)) return {loi: `${o.nhan} chỉ gồm chữ số và tối đa 3 số lẻ.`};
    const so = Number(s);
    if (o.lonHonKhong && so <= 0) return {loi: `${o.nhan} phải lớn hơn 0.`};
    if (so > o.toiDa) return {loi: `${o.nhan} không được vượt quá ${o.toiDa.toLocaleString("vi-VN")}.`};
    return {chuoi: s, so: so};
  }

  /** Tai het nguyen lieu (nhieu trang). tinhTrang: "" = tat ca, "active" = dang dung. */
  async function taiNguyenLieu(tinhTrang) {
    const ds = [];
    for (let trang = 1; trang <= 10; trang++) {
      const p = new URLSearchParams({page: trang, per_page: 100});
      if (tinhTrang) p.set("status", tinhTrang);
      const r = await apiGoi("GET", "/api/v1/ingredients?" + p.toString());
      if (!r.ok) return r;
      ds.push(...r.data.items);
      if (ds.length >= r.data.total || !r.data.items.length) break;
    }
    return {ok: true, data: ds};
  }

  /** Phan trang: dung chung bo nut Truoc / Sau. */
  function veTrang(el, trang, total, soDong, donVi) {
    const soTrang = Math.max(1, Math.ceil(total / soDong));
    const tong = total.toLocaleString("vi-VN");
    if (total <= soDong) {
      el.innerHTML = total ? `<span class="muted">${tong} ${donVi}</span>` : "";
      return;
    }
    el.innerHTML = `
      <span class="muted">Trang ${trang}/${soTrang} · ${tong} ${donVi}</span>
      <button type="button" class="btn-outline" data-trang="${trang - 1}" aria-label="Trang trước" ${trang <= 1 ? "disabled" : ""}>‹ Trước</button>
      <button type="button" class="btn-outline" data-trang="${trang + 1}" aria-label="Trang sau" ${trang >= soTrang ? "disabled" : ""}>Sau ›</button>`;
  }

  /** Goi y ly do: bam chip la dien vao o ly do. */
  function goiYLyDo(khung, o, ds) {
    khung.innerHTML = ds.map((t) =>
      `<button type="button" class="chip" data-ly-do="${escapeHtml(t)}">${escapeHtml(t)}</button>`).join("");
    khung.addEventListener("click", (e) => {
      const b = e.target.closest("button[data-ly-do]");
      if (!b) return;
      o.value = b.dataset.lyDo;
      o.focus();
    });
  }

  /** So luong thay doi co dau: +5 g / -5 g. */
  function chuoiThayDoi(gd) {
    const n = Number(gd.SoLuongThayDoi);
    return (n > 0 ? "+" : "") + dinhDangSoLuong(n, gd.DonViTinh);
  }

  /** Bao loi sau khi goi that bai; tra true neu da bi dua ve trang dang nhap. */
  function hetPhien(r) { return kiemTraHetPhien(r.status); }

  return {$, coQuyen, hienLoi, anLoi, mo, docSo, taiNguyenLieu, veTrang, goiYLyDo, chuoiThayDoi, hetPhien};
})();


/* =========================================================
   Trang "Nguyen lieu va ton kho"
   ========================================================= */
(function trangTonKho() {
  const $ = Kho.$;
  if (!$("trang-ton-kho")) return;

  const quanLy = Kho.coQuyen("inventory.manage");
  const SO_DONG = 20;
  // Thu tu trong main.js: du dung, sap het, het hang; thu tu don: moi, cho, dang pha, xong, huy.
  const [, MA_SAP, MA_HET] = luaChonTinhTrangKho().map((t) => t.ma);
  const [, , MA_DON_PHA, MA_DON_XONG] = luaChonTinhTrangDon().map((t) => t.ma);

  const tbodyTon = document.querySelector("#bang-ton tbody");
  const tbodyLs = document.querySelector("#bang-ls tbody");
  const loiTon = $("tk-loi-trang");
  const loiLs = $("ls-loi-trang");

  let tab = "ton-kho";
  let trangTon = 1;
  let trangLs = 1;
  let dsTon = [];
  let nlDangXem = null;
  let lichSuCu = true;
  let dsNlLichSu = null;
  let seqTon = 0;

  /* ---------- Lua chon loc ---------- */
  $("tk-loc").insertAdjacentHTML("beforeend",
    luaChonTinhTrangKho().map((t) => `<option value="${t.ma}">${escapeHtml(t.nhan)}</option>`).join(""));
  $("ls-loai").insertAdjacentHTML("beforeend",
    luaChonLoaiGiaoDichKho().map((t) => `<option value="${t.ma}">${escapeHtml(t.nhan)}</option>`).join(""));

  /* ---------- Tab ---------- */
  function chonTab(ten) {
    tab = ten;
    document.querySelectorAll("#trang-ton-kho .tab").forEach((t) => {
      const dang = t.dataset.tab === ten;
      t.classList.toggle("active", dang);
      t.setAttribute("aria-selected", dang ? "true" : "false");
    });
    $("tab-ton-kho").classList.toggle("hidden", ten !== "ton-kho");
    $("tab-lich-su").classList.toggle("hidden", ten !== "lich-su");
    if (ten === "lich-su" && lichSuCu) napLichSu();
  }
  document.querySelectorAll("#trang-ton-kho .tab").forEach((t) =>
    t.addEventListener("click", () => chonTab(t.dataset.tab)));

  /* ---------- Thong ke + canh bao ---------- */
  function veCanhBao(ds) {
    const box = $("kho-canh-bao");
    if (!ds.length) { box.classList.add("hidden"); return; }
    const sap = ds.filter((n) => n.TinhTrangKho === MA_SAP).length;
    const het = ds.filter((n) => n.TinhTrangKho === MA_HET).length;
    const can = ds.slice(0, 5).map((n) =>
      `${escapeHtml(n.TenNguyenLieu)} (${escapeHtml(dinhDangSoLuong(n.CanNhapThem, n.DonViTinh))})`).join(", ");
    const nut = [];
    if (sap) nut.push(`<button type="button" class="btn-outline" data-loc-nhanh="${MA_SAP}">Xem ${sap} nguyên liệu sắp hết</button>`);
    if (het) nut.push(`<button type="button" class="btn-outline" data-loc-nhanh="${MA_HET}">Xem ${het} nguyên liệu đã hết</button>`);
    box.innerHTML = `
      <div>
        <div>Có ${ds.length.toLocaleString("vi-VN")} nguyên liệu sắp hết hoặc đã hết hàng.</div>
        <div class="small" style="font-weight:500">Nên nhập thêm: ${can}${ds.length > 5 ? " và một số nguyên liệu khác" : ""}.</div>
      </div>
      <div class="kho-canh-bao-nut">${nut.join("")}</div>`;
    box.classList.remove("hidden");
  }

  async function taiThongKe() {
    const [rTong, rThap] = await Promise.all([
      apiGoi("GET", "/api/v1/inventory?status=active&per_page=1"),
      apiGoi("GET", "/api/v1/inventory/low-stock"),
    ]);
    if (Kho.hetPhien(rTong) || Kho.hetPhien(rThap)) return;
    $("tk-tong").textContent = rTong.ok ? rTong.data.total.toLocaleString("vi-VN") : "—";
    if (rThap.ok) {
      const ds = rThap.data;
      $("tk-sap").textContent = ds.filter((n) => n.TinhTrangKho === MA_SAP).length.toLocaleString("vi-VN");
      $("tk-het").textContent = ds.filter((n) => n.TinhTrangKho === MA_HET).length.toLocaleString("vi-VN");
      veCanhBao(ds);
    } else {
      $("tk-sap").textContent = "—";
      $("tk-het").textContent = "—";
    }
  }

  /* ---------- Bang ton kho ---------- */
  function trongTon(text) {
    tbodyTon.innerHTML = `<tr class="empty-row"><td colspan="5">${escapeHtml(text)}</td></tr>`;
  }

  function dongTon(n) {
    const dangDung = Boolean(n.TrangThai);
    const ten = escapeHtml(n.TenNguyenLieu);
    const nut = quanLy ? `
      <button type="button" class="btn-icon" data-hd="sua" data-id="${n.NguyenLieuID}" aria-label="Sửa ${ten}">Sửa</button>
      <button type="button" class="btn-icon" data-hd="kiem-ke" data-id="${n.NguyenLieuID}" aria-label="Kiểm kê ${ten}">Kiểm kê</button>
      <button type="button" class="btn-icon" data-hd="xuat" data-id="${n.NguyenLieuID}" aria-label="Xuất kho ${ten}">Xuất kho</button>
      <button type="button" class="btn-icon ${dangDung ? "danger" : ""}" data-hd="doi" data-id="${n.NguyenLieuID}"
        aria-label="${dangDung ? "Ngừng dùng" : "Dùng lại"} ${ten}">${dangDung ? "Ngừng dùng" : "Dùng lại"}</button>` : "";
    return `<tr data-id="${n.NguyenLieuID}">
      <td><div class="cell-name">${ten}${dangDung ? "" : ' <span class="badge badge-muted">Đã ngừng dùng</span>'}</div>
        <div class="cell-sub">Tính theo ${escapeHtml(n.DonViTinh)}</div></td>
      <td class="col-num">${escapeHtml(dinhDangSoLuong(n.SoLuongTon, n.DonViTinh))}</td>
      <td class="col-num">${escapeHtml(dinhDangSoLuong(n.MucTonToiThieu, n.DonViTinh))}</td>
      <td>${huyHieuKho(n.TinhTrangKho)}</td>
      <td class="col-actions"><div class="row-actions">
        <button type="button" class="btn-icon" data-hd="xem" data-id="${n.NguyenLieuID}" aria-label="Xem chi tiết ${ten}">Chi tiết</button>
        ${nut}
      </div></td>
    </tr>`;
  }

  async function taiTonKho() {
    const seq = ++seqTon;
    Kho.anLoi(loiTon);
    const p = new URLSearchParams({page: trangTon, per_page: SO_DONG});
    const q = $("tk-tim").value.trim();
    if (q) p.set("q", q);
    if ($("tk-loc").value) p.set("tinh_trang", $("tk-loc").value);
    p.set("status", $("tk-ca-ngung").checked ? "all" : "active");
    const r = await apiGoi("GET", "/api/v1/inventory?" + p.toString());
    if (seq !== seqTon) return;
    if (!r.ok) {
      if (Kho.hetPhien(r)) return;
      Kho.hienLoi(loiTon, thongBaoLoi(r.status, "danh sách tồn kho"));
      trongTon("Không có dữ liệu để hiển thị.");
      $("tk-trang").innerHTML = "";
      return;
    }
    dsTon = r.data.items;
    if (!dsTon.length) {
      const dangLoc = q || $("tk-loc").value;
      trongTon(dangLoc ? "Không có nguyên liệu nào phù hợp." : "Chưa có nguyên liệu nào. Bấm “Thêm nguyên liệu” để bắt đầu.");
    } else {
      tbodyTon.innerHTML = dsTon.map(dongTon).join("");
    }
    Kho.veTrang($("tk-trang"), trangTon, r.data.total, SO_DONG, "nguyên liệu");
  }

  function locLaiTon() { trangTon = 1; taiTonKho(); }

  let henGio;
  $("tk-tim").addEventListener("input", () => { clearTimeout(henGio); henGio = setTimeout(locLaiTon, 300); });
  $("tk-loc").addEventListener("change", locLaiTon);
  $("tk-ca-ngung").addEventListener("change", locLaiTon);
  $("tk-trang").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-trang]");
    if (!b || b.disabled) return;
    trangTon = Number(b.dataset.trang);
    taiTonKho();
  });

  $("kho-canh-bao").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-loc-nhanh]");
    if (!b) return;
    chonTab("ton-kho");
    $("tk-loc").value = b.dataset.locNhanh;
    locLaiTon();
    $("bang-ton").scrollIntoView({block: "start", behavior: "smooth"});
  });

  tbodyTon.addEventListener("click", (e) => {
    if (e.target.closest("button")) return;
    const tr = e.target.closest("tr[data-id]");
    if (tr) moChiTiet(tr.dataset.id);
  });

  function lamMoi() {
    lichSuCu = true;
    dsNlLichSu = null;
    taiTonKho();
    taiThongKe();
    if (tab === "lich-su") napLichSu();
  }

  function timNl(id) {
    const n = dsTon.find((x) => String(x.NguyenLieuID) === String(id));
    if (n) return n;
    return nlDangXem && String(nlDangXem.NguyenLieuID) === String(id) ? nlDangXem : null;
  }

  /* ---------- Chi tiet 1 nguyen lieu ---------- */
  async function moChiTiet(id) {
    const r = await apiGoi("GET", `/api/v1/inventory/ingredients/${id}`);
    if (!r.ok) {
      if (Kho.hetPhien(r)) return;
      hienToast(r.loi);
      return;
    }
    const n = r.data;
    nlDangXem = n;
    const dangDung = Boolean(n.TrangThai);
    const gd = n.GiaoDichGanNhat || [];
    $("ct-tieu-de").textContent = n.TenNguyenLieu;
    $("ct-noi-dung").innerHTML = `
      <dl class="detail-list">
        <div class="detail-row"><dt>Tồn hiện tại</dt><dd>${escapeHtml(dinhDangSoLuong(n.SoLuongTon, n.DonViTinh))}</dd></div>
        <div class="detail-row"><dt>Mức tồn tối thiểu</dt><dd>${escapeHtml(dinhDangSoLuong(n.MucTonToiThieu, n.DonViTinh))}</dd></div>
        <div class="detail-row"><dt>Tình trạng kho</dt><dd>${huyHieuKho(n.TinhTrangKho)}</dd></div>
        <div class="detail-row"><dt>Đang dùng trong</dt><dd>${Number(n.SoMonDungNguyenLieu || 0).toLocaleString("vi-VN")} món</dd></div>
        <div class="detail-row"><dt>Sử dụng</dt><dd>${dangDung ? "Đang dùng" : "Đã ngừng dùng"}</dd></div>
      </dl>
      <h4 class="sub-title">${gd.length ? `${gd.length} lần thay đổi gần nhất` : "Lịch sử kho"}</h4>
      ${gd.length ? `<div class="kho-cuon"><table class="line-table">
        <thead><tr><th>Thời gian</th><th>Loại</th><th class="col-num">Thay đổi</th><th class="col-num">Còn lại</th><th>Người làm / lý do</th></tr></thead>
        <tbody>${gd.map((g) => `<tr>
          <td class="kho-gio">${escapeHtml(dinhDangThoiGian(g.NgayGiaoDich))}</td>
          <td>${escapeHtml(nhanLoaiGiaoDichKho(g.LoaiGiaoDich))}</td>
          <td class="col-num"><span class="${khoTang(g) ? "kho-tang" : "kho-giam"}">${escapeHtml(Kho.chuoiThayDoi(g))}</span></td>
          <td class="col-num">${escapeHtml(dinhDangSoLuong(g.SoLuongSau, g.DonViTinh))}</td>
          <td>${escapeHtml(g.NguoiThucHien || "—")}${g.LyDo ? `<div class="cell-sub">${escapeHtml(g.LyDo)}</div>` : ""}</td>
        </tr>`).join("")}</tbody></table></div>`
        : '<p class="kho-trong">Nguyên liệu này chưa có lần thay đổi nào.</p>'}`;
    $("ct-chan-nut").innerHTML = quanLy ? `
      <button type="button" class="btn-outline" data-hd="sua" data-id="${n.NguyenLieuID}">Sửa thông tin</button>
      <button type="button" class="btn-outline" data-hd="kiem-ke" data-id="${n.NguyenLieuID}">Kiểm kê</button>
      <button type="button" class="btn-outline" data-hd="xuat" data-id="${n.NguyenLieuID}">Xuất kho</button>
      <button type="button" class="btn-outline" data-hd="doi" data-id="${n.NguyenLieuID}">${dangDung ? "Ngừng dùng" : "Dùng lại"}</button>` : "";
    Kho.mo("modal-chi-tiet");
  }

  /* ---------- Hanh dong tren dong / trong chi tiet ---------- */
  // Phan quan ly dang ky ham vao day khi trang co cac hop thoai tuong ung (can quyen inventory.manage).
  const hanhDong = {xem: moChiTiet};

  document.addEventListener("click", (e) => {
    const b = e.target.closest("button[data-hd]");
    if (!b) return;
    const ham = hanhDong[b.dataset.hd];
    if (!ham) return;
    if (b.closest("#modal-chi-tiet")) dongModal("modal-chi-tiet");
    ham(b.dataset.id);
  });

  /* ---------- Phan quan ly: them / sua / ngung dung / kiem ke / xuat kho ---------- */
  function khoiTaoQuanLy() {
  const nlForm = $("nl-form");
  const nlLoi = $("nl-loi");
  let nlDangSua = null;

  function moFormThem() {
    nlDangSua = null;
    nlForm.reset();
    Kho.anLoi(nlLoi);
    $("nl-tieu-de").textContent = "Thêm nguyên liệu";
    $("nl-ton-wrap").classList.remove("hidden");
    $("nl-ghi-chu-sua").classList.add("hidden");
    Kho.mo("modal-nl");
  }

  async function moFormSua(id) {
    const r = await apiGoi("GET", `/api/v1/ingredients/${id}`);
    if (!r.ok) {
      if (Kho.hetPhien(r)) return;
      hienToast(r.loi);
      return;
    }
    const n = r.data;
    nlDangSua = n;
    nlForm.reset();
    Kho.anLoi(nlLoi);
    nlForm.ten.value = n.TenNguyenLieu;
    nlForm.don_vi.value = n.DonViTinh;
    nlForm.muc.value = String(Number(n.MucTonToiThieu));
    $("nl-tieu-de").textContent = "Sửa nguyên liệu";
    $("nl-ton-wrap").classList.add("hidden");
    $("nl-ghi-chu-sua").classList.remove("hidden");
    Kho.mo("modal-nl");
  }

  nlForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    Kho.anLoi(nlLoi);
    const ten = nlForm.ten.value.trim();
    const donVi = nlForm.don_vi.value.trim();
    if (!ten) return Kho.hienLoi(nlLoi, "Vui lòng nhập tên nguyên liệu.");
    if (!donVi) return Kho.hienLoi(nlLoi, "Vui lòng nhập đơn vị tính, ví dụ g, ml hoặc cái.");
    let muc = {chuoi: "0", so: 0};
    if (nlForm.muc.value.trim() !== "") {
      muc = Kho.docSo(nlForm.muc.value, {nhan: "Mức tồn tối thiểu"});
      if (muc.loi) return Kho.hienLoi(nlLoi, muc.loi);
    }
    const nut = $("btn-luu-nl");

    if (nlDangSua) {
      const body = {};
      if (ten !== nlDangSua.TenNguyenLieu) body.ten_nguyen_lieu = ten;
      if (donVi !== nlDangSua.DonViTinh) body.don_vi_tinh = donVi;
      if (muc.so !== Number(nlDangSua.MucTonToiThieu)) body.muc_ton_toi_thieu = muc.chuoi;
      if (!Object.keys(body).length) return Kho.hienLoi(nlLoi, "Bạn chưa thay đổi thông tin nào.");
      nut.disabled = true;
      const r = await apiGoi("PUT", `/api/v1/ingredients/${nlDangSua.NguyenLieuID}`, body);
      nut.disabled = false;
      if (!r.ok) {
        if (Kho.hetPhien(r)) return;
        return Kho.hienLoi(nlLoi, r.loi);
      }
      dongModal("modal-nl");
      hienToast("Đã cập nhật nguyên liệu.");
      lamMoi();
      return;
    }

    const body = {ten_nguyen_lieu: ten, don_vi_tinh: donVi, muc_ton_toi_thieu: muc.chuoi};
    if (nlForm.ton.value.trim() !== "") {
      const ton = Kho.docSo(nlForm.ton.value, {nhan: "Tồn kho ban đầu"});
      if (ton.loi) return Kho.hienLoi(nlLoi, ton.loi);
      body.so_luong_ton_ban_dau = ton.chuoi;
    }
    nut.disabled = true;
    const r = await apiGoi("POST", "/api/v1/ingredients", body);
    nut.disabled = false;
    if (!r.ok) {
      if (Kho.hetPhien(r)) return;
      return Kho.hienLoi(nlLoi, r.loi);
    }
    dongModal("modal-nl");
    hienToast("Đã thêm nguyên liệu mới.");
    lamMoi();
  });

  /* ---------- Ngung dung / dung lai ---------- */
  async function doiDangDung(id) {
    const n = timNl(id);
    if (!n) { hienToast("Không tìm thấy nguyên liệu. Vui lòng tải lại trang."); return; }
    const dangDung = Boolean(n.TrangThai);
    if (dangDung && !xacNhan(`Ngừng dùng “${n.TenNguyenLieu}”? Nguyên liệu sẽ không được chọn thêm vào công thức mới. Lịch sử kho vẫn được giữ.`)) return;
    const r = await apiGoi("PATCH", `/api/v1/ingredients/${id}/status`, {dang_dung: !dangDung});
    if (!r.ok) {
      if (Kho.hetPhien(r)) return;
      hienToast(r.loi);
      return;
    }
    hienToast(dangDung ? "Đã ngừng dùng nguyên liệu này." : "Đã cho dùng lại nguyên liệu này.");
    lamMoi();
  }

  /* ---------- Kiem ke ---------- */
  const kkForm = $("kk-form");
  const kkLoi = $("kk-loi");
  let nlKiemKe = null;
  Kho.goiYLyDo($("kk-goi-y"), kkForm.ly_do, ["Kiểm kê định kỳ", "Hao hụt khi pha chế", "Nhập sai số lúc trước"]);

  function capNhatChenh() {
    const o = $("kk-chenh");
    o.className = "small";
    const kq = Kho.docSo(kkForm.so_dem.value, {nhan: "Số đếm"});
    if (!nlKiemKe || kq.loi) { o.textContent = "Nhập số đếm thực tế để xem chênh lệch sẽ ghi."; return; }
    const ton = Number(nlKiemKe.SoLuongTon);
    const chenh = Math.round((kq.so - ton) * 1000) / 1000;
    if (chenh === 0) { o.textContent = "Bằng với tồn hiện tại, không cần điều chỉnh."; return; }
    o.classList.add(chenh > 0 ? "kho-tang" : "kho-giam");
    o.textContent = `Sẽ ghi ${chenh > 0 ? "tăng" : "giảm"} ${dinhDangSoLuong(Math.abs(chenh), nlKiemKe.DonViTinh)}: ` +
      `từ ${dinhDangSoLuong(ton, nlKiemKe.DonViTinh)} còn ${dinhDangSoLuong(kq.so, nlKiemKe.DonViTinh)}.`;
  }
  kkForm.so_dem.addEventListener("input", capNhatChenh);

  function moKiemKe(id) {
    const n = timNl(id);
    if (!n) { hienToast("Không tìm thấy nguyên liệu. Vui lòng tải lại trang."); return; }
    nlKiemKe = n;
    kkForm.reset();
    Kho.anLoi(kkLoi);
    $("kk-thong-tin").innerHTML = `<div class="cell-name">${escapeHtml(n.TenNguyenLieu)}</div>
      <div class="cell-sub">Tồn trên hệ thống: ${escapeHtml(dinhDangSoLuong(n.SoLuongTon, n.DonViTinh))}</div>`;
    $("kk-don-vi").textContent = n.DonViTinh;
    capNhatChenh();
    Kho.mo("modal-kiem-ke");
  }

  kkForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    Kho.anLoi(kkLoi);
    const so = Kho.docSo(kkForm.so_dem.value, {nhan: "Số đếm"});
    if (so.loi) return Kho.hienLoi(kkLoi, so.loi);
    const lyDo = kkForm.ly_do.value.trim();
    if (!lyDo) return Kho.hienLoi(kkLoi, "Vui lòng nhập lý do kiểm kê.");
    if (so.so === Number(nlKiemKe.SoLuongTon)) return Kho.hienLoi(kkLoi, "Số đếm bằng với tồn hiện tại nên không cần điều chỉnh.");
    const nut = $("btn-luu-kk");
    nut.disabled = true;
    const r = await apiGoi("POST", "/api/v1/inventory/adjustments",
      {nguyen_lieu_id: nlKiemKe.NguyenLieuID, so_luong_thuc_te: so.chuoi, ly_do: lyDo});
    nut.disabled = false;
    if (!r.ok) {
      if (Kho.hetPhien(r)) return;
      return Kho.hienLoi(kkLoi, r.loi);
    }
    dongModal("modal-kiem-ke");
    hienToast(`Đã ghi kiểm kê: ${Kho.chuoiThayDoi(r.data.LichSuKho)}.`);
    lamMoi();
  });

  /* ---------- Xuat kho ---------- */
  const xkForm = $("xk-form");
  const xkLoi = $("xk-loi");
  let nlXuat = null;
  Kho.goiYLyDo($("xk-goi-y"), xkForm.ly_do, ["Hư hỏng", "Hết hạn sử dụng", "Đổ vỡ", "Dùng nội bộ"]);

  function moXuat(id) {
    const n = timNl(id);
    if (!n) { hienToast("Không tìm thấy nguyên liệu. Vui lòng tải lại trang."); return; }
    nlXuat = n;
    xkForm.reset();
    Kho.anLoi(xkLoi);
    $("xk-thong-tin").innerHTML = `<div class="cell-name">${escapeHtml(n.TenNguyenLieu)}</div>
      <div class="cell-sub">Đang còn: ${escapeHtml(dinhDangSoLuong(n.SoLuongTon, n.DonViTinh))}</div>`;
    $("xk-don-vi").textContent = n.DonViTinh;
    Kho.mo("modal-xuat-kho");
  }

  xkForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    Kho.anLoi(xkLoi);
    const so = Kho.docSo(xkForm.so_luong.value, {nhan: "Số lượng xuất", lonHonKhong: true});
    if (so.loi) return Kho.hienLoi(xkLoi, so.loi);
    if (so.so > Number(nlXuat.SoLuongTon)) {
      return Kho.hienLoi(xkLoi, `Chỉ còn ${dinhDangSoLuong(nlXuat.SoLuongTon, nlXuat.DonViTinh)}, không xuất nhiều hơn được.`);
    }
    const lyDo = xkForm.ly_do.value.trim();
    if (!lyDo) return Kho.hienLoi(xkLoi, "Vui lòng nhập lý do xuất kho.");
    const nut = $("btn-luu-xk");
    nut.disabled = true;
    const r = await apiGoi("POST", "/api/v1/inventory/issues",
      {nguyen_lieu_id: nlXuat.NguyenLieuID, so_luong: so.chuoi, ly_do: lyDo});
    nut.disabled = false;
    if (!r.ok) {
      if (Kho.hetPhien(r)) return;
      return Kho.hienLoi(xkLoi, r.loi);
    }
    dongModal("modal-xuat-kho");
    hienToast(`Đã xuất kho ${dinhDangSoLuong(so.so, nlXuat.DonViTinh)}.`);
    lamMoi();
  });

  hanhDong.sua = moFormSua;
  hanhDong["kiem-ke"] = moKiemKe;
  hanhDong.xuat = moXuat;
  hanhDong.doi = doiDangDung;
  const btnThem = $("btn-them-nl");
  if (btnThem) btnThem.addEventListener("click", moFormThem);
  }

  /* ---------- Lich su kho ---------- */
  function trongLs(text) {
    tbodyLs.innerHTML = `<tr class="empty-row"><td colspan="7">${escapeHtml(text)}</td></tr>`;
  }

  async function napLichSu() {
    lichSuCu = false;
    if (!dsNlLichSu) {
      const r = await Kho.taiNguyenLieu("");
      if (!r.ok) {
        if (Kho.hetPhien(r)) return;
        Kho.hienLoi(loiLs, thongBaoLoi(r.status, "danh sách nguyên liệu"));
      } else {
        dsNlLichSu = r.data;
        const cu = $("ls-nl").value;
        $("ls-nl").innerHTML = '<option value="">Tất cả nguyên liệu</option>' +
          dsNlLichSu.map((n) => `<option value="${n.NguyenLieuID}">${escapeHtml(n.TenNguyenLieu)}</option>`).join("");
        $("ls-nl").value = cu;
      }
    }
    taiLichSu();
  }

  async function taiLichSu() {
    Kho.anLoi(loiLs);
    const tu = $("ls-tu").value;
    const den = $("ls-den").value;
    if (tu && den && tu > den) {
      Kho.hienLoi(loiLs, "Ngày bắt đầu phải trước hoặc cùng ngày kết thúc.");
      return;
    }
    const p = new URLSearchParams({page: trangLs, per_page: SO_DONG});
    if ($("ls-nl").value) p.set("nguyen_lieu_id", $("ls-nl").value);
    if ($("ls-loai").value) p.set("loai", $("ls-loai").value);
    if (tu) p.set("tu_ngay", tu);
    if (den) p.set("den_ngay", den);
    trongLs("Đang tải lịch sử kho...");
    const r = await apiGoi("GET", "/api/v1/inventory/transactions?" + p.toString());
    if (!r.ok) {
      if (Kho.hetPhien(r)) return;
      Kho.hienLoi(loiLs, thongBaoLoi(r.status, "lịch sử kho"));
      trongLs("Không có dữ liệu để hiển thị.");
      $("ls-trang").innerHTML = "";
      return;
    }
    const ds = r.data.items;
    if (!ds.length) {
      trongLs("Chưa có lần thay đổi nào phù hợp.");
    } else {
      tbodyLs.innerHTML = ds.map((g) => {
        const chungTu = g.MaDonHang ? `Đơn ${escapeHtml(g.MaDonHang)}`
          : (g.MaPhieuNhap ? `Phiếu nhập ${escapeHtml(g.MaPhieuNhap)}` : "—");
        return `<tr>
          <td class="kho-gio">${escapeHtml(dinhDangThoiGian(g.NgayGiaoDich))}</td>
          <td><div class="cell-name">${escapeHtml(g.TenNguyenLieu)}</div></td>
          <td>${escapeHtml(nhanLoaiGiaoDichKho(g.LoaiGiaoDich))}</td>
          <td class="col-num"><span class="${khoTang(g) ? "kho-tang" : "kho-giam"}">${escapeHtml(Kho.chuoiThayDoi(g))}</span></td>
          <td class="col-num">${escapeHtml(dinhDangSoLuong(g.SoLuongTruoc))} → ${escapeHtml(dinhDangSoLuong(g.SoLuongSau, g.DonViTinh))}</td>
          <td>${escapeHtml(g.NguoiThucHien || "—")}${g.LyDo ? `<div class="cell-sub">${escapeHtml(g.LyDo)}</div>` : ""}</td>
          <td>${chungTu}</td>
        </tr>`;
      }).join("");
    }
    Kho.veTrang($("ls-trang"), trangLs, r.data.total, SO_DONG, "lần thay đổi");
  }

  function locLaiLs() { trangLs = 1; taiLichSu(); }
  ["ls-nl", "ls-loai", "ls-tu", "ls-den"].forEach((id) => $(id).addEventListener("change", locLaiLs));
  $("ls-xoa-loc").addEventListener("click", () => {
    ["ls-nl", "ls-loai", "ls-tu", "ls-den"].forEach((id) => { $(id).value = ""; });
    locLaiLs();
  });
  $("ls-trang").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-trang]");
    if (!b || b.disabled) return;
    trangLs = Number(b.dataset.trang);
    taiLichSu();
  });

  /* ---------- Tru kho theo don (can quyen ban hang) ---------- */
  function khoiTaoTruKho() {
  const tkForm = $("tk-form");
  const tkLoi = $("tk-loi");
  let dsDon = [];
  let donChon = null;
  let seqDon = 0;
  let henDon;

  function veDsDon() {
    const box = $("tk-ds-don");
    if (!dsDon.length) {
      box.innerHTML = '<p class="kho-trong">Không có đơn nào đang pha chế hoặc đã hoàn thành phù hợp.</p>';
      return;
    }
    box.innerHTML = dsDon.map((d) => `
      <button type="button" class="kho-don" data-don="${d.DonHangID}" aria-pressed="${donChon && donChon.DonHangID === d.DonHangID}">
        <span>
          <span class="kho-don-ten">${escapeHtml(d.MaDonHang)}</span>
          <span class="kho-don-phu">${escapeHtml(dinhDangThoiGian(d.ThoiGianDat))} · ${Number(d.SoMon || 0).toLocaleString("vi-VN")} món · ${escapeHtml(dinhDangGia(d.ThanhTien))}</span>
        </span>
        ${huyHieuDon(d.TrangThai)}
      </button>`).join("");
  }

  async function timDon() {
    const seq = ++seqDon;
    Kho.anLoi(tkLoi);
    $("tk-ds-don").innerHTML = '<p class="kho-trong">Đang tìm đơn...</p>';
    const q = tkForm.q.value.trim();
    const lay = (tt) => {
      const p = new URLSearchParams({status: tt, per_page: 20});
      if (q) p.set("q", q);
      return apiGoi("GET", "/api/v1/orders?" + p.toString());
    };
    const [a, b] = await Promise.all([lay(MA_DON_PHA), lay(MA_DON_XONG)]);
    if (seq !== seqDon) return;
    const loi = !a.ok ? a : (!b.ok ? b : null);
    if (loi) {
      if (Kho.hetPhien(loi)) return;
      Kho.hienLoi(tkLoi, thongBaoLoi(loi.status, "danh sách đơn hàng"));
      $("tk-ds-don").innerHTML = "";
      return;
    }
    dsDon = a.data.items.concat(b.data.items).sort((x, y) => y.DonHangID - x.DonHangID).slice(0, 30);
    if (donChon && !dsDon.some((d) => d.DonHangID === donChon.DonHangID)) donChon = null;
    $("btn-tru-kho-xn").disabled = !donChon;
    veDsDon();
  }

  function moTruKho() {
    tkForm.reset();
    donChon = null;
    Kho.anLoi(tkLoi);
    $("tk-chon").classList.remove("hidden");
    $("tk-ket-qua").classList.add("hidden");
    $("tk-ket-qua").innerHTML = "";
    $("btn-tru-kho-xn").classList.remove("hidden");
    $("btn-tru-kho-xn").disabled = true;
    $("tk-dong").textContent = "Huỷ";
    Kho.mo("modal-tru-kho");
    timDon();
  }

  tkForm.q.addEventListener("input", () => { clearTimeout(henDon); henDon = setTimeout(timDon, 300); });
  $("tk-ds-don").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-don]");
    if (!b) return;
    donChon = dsDon.find((d) => String(d.DonHangID) === b.dataset.don) || null;
    $("btn-tru-kho-xn").disabled = !donChon;
    Kho.anLoi(tkLoi);
    veDsDon();
  });

  function veKetQuaTruKho(kq) {
    const dong = kq.ChiTiet.map((g) => `<tr>
      <td>${escapeHtml(g.TenNguyenLieu)}</td>
      <td class="col-num"><span class="kho-giam">${escapeHtml(dinhDangSoLuong(Math.abs(Number(g.SoLuongThayDoi)), g.DonViTinh))}</span></td>
      <td class="col-num">${escapeHtml(dinhDangSoLuong(g.SoLuongSau, g.DonViTinh))}</td>
    </tr>`).join("");
    const chuaCo = kq.MonChuaCoCongThuc || [];
    $("tk-ket-qua").innerHTML = `
      <div class="success-box"><div class="tick" aria-hidden="true">✓</div>
        <h3>Đã trừ kho cho đơn ${escapeHtml(kq.MaDonHang)}</h3></div>
      <div class="kho-cuon"><table class="line-table">
        <thead><tr><th>Nguyên liệu</th><th class="col-num">Đã trừ</th><th class="col-num">Còn lại</th></tr></thead>
        <tbody>${dong}</tbody></table></div>
      ${chuaCo.length ? `<div class="note-box" style="margin-top:12px">Các món sau chưa có công thức nên chưa trừ nguyên liệu:
        <strong>${chuaCo.map(escapeHtml).join(", ")}</strong>. Hãy bổ sung ở trang <a href="/recipes">Công thức pha chế</a>.</div>` : ""}`;
    $("tk-chon").classList.add("hidden");
    $("tk-ket-qua").classList.remove("hidden");
    $("btn-tru-kho-xn").classList.add("hidden");
    $("tk-dong").textContent = "Xong";
    $("tk-dong").focus();
  }

  tkForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    Kho.anLoi(tkLoi);
    if (!donChon) return Kho.hienLoi(tkLoi, "Vui lòng chọn đơn cần trừ kho.");
    if (!xacNhan(`Trừ kho cho đơn ${donChon.MaDonHang}? Mỗi đơn chỉ trừ được một lần.`)) return;
    const nut = $("btn-tru-kho-xn");
    nut.disabled = true;
    const r = await apiGoi("POST", "/api/v1/inventory/consumptions", {don_hang_id: donChon.DonHangID});
    nut.disabled = false;
    if (!r.ok) {
      if (Kho.hetPhien(r)) return;
      const thieu = r.status === 409 && r.loi.startsWith("Tồn kho không đủ");
      return Kho.hienLoi(tkLoi, thieu
        ? r.loi + " Hãy nhập thêm hoặc kiểm kê nguyên liệu còn thiếu rồi thử trừ kho lại."
        : r.loi);
    }
    veKetQuaTruKho(r.data);
    hienToast("Đã trừ kho theo đơn.");
    lamMoi();
  });

  const btnTruKho = $("btn-tru-kho");
  if (btnTruKho) btnTruKho.addEventListener("click", moTruKho);
  }

  /* ---------- Khoi dong ---------- */
  if ($("nl-form")) khoiTaoQuanLy();
  if ($("tk-form")) khoiTaoTruKho();
  taiThongKe();
  taiTonKho();
})();
