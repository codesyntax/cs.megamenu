"""Selenium browser checks for the master-detail menu editor.

These tests need a running Plone site with `collective.megamenu` installed.
Set `PLONE_URL` to run them; they are skipped otherwise.

Example:

    PLONE_URL=http://127.0.0.1:8080/Plone make test-browser
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import json
import os
import pytest
import uuid


PLONE_URL = os.environ.get("PLONE_URL")
LRF_URL = os.environ.get("LRF_URL")
PLONE_USER = os.environ.get("PLONE_USER", "admin")
PLONE_PASSWORD = os.environ.get("PLONE_PASSWORD", "admin")

pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(not PLONE_URL, reason="set PLONE_URL to run browser tests"),
]


@pytest.fixture
def browser():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1400,1200")
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1400, 1200)
    try:
        yield driver
    finally:
        driver.quit()


def login(driver):
    driver.get(f"{PLONE_URL}/login")
    if driver.find_elements(By.ID, "__ac_name"):
        driver.find_element(By.ID, "__ac_name").send_keys(PLONE_USER)
        driver.find_element(By.ID, "__ac_password").send_keys(PLONE_PASSWORD)
        driver.find_element(By.ID, "buttons-login").click()
        WebDriverWait(driver, 20).until(lambda d: "/login" not in d.current_url)


def create_document(driver, title):
    driver.get(f"{PLONE_URL}/++add++Document")
    title_input = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((
            By.CSS_SELECTOR,
            "#form-widgets-IDublinCore-title",
        ))
    )
    title_input.clear()
    title_input.send_keys(title)
    driver.find_element(By.CSS_SELECTOR, "#form-buttons-save").click()
    WebDriverWait(driver, 20).until(
        lambda d: (
            "++add++" not in d.current_url
            and title in d.find_element(By.TAG_NAME, "body").text
        )
    )


def open_editor(driver):
    driver.get(f"{PLONE_URL}/@@edit")
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".megamenu-editor"))
    )
    tabs = driver.find_elements(By.CSS_SELECTOR, "form#form > nav.autotoc-nav a")
    if tabs:
        js_click(driver, tabs[-1])
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".megamenu-editor"))
        )


def reset_to_inherited(driver):
    if driver.find_elements(By.CSS_SELECTOR, '[data-action="use-inherited"]'):
        js_click(
            driver,
            driver.find_element(By.CSS_SELECTOR, '[data-action="use-inherited"]'),
        )
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".megamenu-empty"))
        )


def textarea_value(driver):
    return driver.find_element(By.CSS_SELECTOR, ".megamenu-json").get_attribute("value")


def severe_logs(driver):
    return [entry for entry in driver.get_log("browser") if entry["level"] == "SEVERE"]


def js_click(driver, element):
    driver.execute_script("arguments[0].click();", element)


def test_content_browser_selection_and_cleanup(browser):
    login(browser)
    title = f"Menu Target {uuid.uuid4().hex[:8]}"
    create_document(browser, title)

    open_editor(browser)
    reset_to_inherited(browser)
    js_click(
        browser,
        browser.find_element(
            By.CSS_SELECTOR, '.megamenu-empty [data-action="add-link"]'
        ),
    )
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((
            By.CSS_SELECTOR,
            ".megamenu-picker .content-browser-selected-items-wrapper a",
        ))
    )
    select_link = browser.find_element(
        By.CSS_SELECTOR,
        ".megamenu-picker .content-browser-selected-items-wrapper a",
    )
    browser.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});", select_link
    )
    select_link.click()
    WebDriverWait(browser, 15).until(
        lambda d: any(
            title in item.text
            for item in d.find_elements(By.CSS_SELECTOR, ".contentItem")
        )
    )
    target = next(
        item
        for item in browser.find_elements(By.CSS_SELECTOR, ".contentItem")
        if title in item.text
    )
    js_click(browser, target)
    select_buttons = WebDriverWait(browser, 10).until(
        lambda d: (
            d.find_elements(By.CSS_SELECTOR, ".levelToolbar button.btn-primary")
            or False
        )
    )
    js_click(browser, select_buttons[-1])
    WebDriverWait(browser, 10).until(
        lambda d: not d.find_elements(By.CSS_SELECTOR, ".content-browser")
    )

    uid = browser.find_element(
        By.CSS_SELECTOR, ".megamenu-picker .pat-contentbrowser"
    ).get_attribute("value")
    data = json.loads(textarea_value(browser))
    assert uid
    assert data["items"][0]["internal_uid"] == uid

    js_click(
        browser,
        browser.find_element(
            By.CSS_SELECTOR, '.megamenu-tree-row.is-selected [data-action="delete"]'
        ),
    )
    WebDriverWait(browser, 10).until(
        lambda d: json.loads(textarea_value(d))["items"] == []
    )
    assert not browser.find_elements(By.CSS_SELECTOR, ".megamenu-picker")
    assert severe_logs(browser) == []


def test_external_url_tab(browser):
    login(browser)
    open_editor(browser)
    reset_to_inherited(browser)
    js_click(
        browser,
        browser.find_element(
            By.CSS_SELECTOR, '.megamenu-empty [data-action="add-link"]'
        ),
    )
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((
            By.CSS_SELECTOR,
            ".megamenu-target-editor .autotoc-nav",
        ))
    )

    nav_links = WebDriverWait(browser, 10).until(
        lambda d: (
            d.find_elements(By.CSS_SELECTOR, ".megamenu-target-editor .autotoc-nav a")
            or False
        )
    )
    external_tab = nav_links[1]
    js_click(browser, external_tab)

    external_input = WebDriverWait(browser, 10).until(
        EC.visibility_of_element_located((
            By.CSS_SELECTOR,
            '[data-field="external_url"]',
        ))
    )
    external_input.send_keys("https://example.com")
    external_input.send_keys(Keys.TAB)
    WebDriverWait(browser, 10).until(
        lambda d: (
            json.loads(textarea_value(d))["items"][0].get("external_url")
            == "https://example.com"
        )
    )

    nav_links = WebDriverWait(browser, 10).until(
        lambda d: (
            d.find_elements(By.CSS_SELECTOR, ".megamenu-target-editor .autotoc-nav a")
            or False
        )
    )
    assert "active" in (nav_links[1].get_attribute("class") or "").split()
    assert browser.find_element(
        By.CSS_SELECTOR, '[data-field="external_url"]'
    ).is_displayed()

    js_click(
        browser,
        browser.find_element(
            By.CSS_SELECTOR, '.megamenu-tree-row.is-selected [data-action="delete"]'
        ),
    )
    WebDriverWait(browser, 10).until(
        lambda d: json.loads(textarea_value(d))["items"] == []
    )
    assert severe_logs(browser) == []


def test_use_inherited_menu(browser):
    login(browser)
    open_editor(browser)
    reset_to_inherited(browser)

    js_click(
        browser,
        browser.find_element(
            By.CSS_SELECTOR, '.megamenu-empty [data-action="add-link"]'
        ),
    )
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((
            By.CSS_SELECTOR,
            '[data-action="use-inherited"]',
        ))
    )
    js_click(
        browser,
        browser.find_element(By.CSS_SELECTOR, '[data-action="use-inherited"]'),
    )
    WebDriverWait(browser, 10).until(
        lambda d: (
            textarea_value(d) == ""
            and d.find_elements(By.CSS_SELECTOR, ".megamenu-empty")
        )
    )
    assert severe_logs(browser) == []


@pytest.mark.skipif(not LRF_URL, reason="set LRF_URL to an LRF edit URL")
def test_lrf_edit_form_has_menu_widget(browser):
    login(browser)
    browser.get(LRF_URL)

    WebDriverWait(browser, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".megamenu-widget"))
    )
    tabs = browser.find_elements(By.CSS_SELECTOR, "form#form > nav.autotoc-nav a")
    if tabs:
        js_click(browser, tabs[-1])
        WebDriverWait(browser, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".megamenu-editor"))
        )
    assert browser.find_element(By.CSS_SELECTOR, ".pat-megamenu")
