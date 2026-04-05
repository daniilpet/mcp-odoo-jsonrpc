from typing import Any

import httpx

from mcp_odoo_jsonrpc.config import OdooConfig


class OdooSessionExpiredError(Exception):
    pass


class OdooRPCError(Exception):
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.data = data
        super().__init__(f"Odoo RPC error {code}: {message}")


class OdooTransport:
    def __init__(self, config: OdooConfig) -> None:
        self._config = config
        self._request_id = 0
        self._client = httpx.AsyncClient(
            base_url=config.base_url,
            cookies={"session_id": config.session_id},
            headers={"Content-Type": "application/json"},
            timeout=30.0,
        )

    async def call_kw(
        self,
        model: str,
        method: str,
        args: list[Any],
        kwargs: dict[str, Any],
    ) -> Any:
        url = f"/web/dataset/call_kw/{model}/{method}"
        return await self._rpc(
            url,
            {
                "model": model,
                "method": method,
                "args": args,
                "kwargs": kwargs,
            },
        )

    async def call(self, url: str, params: dict[str, Any]) -> Any:
        return await self._rpc(url, params)

    async def _rpc(self, url: str, params: dict[str, Any]) -> Any:
        self._request_id += 1
        payload = {
            "id": self._request_id,
            "jsonrpc": "2.0",
            "method": "call",
            "params": params,
        }

        response = await self._client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            error = data["error"]
            error_data = error.get("data", {})
            message = error.get("message", "Unknown error")

            if (
                "Session" in message
                or error_data.get("name") == "odoo.http.SessionExpiredException"
            ):
                raise OdooSessionExpiredError(
                    "Сессия Odoo истекла. Выполните 'mcp-odoo-cli login' "
                    "или обновите ODOO_SESSION_ID."
                )

            raise OdooRPCError(
                code=error.get("code", -1),
                message=message,
                data=error_data,
            )

        return data.get("result")

    async def close(self) -> None:
        await self._client.aclose()
