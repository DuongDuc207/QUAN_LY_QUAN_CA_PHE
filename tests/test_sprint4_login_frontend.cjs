const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { test } = require("node:test");

const root = path.join(__dirname, "..", "sprint4", "frontend");
const html = fs.readFileSync(path.join(root, "templates", "login.html"), "utf8");
const main = fs.readFileSync(path.join(root, "static", "js", "main.js"), "utf8");
const script = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)][0][1];

function page(fetch) {
  let submit;
  const button = { disabled: false, textContent: "Đăng nhập" };
  const classes = new Set(["hidden"]);
  const error = {
    textContent: "",
    classList: { add: c => classes.add(c), remove: c => classes.delete(c) },
  };
  const form = {
    addEventListener: (_, handler) => { submit = handler; },
    querySelector: () => button,
  };
  const context = vm.createContext({
    document: {
      addEventListener() {},
      getElementById: id => id === "login-form" ? form : error,
    },
    window: { location: { href: "/login" } },
    FormData: class { get(name) { return name === "email" ? " test@example.com " : "secret123"; } },
    AbortSignal,
    fetch,
  });
  vm.runInContext(main, context);
  vm.runInContext(script, context);
  return {
    button, error, context, classes,
    submit: () => submit({ preventDefault() {}, target: form }),
  };
}

test("successful login redirects and sends trimmed email", async () => {
  const p = page(async (url, options) => {
    assert.equal(url, "/api/v1/auth/login");
    assert.equal(options.method, "POST");
    assert.deepEqual(JSON.parse(options.body), { email: "test@example.com", password: "secret123" });
    assert.ok(options.signal);
    return { ok: true, json: async () => ({ success: true }) };
  });
  await p.submit();
  assert.equal(p.context.window.location.href, "/dashboard");
});

test("HTTP failures, non-JSON bodies and network errors show errors and allow retry", async () => {
  const failures = [
    async () => ({ ok: false, status: 401, json: async () => ({ message: "Email hoac mat khau khong dung" }) }),
    async () => ({ ok: false, status: 503, json: async () => ({ message: "Co so du lieu chua san sang" }) }),
    async () => ({ ok: false, status: 500, json: async () => { throw new SyntaxError("HTML response"); } }),
    async () => ({ ok: false, status: 502, json: async () => null }),
    async () => { throw new TypeError("Network failure"); },
    async () => { throw new DOMException("Timeout", "TimeoutError"); },
  ];
  for (const fail of failures) {
    let calls = 0;
    const p = page(async (...args) => ++calls === 1 ? fail(...args) : { ok: true, json: async () => ({ success: true }) });
    await p.submit();
    assert.equal(p.context.window.location.href, "/login");
    assert.equal(p.classes.has("hidden"), false);
    assert.ok(p.error.textContent.length > 0);
    assert.equal(p.button.disabled, false);
    assert.equal(p.button.textContent, "Đăng nhập");
    await p.submit();
    assert.equal(p.context.window.location.href, "/dashboard");
  }
});

test("a pending request disables the button and prevents duplicate submissions", async () => {
  let resolve;
  let calls = 0;
  const p = page(() => {
    calls++;
    return new Promise(done => { resolve = done; });
  });
  const pending = p.submit();
  assert.equal(p.button.disabled, true);
  assert.equal(p.button.textContent, "Đang đăng nhập…");
  await p.submit();
  assert.equal(calls, 1);
  resolve({ ok: true, json: async () => ({ success: true }) });
  await pending;
  assert.equal(p.button.disabled, false);
});
