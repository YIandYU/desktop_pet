"""
桌面宠物 - 程序主入口

启动桌面宠物程序，全屏透明窗口，宠物在桌面任意处活动。
负责：
- 初始化 Pygame 窗口（无边框透明置顶）
- 事件循环（鼠标点击/拖拽/键盘）
- 绘制宠物和硬件监测面板
- 程序退出时自动保存状态
"""
import sys
import os
import pygame
from config import load_config, save_config
from pet import Pet
from hardware_monitor import HardwareMonitor
from system_tray import SystemTray

# ===== 窗口配置 =====
FPS = 60                # 帧率


class DesktopPetApp:
    """桌面宠物主应用类"""

    def __init__(self):
        """初始化程序，创建窗口、宠物和监测器"""
        pygame.init()
        pygame.display.set_caption('Desktop Pet')

        # 获取屏幕尺寸，全屏覆盖
        info = pygame.display.Info()
        self.screen_w = info.current_w        # 屏幕物理宽度
        self.screen_h = info.current_h        # 屏幕物理高度

        # 创建无边框全屏透明窗口
        # NOFRAME: 无标题栏和边框
        # SRCALPHA: 支持逐像素透明度
        flags = pygame.NOFRAME | pygame.SRCALPHA
        self.disp_w = self.screen_w            # 窗口 = 全屏宽
        self.disp_h = self.screen_h            # 窗口 = 全屏高
        self.screen = pygame.display.set_mode((self.disp_w, self.disp_h), flags)

        # 设置黑色为透明色（所有黑色像素不显示）
        self.screen.set_colorkey((0, 0, 0))
        self.clock = pygame.time.Clock()

        # ----- 加载配置，恢复上次的位置 -----
        config = load_config()
        # 默认位置：屏幕右下角（距离右下边缘各 80 像素）
        default_sx = self.disp_w - 150
        default_sy = self.disp_h - 200
        sx = config.get('pet_x', default_sx)
        sy = config.get('pet_y', default_sy)
        # 边界检查：默认强制右下角位置
        # 如果坐标在屏幕左半边或超出范围 → 使用右下角默认值
        if sx < self.disp_w // 2 or sx > self.disp_w - 96:
            sx = default_sx
        if sy < 1 or sy > self.disp_h - 128:
            sy = default_sy

        # ----- 硬件监测模块 -----
        self.monitor = HardwareMonitor()  # 硬件数据采集器

        # ----- 初始化宠物 -----
        self.pet = Pet(self.disp_w, self.disp_h, sx, sy)
        self.pet._hw_monitor = self.monitor
        self.monitor_open = False         # 监测面板是否打开
        self.monitor_data = []            # 缓存的面板数据
        self.monitor_rect = None          # 面板区域（用于检测点击关闭）

        # ----- 交互状态 -----
        self.dragging = False             # 是否正在拖拽
        self.last_click_time = 0          # 上次点击时间戳

        # ----- 隐藏/显示状态 -----
        self._hidden = False
        self.anim_counter = 0

        # ----- 系统托盘图标 -----
        self.tray = SystemTray(self.pet, self._on_toggle_visible, self._on_tray_exit)

        # ----- 字体初始化 -----
        pygame.font.init()
        self.mfont = pygame.font.SysFont('simhei', 12)  # 使用中文字体
        if self.mfont is None:
            self.mfont = pygame.font.Font(None, 14)     # 回退到默认字体

        # 将窗口定位到屏幕右下角并置顶
        self._init_window_win32()

        # 启动系统托盘图标
        self.tray.start()

        print(f'Desktop Pet started! Screen: {self.disp_w}x{self.disp_h}, pet at bottom-right')
        print('Left click: interact | Left drag: move | Right click: monitor | ESC: exit')

    def _on_toggle_visible(self):
        """托盘切换隐藏/显示：返回新状态"""
        self._hidden = not self._hidden
        if self._hidden:
            # 隐藏：最小化窗口到屏幕外
            if sys.platform == 'win32':
                try:
                    import ctypes
                    hwnd = pygame.display.get_wm_info()['window']
                    # 移到屏幕外（-32000, -32000），相当于隐藏
                    ctypes.windll.user32.SetWindowPos(
                        hwnd, 0, -32000, -32000, 0, 0, 0x0001
                    )
                except Exception:
                    pass
            print(" 宠物已隐藏 (托盘图标可见)")
        else:
            # 显示：恢复到全屏置顶
            self._set_topmost_win32()
            if sys.platform == 'win32':
                try:
                    import ctypes
                    hwnd = pygame.display.get_wm_info()['window']
                    ctypes.windll.user32.SetWindowPos(
                        hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0010
                    )
                except Exception:
                    pass
            print(" 宠物已显示")
        return not self._hidden

    def _on_tray_exit(self):
        """系统托盘"退出"回调：标记主循环结束"""
        self._exit_requested = True

    def _set_topmost_win32(self):
        """置顶：带重试的强力方式"""
        try:
            if sys.platform == 'win32':
                import ctypes
                hwnd = pygame.display.get_wm_info()['window']
                # 重试3次确保生效
                for _ in range(3):
                    ctypes.windll.user32.SetWindowPos(
                        hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0010)
        except Exception:
            pass

    def _init_window_win32(self):
        """窗口初始化：分层透明 + 隐藏任务栏"""
        try:
            if sys.platform == 'win32':
                import ctypes
                hwnd = pygame.display.get_wm_info()['window']
                GWL_EXSTYLE = -20
                WS_EX_LAYERED = 0x80000
                WS_EX_TOOLWINDOW = 0x80
                cur = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE,
                    cur | WS_EX_LAYERED | WS_EX_TOOLWINDOW)
                ctypes.windll.user32.SetLayeredWindowAttributes(
                    hwnd, 0x000000, 0, 1)
                self._set_topmost_win32()

                # 启动后台线程：每 0.1 秒强制置顶
                import threading as _thr
                def _keep_topmost():
                    while True:
                        try:
                            _thr.Event().wait(0.1)
                            ctypes.windll.user32.SetWindowPos(
                                hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0010)
                        except Exception:
                            pass
                t = _thr.Thread(target=_keep_topmost, daemon=True)
                t.start()
        except Exception:
            pass


    def _draw_monitor_panel(self):
        """
        绘制硬件监测面板

        面板外观：
        - 半透明深色背景，蓝色边框
        - 标题栏带 "X" 关闭按钮
        - 数据行根据使用率自动变色（绿/黄/红）
        - 面板位置自适应（优先显示在宠物上方，否则下方）
        """
        if not self.monitor_open:
            return

        # 先获取数据行数，计算面板高度
        lines = self.monitor.get_display_data()
        # 计算高度：标题22px + 上边距6px + 每行16px + 每行文字换行 + 分割线额外6px + 底部内边距6px
        data_height = 22 + 6  # 标题栏 + 顶部间距
        for line in lines:
            if line.startswith('==='):
                data_height += 6 + 1  # 分割线行
            else:
                data_height += 16
        data_height += 6  # 底部内边距
        data_height = max(data_height, 50)  # 最小高度

        # 面板宽度固定，高度自适应
        pw, ph = 260, data_height

        # 面板位置：默认在宠物右侧
        px = self.pet.x + self.pet.rect.width + 10
        py = max(self.pet.y - 10, 5)
        # 右侧放不下则改到左侧
        if px + pw > self.disp_w:
            px = self.pet.x - pw - 10
        # 仍然超出则靠边
        px = max(5, min(px, self.disp_w - pw - 5))
        py = min(py, self.disp_h - ph - 5)

        # 创建半透明毛玻璃风格背景
        bg = pygame.Surface((pw, ph), pygame.SRCALPHA)
        # 深紫灰色半透明底色
        bg.fill((35, 30, 55, 195))
        # 顶部淡蓝高光线
        hl_top = pygame.Surface((pw, 3), pygame.SRCALPHA)
        hl_top.fill((120, 160, 255, 50))
        bg.blit(hl_top, (0, 0))
        hl_bot = pygame.Surface((pw, 3), pygame.SRCALPHA)
        hl_bot.fill((120, 160, 255, 25))
        bg.blit(hl_bot, (0, ph - 3))
        # 蓝紫色像素风边框
        pygame.draw.rect(bg, (130, 170, 255, 210), bg.get_rect(), 2)

        # ----- 标题栏 -----
        # 渐变色标题栏：比底色稍亮
        title_bar = pygame.Surface((pw, 22), pygame.SRCALPHA)
        title_bar.fill((70, 90, 180, 160))
        pygame.draw.rect(title_bar, (130, 170, 255, 180), title_bar.get_rect(), 1)
        bg.blit(title_bar, (0, 0))
        title = self.mfont.render('Hardware Monitor', True, (220, 235, 255))
        bg.blit(title, (6, 4))
        close = self.mfont.render('X', True, (255, 120, 120))
        bg.blit(close, (pw - 16, 4))

        # ----- 数据行 -----
        y = 28
        for line in lines:
            if line.startswith('==='):
                # 分割线
                sep = pygame.Surface((pw - 16, 1))
                sep.fill((100, 130, 200, 100))
                bg.blit(sep, (8, y))
                y += 6
                continue

            # 数据行颜色规则
            # 通用：>80% 红色 | >50% 黄色 | <50% 绿色
            # 电池：>80% 绿色 | >50% 黄色 | <20% 红色（越低越危险）
            color = (180, 220, 255) if ':' in line else (150, 150, 150)
            if '%' in line and ':' in line:
                import re
                match = re.search(r'(\d+(?:\.\d+)?)\s*%', line)
                if match:
                    try:
                        v = float(match.group(1))
                        if line.startswith('BATT:'):
                            # 电池：高电量绿色，低电量红色
                            color = (100, 255, 100) if v > 80 else ((255, 255, 100) if v > 50 else ((255, 200, 80) if v > 20 else (255, 100, 100)))
                        else:
                            # 其他（CPU/GPU/MEM/磁盘等）：低占用绿色
                            color = (100, 255, 100) if v < 50 else ((255, 200, 80) if v < 80 else (255, 100, 100))
                    except ValueError:
                        pass

            # 渲染并绘制当前行
            ts = self.mfont.render(line, True, color)
            bg.blit(ts, (8, y))
            y += 16

        # 绘制面板到窗口
        self.screen.blit(bg, (px, py))
        self.monitor_rect = pygame.Rect(px, py, pw, ph)

    def _check_monitor_close(self, mx, my):
        """
        检查鼠标是否点击了面板的关闭按钮

        关闭按钮在面板右上角 (X)
        """
        if not self.monitor_open or not self.monitor_rect:
            return False
        cr = pygame.Rect(
            self.monitor_rect.x + self.monitor_rect.width - 20,
            self.monitor_rect.y + 2,
            18, 18
        )
        return cr.collidepoint(mx, my)

    def run(self):
        """主循环：事件处理 + 更新 + 绘制，60FPS 运行"""
        self._exit_requested = False
        running = True
        self.anim_counter = 0
        self.monitor.start()  # 启动硬件数据后台采集

        try:
            while running and not self._exit_requested:
                mx, my = pygame.mouse.get_pos()

                # ===== 事件处理 =====
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False

                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1:  # 左键
                            # 检查是否点击了监测面板关闭按钮
                            if self.monitor_open and self._check_monitor_close(
                                    event.pos[0], event.pos[1]):
                                self.monitor_open = False
                                continue

                            # 点击宠物区域
                            if self.pet.rect.collidepoint(event.pos):
                                ct = pygame.time.get_ticks()
                                # 双击检测：两次点击间隔 < 400ms
                                if ct - self.last_click_time < 400:
                                    self.pet.on_double_click()
                                    self.last_click_time = 0
                                else:
                                    self.last_click_time = ct
                                    self.pet.on_click()
                                # 长按检测开始
                                self.pet.on_long_press_start()
                                self.dragging = True
                            elif self.monitor_open:
                                # 点击面板外区域关闭面板
                                self.monitor_open = False

                        elif event.button == 3:  # 右键
                            if self.pet.rect.collidepoint(event.pos):
                                # 切换监测面板开关
                                self.monitor_open = not self.monitor_open
                                self.pet.on_right_click()

                    elif event.type == pygame.MOUSEBUTTONUP:
                        if event.button == 1:  # 左键释放
                            if self.dragging:
                                self.dragging = False
                                self.pet.release_drag()
                            if self.pet.is_long_pressing:
                                self.pet.on_long_press_end()

                    elif event.type == pygame.MOUSEMOTION:
                        if self.dragging:
                            # 拖拽宠物跟随鼠标
                            self.pet.handle_drag(event.pos[0], event.pos[1])

                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            running = False  # ESC 退出

                self.anim_counter += 1

                # ===== 长按持续检测（每帧检测鼠标状态）=====
                if self.pet.is_long_pressing and pygame.mouse.get_pressed()[0]:
                    self.pet.on_long_press()

                # ===== 更新宠物状态 =====
                self.pet.update()

                # ===== 绘制画面 =====
                self.screen.fill((0, 0, 0))   # 填黑色（透明）
                self.pet.draw(self.screen)     # 绘制宠物
                if self.monitor_open:
                    self._draw_monitor_panel()  # 绘制监测面板

                pygame.display.flip()          # 刷新显示


                self._set_topmost_win32()
                self.clock.tick(FPS)           # 控制帧率

        finally:
            self._shutdown()  # 安全退出

    def _shutdown(self):
        """程序退出前的清理工作：停止监测，保存状态"""
        self.monitor.stop()                     # 停止硬件采集
        try:
            self.tray.stop()                    # 停止托盘图标
        except Exception:
            pass
        state = self.pet.save_state()           # 保存宠物状态
        cfg = load_config()
        cfg.update(state)                       # 更新配置
        save_config(cfg)                        # 写入文件
        pygame.quit()                           # 退出 Pygame
        print('Desktop Pet exited!')            # 控制台提示


if __name__ == '__main__':
    """程序入口"""
    DesktopPetApp().run()
