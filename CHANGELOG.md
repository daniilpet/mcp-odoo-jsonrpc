# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [0.1.0] - 2026-04-05

### Added
- MCP-сервер с 7 инструментами: list_tasks, get_task, create_task,
  update_task, change_task_stage, log_timesheet, get_timesheets
- Odoo CLI с интерактивным меню и браузерной авторизацией
- Anti-Corruption Layer (ACL) с тремя слоями: Transport, Protocol, Mapper
- Двухуровневая модель безопасности: restricted (по умолчанию) / full
- Фильтрация по проектам через ODOO_ALLOWED_PROJECTS
- Безопасное хранение session_id через системный keyring
- Поддержка Odoo 17 JSON-RPC протокола
- 11 доменных моделей (Pydantic v2)
- 5 архитектурных решений (ADR)
- Справочник из 9 Odoo JSON-RPC эндпоинтов
