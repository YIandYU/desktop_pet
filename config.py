"""
全局配置管理模块

负责宠物程序配置的持久化存储和读取。
程序退出时保存宠物的位置、状态等信息，
下次启动时自动恢复。
"""
import json
import os

# 配置文件路径：与程序文件同目录下的 pet_config.json
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pet_config.json")

# 配置项默认值
# pet_x, pet_y: 宠物在窗口中的初始位置
# state: 宠物初始状态
# monitor_panel_open: 硬件监测面板默认关闭
# window_topmost: 窗口默认置顶
DEFAULT_CONFIG = {
    # 默认位置用 -1 表示"未保存过"，main.py 会替换为右下角位置
    "pet_x": -1,
    "pet_y": -1,
    "state": "idle",
    "monitor_panel_open": False,
    "window_topmost": True,
}


def load_config():
    """从 JSON 文件加载配置，文件不存在或损坏则返回默认值"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 补充缺失的配置项（用默认值填充）
                for k, v in DEFAULT_CONFIG.items():
                    data.setdefault(k, v)
                return data
        except (json.JSONDecodeError, IOError):
            pass  # 配置文件损坏，使用默认值
    return dict(DEFAULT_CONFIG)


def save_config(config):
    """将配置保存到 JSON 文件"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def reset_config():
    """删除配置文件，重置为默认配置"""
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
    return dict(DEFAULT_CONFIG)
