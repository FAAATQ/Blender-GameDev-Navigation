# Blender-GameDev-Navigation

![GameDev Navigation in Blender](https://raw.githubusercontent.com/FAAATQ/Blender-GameDev-Navigation/main/images/image_mt02k15g_9c37.png)

[English](README.md) · [简体中文](README.SC.md) · **繁體中文**

一個適用於 Blender 4.x/5.x 的附加元件，為 3D 視圖提供接近 Unity 或 Unreal Scene View 的導覽方式。

本專案此前以 `Blender-Unity-Controls` 發布；目前附加元件和 Release 資產使用 GameDev Navigation 名稱。

## 功能

- 按住可設定的觸發鍵進入導覽模式，並移動滑鼠控制視角。
- 導覽期間使用 `W/A/S/D` 移動、`Q/E` 上下移動、按住 `Shift` 加速。
- 導覽期間使用滑鼠滾輪調整目前導覽速度。
- 可在附加元件偏好中設定。
- 支援英文、簡體中文和繁體中文介面。

## 安裝

1. 從 GitHub Releases 下載 `Blender-GameDev-Navigation.zip`。
2. 在 Blender 中開啟 **編輯 → 偏好設定 → 附加元件**。
3. 選擇**從磁碟安裝**，選取 ZIP，然後啟用 **GameDev Navigation**。

如果需要多語言，請不要單獨安裝 `Blender-GameDev-Navigation.py`。Release ZIP 包含執行所需的 `locales/` 資源。

## 預設操作

按住滑鼠右鍵進入導覽模式；以下轉向和移動操作只會在按住右鍵期間生效。放開右鍵即可結束導覽並保留目前視點。

| 導覽模式內的操作 | 輸入 |
| --- | --- |
| 進入導覽模式 | 按住滑鼠右鍵 |
| 轉向 | 按住滑鼠右鍵並移動滑鼠 |
| 前後左右移動 | 按住滑鼠右鍵並使用 `W/A/S/D` |
| 下移/上移 | 按住滑鼠右鍵並使用 `Q/E` |
| 加速移動 | 導覽期間按住 `Shift` |
| 調整目前導覽速度 | 導覽期間滾動滑鼠滾輪 |
| 結束並保留目前視點 | 放開滑鼠右鍵 |
| 取消導覽 | 導覽期間按 `Esc` |

完整設定：**編輯 → 偏好設定 → 附加元件 → GameDev Navigation**。

## 相關連結

- 翻譯指南：[locales/README.md](locales/README.md)
- 版本變更：[CHANGELOG.md](CHANGELOG.md)

本專案採用 [MIT License](LICENSE)。
