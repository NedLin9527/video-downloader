# Tasks

- [x] 統一套件、桌面及 Web 版本來源，維持既有套件版本。
- [x] 對齊環境、操作、測試及架構文件，標示歷史版本未核實。
- [x] 驗證版本一致性、套件建置及測試；記錄驗證限制。

## 驗證結果

- `python -m unittest discover -s tests -q`：23 項通過。
- 在暫存副本以 setuptools 68.2.0 / wheel 0.41.2 離線建置 wheel，確認套件版本、Python 需求、依賴、入口與 Web 資源。
- 將 wheel 安裝至暫存目錄並在專案外驗證套件、桌面標題與 Web API 版本均為 2.0.0。
- 歷史發布日期及版本未有 Git tag 作佐證，已在 README 標註未核實。
