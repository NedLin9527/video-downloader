# OpenSpec Agent Workflow

本專案使用 OpenSpec 管理功能行為與變更，請依以下流程執行。

## 1) Determine if proposal is required
下列情況「必須」先開 proposal：
- 會改變外部可見行為（UI/API/輸出檔案命名/預設值）
- 會新增或移除需求
- 會影響跨模組流程

下列情況可直接實作（仍建議補測試）：
- 修正程式使其重新符合既有 spec
- 純註解、排版、錯字
- 非破壞性相依套件更新
- 不改變行為的設定重構

## 2) Proposal phase
在 `openspec/changes/<change-id>/` 建立：
- `proposal.md`：包含 `Why / What Changes / Impact`
- `tasks.md`：可執行、可勾選項目
- `specs/<capability>/spec.md`：以 Delta 格式撰寫

Delta 章節僅可使用：
- `## ADDED`
- `## MODIFIED`
- `## REMOVED`
- `## RENAMED`

`MODIFIED` 必須貼出完整修改後需求內容，不能只寫差異。

## 3) Apply phase
- 僅實作 `tasks.md` 內已定義範圍。
- 完成一項即勾選一項，避免超規格實作。
- 實作後更新必要測試與文件。

## 4) Archive phase
完成並驗收後：
- 將變更移動到 `openspec/changes/archive/`
- 將 delta 合併到 `openspec/specs/` 成為最新真相

## Spec Authoring Rules
- 每個 Requirement 至少一個 Scenario。
- Scenario 標題必須是：`#### Scenario:`
- Requirement 內容需使用 `SHALL` 或 `MUST`。
