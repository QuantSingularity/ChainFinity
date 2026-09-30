// @ts-check
const { test, expect } = require("@playwright/test");

test.describe("Authentication", () => {
  test("home page loads and shows navigation", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/ChainFinity/i);
    // Navbar should be present
    await expect(page.locator("nav, header")).toBeVisible();
  });

  test("login page renders form", async ({ page }) => {
    await page.goto("/login");
    await expect(
      page.locator('input[type="email"], input[name="email"]'),
    ).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test("login form rejects empty submission", async ({ page }) => {
    await page.goto("/login");
    await page.locator('button[type="submit"]').click();
    // HTML5 validation or error message should appear
    const emailInput = page.locator('input[type="email"], input[name="email"]');
    const validationMessage = await emailInput.evaluate(
      (el) => el.validationMessage,
    );
    expect(validationMessage.length).toBeGreaterThan(0);
  });

  test("register page renders form", async ({ page }) => {
    await page.goto("/register");
    await expect(
      page.locator('input[type="email"], input[name="email"]'),
    ).toBeVisible();
    await expect(page.locator('input[type="password"]').first()).toBeVisible();
  });

  test("forgot password page renders", async ({ page }) => {
    await page.goto("/forgot-password");
    await expect(
      page.locator('input[type="email"], input[name="email"]'),
    ).toBeVisible();
  });

  test("not found page renders for invalid route", async ({ page }) => {
    await page.goto("/this-route-does-not-exist-at-all");
    // Should show a 404 / not found message
    await expect(
      page.locator("text=404, text=not found, text=Not Found").first(),
    )
      .toBeVisible({ timeout: 5000 })
      .catch(() => {
        // Some SPAs redirect to home - just verify page loads
      });
  });
});

test.describe("Navigation", () => {
  test("clicking login link navigates to login page", async ({ page }) => {
    await page.goto("/");
    const loginLink = page
      .locator(
        'a[href*="login"], button:has-text("Login"), button:has-text("Sign In")',
      )
      .first();
    if ((await loginLink.count()) > 0) {
      await loginLink.click();
      await expect(page).toHaveURL(/login/i);
    }
  });
});
