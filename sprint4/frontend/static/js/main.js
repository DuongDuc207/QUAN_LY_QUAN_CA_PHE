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
  "promotion.view": "Xem chương trình khuyến mãi",
  "promotion.manage": "Tạo và sửa chương trình khuyến mãi",
  "report.view": "Xem báo cáo kinh doanh",
  "employee.view": "Xem hồ sơ nhân viên và lịch làm của mọi người",
  "employee.manage": "Quản lý hồ sơ nhân viên, ca làm và xếp lịch",
  "schedule.view": "Xem ca làm và lịch làm của mình",
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
  // Khuyen mai
  ["ma khuyen mai phai tu", "Mã khuyến mãi cần từ 3 đến 50 ký tự, chỉ gồm chữ không dấu, số và dấu gạch."],
  ["ma khuyen mai da ton tai", "Đã có chương trình dùng mã này. Vui lòng chọn mã khác."],
  ["ma khuyen mai khong ton tai", "Mã khuyến mãi không đúng."],
  ["ten khuyen mai la bat buoc", "Vui lòng nhập tên chương trình."],
  ["loai giam gia khong hop le", "Vui lòng chọn cách giảm giá."],
  ["gia tri giam phai lon hon 0", "Mức giảm phải lớn hơn 0."],
  ["giam theo phan tram chi tu", "Giảm theo phần trăm chỉ từ 1 đến 100%."],
  ["gia tri giam qua lon", "Mức giảm quá lớn."],
  ["don hang toi thieu khong hop le", "Giá trị đơn tối thiểu chưa hợp lệ."],
  ["muc giam toi da khong hop le", "Mức giảm tối đa chưa hợp lệ."],
  ["so luot su dung phai la so nguyen", "Số lượt dùng phải là số nguyên từ 1 trở lên."],
  ["thoi gian ap dung khong hop le", "Vui lòng chọn thời gian bắt đầu và kết thúc."],
  ["ngay ket thuc phai sau ngay bat dau", "Thời gian kết thúc phải sau thời gian bắt đầu."],
  ["khuyen mai khong ton tai", "Không tìm thấy chương trình khuyến mãi."],
  ["khuyen mai dang tam tat", "Chương trình khuyến mãi này đang tạm tắt."],
  ["khuyen mai chua den thoi gian", "Chương trình khuyến mãi chưa bắt đầu."],
  ["khuyen mai da het han", "Chương trình khuyến mãi đã kết thúc."],
  ["khuyen mai da het luot", "Mã khuyến mãi đã hết lượt dùng."],
  ["chua dat gia tri toi thieu", "Đơn chưa đạt giá trị tối thiểu để dùng mã này."],
  ["khong the doi ma", "Chương trình đã được dùng cho đơn hàng nên không đổi mã được."],
  ["khong duoc nho hon so luot da dung", "Số lượt dùng không được ít hơn số lượt khách đã dùng."],
  ["can danh sach mon hoac don hang", "Vui lòng chọn món trước khi nhập mã."],
  ["tinh trang khuyen mai khong hop le", "Cách lọc chưa hợp lệ. Vui lòng chọn lại."],
  // Bao cao
  ["ngay bat dau phai truoc", "Ngày bắt đầu phải trước hoặc bằng ngày kết thúc."],
  ["khoang thoi gian toi da", "Khoảng thời gian quá dài. Vui lòng chọn ngắn hơn."],
  ["cach nhom khong hop le", "Cách xem chưa hợp lệ. Vui lòng chọn lại."],
  // Nhan vien, ca, lich
  ["ho ten nhan vien la bat buoc", "Vui lòng nhập họ tên nhân viên."],
  ["ma nhan vien phai tu", "Mã nhân viên cần từ 2 đến 30 ký tự, chỉ gồm chữ không dấu, số và dấu gạch."],
  ["ma nhan vien da ton tai", "Đã có nhân viên dùng mã này."],
  ["tai khoan nay da gan cho nhan vien khac", "Tài khoản đăng nhập này đã gắn với nhân viên khác."],
  ["ngay vao lam khong hop le", "Ngày vào làm chưa hợp lệ."],
  ["nhan vien khong ton tai", "Không tìm thấy nhân viên."],
  ["trang thai nhan vien khong hop le", "Tình trạng làm việc chưa hợp lệ."],
  ["ten ca la bat buoc", "Vui lòng nhập tên ca."],
  ["ten ca da ton tai", "Đã có ca trùng tên."],
  ["gio lam viec khong hop le", "Giờ làm chưa hợp lệ."],
  ["gio bat dau va gio ket thuc khong duoc trung", "Giờ bắt đầu và giờ kết thúc không được trùng nhau."],
  ["ca lam viec khong ton tai", "Không tìm thấy ca làm."],
  ["ca lam viec da ngung su dung", "Ca này đã ngừng sử dụng."],
  ["gio moi bi chong", "Giờ mới bị trùng với ca khác mà nhân viên đã được xếp."],
  ["lich lam viec khong ton tai", "Không tìm thấy lịch làm."],
  ["nhan vien khong o trang thai dang lam", "Nhân viên đang nghỉ nên không xếp lịch được."],
  ["nhan vien da co ca lam viec trung gio", "Nhân viên đã có ca khác trùng giờ trong ngày này."],
  ["nhan vien da duoc xep vao ca nay", "Nhân viên đã được xếp vào ca này trong ngày."],
  ["ngay lam khong hop le", "Vui lòng chọn ngày làm."],
  ["khong the xep lich cho ngay da qua", "Không xếp lịch được cho ngày đã qua."],
  ["lich da huy, khong the sua", "Lịch đã huỷ nên không sửa được. Hãy xếp lịch mới."],
  ["lich da cham cong", "Lịch đã chấm công nên không đổi ca hoặc ngày được."],
  ["chua den ngay lam", "Chưa đến ngày làm nên chưa chấm công được."],
  ["trang thai lich khong hop le", "Tình trạng lịch chưa hợp lệ."],
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

/* Khuyen mai, nhan vien, lich lam: ma he thong -> nhan. */
const TINH_TRANG_KHUYEN_MAI = {
  DANG_DIEN_RA: {nhan: "Đang áp dụng", mau: "badge-on"},
  SAP_DIEN_RA: {nhan: "Sắp diễn ra", mau: "badge-info"},
  HET_LUOT: {nhan: "Hết lượt", mau: "badge-wait"},
  DA_KET_THUC: {nhan: "Đã kết thúc", mau: "badge-muted"},
  DA_TAT: {nhan: "Đang tắt", mau: "badge-off"},
};
const CACH_GIAM_GIA = {PHAN_TRAM: "Giảm theo %", SO_TIEN: "Giảm số tiền"};
const TINH_TRANG_NHAN_VIEN = {
  DANG_LAM: {nhan: "Đang làm", mau: "badge-on"},
  TAM_NGHI: {nhan: "Tạm nghỉ", mau: "badge-wait"},
  NGHI_VIEC: {nhan: "Đã nghỉ việc", mau: "badge-muted"},
};
const TINH_TRANG_LICH = {
  DA_XEP: {nhan: "Đã xếp", mau: "badge-info"},
  DA_LAM: {nhan: "Đã đi làm", mau: "badge-on"},
  VANG: {nhan: "Vắng", mau: "badge-off"},
  DA_HUY: {nhan: "Đã huỷ", mau: "badge-muted"},
};

const _luaChon = (bang) => Object.entries(bang).map(([ma, t]) => ({ma, nhan: t.nhan || t}));
function huyHieuKhuyenMai(ma) { return huyHieu(TINH_TRANG_KHUYEN_MAI, ma); }
function huyHieuNhanVien(ma) { return huyHieu(TINH_TRANG_NHAN_VIEN, ma); }
function huyHieuLich(ma) { return huyHieu(TINH_TRANG_LICH, ma); }
function luaChonTinhTrangKhuyenMai() { return _luaChon(TINH_TRANG_KHUYEN_MAI); }
function luaChonCachGiam() { return _luaChon(CACH_GIAM_GIA); }
function luaChonTinhTrangNhanVien() { return _luaChon(TINH_TRANG_NHAN_VIEN); }
function luaChonTinhTrangLich() { return _luaChon(TINH_TRANG_LICH); }
function nhanCachGiam(ma) { return CACH_GIAM_GIA[ma] || "Khác"; }
function giamTheoPhanTram(km) { return !!km && km.LoaiGiamGia === "PHAN_TRAM"; }
function nhanVienDangLam(nv) { return !!nv && nv.TrangThai === "DANG_LAM"; }
function lichConXep(l) { return !!l && l.TrangThai === "DA_XEP"; }
function lichDaHuy(l) { return !!l && l.TrangThai === "DA_HUY"; }
/* Ma gui len khi cham cong / huy lich - trang goi qua ten viec, khong viet ma. */
const MA_VIEC_LICH = {diLam: "DA_LAM", vang: "VANG", huy: "DA_HUY"};
function maViecLich(viec) { return MA_VIEC_LICH[viec]; }
/** Mo ta muc giam: "10% (tối đa 20.000 ₫)" / "15.000 ₫". */
function moTaMucGiam(km) {
  if (!km) return "—";
  if (giamTheoPhanTram(km)) {
    const s = `${Number(km.GiaTriGiam).toLocaleString("vi-VN")}%`;
    return km.GiamToiDa ? `${s} (tối đa ${dinhDangGia(km.GiamToiDa)})` : s;
  }
  return dinhDangGia(km.GiaTriGiam);
}

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

/** Hop thoai xac nhan dung chung, thay cho confirm() cua trinh duyet.
 *
 * Tra ve Promise<boolean>: true khi nguoi dung dong y. Cach goi:
 *   if (!(await xacNhan("Xoa nhom nay?"))) return;
 * tuyChon: {nhanDongY, nhanHuy, nguyHiem} - nut dong y mau do khi nguyHiem.
 */
let _xnDangCho = null;  // {ketThuc} cua lan goi chua tra loi

function xacNhan(text, tuyChon) {
  const o = tuyChon || {};
  // Lan goi truoc chua duoc tra loi (vd bam nut khac khi hop thoai dang mo) -> coi nhu huy.
  if (_xnDangCho) _xnDangCho(false);

  return new Promise((traLoi) => {
    let m = document.getElementById("modal-xac-nhan");
    if (!m) {
      m = document.createElement("div");
      m.id = "modal-xac-nhan";
      m.className = "modal hidden";
      m.setAttribute("role", "alertdialog");
      m.setAttribute("aria-modal", "true");
      m.setAttribute("aria-labelledby", "xac-nhan-title");
      m.innerHTML = `
        <div class="modal-card modal-nhan">
          <div class="modal-head">
            <h3 id="xac-nhan-title">Xác nhận</h3>
            <button type="button" class="modal-close" data-xn-huy aria-label="Đóng">×</button>
          </div>
          <div class="modal-body"><p class="modal-nhan-text" id="xac-nhan-text"></p></div>
          <div class="modal-foot">
            <button type="button" class="btn-outline" data-xn-huy id="xac-nhan-huy">Huỷ</button>
            <button type="button" id="xac-nhan-dong-y">Đồng ý</button>
          </div>
        </div>`;
      document.body.appendChild(m);
    }

    const nutDongY = m.querySelector("#xac-nhan-dong-y");
    const nutHuy = m.querySelector("#xac-nhan-huy");
    const truocDo = document.activeElement;
    m.querySelector("#xac-nhan-text").textContent = text;
    nutDongY.textContent = o.nhanDongY || "Đồng ý";
    nutHuy.textContent = o.nhanHuy || "Huỷ";
    nutDongY.classList.toggle("btn-danger", Boolean(o.nguyHiem));

    let daXong = false;
    const ketThuc = (kq) => {
      if (daXong) return;
      daXong = true;
      _xnDangCho = null;
      document.removeEventListener("keydown", nghePhim, true);
      m.removeEventListener("click", ngheNen);
      m.querySelectorAll("[data-xn-huy]").forEach((b) => b.removeEventListener("click", huy));
      nutDongY.removeEventListener("click", dongYNut);
      m.classList.add("hidden");
      if (truocDo && truocDo.focus) truocDo.focus();
      traLoi(kq);
    };
    const huy = () => ketThuc(false);
    const dongYNut = () => ketThuc(true);
    const ngheNen = (e) => {
      if (e.target === m) ketThuc(false);  // bam ra nen mo = huy
    };
    const nghePhim = (e) => {
      if (m.classList.contains("hidden")) return;
      if (e.key === "Escape") { e.stopPropagation(); ketThuc(false); }
      if (e.key === "Enter" && document.activeElement !== nutHuy) { e.preventDefault(); ketThuc(true); }
    };

    nutDongY.addEventListener("click", dongYNut);
    m.querySelectorAll("[data-xn-huy]").forEach((b) => b.addEventListener("click", huy));
    m.addEventListener("click", ngheNen);
    document.addEventListener("keydown", nghePhim, true);
    _xnDangCho = ketThuc;

    m.classList.remove("hidden");
    setTimeout(() => nutDongY.focus(), 30);
  });
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
