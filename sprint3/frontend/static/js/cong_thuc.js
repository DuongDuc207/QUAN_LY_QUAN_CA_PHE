/* Trang "Cong thuc pha che". Can main.js va kho.js nap truoc (dung doi tuong Kho + cau dien giai loi). */
(function trangCongThuc() {
  const $ = Kho.$;
  if (!$("trang-cong-thuc")) return;

  const quanLy = Kho.coQuyen("inventory.manage");
  const SO_PHAN_LICH_SU = 10;
  const TOI_DA_DONG = 100;
  const TOI_DA_THEO_DOI = 200;   // qua so mon nay thi khong tai san de lay huy hieu "da co cong thuc"

  const phai = $("ct-phai");
  const dsEl = $("cm-ds");
  const loiTrang = $("ct-loi-trang");

  let dsMon = [];
  let nhom = new Map();       // DanhMucID -> ten (chi de loc)
  const coCT = new Map();     // MonID -> true / false khi da biet
  let monChon = null;         // MonID dang xem
  let ct = null;              // cong thuc dang xem
  let seqCt = 0;
  let trangLs = 1;
  let seqLs = 0;
  let dsNL = [];

  /* ---------- Danh sach mon ---------- */
  function veDsMon() {
    const q = boDau($("cm-tim").value.trim());
    const nh = $("cm-nhom").value;
    const co = $("cm-co").value;
    const ds = dsMon.filter((m) => {
      if (q && !boDau(m.TenMon).includes(q)) return false;
      if (nh && String(m.DanhMucID) !== nh) return false;
      if (co === "co" && coCT.get(m.MonID) !== true) return false;
      if (co === "chua" && coCT.get(m.MonID) !== false) return false;
      return true;
    });
    $("cm-dem").textContent = dsMon.length ? `${ds.length.toLocaleString("vi-VN")}/${dsMon.length.toLocaleString("vi-VN")} món` : "";
    if (!ds.length) {
      const dangTai = dsMon.length && (co === "co" || co === "chua") && coCT.size < dsMon.length;
      dsEl.innerHTML = `<li class="kho-trong">${dangTai ? "Đang kiểm tra công thức của các món..." : (dsMon.length ? "Không có món nào phù hợp." : "Chưa có món nào trong thực đơn.")}</li>`;
      return;
    }
    dsEl.innerHTML = ds.map((m) => {
      const biet = coCT.get(m.MonID);
      const hh = biet === true ? '<span class="badge badge-on">Đã có công thức</span>'
        : (biet === false ? '<span class="badge badge-muted">Chưa có công thức</span>' : "");
      const phu = [m.TenDanhMuc, m.TrangThai ? "" : "Tạm ngưng bán"].filter(Boolean).map(escapeHtml).join(" · ");
      return `<li><button type="button" class="kho-mon" data-mon="${m.MonID}" aria-pressed="${m.MonID === monChon}">
        <span class="kho-mon-ten">${escapeHtml(m.TenMon)}</span>
        <span class="kho-mon-phu">${phu}</span>${hh}
      </button></li>`;
    }).join("");
  }

  async function taiMon() {
    const tat = [];
    for (let trang = 1; trang <= 10; trang++) {
      const r = await apiGoi("GET", `/api/v1/menu?per_page=100&page=${trang}`);
      if (!r.ok) {
        if (Kho.hetPhien(r)) return false;
        Kho.hienLoi(loiTrang, thongBaoLoi(r.status, "danh sách món"));
        dsEl.innerHTML = '<li class="kho-trong">Không có dữ liệu để hiển thị.</li>';
        return false;
      }
      tat.push(...r.data.items);
      if (tat.length >= r.data.total || !r.data.items.length) break;
    }
    dsMon = tat.sort((a, b) => a.TenMon.localeCompare(b.TenMon, "vi"));
    return true;
  }

  async function taiNhom() {
    const r = await apiGoi("GET", "/api/v1/categories?all=1");
    if (!r.ok) return;
    nhom = new Map(r.data.map((d) => [d.DanhMucID, d.TenDanhMuc]));
    $("cm-nhom").insertAdjacentHTML("beforeend",
      r.data.map((d) => `<option value="${d.DanhMucID}">${escapeHtml(d.TenDanhMuc)}</option>`).join(""));
  }

  /** Hoi san cong thuc cua tung mon (vai mon cung luc) de hien "da / chua co". */
  async function theoDoiCongThuc() {
    if (dsMon.length > TOI_DA_THEO_DOI) return;
    const cho = dsMon.filter((m) => !coCT.has(m.MonID));
    for (let i = 0; i < cho.length; i += 6) {
      const lo = cho.slice(i, i + 6);
      const kq = await Promise.all(lo.map((m) => apiGoi("GET", `/api/v1/recipes/${m.MonID}`)));
      let hong = false;
      kq.forEach((r, k) => {
        if (r.ok) coCT.set(lo[k].MonID, r.data.items.length > 0);
        else if (r.status === 401 || r.status === 403) hong = true;
      });
      if (hong) { kq.forEach((r) => Kho.hetPhien(r)); return; }
      veDsMon();
    }
  }

  let henGio;
  $("cm-tim").addEventListener("input", () => { clearTimeout(henGio); henGio = setTimeout(veDsMon, 200); });
  $("cm-nhom").addEventListener("change", veDsMon);
  $("cm-co").addEventListener("change", veDsMon);
  dsEl.addEventListener("click", (e) => {
    const b = e.target.closest("button[data-mon]");
    if (b) chonMon(Number(b.dataset.mon));
  });

  /* ---------- Cong thuc cua mon ---------- */
  function monCuaCt() { return dsMon.find((m) => m.MonID === monChon) || {}; }

  /** Dong gioi han so phan pha duoc (it phan nhat). */
  function dongGioiHan(items) {
    let tot = null;
    items.forEach((r) => {
      const n = Math.floor(Number(r.SoLuongTon) / Number(r.SoLuongCan));
      if (tot === null || n < tot.n) tot = {n: n, r: r};
    });
    return tot;
  }

  function veCongThuc() {
    const mon = monCuaCt();
    const items = ct.items;
    const phu = [mon.TenDanhMuc, dinhDangGia(ct.GiaBan)].filter(Boolean).map(escapeHtml).join(" · ");
    const gh = items.length ? dongGioiHan(items) : null;

    let phan;
    if (!items.length) {
      phan = `<div class="stat-tile kho-phan"><span class="stat-label">Pha được khoảng</span>
        <span class="stat-value">—</span>
        <span class="stat-foot">Món chưa có công thức nên chưa tính được số phần.</span></div>`;
    } else {
      const foot = gh.n > 0
        ? `phần với tồn kho hiện tại. Nguyên liệu dùng hết đầu tiên: ${escapeHtml(gh.r.TenNguyenLieu)}.`
        : `Không đủ nguyên liệu để pha thêm. Cần nhập thêm: ${escapeHtml(gh.r.TenNguyenLieu)}.`;
      phan = `<div class="stat-tile kho-phan"><span class="stat-label">Pha được khoảng</span>
        <span class="stat-value ${gh.n === 0 ? "kho-het" : ""}">${gh.n.toLocaleString("vi-VN")} phần</span>
        <span class="stat-foot">${foot}</span></div>`;
    }

    const bang = items.length ? `<div class="kho-ct-khung"><table class="kho-ct-bang">
      <thead><tr><th>Nguyên liệu</th><th class="col-num">Dùng cho 1 phần</th><th class="col-num">Tồn hiện tại</th><th class="col-num">Đủ pha</th></tr></thead>
      <tbody>${items.map((r) => {
        const du = Math.floor(Number(r.SoLuongTon) / Number(r.SoLuongCan));
        return `<tr>
          <td><div class="cell-name">${escapeHtml(r.TenNguyenLieu)}${r.NguyenLieuDangDung ? "" : ' <span class="badge badge-muted">Đã ngừng dùng</span>'}</div></td>
          <td class="col-num">${escapeHtml(dinhDangSoLuong(r.SoLuongCan, r.DonViTinh))}</td>
          <td class="col-num">${escapeHtml(dinhDangSoLuong(r.SoLuongTon, r.DonViTinh))}</td>
          <td class="col-num">${du.toLocaleString("vi-VN")} phần</td>
        </tr>`;
      }).join("")}</tbody></table></div>`
      : '<p class="kho-trong">Món này chưa có công thức.' + (quanLy ? " Bấm “Sửa công thức” để thêm nguyên liệu." : "") + "</p>";

    phai.innerHTML = `
      <div class="kho-ct-dau">
        <div><h3>${escapeHtml(ct.TenMon)}</h3><p class="muted">${phu}</p></div>
        ${quanLy ? `<button type="button" id="btn-sua-ct">${items.length ? "Sửa công thức" : "Thêm công thức"}</button>` : ""}
      </div>
      ${phan}
      ${bang}
      <h4 class="sub-title">Lịch sử thay đổi</h4>
      <div id="ct-lich-su"><p class="kho-trong">Đang tải lịch sử...</p></div>
      <div class="pager" id="ct-ls-trang"></div>`;
  }

  async function chonMon(id) {
    const seq = ++seqCt;
    monChon = id;
    ct = null;
    Kho.anLoi(loiTrang);
    veDsMon();
    phai.innerHTML = '<p class="kho-trong">Đang tải công thức...</p>';
    const r = await apiGoi("GET", `/api/v1/recipes/${id}`);
    if (seq !== seqCt) return;
    if (!r.ok) {
      if (Kho.hetPhien(r)) return;
      phai.innerHTML = `<div class="alert error" role="alert">${escapeHtml(r.status === 404 ? "Không tìm thấy món này. Vui lòng tải lại trang." : thongBaoLoi(r.status, "công thức"))}</div>`;
      return;
    }
    ct = r.data;
    coCT.set(id, ct.items.length > 0);
    veDsMon();
    veCongThuc();
    trangLs = 1;
    taiLichSu(false);
  }

  /* ---------- Lich su thay doi ---------- */
  function soSanh(truoc, sau) {
    const t = new Map((truoc || []).map((r) => [r.NguyenLieuID, r]));
    const s = new Map((sau || []).map((r) => [r.NguyenLieuID, r]));
    const kq = [];
    s.forEach((r, id) => {
      if (!t.has(id)) kq.push({loai: "them", r: r});
      else if (Number(t.get(id).SoLuongCan) !== Number(r.SoLuongCan)) kq.push({loai: "doi", r: r, cu: t.get(id)});
    });
    t.forEach((r, id) => { if (!s.has(id)) kq.push({loai: "bo", r: r}); });
    return kq;
  }

  const NHAN_THAY_DOI = {
    them: {nhan: "Thêm", mau: "badge-on"},
    bo: {nhan: "Bỏ", mau: "badge-off"},
    doi: {nhan: "Đổi", mau: "badge-wait"},
  };

  function moTaThayDoi(d) {
    const ten = `<strong>${escapeHtml(d.r.TenNguyenLieu)}</strong>`;
    const sl = (x) => escapeHtml(dinhDangSoLuong(x.SoLuongCan, x.DonViTinh));
    if (d.loai === "them") return `${ten}: ${sl(d.r)} cho 1 phần`;
    if (d.loai === "bo") return `${ten} (trước đó ${sl(d.r)})`;
    return `${ten}: ${sl(d.cu)} → ${sl(d.r)}`;
  }

  function veMucLichSu(h) {
    const diff = soSanh(h.Truoc, h.Sau);
    const dong = diff.length ? diff.map((d) => {
      const n = NHAN_THAY_DOI[d.loai];
      return `<li><span class="badge ${n.mau}">${escapeHtml(n.nhan)}</span>${moTaThayDoi(d)}</li>`;
    }).join("") : '<li class="muted">Không có thay đổi về nguyên liệu.</li>';
    return `<li class="kho-ls-muc">
      <div class="kho-ls-dau">
        <span class="cell-name">${escapeHtml(h.NguoiThayDoi || "Không rõ người sửa")}</span>
        <span class="muted small">${escapeHtml(dinhDangThoiGian(h.NgayThayDoi))}</span>
      </div>
      ${h.LyDo ? `<div class="cell-sub">Lý do: ${escapeHtml(h.LyDo)}</div>` : ""}
      <ul class="kho-diff">${dong}</ul>
    </li>`;
  }

  async function taiLichSu(them) {
    const seq = ++seqLs;
    const id = monChon;
    const box = $("ct-lich-su");
    if (!box) return;
    const p = new URLSearchParams({page: trangLs, per_page: SO_PHAN_LICH_SU});
    const r = await apiGoi("GET", `/api/v1/recipes/${id}/history?` + p.toString());
    if (seq !== seqLs || id !== monChon) return;
    const ben = $("ct-ls-trang");
    if (!r.ok) {
      if (Kho.hetPhien(r)) return;
      if (!them) box.innerHTML = "";
      box.insertAdjacentHTML("beforeend", `<div class="alert error" role="alert">${escapeHtml(thongBaoLoi(r.status, "lịch sử thay đổi"))}</div>`);
      ben.innerHTML = "";
      return;
    }
    const ds = r.data.items;
    if (!them) {
      box.innerHTML = ds.length ? '<ul class="kho-ls-ds"></ul>'
        : '<p class="kho-trong">Công thức này chưa từng được thay đổi.</p>';
    }
    const ul = box.querySelector("ul");
    if (ul) ul.insertAdjacentHTML("beforeend", ds.map(veMucLichSu).join(""));
    const daLay = (trangLs - 1) * SO_PHAN_LICH_SU + ds.length;
    ben.innerHTML = daLay < r.data.total
      ? `<span class="muted">Đang xem ${daLay.toLocaleString("vi-VN")}/${r.data.total.toLocaleString("vi-VN")} lần thay đổi</span><button type="button" class="btn-outline" id="ct-ls-them">Xem thêm</button>`
      : (r.data.total ? `<span class="muted">${r.data.total.toLocaleString("vi-VN")} lần thay đổi</span>` : "");
  }

  phai.addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    if (b.id === "ct-ls-them") { trangLs += 1; taiLichSu(true); }
    else if (b.id === "btn-sua-ct") moSua();
  });

  /* ---------- Sua cong thuc ---------- */
  function khoiTaoSua() {
    const form = $("sua-ct-form");
    const loi = $("sua-ct-loi");
    const dongBox = $("sua-ct-dong");
    const nutThem = $("sua-ct-them");
    let nguon = [];

    function cacDong() { return [...dongBox.querySelectorAll("[data-dong]")]; }

    function danhLai() {
      const dong = cacDong();
      const chon = new Set(dong.map((d) => d.querySelector("select").value).filter(Boolean));
      dong.forEach((d, i) => {
        const sel = d.querySelector("select");
        sel.setAttribute("aria-label", `Nguyên liệu, dòng ${i + 1}`);
        d.querySelector("input").setAttribute("aria-label", `Định lượng cho 1 phần, dòng ${i + 1}`);
        d.querySelector("button").setAttribute("aria-label", `Bỏ dòng ${i + 1}`);
        [...sel.options].forEach((o) => { o.disabled = !!o.value && o.value !== sel.value && chon.has(o.value); });
        const nl = nguon.find((n) => String(n.NguyenLieuID) === sel.value);
        d.querySelector(".kho-dv").textContent = nl ? nl.DonViTinh : "";
      });
      nutThem.disabled = dong.length >= TOI_DA_DONG;
    }

    function themDong(nlId, can) {
      const d = document.createElement("div");
      d.className = "kho-dong-ct";
      d.dataset.dong = "1";
      d.innerHTML = `
        <select><option value="">Chọn nguyên liệu</option>${nguon.map((n) =>
          `<option value="${n.NguyenLieuID}">${escapeHtml(n.TenNguyenLieu)} (${escapeHtml(n.DonViTinh)})</option>`).join("")}</select>
        <div class="kho-so"><input type="text" inputmode="decimal" autocomplete="off" placeholder="0"><span class="kho-dv"></span></div>
        <button type="button" class="btn-icon danger">Bỏ</button>`;
      dongBox.appendChild(d);
      if (nlId) d.querySelector("select").value = String(nlId);
      if (can !== undefined) d.querySelector("input").value = String(Number(can));
      danhLai();
      return d;
    }

    dongBox.addEventListener("change", (e) => { if (e.target.tagName === "SELECT") danhLai(); });
    dongBox.addEventListener("click", (e) => {
      const b = e.target.closest("button");
      if (!b) return;
      b.closest("[data-dong]").remove();
      danhLai();
    });
    nutThem.addEventListener("click", () => {
      const d = themDong(null);
      d.querySelector("select").focus();
    });

    window.moSuaCongThuc = async function () {
      if (!ct) return;
      const r = await Kho.taiNguyenLieu("active");
      if (!r.ok) {
        if (Kho.hetPhien(r)) return;
        hienToast(thongBaoLoi(r.status, "danh sách nguyên liệu"));
        return;
      }
      dsNL = r.data;
      // Nguyen lieu da ngung dung nhung van nam trong cong thuc: van cho giu lai.
      nguon = dsNL.slice();
      ct.items.forEach((x) => {
        if (!nguon.some((n) => n.NguyenLieuID === x.NguyenLieuID)) {
          nguon.push({NguyenLieuID: x.NguyenLieuID, TenNguyenLieu: x.TenNguyenLieu, DonViTinh: x.DonViTinh});
        }
      });
      nguon.sort((a, b) => a.TenNguyenLieu.localeCompare(b.TenNguyenLieu, "vi"));
      form.reset();
      Kho.anLoi(loi);
      dongBox.innerHTML = "";
      $("sua-ct-tieu-de").textContent = "Công thức: " + ct.TenMon;
      ct.items.forEach((x) => themDong(x.NguyenLieuID, x.SoLuongCan));
      if (!ct.items.length) themDong(null);
      Kho.mo("modal-sua-ct");
    };

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      Kho.anLoi(loi);
      const items = [];
      const daChon = new Set();
      const dong = cacDong();
      for (let i = 0; i < dong.length; i++) {
        const nlId = dong[i].querySelector("select").value;
        const o = dong[i].querySelector("input");
        const nhan = `Dòng ${i + 1}`;
        if (!nlId) return Kho.hienLoi(loi, `${nhan}: vui lòng chọn nguyên liệu hoặc bấm Bỏ.`);
        if (daChon.has(nlId)) return Kho.hienLoi(loi, `${nhan}: nguyên liệu này đã có ở dòng khác. Mỗi nguyên liệu chỉ nhập một lần.`);
        daChon.add(nlId);
        const so = Kho.docSo(o.value, {nhan: "Định lượng", lonHonKhong: true, toiDa: 1000000});
        if (so.loi) return Kho.hienLoi(loi, `${nhan}: ${so.loi[0].toLowerCase()}${so.loi.slice(1)}`);
        items.push({nguyen_lieu_id: Number(nlId), so_luong_can: so.chuoi, so: so.so});
      }

      const cu = new Map(ct.items.map((x) => [x.NguyenLieuID, Number(x.SoLuongCan)]));
      const khongDoi = cu.size === items.length &&
        items.every((x) => cu.has(x.nguyen_lieu_id) && cu.get(x.nguyen_lieu_id) === x.so);
      if (khongDoi) return Kho.hienLoi(loi, "Bạn chưa thay đổi công thức nào.");
      if (!items.length && !xacNhan(`Xoá hết nguyên liệu trong công thức “${ct.TenMon}”? Món sẽ không còn công thức.`)) return;

      const body = {items: items.map((x) => ({nguyen_lieu_id: x.nguyen_lieu_id, so_luong_can: x.so_luong_can}))};
      const lyDo = form.ly_do.value.trim();
      if (lyDo) body.ly_do = lyDo;

      const nut = $("btn-luu-ct");
      nut.disabled = true;
      const r = await apiGoi("PUT", `/api/v1/recipes/${ct.MonID}`, body);
      nut.disabled = false;
      if (!r.ok) {
        if (Kho.hetPhien(r)) return;
        return Kho.hienLoi(loi, r.loi);
      }
      dongModal("modal-sua-ct");
      hienToast("Đã lưu công thức.");
      ct = r.data;
      coCT.set(ct.MonID, ct.items.length > 0);
      veDsMon();
      veCongThuc();
      trangLs = 1;
      taiLichSu(false);
    });
  }

  function moSua() { if (window.moSuaCongThuc) window.moSuaCongThuc(); }

  /* ---------- Khoi dong ---------- */
  if ($("sua-ct-form")) khoiTaoSua();
  (async () => {
    await taiNhom();
    if (await taiMon()) {
      veDsMon();
      theoDoiCongThuc();
    }
  })();
})();
