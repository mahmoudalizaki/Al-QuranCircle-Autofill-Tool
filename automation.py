import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

from playwright.sync_api import Playwright, sync_playwright, TimeoutError as PlaywrightTimeoutError

from utils import log_action, load_profile


EXTENSION_ID = "mpbjkejclgfgadiemmefgebjfooflfhl"


def get_extension_dir() -> Optional[Path]:
    """Resolve the latest version folder of the Chrome extension for the current user.

    Looks under:
        %LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Extensions\\{EXTENSION_ID}\\
    """

    local_appdata = os.environ.get("LOCALAPPDATA")
    if not local_appdata:
        logging.warning("LOCALAPPDATA not set; cannot resolve Chrome extension directory.")
        return None

    base_dir = (
        Path(local_appdata)
        / "Google"
        / "Chrome"
        / "User Data"
        / "Default"
        / "Extensions"
        / EXTENSION_ID          # <-- لا تضف هنا 3.1.0_0
    )

    if not base_dir.is_dir():
        logging.warning("Chrome extension base directory not found: %s", base_dir)
        return None

    version_dirs = [p for p in base_dir.iterdir() if p.is_dir()]
    if not version_dirs:
        logging.warning("No version subfolders found under Chrome extension directory: %s", base_dir)
        return None

    # Choose the version folder with the highest name (e.g. 3.1.0_0 > 3.0.0_0)
    latest = sorted(version_dirs, key=lambda p: p.name)[-1]
    logging.info("Using Chrome extension directory: %s", latest)
    return latest


DEFAULT_SELECTORS: Dict[str, str] = {
    # Map profile keys to CSS selectors of the Google Form fields
    # These selectors are derived from the provided form HTML.
    # Email: <input type="email" ... aria-label="Your email">
    "email": "input[type='email'][aria-label='Your email']",
    # Date: <input type="date" ... aria-labelledby="i10">
    "date": "input[type='date'][aria-labelledby='i10']",
    # Teacher Name: text input labelled by i11 i14
    "teacher_name": "input[type='text'][aria-labelledby='i11 i14']",
    # Student Name: text input labelled by i16 i19
    "student_name": "input[type='text'][aria-labelledby='i16 i19']",
    # Quran Surah: text input labelled by i21 i24
    "quran_surah": "input[type='text'][aria-labelledby='i21 i24']",
    # Noor Elbayan Page no.: text input labelled by i37 i40
    "noor_page": "input[type='text'][aria-labelledby='i37 i40']",
    # Tajweed Rules: text input labelled by i42 i45
    "tajweed_rules": "input[type='text'][aria-labelledby='i42 i45']",
    # Islamic Topic / AlQurancircle Duaa Book: text input labelled by i47 i50
    "topic": "input[type='text'][aria-labelledby='i47 i50']",
    # H.W: textarea labelled by i52 i55
    "homework": "textarea[aria-labelledby='i52 i55']",
    # Additional Notes for parent: textarea labelled by i57 i60
    "parent_notes": "textarea[aria-labelledby='i57 i60']",
    # Additional Notes for Admins: textarea labelled by i62 i65
    "admin_notes": "textarea[aria-labelledby='i62 i65']",
    # Tafseer: radio buttons with aria-label matching the profile value
    "tafseer": "",
    # Submit button: <div role="button" jsname="M2UYVd">Submit</div>
    "submit_button": "div[role='button'][jsname='M2UYVd']",
    # "Send me a copy of my responses." checkbox: <div role="checkbox" aria-label="Send me a copy of my responses.">
    "send_copy_checkbox": "div[role='checkbox'][aria-label='Send me a copy of my responses.']",
    # Text shown on the confirmation page after successful submission
    # This uses Playwright's text locator syntax by default.
    "success_text": "text=Jazakom Allah Khyran, your daily report is submitted successfully",
}


def load_selectors_from_json(path: Optional[str]) -> Dict[str, str]:
    """
    Load field selectors from a JSON file if provided, otherwise use defaults.
    """
    if not path:
        return DEFAULT_SELECTORS
    selector_path = Path(path)
    if not selector_path.is_file():
        logging.warning("Selectors file not found; using default selectors.")
        return DEFAULT_SELECTORS

    with selector_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Merge defaults with overrides
    merged = DEFAULT_SELECTORS.copy()
    merged.update(data)
    return merged


def _fill_form(
    playwright: Playwright,
    profile_data: Dict[str, Any],
    form_url: str,
    selectors: Dict[str, str],
    headless: bool = True,
    send_copy: bool = False,
    use_extension: bool = False,
) -> bool:
    """Internal helper to open a browser and fill the form using profile_data."""

    browser = None
    context = None

    if use_extension:
        ext_dir = get_extension_dir()
        if ext_dir is not None:
            # Use a persistent context so the extension can be loaded from the Chrome profile path.
            user_data_dir = str(Path(__file__).resolve().parent / "playwright_profile")
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=False,  # extensions require headed mode
                args=[
                    f"--disable-extensions-except={ext_dir}",
                    f"--load-extension={ext_dir}",
                ],
                locale="en-US",
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                },
            )
            page = context.new_page()
        else:
            logging.warning("Proceeding without extension because extension directory could not be resolved.")

    if context is None:
        # Normal headless/headed launch without extension
        browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context(
            locale="en-US",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        page = context.new_page()

    success = False

    try:
        # Normalize URL to request English UI explicitly (hl=en)
        parsed = urlparse(form_url)
        query_params = dict(parse_qsl(parsed.query))
        query_params.setdefault("hl", "en")
        english_form_url = urlunparse(
            parsed._replace(query=urlencode(query_params, doseq=True)),
        )

        page.goto(english_form_url, timeout=60_000)

        # Normalize date value from profile to HTML5 date input format (YYYY-MM-DD)
        raw_date = profile_data.get("date")
        if raw_date:
            # Accept common formats like DD/MM/YYYY or MM/DD/YYYY and keep YYYY-MM-DD as is
            from datetime import datetime  # local import to avoid unused at module level

            normalized = None
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y"):
                try:
                    normalized = datetime.strptime(raw_date, fmt).strftime("%Y-%m-%d")
                    break
                except ValueError:
                    continue
            if normalized:
                profile_data["date"] = normalized

        def set_value(field_key: str, profile_key: str) -> None:
            selector = selectors.get(field_key)
            if not selector:
                return
            value = profile_data.get(profile_key, "")
            if value is None:
                value = ""
            if not value:
                return
            try:
                page.fill(selector, str(value), timeout=15_000)
            except PlaywrightTimeoutError as exc:
                logging.error("Timeout filling %s with selector %s: %s", field_key, selector, exc)

        # Email, dates, text fields
        set_value("email", "email")
        set_value("date", "date")
        set_value("teacher_name", "teacher_name")
        set_value("student_name", "student_name")
        set_value("quran_surah", "quran_surah")
        set_value("noor_page", "noor_page")
        set_value("tajweed_rules", "tajweed_rules")
        set_value("topic", "topic")
        set_value("homework", "homework")
        set_value("parent_notes", "parent_notes")
        set_value("admin_notes", "admin_notes")

        # Tafseer radios: choose the option whose aria-label matches the profile value
        tafseer_value = profile_data.get("tafseer")
        if tafseer_value:
            tafseer_radio_selector = (
                f"div[role='radio'][aria-label='{tafseer_value}']"
            )
            try:
                page.click(tafseer_radio_selector, timeout=15_000)
            except PlaywrightTimeoutError as exc:
                logging.error(
                    "Timeout clicking tafseer radio %s: %s",
                    tafseer_radio_selector,
                    exc,
                )

        # Optional: "Send me a copy of my responses" checkbox
        send_copy_selector = selectors.get("send_copy_checkbox")
        if send_copy and send_copy_selector:
            try:
                # Prefer check() to ensure it is selected
                page.check(send_copy_selector, timeout=15_000)
            except Exception as exc:  # noqa: BLE001
                logging.error(
                    "Error setting send-copy checkbox %s: %s",
                    send_copy_selector,
                    exc,
                )

        # Submit
        submit_selector = selectors.get("submit_button")
        if submit_selector:
            try:
                page.click(submit_selector, timeout=30_000)
            except PlaywrightTimeoutError as exc:
                logging.error("Timeout clicking submit button %s: %s", submit_selector, exc)

        # Wait for confirmation that the form was submitted successfully
        success_locator = selectors.get("success_text")
        try:
            if success_locator:
                # Wait until the confirmation text/element appears
                page.wait_for_selector(success_locator, timeout=20_000)
                success = True
            else:
                # Fallback: wait briefly and consider a URL change as success
                previous_url = page.url
                page.wait_for_timeout(3_000)
                if page.url != previous_url:
                    success = True
        except Exception as exc:  # noqa: BLE001
            logging.error("Did not detect form submission confirmation: %s", exc)

    finally:
        if context is not None:
            context.close()
        if browser is not None:
            browser.close()

    return success


def submit_profile_to_form(
    profile_path: str,
    form_url: str,
    selectors_json_path: Optional[str] = None,
    max_retries: int = 3,
    headless: bool = True,
    send_copy: bool = False,
    use_extension: bool = False,
    retry_delay_seconds: float = 5.0,
) -> bool:
    """
    Read a student profile JSON and fill the corresponding Google Form.

    Args:
        profile_path: Path to student profile JSON file.
        form_url: URL of the Google Form.
        selectors_json_path: Optional path to JSON with selector overrides.
        max_retries: Number of times to retry on failure.
        headless: Run browser in headless mode if True.
        send_copy: Whether to check the "Send me a copy of my responses" checkbox.
        use_extension: Whether to use the Chrome extension.
        retry_delay_seconds: Seconds to wait between retries.

    Returns:
        True if at least one submission appears to succeed, False otherwise.
        
    Raises:
        FileNotFoundError: If profile file doesn't exist
        ValueError: If profile file is corrupted or invalid
        RuntimeError: If form submission fails after all retries
    """
    # Validate profile path
    profile_file = Path(profile_path)
    if not profile_file.exists():
        raise FileNotFoundError(f"Profile file not found: {profile_path}")
    
    if not profile_file.is_file():
        raise ValueError(f"Profile path is not a file: {profile_path}")
    
    # Load and validate profile
    try:
        profile = load_profile(profile_file)
    except json.JSONDecodeError as e:
        raise ValueError(f"Profile file is corrupted (invalid JSON): {e}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to load profile: {e}") from e
    
    # Validate form URL
    if not form_url or not form_url.strip():
        raise ValueError("Form URL is required")
    
    if not form_url.startswith(('http://', 'https://')):
        raise ValueError("Form URL must start with http:// or https://")
    
    selectors = load_selectors_from_json(selectors_json_path)

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            with sync_playwright() as p:
                success = _fill_form(
                    playwright=p,
                    profile_data=profile,
                    form_url=form_url,
                    selectors=selectors,
                    headless=headless,
                    send_copy=send_copy,
                    use_extension=use_extension,
                )
            if success:
                log_action(
                    f"Form submission confirmed for {profile_path} on attempt {attempt}",
                )
                return True
            logging.warning(
                "Form submission attempt %d for %s did not show confirmation text.",
                attempt,
                profile_path,
            )
        except PlaywrightTimeoutError as e:
            last_error = e
            logging.error(
                "Form submission timeout for %s on attempt %d: %s",
                profile_path,
                attempt,
                e,
            )
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            logging.error(
                "Form submission error for %s on attempt %d: %s",
                profile_path,
                attempt,
                exc,
                exc_info=True,
            )
        # Wait before next retry, unless this was the last attempt
        if attempt < max_retries and retry_delay_seconds > 0:
            time.sleep(retry_delay_seconds)

    log_action(f"Form submission failed after {max_retries} attempts for {profile_path}")
    # Return False instead of raising - let caller handle the error
    return False