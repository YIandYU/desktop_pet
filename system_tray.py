"""
系统托盘模块 - 在任务栏通知区域显示宠物图标
"""
import pystray
from PIL import Image
import pygame
import threading
from auto_start import is_auto_start_enabled, toggle_auto_start


class SystemTray:
    """系统托盘图标管理"""

    def __init__(self, pet, on_toggle_visible, on_exit_callback):
        """
        pet: 宠物实例（用来获取精灵图和图标）
        on_toggle_visible: 切换隐藏/显示的回调，返回新状态（True=显示）
        on_exit_callback: 退出时的回调函数
        """
        self.pet = pet
        self.on_toggle_visible = on_toggle_visible
        self.on_exit_callback = on_exit_callback
        self._icon = None
        self._thread = None

    def start(self):
        """在后台线程中启动托盘图标"""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _create_image(self):
        """从宠物待机精灵创建托盘图标图像"""
        # 渲染宠物待机精灵
        surf = self.pet.get_surface_for_icon()
        # 转换为 PIL Image
        raw_str = pygame.image.tostring(surf, "RGBA")
        w, h = surf.get_size()
        img = Image.frombytes("RGBA", (w, h), raw_str)
        # 缩放到托盘图标大小（保持像素风格）
        img = img.resize((64, 64), Image.NEAREST)
        return img

    def _run(self):
        """运行托盘图标（在单独线程中）"""
        img = self._create_image()

        # 开机自启动菜单项（带复选框）
        self._auto_start_item = pystray.MenuItem(
            "开机自启动",
            self._on_toggle_auto_start,
            checked=lambda item: is_auto_start_enabled(),
        )

        # 显示/隐藏切换菜单项（带复选框，默认显示）
        self._visible = True
        self._visible_item = pystray.MenuItem(
            "显示宠物",
            self._on_toggle_visible_menu,
            checked=lambda item: self._visible,
            default=True,
        )

        menu = pystray.Menu(
            self._visible_item,
            pystray.Menu.SEPARATOR,
            self._auto_start_item,
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("作者以及声明", self._on_about),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出本桌宠程序", self._on_exit),
        )

        self._icon = pystray.Icon("desktop_pet", img, "桌面宠物", menu)
        self._icon.run()

    def _on_toggle_visible_menu(self, icon, item):
        """点击"显示宠物"：切换隐藏/显示"""
        self._visible = self.on_toggle_visible()
        # 更新菜单勾选状态
        if hasattr(icon, 'update_menu'):
            icon.update_menu()

    def _on_toggle_auto_start(self, icon, item):
        """点击"开机自启动"：切换自启动状态"""
        new_state = toggle_auto_start()
        if new_state:
            print("✅ 开机自启动已开启")
        else:
            print(" 开机自启动已关闭")

    def _on_about(self, icon, item):
        """点击"作者以及声明"：弹窗显示作者和免责声明"""
        title = "作者以及声明"
        line1 = "创作作者：爱摸鱼的YI..（以下简称\u201c作者\u201d）\n\n"
        line2 = "免责声明：\n\n"
        line3 = "1. 项目性质：本软件为作者个人开源项目，开发过程借助 AI 大模型辅助，免费提供用于学习与非商业用途，不构成任何服务承诺。\n\n"
        line4 = "2. 概不担保：软件按现状封装，作者不担保其稳定性、兼容性、安全性，不保证无缺陷或适配所有环境。\n\n"
        line5 = "3. 风险自担：使用者自行承担安装、运行、修改本软件产生的全部风险，包括系统故障、数据丢失等，作者不对任何直接或间接损失承担责任。\n\n"
        line6 = "4. 二次开发：修改与再分发需保留本声明，衍生版本的所有责任由修改方独立承担，与原作者无关。\n\n"
        line7 = "5. 作者有权随时终止项目维护，本声明适用中华人民共和国法律。\n\n"
        line8 = "创作时间：2026/6/28\n"
        line9 = "封装时间：2026/7/01"
        msg = line1 + line2 + line3 + line4 + line5 + line6 + line7 + line8 + line9
        # 弹窗放在新线程中运行，不阻塞托盘线程
        import threading
        def _show():
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(0, msg, title, 0)
            except Exception as e:
                print(f"弹窗失败: {e}")
                print(f"=== {title} ===")
                print(msg)
        t = threading.Thread(target=_show, daemon=True)
        t.start()

    def _on_exit(self, icon, item):
        """点击"退出程序"：退出托盘图标并触发程序退出"""
        self._icon.stop()
        self.on_exit_callback()

    def stop(self):
        """停止托盘图标"""
        if self._icon:
            self._ico