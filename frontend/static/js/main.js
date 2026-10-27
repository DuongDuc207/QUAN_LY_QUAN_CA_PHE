/* Tien ich dung chung cho cac trang giao dien. */

/* =========================================================
   Nhan hien thi - doi thuat ngu he thong sang ngon ngu nguoi dung
   ========================================================= */

/** Ten quyen ky thuat -> nhan hien thi cho nguoi dung. */
const NHAN_QUYEN = {
  "account.view": "Xem danh sách nhân sự",
  "account.create": "Thêm nhân viên",
  "account.update": "Cập nhật thông tin nhân viên",
  "account.lock": "Tạm ngưng / mở lại tài khoản",
  "role.manage": "Phân quyền theo vị trí",
  "menu.view": "Xem thực đơn",
  "menu.manage": "Quản lý thực đơn và nhóm món",
};

function nhanQuyen(ten) {
  return NHAN_QUYEN[ten] || ten;
}

/** Thong bao tu he thong -> cau tieng Viet than thien. */
const DIEN_GIAI_LOI = [
  ["email da duoc su dung", "Email này đã có người dùng. Vui lòng chọn email khác."],
  ["email hoac mat khau", "Email hoặc mật khẩu chưa đúng."],
  ["mat khau phai tu", "Mật khẩu cần ít nhất 6 ký tự."],
  ["ho ten, email va mat khau", "Vui lòng nhập đủ họ tên, email và mật khẩu."],
  ["ho ten khong duoc de trong", "Vui lòng nhập họ tên."],
  ["tai khoan da bi khoa", "Tài khoản đang tạm ngưng. Vui lòng liên hệ quản lý."],
  ["tai khoan khong ton tai", "Không tìm thấy nhân viên này."],
  ["tu khoa tai khoan cua chinh minh", "Bạn không thể tự tạm ngưng tài khoản của mình."],
  ["trang thai phai la", "Tình trạng không hợp lệ."],
  ["vai tro khong ton tai", "Vị trí công việc không hợp lệ."],
  ["quyen khong ton tai", "Có quyền không hợp lệ. Vui lòng tải lại trang."],
  ["ten danh muc la bat buoc", "Vui lòng nhập tên nhóm."],
  ["ten danh muc khong duoc de trong", "Vui lòng nhập tên nhóm."],
  ["danh muc dang co mon", "Nhóm này đang có món nên không xoá được. Hãy chuyển món sang nhóm khác hoặc ẩn nhóm."],
  ["danh muc la bat buoc", "Vui lòng chọn nhóm cho món."],
  ["danh muc khong ton tai", "Nhóm này không còn tồn tại. Vui lòng tải lại trang."],
  ["ten mon la bat buoc", "Vui lòng nhập tên món."],
  ["ten mon khong duoc de trong", "Vui lòng nhập tên món."],
  ["mon khong ton tai", "Không tìm thấy món này."],
  ["gia ban khong duoc am", "Giá bán không được là số âm."],
  ["gia ban khong hop le", "Giá bán chưa hợp lệ. Vui lòng nhập một con số."],
  ["khong co gi de cap nhat", "Bạn chưa thay đổi thông tin nào."],
  ["khong co quyen", "Bạn không có quyền thực hiện việc này."],
  ["chua dang nhap", "Phiên làm việc đã kết thúc. Vui lòng đăng nhập lại."],
];

/** Doi thong bao he thong sang cau than thien; khong in nguyen van. */
function dienGiaiLoi(raw, status) {
  const text = (raw || "").toLowerCase();
  for (const [dauHieu, cau] of DIEN_GIAI_LOI) {
    if (text.includes(dauHieu)) return cau;
  }
  if (status === 403) return "Bạn không có quyền thực hiện việc này.";
  if (status === 404) return "Không tìm thấy dữ liệu.";
  return "Chưa lưu được. Vui lòng kiểm tra lại thông tin.";
}

/** Thong bao khi khong tai duoc danh sach. */
function thongBaoLoi(status, mucDich) {
  if (status === 401) return "Phiên làm việc đã kết thúc. Vui lòng đăng nhập lại.";
  if (status === 403) return "Bạn không có quyền xem " + mucDich + ".";
  if (status === 404) return "Không tìm thấy " + mucDich + ".";
  return "Hiện chưa tải được " + mucDich + ". Vui lòng thử lại.";
}

const LOI_KET_NOI = "Không kết nối được tới hệ thống. Vui lòng thử lại.";

/** Thong bao rieng cho trang dang nhap. */
function thongBaoDangNhap(status, raw) {
  const text = (raw || "").toLowerCase();
  if (text.includes("khoa") || text.includes("khóa")) {
    return "Tài khoản đang tạm ngưng. Vui lòng liên hệ quản lý.";
  }
  if (status === 400) return "Vui lòng nhập đầy đủ email và mật khẩu.";
  if (status === 401) return "Email hoặc mật khẩu chưa đúng.";
  return "Chưa đăng nhập được. Vui lòng thử lại.";
}

/* =========================================================
   Tien ich chung
   ========================================================= */

/** Chen van ban an toan vao HTML. */
function escapeHtml(value) {
  return String(value == null ? "" : value).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}

/* Ma tinh trang tai khoan cua he thong - chi dung trong file nay. */
const MA_DANG_LAM = "HOAT_DONG";
const MA_TAM_NGUNG = "KHOA";

/** Nhan vien co dang di lam hay tam ngung. */
function dangLamViec(nhanVien) {
  return (nhanVien || {}).TrangThai === MA_DANG_LAM;
}

/** Lua chon tren giao dien -> ma he thong. */
function maTinhTrang(luaChon) {
  return luaChon === "tam-ngung" ? MA_TAM_NGUNG : MA_DANG_LAM;
}

/** Ma he thong tuong ung khi bat/tat tai khoan. */
function maDoiTinhTrang(dangLam) {
  return dangLam ? MA_TAM_NGUNG : MA_DANG_LAM;
}

/** Dinh dang gia tien theo kieu Viet Nam. */
function dinhDangGia(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n.toLocaleString("vi-VN") + " ₫" : "—";
}

/** Het phien thi dua ve trang dang nhap. */
function kiemTraHetPhien(status) {
  if (status === 401) {
    window.location.href = "/login";
    return true;
  }
  return false;
}

/* =========================================================
   Goi he thong
   ========================================================= */

/** Goi API, tra ve {ok, data, status, loi} voi loi da dien giai san. */
async function apiGoi(method, url, body) {
  try {
    const opts = {method: method};
    if (body !== undefined) {
      opts.headers = {"Content-Type": "application/json"};
      opts.body = JSON.stringify(body);
    }
    const res = await fetch(url, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.success) {
      return {
        ok: false,
        status: res.status,
        loi: dienGiaiLoi(data.message, res.status),
      };
    }
    return {ok: true, status: res.status, data: data.data};
  } catch (e) {
    return {ok: false, status: 0, loi: LOI_KET_NOI};
  }
}

/* =========================================================
   Hop thoai & thong bao nhanh
   ========================================================= */

function moModal(id) {
  const m = document.getElementById(id);
  if (!m) return;
  m.classList.remove("hidden");
  const first = m.querySelector("input, select, textarea");
  if (first) setTimeout(() => first.focus(), 30);
}

function dongModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.add("hidden");
}

/** Thong bao nhanh goc duoi man hinh. */
function hienToast(text) {
  let box = document.getElementById("toast-box");
  if (!box) {
    box = document.createElement("div");
    box.id = "toast-box";
    box.className = "toast-box";
    document.body.appendChild(box);
  }
  const t = document.createElement("div");
  t.className = "toast";
  t.textContent = text;
  box.appendChild(t);
  setTimeout(() => t.classList.add("toast-out"), 2400);
  setTimeout(() => t.remove(), 2800);
}

/** Hop thoai xac nhan dung chung. */
function xacNhan(text) {
  return window.confirm(text);
}

/* =========================================================
   Su kien chung
   ========================================================= */

document.addEventListener("click", async (e) => {
  const t = e.target;
  if (!t) return;

  if (t.id === "btn-logout") {
    await fetch("/api/v1/auth/logout", {method: "POST"});
    window.location.href = "/login";
    return;
  }

  // Dong hop thoai khi bam nen mo hoac nut dong
  if (t.dataset && t.dataset.dongModal) {
    dongModal(t.dataset.dongModal);
  } else if (t.classList && t.classList.contains("modal")) {
    t.classList.add("hidden");
  }
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    document.querySelectorAll(".modal:not(.hidden)").forEach((m) => m.classList.add("hidden"));
  }
});
