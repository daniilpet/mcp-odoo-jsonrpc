import contextlib
import sys
from typing import Any

import httpx

from mcp_odoo_jsonrpc.config import OdooSession


async def _resolve_user_info(
    base_url: str,
    session_id: str,
    uid: int,
) -> dict[str, Any]:
    async with httpx.AsyncClient(
        base_url=base_url,
        cookies={"session_id": session_id},
        headers={"Content-Type": "application/json"},
        timeout=15.0,
    ) as client:
        user_resp = await client.post(
            "/web/dataset/call_kw/res.users/search_read",
            json={
                "id": 1,
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "model": "res.users",
                    "method": "search_read",
                    "args": [],
                    "kwargs": {
                        "domain": [["id", "=", uid]],
                        "fields": ["display_name", "company_ids", "company_id", "lang", "tz"],
                        "context": {"uid": uid},
                    },
                },
            },
        )
        user_data = user_resp.json()
        if "error" in user_data:
            raise RuntimeError(f"Ошибка при запросе пользователя: {user_data['error']}")
        users = user_data.get("result", [])
        if not users:
            raise RuntimeError(f"Пользователь uid={uid} не найден.")
        user = users[0]

        emp_resp = await client.post(
            "/web/dataset/call_kw/hr.employee/search_read",
            json={
                "id": 2,
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "model": "hr.employee",
                    "method": "search_read",
                    "args": [],
                    "kwargs": {
                        "domain": [["user_id", "=", uid]],
                        "fields": ["display_name"],
                        "context": {"uid": uid},
                    },
                },
            },
        )
        emp_data = emp_resp.json()
        employees = emp_data.get("result", [])
        employee_id = employees[0]["id"] if employees else uid

    company_id_raw = user.get("company_id")
    if isinstance(company_id_raw, list):
        company_id = company_id_raw[0]
    elif isinstance(company_id_raw, dict):
        company_id = company_id_raw["id"]
    else:
        company_id = company_id_raw or 1

    company_ids_raw = user.get("company_ids", [company_id])
    if company_ids_raw and isinstance(company_ids_raw[0], dict):
        company_ids = [c["id"] for c in company_ids_raw]
    else:
        company_ids = company_ids_raw or [company_id]

    return {
        "display_name": user.get("display_name", ""),
        "employee_id": employee_id,
        "company_ids": company_ids,
        "lang": user.get("lang", "ru_RU"),
        "tz": user.get("tz", "Europe/Moscow") or "Europe/Moscow",
    }


async def _get_session_info(base_url: str, session_id: str) -> dict[str, Any] | None:
    async with httpx.AsyncClient(
        base_url=base_url,
        cookies={"session_id": session_id},
        headers={"Content-Type": "application/json"},
        timeout=10.0,
    ) as client:
        resp = await client.post(
            "/web/session/get_session_info",
            json={"id": 0, "jsonrpc": "2.0", "method": "call", "params": {}},
        )
        data = resp.json()
        result = data.get("result", {})
        if result.get("uid"):
            return result
    return None


async def browser_login(base_url: str) -> OdooSession:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print(
            "Playwright не установлен. Выполните: "
            "pip install playwright && playwright install chromium"
        )
        sys.exit(1)

    base_url = base_url.rstrip("/")
    print(f"Открываю браузер для авторизации в {base_url}...")
    print("Войдите в Odoo. Окно закроется автоматически после входа.")

    session_id: str | None = None
    uid: int | None = None
    browser_closed = False

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        page.on("close", lambda _: None)

        await page.goto(f"{base_url}/web/login")

        while not browser_closed:
            try:
                await page.wait_for_timeout(1500)
            except Exception:
                browser_closed = True
                break

            try:
                cookies = await context.cookies()
            except Exception:
                browser_closed = True
                break

            for cookie in cookies:
                if cookie["name"] == "session_id" and cookie["value"]:
                    session_id = cookie["value"]

            if not session_id:
                continue

            info = await _get_session_info(base_url, session_id)
            if info and info.get("uid"):
                uid = info["uid"]
                print(f"Сессия получена (uid={uid}). Закрываю браузер...")
                with contextlib.suppress(Exception):
                    await browser.close()
                break

        if not browser_closed:
            with contextlib.suppress(Exception):
                await browser.close()

    if not session_id:
        raise RuntimeError("Не удалось получить session_id. Попробуйте снова.")

    if not uid:
        print("Браузер закрыт до определения uid. Пробую с имеющимся session_id...")
        info = await _get_session_info(base_url, session_id)
        if info and info.get("uid"):
            uid = info["uid"]
        else:
            raise RuntimeError(
                "Не удалось определить uid. Возможно, вы не завершили авторизацию. "
                "Попробуйте снова."
            )

    print(f"Загружаю данные пользователя (uid={uid})...")

    user_info = await _resolve_user_info(base_url, session_id, uid)

    session = OdooSession(
        base_url=base_url,
        session_id=session_id,
        uid=uid,
        employee_id=user_info["employee_id"],
        company_ids=user_info["company_ids"],
        lang=user_info["lang"],
        tz=user_info["tz"],
        display_name=user_info["display_name"],
    )
    session.save()

    print(f"Авторизация успешна: {session.display_name}")
    print("Сессия сохранена: ~/.config/odoo-cli/session.json")

    return session
