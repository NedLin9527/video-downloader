# Project Context

## Purpose
`video-downloader` 是以 Python 實作的影片/音訊下載工具，提供桌面 UI（Tkinter）與 Web UI（FastAPI）兩種使用方式，核心下載由 `yt-dlp` 執行，並支援檔名繁簡轉換與批次重試。

## Current Stack
- Language: Python 3.8+
- Core dependency: `yt-dlp`
- Desktop UI: `tkinter`
- Web UI/API: `fastapi`, `uvicorn`, `jinja2`
- Optional filename conversion: `opencc-python-reimplemented`
- Testing: `pytest`, `unittest`（現況混用）

## Runtime/Environment
- FFmpeg 為音訊抽取必要依賴。
- Web 介面下載目錄可由 `.env` 的 `DOWNLOAD_DIR` 指定，未設定時使用 `./downloads`。

## Repository Conventions
- 核心業務邏輯集中於 `src/core/`。
- 介面層分為 `src/ui/`（桌面）與 `src/web/`（Web）。
- 共用工具在 `src/utils/`。
- 行為變更需先在 `openspec/changes/<change-id>/` 建立 proposal 與 delta spec。
- Bug fix（使實作重新符合既有 spec）可直接修復，但需補測試。

## Domain Terminology
- Download Task: 單一 URL 的下載任務。
- Batch Task: 批次佇列中的單一任務狀態項目。
- Batch Download: 多 URL 依序執行、可重試的流程。
- Format Option: 下載格式選項（影片解析度或音訊編碼品質）。

## Non-Goals (Current)
- 不提供登入帳號、雲端同步與遠端儲存。
- 不保證所有平台站點可用（取決於 `yt-dlp` 支援與來源站限制）。
