"""
Bootstrap 5 Web UI，提供影片/音訊下載服務。
保留原有桌面 UI，同時新增 FastAPI 介面。
"""

from __future__ import annotations

import os
import sys
import threading
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, field_validator

# 確保 src/ 在 sys.path 中，讓 core/utils 模組可被匯入
SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from core.constants import (  # noqa: E402
    AUDIO_FORMATS,
    DEFAULT_DOWNLOAD_PATH,
    DOWNLOAD_TYPE_AUDIO,
    DOWNLOAD_TYPE_VIDEO,
    ERROR_MESSAGES,
    VIDEO_FORMATS,
)
from core.downloader import DownloadManager  # noqa: E402
from utils import Logger, format_size, format_time  # noqa: E402
from utils.validators import validate_url  # noqa: E402

PROJECT_ROOT = SRC_ROOT.parent
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(ENV_PATH)

RAW_DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", DEFAULT_DOWNLOAD_PATH)
DOWNLOAD_ROOT = Path(RAW_DOWNLOAD_DIR).expanduser()
if not DOWNLOAD_ROOT.is_absolute():
    DOWNLOAD_ROOT = (PROJECT_ROOT / DOWNLOAD_ROOT).resolve()
DOWNLOAD_ROOT.mkdir(parents=True, exist_ok=True)

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))

app = FastAPI(
    title="Video Downloader Web UI",
    description="基於 FastAPI 的影片/音訊下載服務，使用 yt-dlp",
    version="2.2.0",
)


class DownloadPayload(BaseModel):
    """下載請求的驗證模型"""

    url: str
    download_type: str
    format_option: str

    @field_validator("url")
    @classmethod
    def _validate_url(cls, value: str) -> str:
        clean_value = value.strip()
        if not clean_value:
            raise ValueError(ERROR_MESSAGES["empty_url"])
        if not validate_url(clean_value):
            raise ValueError(ERROR_MESSAGES["invalid_url"])
        return clean_value

    @field_validator("download_type")
    @classmethod
    def _validate_type(cls, value: str) -> str:
        if value not in {DOWNLOAD_TYPE_VIDEO, DOWNLOAD_TYPE_AUDIO}:
            raise ValueError("download_type 必須為 video 或 audio")
        return value

    @field_validator("format_option")
    @classmethod
    def _validate_format(cls, value: str) -> str:
        if not value:
            raise ValueError("格式選項不可為空")
        return value


class WebDownloadService:
    """提供 Web 版下載任務管理"""

    def __init__(self, download_root: Path):
        self.download_root = download_root
        self.manager = DownloadManager()
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        self.logger = Logger()

    def start_task(self, payload: DownloadPayload) -> str:
        task_id = str(uuid.uuid4())
        initial_state = {
            "id": task_id,
            "url": payload.url,
            "download_type": payload.download_type,
            "format_option": payload.format_option,
            "status": "pending",
            "progress": 0.0,
            "message": "排隊中",
            "speed": None,
            "eta": None,
            "file_path": None,
        }
        with self.lock:
            self.tasks[task_id] = initial_state

        thread = threading.Thread(
            target=self._run_task,
            args=(task_id, payload),
            daemon=True,
        )
        thread.start()
        return task_id

    def _run_task(self, task_id: str, payload: DownloadPayload):
        def _progress_callback(data: Dict[str, Any]):
            status = data.get("status")
            if status == "downloading":
                downloaded = data.get("downloaded") or 0
                total = data.get("total") or 0
                percentage = float(data.get("percentage") or 0.0)
                speed = data.get("speed") or 0
                eta = data.get("eta") or 0

                self._update_task(
                    task_id,
                    status="downloading",
                    progress=max(0.0, min(100.0, percentage)),
                    speed=format_size(speed) + "/s" if speed else None,
                    eta=format_time(int(eta)) if eta else None,
                    message=f"已下載 {format_size(downloaded)} / {format_size(total) if total else '未知'}",
                )
            elif status == "finished":
                self._update_task(
                    task_id,
                    status="postprocessing",
                    progress=100.0,
                    message="後處理中...",
                )

        def _complete_callback(file_path: str, info: Dict[str, Any]):
            self._update_task(
                task_id,
                status="completed",
                progress=100.0,
                message="下載完成",
                file_path=file_path,
            )

        def _error_callback(error_msg: str):
            self._update_task(
                task_id,
                status="failed",
                message=error_msg or ERROR_MESSAGES.get("download_error", "下載失敗"),
            )

        download_task = self.manager.create_task(
            url=payload.url,
            download_type=payload.download_type,
            output_path=str(self.download_root),
            format_option=payload.format_option,
            progress_callback=_progress_callback,
            complete_callback=_complete_callback,
            error_callback=_error_callback,
        )

        self._update_task(task_id, status="downloading", message="開始下載...")

        success = download_task.execute()
        self.manager.remove_task(download_task)

        with self.lock:
            state = self.tasks.get(task_id)
            if not state:
                return
            if state["status"] not in {"completed", "failed"}:
                state["status"] = "completed" if success else "failed"
                state["progress"] = 100.0 if success else state.get("progress", 0.0)
                if not state.get("message"):
                    state["message"] = "下載完成" if success else ERROR_MESSAGES.get("download_error", "下載失敗")
                self.tasks[task_id] = state

    def _update_task(
        self,
        task_id: str,
        *,
        status: Optional[str] = None,
        progress: Optional[float] = None,
        message: Optional[str] = None,
        speed: Optional[str] = None,
        eta: Optional[str] = None,
        file_path: Optional[str] = None,
    ):
        with self.lock:
            state = self.tasks.get(task_id)
            if not state:
                return
            if status:
                state["status"] = status
            if progress is not None:
                state["progress"] = progress
            if message is not None:
                state["message"] = message
            if speed is not None:
                state["speed"] = speed
            if eta is not None:
                state["eta"] = eta
            if file_path is not None:
                state["file_path"] = file_path
            self.tasks[task_id] = state

    def get_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            state = self.tasks.get(task_id)
            if not state:
                return None
            return dict(state)


service = WebDownloadService(DOWNLOAD_ROOT)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """首頁，回傳 Bootstrap 介面"""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "video_formats": list(VIDEO_FORMATS.keys()),
            "audio_formats": list(AUDIO_FORMATS.keys()),
            "download_dir": str(DOWNLOAD_ROOT),
        },
    )


@app.post("/api/download")
async def start_download(payload: DownloadPayload):
    """新增下載任務"""
    task_id = service.start_task(payload)
    Logger().info(f"Web 任務建立: {payload.url} -> {task_id}")
    return {"task_id": task_id, "status": "queued"}


@app.get("/api/status/{task_id}")
async def get_status(task_id: str):
    """查詢任務狀態"""
    status = service.get_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="找不到指定任務")
    return status


def run():
    """提供直接執行的入口"""
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("src.web.app:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    run()
