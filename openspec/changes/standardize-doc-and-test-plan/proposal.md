# Proposal: standardize-doc-and-test-plan

## Why
目前專案已有桌面與 Web 兩條介面路徑，但規格與測試策略分散在 `README`、`docs/`、零星測試檔，缺少可被持續維護的 OpenSpec 變更流程。這使未來功能調整容易出現「程式、文件、測試預期」不同步。

## What Changes
1. 建立 OpenSpec 基線能力：`download-core`、`batch-download`、`desktop-ui`、`web-ui-api`、`config-and-filename`。
2. 新增「測試與文件治理」能力規格，定義變更時的最小驗證要求。
3. 規劃後續將既有測試重整為可重複執行的自動化檢查流程（不在本提案直接改功能）。

## Impact
- 受影響文件：`openspec/project.md`、`openspec/specs/*`、`openspec/changes/*`
- 受影響流程：後續所有行為變更需先開 proposal 再 apply
- 程式行為：本提案不改執行行為，只補治理與規格基線
