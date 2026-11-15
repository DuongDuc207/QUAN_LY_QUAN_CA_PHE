const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { test } = require("node:test");

const source = fs.readFileSync(path.join(__dirname, "..", "sprint4", "frontend", "static", "js", "main.js"), "utf8");
function api(fetch) {
  const context = vm.createContext({fetch, document: {addEventListener() {}}});
  vm.runInContext(source, context);
  return context.apiGoi;
}

test("server failures show a system message instead of blaming order input", async () => {
  for (const status of [500, 502, 503]) {
    const call = api(async () => ({ok: false, status, json: async () => ({success: false, message: "Co so du lieu chua san sang"})}));
    const result = await call("POST", "/api/v1/orders", {items: []});
    assert.equal(result.ok, false);
    assert.equal(result.status, status);
    assert.ok(result.loi.includes("Hệ thống"));
    assert.ok(!result.loi.includes("kiểm tra lại thông tin"));
    assert.ok(!result.loi.includes("Co so du lieu"));
  }
});

test("business validation still explains the actual order error", async () => {
  const call = api(async () => ({ok: false, status: 400, json: async () => ({success: false, message: "Mon dang tam ngung ban"})}));
  const result = await call("POST", "/api/v1/orders", {});
  assert.ok(result.loi.includes("tạm ngưng bán"));
});

test("network failure remains a connection error", async () => {
  const call = api(async () => { throw new TypeError("Offline"); });
  const result = await call("POST", "/api/v1/orders", {});
  assert.equal(result.status, 0);
  assert.ok(result.loi.includes("Không kết nối"));
});
