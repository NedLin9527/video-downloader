# 開發指南

## 開發環境設置

需要 Python 3.11 以上版本。FFmpeg 用於音訊轉換及部分影音合併；YouTube JavaScript 驗證需要 Deno。

### 1. 克隆專案
```bash
git clone <repository_url>
cd video-downloader
```

### 2. 建立虛擬環境
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows
```

### 3. 安裝依賴
```bash
pip install -r requirements.txt
```

### 4. 開發模式安裝
```bash
pip install -e .
```

## 開發工作流程

### 啟動開發環境
```bash
# 方法 1: 使用開發腳本
python scripts/run_dev.py

# 方法 2: 直接執行
python main.py

# 方法 3: 以模組方式執行
python -m src.main
```

### 執行測試

以下 unittest 指令使用標準函式庫；若要使用覆蓋率指令，需另行安裝 `pytest` 與 `pytest-cov`。

```bash
# 執行所有測試
python -m unittest discover -s tests -v

# 執行特定測試檔案
python -m unittest tests.test_utils -v

# 執行測試並顯示覆蓋率
python -m pytest tests/ --cov=src
```

### 程式碼品質檢查

以下工具需另行安裝：`flake8`、`black`、`isort`。

```bash
# 使用 flake8 檢查程式碼風格
flake8 src/

# 使用 black 格式化程式碼
black src/

# 使用 isort 排序 import
isort src/
```

## 建置與發布

### 建置套件

先安裝 `build` 套件。`scripts/build.py` 會刪除現有的 `build/`、`dist/` 與根目錄的 `*.egg-info`，使用前請先確認其中沒有要保留的檔案。該腳本使用 `rm`，適用 macOS／Linux；Windows 請使用 `python -m build`。

```bash
# 使用建置腳本
python scripts/build.py

# 或手動建置
python -m build
```

### 本地安裝測試
```bash
# 將下方檔名替換為 dist 目錄中的實際 wheel 檔名
python -m pip install dist/實際檔名.whl
```

## 程式碼規範

### 命名規範
- 類別: PascalCase (例: `DownloadManager`)
- 函式/變數: snake_case (例: `download_video`)
- 常數: UPPER_SNAKE_CASE (例: `DEFAULT_DOWNLOAD_PATH`)
- 私有方法: 前綴 `_` (例: `_setup_logger`)

### 文檔字串
```python
def function_name(param1: str, param2: int) -> bool:
    \"\"\"
    函式簡短描述
    
    Args:
        param1: 參數1說明
        param2: 參數2說明
        
    Returns:
        bool: 返回值說明
        
    Raises:
        ValueError: 錯誤情況說明
    \"\"\"
    pass
```

### 類型提示
- 所有公開函式都應包含類型提示
- 使用 `typing` 模組的類型
- 複雜類型使用 `Union`, `Optional` 等

### 錯誤處理
- 使用具體的異常類型
- 提供有意義的錯誤訊息
- 記錄錯誤到日誌系統

## 除錯技巧

### 日誌除錯
```python
from src.utils.logger import Logger

logger = Logger()
logger.debug("除錯訊息")
logger.info("一般訊息")
logger.warning("警告訊息")
logger.error("錯誤訊息")
```

### 使用 IDE 除錯器
- 設定中斷點在關鍵位置
- 檢查變數狀態
- 逐步執行程式碼

### 常見問題
1. **模組匯入錯誤**: 確認 Python 路徑設定正確
2. **FFmpeg 未安裝**: 音訊下載功能需要 FFmpeg
3. **權限問題**: 確認下載目錄有寫入權限

## 貢獻指南

### 提交程式碼前檢查清單
- [ ] 程式碼通過所有測試
- [ ] 新功能包含測試案例
- [ ] 程式碼符合風格規範
- [ ] 更新相關文檔
- [ ] 提交訊息清楚描述變更

### Git 工作流程
```bash
# 建立功能分支
git checkout -b feature/new-feature

# 提交變更
git add .
git commit -m "feat: 添加新功能"

# 推送到遠端
git push origin feature/new-feature

# 建立 Pull Request
```

### 提交訊息格式
```
type(scope): description

[optional body]

[optional footer]
```

類型:
- `feat`: 新功能
- `fix`: 錯誤修復
- `docs`: 文檔更新
- `style`: 程式碼格式
- `refactor`: 重構
- `test`: 測試相關
- `chore`: 建置/工具相關
## 版本資訊

版本只在 `src/__init__.py` 的 `__version__` 維護；套件中繼資料、桌面標題及 Web API 均使用該值。修改版本時應同時更新可核實的發布紀錄。
