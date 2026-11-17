## ADDED
### Requirement: Stop and restart batch safely
批次停止時 MUST 取消目前任務與尚未執行任務，並在背景工作收尾完成前維持忙碌狀態。取消的任務 SHALL 標示為 `CANCELLED`，且不得重試。重新開始 SHALL 建立新批次，不得與舊下載同時執行。

#### Scenario: Stop and immediately restart
- **Given** 批次中的任務仍在執行
- **When** 使用者取消批次並立即要求重新開始
- **Then** 系統 SHALL 拒絕重新開始直到舊工作收尾
- **And** 已取消任務 SHALL 不計為失敗

#### Scenario: Clear while stopping
- **Given** 批次仍在收尾
- **When** 使用者清除佇列
- **Then** 系統 SHALL 在舊工作收尾後清除任務與佇列
