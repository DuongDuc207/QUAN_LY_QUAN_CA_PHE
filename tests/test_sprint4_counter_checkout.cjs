const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { test } = require("node:test");
const context = vm.createContext({document:{addEventListener() {}}});
vm.runInContext(fs.readFileSync(path.join(__dirname,"..","sprint4","frontend","static","js","main.js"),"utf8"),context);

test("preparation and service actions require confirmed payment", () => {
  for (const status of ["CHUA_THANH_TOAN","CHO_XAC_NHAN","THAT_BAI","HOAN_MOT_PHAN","DA_HOAN_TIEN"]) {
    for (const state of ["MOI","CHO_PHA_CHE","DANG_PHA_CHE"]) {
      assert.equal(context.buocTiepDon({TrangThai:state,TrangThaiThanhToan:status}),null);
    }
  }
  assert.equal(context.buocTiepDon({TrangThai:"CHO_PHA_CHE",TrangThaiThanhToan:"THANH_CONG"}).ma,"DANG_PHA_CHE");
  assert.equal(context.buocTiepDon({TrangThai:"DANG_PHA_CHE",TrangThaiThanhToan:"THANH_CONG"}).ma,"HOAN_THANH");
  assert.equal(context.buocTiepDon({TrangThai:"DA_HUY",TrangThaiThanhToan:"THANH_CONG"}),null);
});

test("zero-total checkout does not offer refunds or claim money is held", () => {
  assert.equal(context.donConGiuTien({ThanhTien:0,TrangThaiThanhToan:"THANH_CONG"}),false);
  assert.equal(context.thanhToanHoanDuoc({SoTien:0,TrangThai:"THANH_CONG"}),false);
});
