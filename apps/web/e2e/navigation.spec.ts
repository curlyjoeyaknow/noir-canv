import { test, expect } from "@playwright/test";

test.describe("Navigation", () => {
  test("home page loads with Noir Canvas heading", async ({ page }) => {
    await page.goto("/");
    await expect(
      page.locator("h1", { hasText: "Noir Canvas" }),
    ).toBeVisible();
  });

  test("home page has featured works section", async ({ page }) => {
    await page.goto("/");
    await expect(
      page.locator("h2", { hasText: "Featured Works" }),
    ).toBeVisible();
  });

  test("navigates to /artists page", async ({ page }) => {
    await page.goto("/artists");
    await expect(
      page.locator("h1", { hasText: "Our Artists" }),
    ).toBeVisible();
  });

  test("artists page lists multiple artists", async ({ page }) => {
    await page.goto("/artists");
    const artistCards = page.locator("article");
    await expect(artistCards.first()).toBeVisible();
    const count = await artistCards.count();
    expect(count).toBeGreaterThan(1);
  });

  test("navigates to artist detail page", async ({ page }) => {
    await page.goto("/artists/kai-voss");
    await expect(
      page.locator("h1", { hasText: "Kai Voss" }),
    ).toBeVisible();
  });

  test("artist detail page shows artist statement", async ({ page }) => {
    await page.goto("/artists/kai-voss");
    await expect(page.locator("blockquote")).toBeVisible();
  });

  test("navigates to piece detail page", async ({ page }) => {
    await page.goto("/pieces/kai-voss-001");
    await expect(
      page.locator("h1", { hasText: "Dusk Amber II" }),
    ).toBeVisible();
  });

  test("piece detail page shows artist name link", async ({ page }) => {
    await page.goto("/pieces/kai-voss-001");
    const artistLink = page.locator("a", { hasText: "Kai Voss" });
    await expect(artistLink).toBeVisible();
    await expect(artistLink).toHaveAttribute("href", "/artists/kai-voss");
  });

  test("piece detail page shows edition badge", async ({ page }) => {
    await page.goto("/pieces/kai-voss-001");
    const progressBar = page.locator("[role='progressbar']");
    await expect(progressBar).toBeVisible();
  });

  test("navigates to collections page", async ({ page }) => {
    await page.goto("/collections");
    await expect(
      page.locator("h1", { hasText: "Collections" }),
    ).toBeVisible();
  });

  test("collections page lists multiple collections", async ({ page }) => {
    await page.goto("/collections");
    const articles = page.locator("article");
    await expect(articles.first()).toBeVisible();
    const count = await articles.count();
    expect(count).toBeGreaterThan(1);
  });

  test("clicking an artist card navigates to artist detail page", async ({ page }) => {
    await page.goto("/artists");
    const firstCard = page.locator("article").first();
    await firstCard.click();
    await expect(page).toHaveURL(/\/artists\/[a-z][a-z0-9-]+$/);
    await expect(page.locator("h1")).toBeVisible();
  });

  test("returns 404 for invalid artist slug", async ({ page }) => {
    const response = await page.goto("/artists/this-artist-does-not-exist");
    expect(response?.status()).toBe(404);
  });

  test("returns 404 for invalid piece slug", async ({ page }) => {
    const response = await page.goto("/pieces/fake-piece-999");
    expect(response?.status()).toBe(404);
  });

  test("404 page displays helpful content", async ({ page }) => {
    await page.goto("/nonexistent-route-xyz");
    await expect(
      page.locator("h1", { hasText: "Page not found" }),
    ).toBeVisible();
    await expect(
      page.locator("a", { hasText: "Go Home" }),
    ).toBeVisible();
  });

  test("home page discover artists link works", async ({ page }) => {
    await page.goto("/");
    await page.click("a:has-text('Discover Artists')");
    await expect(page).toHaveURL(/\/artists$/);
    await expect(
      page.locator("h1", { hasText: "Our Artists" }),
    ).toBeVisible();
  });

  test("home page browse collections link works", async ({ page }) => {
    await page.goto("/");
    await page.click("a:has-text('Browse Collections')");
    await expect(page).toHaveURL(/\/collections$/);
    await expect(
      page.locator("h1", { hasText: "Collections" }),
    ).toBeVisible();
  });
});
