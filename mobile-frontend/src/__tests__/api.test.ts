import { handleApiError } from "../services/api";

describe("handleApiError", () => {
  it("maps response errors", () => {
    const result = handleApiError({
      response: { status: 404, data: { detail: "Not found" } },
    });
    expect(result).toEqual({ status: 404, message: "Not found" });
  });

  it("maps missing-detail response errors", () => {
    const result = handleApiError({
      response: { status: 500, data: {} },
    });
    expect(result).toEqual({ status: 500, message: "An error occurred" });
  });

  it("maps network errors", () => {
    const result = handleApiError({ request: {} });
    expect(result.status).toBe(0);
    expect(result.message).toMatch(/No response from server/);
  });

  it("maps unknown errors", () => {
    const result = handleApiError(new Error("boom"));
    expect(result).toEqual({ status: 0, message: "boom" });
  });
});

describe("API endpoint paths", () => {
  it("uses versioned backend routes", () => {
    // Guards against regressing to the unversioned paths the web app
    // originally used; the backend serves everything under /api/v1.
    const fs = require("fs") as typeof import("fs");
    const path = require("path") as typeof import("path");
    const source = fs.readFileSync(
      path.join(__dirname, "../services/api.ts"),
      "utf8",
    );
    expect(source).toContain("/api/v1/auth/login");
    expect(source).toContain("/api/v1/auth/me");
    expect(source).toContain("/api/v1/auth/register");
    expect(source).toContain("/api/v1/blockchain/portfolio");
    expect(source).not.toContain('"/api/auth/token"');
    expect(source).toContain("/api/v1/portfolios/");
    expect(source).toContain("/api/v1/risk/assess/");
    expect(source).toContain("/api/v1/ai/status");
    expect(source).toContain("/api/v1/ai/portfolio/");
  });
});
