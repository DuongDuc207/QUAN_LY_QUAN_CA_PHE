const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { test } = require("node:test");
const root = path.join(__dirname, "..", "sprint4", "frontend", "static", "js");

function catalog(apiGoi) {
  const context = vm.createContext({
    URLSearchParams, apiGoi,
    document: { addEventListener() {} }, window: { addEventListener() {} },
  });
  vm.runInContext(fs.readFileSync(path.join(root, "main.js"), "utf8"), context);
  // Inject apiGoi after main.js defines its browser implementation.
  context.apiGoi = apiGoi;
  vm.runInContext(fs.readFileSync(path.join(root, "thuc_don.js"), "utf8"), context);
  return vm.runInContext("ThucDon", context);
}

const mon = (id, extra = {}) => ({
  MonID: id, DanhMucID: 1, TenDanhMuc: "Cà phê", TenMon: `Món ${id}`,
  GiaBan: 35000, TrangThai: true, DanhMucHienThi: true, ...extra,
});

test("loads every page, with the same ordering for sales and menu", async () => {
  const items = Array.from({length: 205}, (_, i) => mon(i + 1));
  const calls = [];
  const td = catalog(async (_, url) => {
    const p = new URL(url, "http://localhost").searchParams;
    calls.push(p);
    const offset = (Number(p.get("page")) - 1) * 100;
    return {ok: true, data: {items: items.slice(offset, offset + 100), total: items.length}};
  });
  const menu = await td.taiTatCa();
  const sales = await td.taiTatCa(true);
  assert.equal(menu.data.length, 205);
  assert.deepEqual(menu.data, sales.data);
  assert.equal(calls.length, 6);
  assert.ok(calls.slice(3).every(p => p.get("dang_ban") === "1"));
});

test("page failure never exposes an incomplete menu as a success", async () => {
  let calls = 0;
  const td = catalog(async () => ++calls === 1
    ? {ok: true, data: {items: [mon(1)], total: 2}}
    : {ok: false, status: 503});
  const result = await td.taiTatCa();
  assert.equal(result.ok, false);
  assert.equal(result.status, 503);
});

test("active menu matches sales and keeps stopped or hidden items manageable", () => {
  const td = catalog();
  const items = [mon(1), mon(2, {TrangThai: false}), mon(3, {DanhMucHienThi: false})];
  assert.deepEqual(Array.from(td.loc(items, "", "", "dang-ban"), m => m.MonID), [1]);
  assert.deepEqual(Array.from(td.loc(items, "", "", "ngung-ban"), m => m.MonID), [2, 3]);
  assert.equal(td.loc(items).length, 3);
});

test("accent-insensitive search combines group and availability filters", () => {
  const td = catalog();
  const items = [
    mon(1, {TenMon: "Cà phê đen đá"}),
    mon(2, {TenMon: "Cà phê đen đá", DanhMucID: 2}),
    mon(3, {TenMon: "Cà phê đen đá", TrangThai: false}),
  ];
  assert.deepEqual(Array.from(td.loc(items, "ca phe den da", "1", "dang-ban"), m => m.MonID), [1]);
  assert.deepEqual(Array.from(td.loc(items, "ca phe den da", "1", "ngung-ban"), m => m.MonID), [3]);
});

test("shared cards escape names and block unsafe image protocols", () => {
  const td = catalog();
  const html = td.noiDungThe(mon(1, {TenMon: '<script>alert("x")</script>', HinhAnh: 'javascript:alert(1)'}));
  assert.ok(!html.includes("<script>"));
  assert.ok(!html.includes("javascript:"));
  assert.ok(html.includes("&lt;script&gt;"));
  assert.ok(td.noiDungThe(mon(2, {HinhAnh: "/static/images/drink.png"})).includes('src="/static/images/drink.png"'));
});
