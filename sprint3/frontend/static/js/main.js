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
  "order.view": "Xem đơn hàng",
  "order.manage": "Bán hàng: tạo đơn, sửa món, chuyển bước pha chế",
  "order.cancel": "Huỷ đơn hàng",
  "payment.manage": "Thu tiền và in hoá đơn",
  "payment.refund": "Hoàn tiền cho khách",
  "inventory.view": "Xem nguyên liệu, tồn kho và công thức pha chế",
  "inventory.manage": "Quản lý nguyên liệu, kiểm kê kho và công thức",
  "supplier.view": "Xem nhà cung cấp và phiếu nhập hàng",
  "supplier.manage": "Quản lý nhà cung cấp, lập và sửa phiếu nhập",
  "purchase.confirm": "Xác nhận đã nhận hàng (cập nhật kho)",
};

function nhanQuyen(ten) {
  return NHAN_QUYEN[ten] || ten;
}

/** Thong bao tu he thong -> cau tieng Viet than thien. */
const DIEN_GIAI_LOI = [
  ["co so du lieu chua san sang", "Hệ thống chưa sẵn sàng. Vui lòng liên hệ quản lý hoặc thử lại sau."],
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
  // Don hang
  ["muon bo het mon thi hay huy don", "Đơn cần còn ít nhất 1 món. Nếu khách không lấy nữa, hãy huỷ đơn."],
  ["don hang phai co it nhat 1 mon", "Đơn cần có ít nhất 1 món."],
  ["so luong phai la so nguyen", "Số lượng phải là số nguyên từ 1 đến 999."],
  ["mon dang tam ngung ban", "Có món đang tạm ngưng bán. Vui lòng bỏ món đó ra khỏi đơn."],
  ["mon trong don khong ton tai", "Món này không còn trong đơn. Vui lòng tải lại."],
  ["danh sach mon khong hop le", "Danh sách món chưa hợp lệ. Vui lòng tải lại trang."],
  ["don hang khong ton tai", "Không tìm thấy đơn hàng."],
  ["don da thu tien hoac dang cho xac nhan", "Đơn đã thu tiền hoặc đang chờ xác nhận thanh toán nên không sửa món được."],
  ["don da bat dau pha che", "Đơn đã bắt đầu pha chế nên không sửa món được."],
  ["trang thai don khong hop le", "Tình trạng đơn không hợp lệ."],
  ["huy don phai kem ly do", "Vui lòng huỷ đơn kèm lý do."],
  ["khong the chuyen don sang trang thai nay", "Đơn vừa được người khác cập nhật. Vui lòng tải lại."],
  ["ly do huy la bat buoc", "Vui lòng nhập lý do huỷ đơn."],
  ["don hang da huy truoc do", "Đơn này đã được huỷ trước đó."],
  ["don da hoan thanh, khong the huy", "Đơn đã hoàn thành nên không huỷ được. Nếu khách trả lại, hãy hoàn tiền."],
  ["can hoan tien cho khach truoc khi huy", "Đơn đã thu tiền. Hãy chọn hoàn tiền cho khách khi huỷ."],
  ["khong co quyen hoan tien", "Bạn không có quyền hoàn tiền. Vui lòng nhờ quản lý."],
  ["ngay khong hop le", "Ngày chưa hợp lệ."],
  // Thanh toan & hoa don
  ["phuong thuc thanh toan khong hop le", "Vui lòng chọn hình thức thanh toán."],
  ["don hang da huy, khong the thanh toan", "Đơn đã huỷ nên không thanh toán được."],
  ["don dang co giao dich cho xac nhan", "Đơn đang có một lần thu tiền chờ xác nhận. Hãy xác nhận hoặc báo không thành công trước."],
  ["don hang da duoc thanh toan", "Đơn này đã được thanh toán."],
  ["chua co mon nao de thanh toan", "Đơn chưa có món nào để thanh toán."],
  ["so tien thanh toan khong khop", "Số tiền không khớp với số cần thu. Vui lòng tải lại đơn."],
  ["ma giao dich da duoc su dung", "Mã giao dịch này đã được dùng cho lần thanh toán khác."],
  ["du lieu thanh toan khong hop le", "Thông tin thanh toán chưa hợp lệ."],
  ["giao dich thanh toan khong ton tai", "Không tìm thấy lần thanh toán này."],
  ["giao dich nay da duoc xu ly truoc do", "Lần thanh toán này đã được xử lý rồi. Vui lòng tải lại."],
  ["can nhap ma giao dich", "Vui lòng nhập mã giao dịch ngân hàng."],
  ["ly do hoan tien la bat buoc", "Vui lòng nhập lý do hoàn tiền."],
  ["so tien hoan khong hop le", "Số tiền hoàn chưa hợp lệ."],
  ["so tien hoan phai lon hon 0", "Số tiền hoàn phải lớn hơn 0."],
  ["so tien hoan vuot qua", "Số tiền hoàn vượt quá số tiền còn có thể hoàn."],
  ["chi hoan tien cho giao dich da thanh toan", "Chỉ hoàn tiền được cho lần thanh toán đã thu thành công."],
  ["so tien khong hop le", "Số tiền chưa hợp lệ."],
  ["hoa don khong ton tai", "Không tìm thấy hoá đơn."],
  ["chua co hoa don", "Đơn chưa thanh toán nên chưa có hoá đơn."],
  // Kho nguyen lieu & cong thuc
  ["ten nguyen lieu la bat buoc", "Vui lòng nhập tên nguyên liệu."],
  ["ten nguyen lieu da ton tai", "Đã có nguyên liệu trùng tên."],
  ["don vi tinh la bat buoc", "Vui lòng nhập đơn vị tính."],
  ["khong the doi don vi tinh", "Nguyên liệu đã có lịch sử kho hoặc nằm trong công thức nên không đổi được đơn vị tính."],
  ["muc ton toi thieu khong hop le", "Mức tồn tối thiểu chưa hợp lệ."],
  ["so luong ton ban dau khong hop le", "Số lượng tồn ban đầu chưa hợp lệ."],
  ["so luong thuc te khong hop le", "Số lượng thực tế chưa hợp lệ."],
  ["ton kho khong thay doi", "Số lượng thực tế bằng tồn hiện tại, không cần điều chỉnh."],
  ["so luong xuat phai lon hon 0", "Số lượng xuất phải lớn hơn 0."],
  ["so luong can phai lon hon 0", "Định lượng phải lớn hơn 0."],
  ["cong thuc toi da", "Công thức có quá nhiều nguyên liệu."],
  ["nguyen lieu bi trung", "Một nguyên liệu đang bị chọn hai lần."],
  ["danh sach nguyen lieu khong hop le", "Danh sách nguyên liệu chưa hợp lệ."],
  ["nguyen lieu khong ton tai", "Không tìm thấy nguyên liệu này. Vui lòng tải lại trang."],
  ["nguyen lieu khong hop le", "Vui lòng chọn nguyên liệu."],
  ["da ngung su dung", "Có nguyên liệu đã ngừng sử dụng. Vui lòng kiểm tra lại."],
  ["da ngung dung", "Có nguyên liệu đã ngừng sử dụng. Vui lòng kiểm tra lại."],
  ["ly do la bat buoc", "Vui lòng nhập lý do."],
  ["don hang da huy, khong the tru kho", "Đơn đã huỷ nên không trừ kho."],
  ["chua o buoc pha che", "Đơn chưa bắt đầu pha chế nên chưa trừ kho."],
  ["don nay da duoc tru kho", "Đơn này đã được trừ kho nguyên liệu rồi."],
  ["khong co mon nao co cong thuc", "Các món trong đơn chưa có công thức pha chế nên không trừ kho."],
  ["he thong dang ban", "Hệ thống đang bận. Vui lòng thử lại."],
  // Nha cung cap & nhap hang
  ["ten nha cung cap la bat buoc", "Vui lòng nhập tên nhà cung cấp."],
  ["nha cung cap da ton tai", "Đã có nhà cung cấp trùng tên."],
  ["nha cung cap khong ton tai", "Không tìm thấy nhà cung cấp."],
  ["nha cung cap khong hop le", "Vui lòng chọn nhà cung cấp."],
  ["nha cung cap da ngung hop tac", "Nhà cung cấp này đã ngừng hợp tác."],
  ["so dien thoai khong hop le", "Số điện thoại chưa hợp lệ."],
  ["email khong hop le", "Email chưa hợp lệ."],
  ["phieu nhap phai co it nhat 1 dong", "Phiếu nhập cần có ít nhất 1 nguyên liệu."],
  ["phieu nhap toi da", "Phiếu nhập có quá nhiều dòng."],
  ["so luong phai lon hon 0 va khong qua", "Số lượng nhập phải lớn hơn 0."],
  ["don gia nhap phai tu", "Đơn giá nhập chưa hợp lệ."],
  ["tong tien phieu nhap qua lon", "Tổng tiền phiếu nhập quá lớn."],
  ["phieu nhap khong ton tai", "Không tìm thấy phiếu nhập."],
  ["phieu nhap khong co dong nao", "Phiếu nhập chưa có nguyên liệu nào."],
  ["phieu da xac nhan hoac da huy", "Phiếu đã nhận hàng hoặc đã huỷ nên không sửa được."],
  ["phieu da duoc xac nhan truoc do", "Phiếu này đã được nhận hàng trước đó."],
  ["phieu da huy, khong the xac nhan", "Phiếu đã huỷ nên không nhận hàng được."],
  ["phieu da huy truoc do", "Phiếu này đã được huỷ trước đó."],
  ["khong co quyen huy phieu da xac nhan", "Bạn không có quyền huỷ phiếu đã nhận hàng. Vui lòng nhờ quản lý."],
  ["du lieu gui len khong hop le", "Thông tin gửi lên chưa hợp lệ. Vui lòng tải lại trang."],
  ["khong co gi de cap nhat", "Bạn chưa thay đổi thông tin nào."],
  ["khong co quyen", "Bạn không có quyền thực hiện việc này."],
  ["chua dang nhap", "Phiên làm việc đã kết thúc. Vui lòng đăng nhập lại."],
];

/** Trang rieng co the them cau dien giai vao day; duoc xet truoc bang chung o tren. */
const DIEN_GIAI_LOI_RIENG = [];

/** Doi thong bao he thong sang cau than thien; khong in nguyen van. */
function dienGiaiLoi(raw, status) {
  const text = (raw || "").toLowerCase();
  for (const [dauHieu, cau] of DIEN_GIAI_LOI_RIENG.concat(DIEN_GIAI_LOI)) {
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
  if (status >= 500) return "Hệ thống chưa sẵn sàng. Vui lòng liên hệ quản lý hoặc thử lại sau.";
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

/* Ma tinh trang don hang / thanh toan -> nhan + mau huy hieu. Chi dung trong file nay
   va qua cac ham ben duoi, template khong viet ma truc tiep. */
const TINH_TRANG_DON = {
  MOI: {nhan: "Mới tạo", mau: "badge-info"},
  CHO_PHA_CHE: {nhan: "Chờ pha chế", mau: "badge-wait"},
  DANG_PHA_CHE: {nhan: "Đang pha chế", mau: "badge-wait"},
  HOAN_THANH: {nhan: "Hoàn thành", mau: "badge-on"},
  DA_HUY: {nhan: "Đã huỷ", mau: "badge-off"},
};

/* Buoc tiep theo cua don: nhan nut bam. */
const BUOC_TIEP_DON = {
  MOI: {ma: "CHO_PHA_CHE", nut: "Gửi pha chế"},
  CHO_PHA_CHE: {ma: "DANG_PHA_CHE", nut: "Bắt đầu pha"},
  DANG_PHA_CHE: {ma: "HOAN_THANH", nut: "Hoàn thành đơn"},
};

const TINH_TRANG_THU_TIEN = {
  CHUA_THANH_TOAN: {nhan: "Chưa thu tiền", mau: "badge-wait"},
  CHO_XAC_NHAN: {nhan: "Chờ xác nhận", mau: "badge-info"},
  THANH_CONG: {nhan: "Đã thu tiền", mau: "badge-on"},
  THAT_BAI: {nhan: "Không thành công", mau: "badge-off"},
  HOAN_MOT_PHAN: {nhan: "Đã hoàn một phần", mau: "badge-muted"},
  DA_HOAN_TIEN: {nhan: "Đã hoàn tiền", mau: "badge-muted"},
};

const TINH_TRANG_HOA_DON = {
  DA_THANH_TOAN: "Đã thanh toán",
  HOAN_MOT_PHAN: "Đã hoàn một phần",
  DA_HOAN_TIEN: "Đã hoàn tiền",
};

const HINH_THUC_THANH_TOAN = {
  TIEN_MAT: "Tiền mặt",
  CHUYEN_KHOAN: "Chuyển khoản",
  THE: "Quẹt thẻ",
};

/** Huy hieu tinh trang (don hoac thanh toan) da escape san. */
function huyHieu(bang, ma) {
  const t = bang[ma] || {nhan: "Không rõ", mau: "badge-muted"};
  return `<span class="badge ${t.mau}">${escapeHtml(t.nhan)}</span>`;
}

function huyHieuDon(ma) { return huyHieu(TINH_TRANG_DON, ma); }
function huyHieuThuTien(ma) { return huyHieu(TINH_TRANG_THU_TIEN, ma); }
function buocTiepDon(ma) { return BUOC_TIEP_DON[ma] || null; }
function nhanHinhThuc(ma) { return HINH_THUC_THANH_TOAN[ma] || "Khác"; }
function nhanHoaDon(ma) { return TINH_TRANG_HOA_DON[ma] || "Không rõ"; }
function canMaGiaoDich(ma) { return ma !== "TIEN_MAT"; }

function nhanTinhTrangDon(ma) { return (TINH_TRANG_DON[ma] || {nhan: "Không rõ"}).nhan; }

/* Kho hang & nhap hang: ma he thong -> nhan. Template va file JS cua trang KHONG viet ma truc tiep. */
const TINH_TRANG_KHO = {
  DU: {nhan: "Đủ dùng", mau: "badge-on"},
  SAP_HET: {nhan: "Sắp hết", mau: "badge-wait"},
  HET: {nhan: "Hết hàng", mau: "badge-off"},
};

const TINH_TRANG_PHIEU_NHAP = {
  NHAP: {nhan: "Chờ nhận hàng", mau: "badge-wait"},
  DA_NHAN: {nhan: "Đã nhận hàng", mau: "badge-on"},
  DA_HUY: {nhan: "Đã huỷ", mau: "badge-off"},
};

const LOAI_GIAO_DICH_KHO = {
  NHAP_HANG: "Nhập hàng",
  HUY_NHAP: "Huỷ phiếu nhập",
  XUAT_KHO: "Xuất kho",
  TIEU_HAO: "Dùng để pha chế",
  DIEU_CHINH: "Kiểm kê, điều chỉnh",
};

function huyHieuKho(ma) { return huyHieu(TINH_TRANG_KHO, ma); }
function huyHieuPhieuNhap(ma) { return huyHieu(TINH_TRANG_PHIEU_NHAP, ma); }
function nhanLoaiGiaoDichKho(ma) { return LOAI_GIAO_DICH_KHO[ma] || "Khác"; }
function luaChonTinhTrangKho() {
  return Object.entries(TINH_TRANG_KHO).map(([ma, t]) => ({ma, nhan: t.nhan}));
}
function luaChonTinhTrangPhieuNhap() {
  return Object.entries(TINH_TRANG_PHIEU_NHAP).map(([ma, t]) => ({ma, nhan: t.nhan}));
}
function luaChonLoaiGiaoDichKho() {
  return Object.entries(LOAI_GIAO_DICH_KHO).map(([ma, nhan]) => ({ma, nhan}));
}
function phieuNhapChoNhan(p) { return !!p && p.TrangThai === "NHAP"; }
function phieuNhapDaNhan(p) { return !!p && p.TrangThai === "DA_NHAN"; }
function phieuNhapDaHuy(p) { return !!p && p.TrangThai === "DA_HUY"; }
/** Giao dich kho lam tang (>0) hay giam (<0) ton. */
function khoTang(gd) { return !!gd && Number(gd.SoLuongThayDoi) > 0; }

/** So luong nguyen lieu: toi da 3 so le, bo so 0 thua. 1250.5 -> "1.250,5". */
function dinhDangSoLuong(value, donVi) {
  const n = Number(value);
  if (!Number.isFinite(n)) return "—";
  const s = n.toLocaleString("vi-VN", {maximumFractionDigits: 3});
  return donVi ? `${s} ${donVi}` : s;
}

/** Don da thu tien (co hoa don), ke ca da hoan. */
function daCoHoaDon(don) {
  return don && ["THANH_CONG", "HOAN_MOT_PHAN", "DA_HOAN_TIEN"].includes(don.TrangThaiThanhToan);
}
/** Don dang giu tien cua khach (huy thi phai hoan). */
function donConGiuTien(don) {
  return don && ["THANH_CONG", "HOAN_MOT_PHAN"].includes(don.TrangThaiThanhToan);
}

/** Don con mo (chua hoan thanh / chua huy). */
function donConMo(don) {
  return don && don.TrangThai !== "HOAN_THANH" && don.TrangThai !== "DA_HUY";
}
function donDaHuy(don) { return don && don.TrangThai === "DA_HUY"; }
function chuaThuTien(don) { return don && don.TrangThaiThanhToan === "CHUA_THANH_TOAN"; }
function thanhToanDangCho(tt) { return tt && tt.TrangThai === "CHO_XAC_NHAN"; }
function thanhToanHoanDuoc(tt) {
  return tt && (tt.TrangThai === "THANH_CONG" || tt.TrangThai === "HOAN_MOT_PHAN");
}

/** Danh sach lua chon {ma, nhan} de dung cho select / radio. */
function luaChonTinhTrangDon() {
  return Object.entries(TINH_TRANG_DON).map(([ma, t]) => ({ma, nhan: t.nhan}));
}
function luaChonHinhThuc() {
  return Object.entries(HINH_THUC_THANH_TOAN).map(([ma, nhan]) => ({ma, nhan}));
}

/** "2026-10-22T14:05:09" -> "14:05 22/10/2026". */
function dinhDangThoiGian(value, chiGio) {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "—";
  const gio = d.toLocaleTimeString("vi-VN", {hour: "2-digit", minute: "2-digit"});
  return chiGio ? gio : `${gio} ${d.toLocaleDateString("vi-VN")}`;
}

/** Ngay hom nay dang YYYY-MM-DD theo gio may. */
function ngayHomNay() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

/** Bo dau tieng Viet de tim kiem "ca phe" khop "Cà phê". */
function boDau(text) {
  return String(text || "").normalize("NFD").replace(/[̀-ͯ]/g, "")
    .replace(/đ/g, "d").replace(/Đ/g, "D").toLowerCase();
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
