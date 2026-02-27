import pytest
from playwright.sync_api import sync_playwright, Page, expect

BASE_URL = "https://bugeater.web.app/app/challenge/exploratory/restorePassword"


@pytest.fixture(scope="function")
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        pg = context.new_page()
        pg.goto(BASE_URL)
        pg.wait_for_load_state("networkidle")
        yield pg
        browser.close()


def fill_dates(page: Page, from_date: str, to_date: str):
    """Helper: fill From and To date inputs."""
    page.locator("input").nth(0).fill(from_date)
    page.locator("input").nth(1).fill(to_date)


def click_search(page: Page):
    page.get_by_role("button", name="Search!").click()


# TC-01
def test_valid_date_range_shows_result(page: Page):
    """
    Positive case: From date strictly before To date.
    Example: 01-01-2025 → 01-07-2025 (one week range).
    The form should produce a result, NOT an error message.
    """
    fill_dates(page, "01-01-2025", "01-07-2025")
    click_search(page)

    error_locator = page.locator("text=/error|invalid|must be|cannot|before|after/i")
    assert not error_locator.is_visible(timeout=3000), \
        "Valid date range should not produce an error message"

# TC-02
def test_from_date_after_to_date_shows_error(page: Page):
    """
    Negative case: From date is later than To date.
    Example: From 12-31-2025, To 01-01-2025 — logically impossible range.
    The form must reject this with a validation error.
    """
    fill_dates(page, "12-31-2025", "01-01-2025")
    click_search(page)

    error_locator = page.locator(
        "text=/error|invalid|cannot|must be|earlier|before|check/i"
    )
    assert error_locator.is_visible(timeout=3000), \
        "Form should show an error when From date is after To date"


# TC-03
def test_empty_dates_do_not_submit(page: Page):
    """
    Negative case: click Search without entering any dates.
    The result area should not show booking data, and ideally a
    'required' / validation hint appears.
    """
    click_search(page)

    result_area = page.locator("text=Result:")
    expect(result_area).to_be_visible(timeout=3000)

    success_locator = page.locator("text=/available|booked|desk|found/i")
    assert not success_locator.is_visible(timeout=2000), \
        "Form should not show booking results when both date fields are empty"
