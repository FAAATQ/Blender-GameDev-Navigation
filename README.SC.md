# Blender-GameDev-Navigation

![GameDev Navigation in Blender](https://raw.githubusercontent.com/FAAATQ/Blender-GameDev-Navigation/main/images/image_mt02k15g_9c37.png)

[English](README.md) · **简体中文** · [繁體中文](README.TC.md)

一个面向 Blender 4.x/5.x 的插件，为 3D 视图提供接近 Unity 或 Unreal Scene View 的导航方式。

本项目此前以 `Blender-Unity-Controls` 发布；当前插件和 Release 资产使用 GameDev Navigation 名称。

## 功能

- 按住可配置触发键进入导航模式，并移动鼠标控制视角。
- 导航期间使用 `W/A/S/D` 移动、`Q/E` 上下移动、按住 `Shift` 加速。
- 导航期间使用鼠标滚轮调整当前导航速度。
- 可在插件偏好中配置。
- 支持英文、简体中文和繁体中文界面。

## 安装

1. 从 GitHub Releases 下载 `Blender-GameDev-Navigation.zip`。
2. 在 Blender 中打开 **编辑 → 偏好设置 → 插件**。
3. 选择**从磁盘安装**，选中 ZIP，然后启用 **GameDev Navigation**。

如果需要多语言，请不要单独安装 `Blender-GameDev-Navigation.py`。Release ZIP 包含运行所需的 `locales/` 资源。

## 默认操作

按住鼠标右键进入导航模式；以下转向和移动操作仅在按住右键期间生效。松开右键即可结束导航并保留当前位置。

| 导航模式内的操作 | 输入 |
| --- | --- |
| 进入导航模式 | 按住鼠标右键 |
| 转向 | 按住鼠标右键并移动鼠标 |
| 前后左右移动 | 按住鼠标右键并使用 `W/A/S/D` |
| 下移/上移 | 按住鼠标右键并使用 `Q/E` |
| 加速移动 | 导航期间按住 `Shift` |
| 调整当前导航速度 | 导航期间滚动鼠标滚轮 |
| 结束并保留当前位置 | 松开鼠标右键 |
| 取消导航 | 导航期间按 `Esc` |

完整设置：**编辑 → 偏好设置 → 插件 → GameDev Navigation**。

## 相关链接

- 翻译指南：[locales/README.md](locales/README.md)
- 版本变化：[CHANGELOG.md](CHANGELOG.md)

项目采用 [MIT License](LICENSE)。
