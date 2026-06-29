# 项目依赖清单

> 桌面宠物程序运行所需的 Python 第三方库

---

## 依赖列表

| 包名 | 版本要求 | 用途 | 安装命令 |
|------|----------|------|----------|
| pygame-ce | >= 2.5.0 | 游戏引擎：窗口创建、图形绘制、事件处理 | pip install pygame-ce |
| psutil | >= 5.9.0 | 系统监控：CPU、内存、磁盘、网络等 | pip install psutil |
| pystray | >= 0.19.0 | 系统托盘图标和右键菜单 | pip install pystray |
| Pillow | >= 10.0.0 | 图片处理：Pygame 表面转托盘图标 | pip install Pillow |

---

## 一键安装

```
pip install pygame-ce psutil pystray Pillow
```

注意：Python 3.14 必须使用 pygame-ce（官方 pygame 尚未支持 3.14）

## 运行

```
python main.py
```
