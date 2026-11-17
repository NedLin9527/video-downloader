## ADDED
### Requirement: Final output path
下載完成回呼 MUST 回報 yt-dlp 後處理完成且檔名轉換後的實際輸出路徑。

#### Scenario: Audio is converted after downloading
- **Given** 音訊下載後被轉換為不同副檔名
- **When** 下載與後處理成功完成
- **Then** 完成回呼 SHALL 回報已存在的最終音訊檔案路徑
