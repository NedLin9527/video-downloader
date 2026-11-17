## ADDED
### Requirement: Reject invalid batch inputs atomically
批次輸入 MUST 在加入佇列前完成驗證；任一 URL 無效時 SHALL 指明項次並拒絕整批，保留原有佇列。

#### Scenario: Mixed valid and invalid URLs
- **Given** 批次清單包含有效和無效 URL
- **When** 使用者提交清單
- **Then** 系統 SHALL 提示無效項次
- **And** 不新增任何任務或清除既有佇列
