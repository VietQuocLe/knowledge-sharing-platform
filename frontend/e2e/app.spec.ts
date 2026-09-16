import { test, expect } from '@playwright/test'

test.describe('Knowledge Sharing Platform - E2E Core User Journeys', () => {
  test('1. Home Page renders brand and core hero sections', async ({ page }) => {
    await page.goto('/')

    // Verify brand title in header/sidebar
    await expect(page.getByText('HCMC-VAULT').first()).toBeVisible()

    // Verify main hero heading
    const heroHeading = page.locator('h1')
    await expect(heroHeading).toContainText('Nền tảng chia sẻ học liệu trực tuyến')

    // Verify department browse section
    const sectionHeading = page.locator('h2')
    await expect(sectionHeading).toContainText('Danh sách Khoa đào tạo')
  })

  test('2. Login Page displays credentials form and validation controls', async ({ page }) => {
    await page.goto('/login')

    // Verify login headline
    await expect(page.getByRole('heading', { name: 'Chào mừng trở lại' })).toBeVisible()

    // Verify form input elements
    const emailInput = page.locator('input[type="email"]')
    const passwordInput = page.locator('input[type="password"]')
    const submitBtn = page.locator('button[type="submit"]')

    await expect(emailInput).toBeVisible()
    await expect(passwordInput).toBeVisible()
    await expect(submitBtn).toBeVisible()

    // Fill sample demo credentials
    await emailInput.fill('user@ou.edu.vn')
    await passwordInput.fill('User@123456')

    await expect(emailInput).toHaveValue('user@ou.edu.vn')
  })

  test('3. Protected Admin Route Guard redirects unauthenticated visitors to /login', async ({ page }) => {
    // Attempting to visit /admin without session should redirect to /login
    await page.goto('/admin')

    await page.waitForURL('**/login**')
    expect(page.url()).toContain('/login')

    // Verify login page is rendered
    await expect(page.getByRole('heading', { name: 'Chào mừng trở lại' })).toBeVisible()
  })

  test('4. Registration page navigation from login page', async ({ page }) => {
    await page.goto('/login')

    // Click register navigation link ("Tạo tài khoản")
    const registerLink = page.getByRole('link', { name: /tạo tài khoản/i })
    await expect(registerLink).toBeVisible()
    await registerLink.click()

    // Verify URL transitions to /register
    await page.waitForURL('**/register**')
    expect(page.url()).toContain('/register')
  })
})
