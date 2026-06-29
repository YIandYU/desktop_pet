"""
宠物核心类

管理宠物的状态、位置、动画和行为逻辑。
包含完整的有限状态机，负责：
- 状态切换（待机/走路/睡觉/开心/被拖拽）
- AI 自动行为（随机走动、日夜模式、无聊入睡）
- 用户交互响应（单击/双击/长按/拖拽/右键）
"""
import random
import pygame
import datetime
from pixel_sprite import get_sprite, get_sprite_size
from bubble import Bubble


class Pet:
    """桌面宠物 - 核心类"""

    # 状态常量定义
    STATE_IDLE = 'idle'      # 待机 - 默认状态，呼吸眨眼
    STATE_WALK = 'walk'      # 走路 - 自动随机行走
    STATE_SLEEP = 'sleep'    # 睡觉 - 夜间或长时间无交互
    STATE_HAPPY = 'happy'    # 开心 - 点击互动反馈
    STATE_ANGRY = 'angry'    # 生气 - 长按 >0.5秒触发
    STATE_CLICKED = 'clicked' # 点击（复用开心动画）
    STATE_DRAGGED = 'dragged' # 被拖拽

    def __init__(self, screen_w, screen_h, start_x, start_y):
        """
        初始化宠物

        screen_w, screen_h: 窗口/活动区域尺寸
        start_x, start_y: 宠物初始位置
        """
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.x = start_x
        self.y = start_y
        sw, sh = get_sprite_size()
        self.rect = pygame.Rect(self.x, self.y, sw, sh)  # 碰撞检测矩形

        # ----- 状态管理 -----
        self.state = self.STATE_IDLE          # 当前状态
        self.prev_state = self.STATE_IDLE     # 上一个状态
        self.anim_frame = 0                   # 动画帧计数器
        self.state_timer = 0                  # 当前状态持续帧数

        # ----- 行走参数 -----
        self.walk_target_x = self.x            # 行走目标 X
        self.walk_target_y = self.y            # 行走目标 Y
        self.walk_dir = 1                      # 行走方向：1=右, -1=左
        self.walk_speed = 1.2                  # 行走速度（像素/帧）
        self.walk_dist = 0                     # 已行走距离
        self.walk_max_dist = random.randint(60, 200)  # 本次行走最大距离

        # ----- 行为计时器 -----
        self.idle_timer = 0                    # 待机已持续帧数
        self.idle_threshold = random.randint(120, 300)  # 待机多久后走动（2~5秒）
        self.boredom_timer = 0                 # 无聊计时器
        self.boredom_threshold = 60 * 60       # 无聊阈值（1分钟无交互 → 睡觉）

        # ----- 点击交互参数 -----
        self.click_timer = 0                   # 点击状态剩余帧数
        self.happy_duration = 30               # 开心状态持续帧数（约0.5秒）
        self.angry_timer = 0                  # 生气状态剩余帧数
        self._next_is_hw = False              # 行走气泡：下一条是否是硬件监测
        self.long_press_timer = 0              # 长按已持续帧数
        self.is_long_pressing = False           # 是否正在长按中
        self.last_click_time = 0                # 上次点击时间（用于双击检测）
        self.double_click_threshold = 400       # 双击判定时间窗口（毫秒）

        # 对话气泡
        self.bubble = Bubble()

        # 是否因无聊入睡（用于区分白天是否自动唤醒）
        self._boredom_slept = False

        # 初始化日夜模式
        self.update_day_night()

    def update_day_night(self):
        """根据系统时间更新日夜模式（夜间: 18:00~6:00）"""
        # 如果设置了 _night_override 标记，跳过自动更新（测试用）
        if hasattr(self, '_night_override') and self._night_override:
            return
        h = datetime.datetime.now().hour
        self.is_night = h < 6 or h >= 18

    def set_pos(self, x, y):
        """
        设置宠物位置（自动限制在窗口边界内）

        超出边界时会被 clamp 到有效范围内
        """
        sw, sh = get_sprite_size()
        self.x = max(0, min(x, self.screen_w - sw))
        self.y = max(0, min(y, self.screen_h - sh))
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    def set_screen(self, w, h):
        """更新窗口尺寸，并确保宠物不超出新窗口"""
        self.screen_w = w
        self.screen_h = h
        self.set_pos(self.x, self.y)

    def change_state(self, new_state):
        """
        切换到新状态

        切换时重置计时器和动画帧，保证每次进入新状态从头开始播放动画
        进入睡眠时重置无聊计时器，避免睡→醒→睡闪烁
        """
        if self.state != new_state:
            self.prev_state = self.state
            self.state = new_state
            self.state_timer = 0
            self.anim_frame = 0
            # 进入睡眠时重置无聊度
            if new_state == self.STATE_SLEEP:
                self.boredom_timer = 0


    # ========== 交互事件处理 ==========

    def on_click(self):
        """左键单击：进入开心状态 + 显示对话气泡"""
        self.change_state(self.STATE_HAPPY)
        self.click_timer = self.happy_duration
        self.boredom_timer = 0
        
        self._boredom_slept = False
        self.bubble.show('click')

    def on_double_click(self):
        """左键双击：进入开心状态（持续更久）+ 害羞气泡"""
        self.change_state(self.STATE_HAPPY)
        self.click_timer = self.happy_duration + 15
        self.boredom_timer = 0
        
        self._boredom_slept = False
        self.bubble.show('double_click')

    def on_long_press_start(self):
        """长按开始：记录长按状态"""
        self.is_long_pressing = True
        self.long_press_timer = 0

    def on_long_press(self):
        """长按持续中：超过 0.5 秒触发愤怒反应"""
        self.long_press_timer += 1
        if self.long_press_timer > 30:  # 30帧 ≈ 0.5秒
            self.change_state(self.STATE_HAPPY)
            self.click_timer = self.happy_duration
            if self.bubble.timer <= 0:
                self.bubble.show('long_press')
            self.boredom_timer = 0

    def on_long_press_end(self):
        """长按结束：回到待机状态"""
        self.is_long_pressing = False
        self.long_press_timer = 0
        if self.state == self.STATE_HAPPY:
            self.change_state(self.STATE_IDLE)

    def on_right_click(self):
        """右键单击：显示监测相关气泡，通知主程序打开面板"""
        self.bubble.show('monitor')
        return True

    # ========== 主更新循环 ==========

    def update(self):
        """
        每帧更新一次

        执行顺序：
        1. 递增动画帧和状态计时器
        2. 更新日夜模式
        3. 更新对话气泡
        4. 处理交互状态的计时退出
        5. 执行 AI 行为逻辑
        6. 更新行走位置
        """
        self.anim_frame += 1
        self.state_timer += 1
        self.update_day_night()
        self.bubble.update()

        # 交互状态计时：快乐/点击状态持续一段时间后自动恢复待机
        if self.state in (self.STATE_HAPPY, self.STATE_CLICKED):
            self.click_timer -= 1
            if self.click_timer <= 0 and not self.is_long_pressing:
                self.change_state(self.STATE_IDLE)

        # AI 行为仅在非交互状态下执行
        if self.state in (self.STATE_IDLE, self.STATE_WALK, self.STATE_SLEEP):
            self._update_ai()

        # 行走位置更新
        if self.state == self.STATE_WALK:
            self._update_walk()

    def _update_ai(self):
        """
        AI 行为逻辑

        - 白天：待机 → 随机走动 → 待机 循环
        - 夜晚：短暂 idle 后入睡
        - 1分钟无交互：入睡（夜晚或无聊度>阈值时）
        - 睡眠中点击唤醒，白天自动唤醒
        """
        self.idle_timer += 1

        # 非用户交互状态累计无聊度（睡眠中不累加，由其自身的 timer 管理）
        if self.state not in (self.STATE_HAPPY, self.STATE_DRAGGED, self.STATE_SLEEP):
            self.boredom_timer += 1

        # 如果正在睡眠中
        if self.state == self.STATE_SLEEP:
            # 白天自动唤醒（仅限夜间睡眠，无聊入睡的白天不唤醒）
            if not self.is_night and self.state_timer > 120:
                if not getattr(self, '_boredom_slept', False):
                    self.change_state(self.STATE_IDLE)
                    self.bubble.show('morning')
            # 睡眠气泡
            elif random.random() < 0.002:
                self.bubble.show('night')
            return

        # 以下逻辑仅对非睡眠状态执行
        if self.state in (self.STATE_IDLE, self.STATE_WALK):

            # 无聊度达到阈值 → 入睡（标记为无聊入睡）
            if self.boredom_timer >= self.boredom_threshold:
                self._boredom_slept = True
                self.change_state(self.STATE_SLEEP)
                self.bubble.show('bored')
                return

            # 夜间：短暂 idle 就睡（不标记，白天自动唤醒）
            if self.is_night and self.state == self.STATE_IDLE and self.boredom_timer > 30:
                self._boredom_slept = False
                self.change_state(self.STATE_SLEEP)
                return

            # 白天 idle 够久 → 随机走动
            if not self.is_night and self.state == self.STATE_IDLE:
                if self.idle_timer >= self.idle_threshold:
                    self._start_walk()
                    self.idle_timer = 0
                    self.idle_threshold = random.randint(120, 300)

    def _show_hw_bubble(self, data):
        """根据硬件数据显示彩色气泡"""
        # 随机选一项硬件数据
        items = []

        cpu = data.get('cpu_percent')
        if cpu is not None:
            items.append(('CPU', cpu, 50, 80, True))

        mem = data.get('mem_percent')
        if mem is not None:
            items.append(('MEM', mem, 50, 80, True))

        batt = data.get('battery_percent')
        if batt is not None:
            # 电池颜色规则相反：越高越绿
            items.append(('BATT', batt, 80, 50, False))

        disks = data.get('disk', [])
        if disks:
            d = disks[0]
            items.append(('DISK', d['percent'], 50, 80, True))

        gpu = data.get('gpu')
        if gpu and gpu.get('gpus'):
            try:
                util = float(gpu['gpus'][0].get('util', -1))
                if util >= 0:
                    items.append(('GPU', util, 50, 80, True))
            except (ValueError, TypeError):
                pass

        if not items:
            return

        name, val, low, high, lower_is_better = random.choice(items)

        # 确定颜色
        if lower_is_better:
            color = (100, 255, 100) if val < low else ((255, 200, 80) if val < high else (255, 100, 100))
        else:
            color = (255, 100, 100) if val < 20 else ((255, 200, 80) if val < low else ((255, 255, 100) if val < high else (100, 255, 100)))

        text = f"{name} {val:.1f}%"
        self.bubble.show_text_color(text, color)

    def _start_walk(self):
        """
        开始随机行走

        随机选择一个方向和距离，计算目标位置
        目标位置会被限制在窗口边界内
        """
        self.change_state(self.STATE_WALK)
        self.walk_dist = 0
        self.walk_max_dist = random.randint(60, 200)
        self.walk_dir = random.choice([-1, 1])

        # 行走时随机显示对话气泡（约1/3概率）
        if random.random() < 0.33:
            if self._next_is_hw and hasattr(self, '_hw_monitor'):
                # 显示硬件监测数据
                hw_data = self._hw_monitor.get_data()
                if hw_data:
                    self._show_hw_bubble(hw_data)
                else:
                    walk_msgs = ["出去走走~", "溜达溜达~", "动一动~", "今天天气不错~", "散个步~", "嘿咻嘿咻~"]
                    self.bubble.show_text(random.choice(walk_msgs))
            else:
                walk_msgs = ["出去走走~", "溜达溜达~", "动一动~", "今天天气不错~", "散个步~", "嘿咻嘿咻~"]
                self.bubble.show_text(random.choice(walk_msgs))
            # 切换标记：下次行走显示另一种类型
            self._next_is_hw = not self._next_is_hw

        # 计算目标位置（水平方向为主，垂直略有偏移）
        tx = self.x + self.walk_dir * self.walk_max_dist
        ty = self.y + random.randint(-30, 30)

        # 限制在窗口内
        sw, sh = get_sprite_size()
        self.walk_target_x = max(0, min(tx, self.screen_w - sw))
        self.walk_target_y = max(0, min(ty, self.screen_h - sh))

    def _update_walk(self):
        """更新行走位置：向目标点移动"""
        dx = self.walk_target_x - self.x
        dy = self.walk_target_y - self.y
        dist = (dx * dx + dy * dy) ** 0.5

        if dist < self.walk_speed:
            # 到达目标，停下来待机
            self.set_pos(self.walk_target_x, self.walk_target_y)
            self.change_state(self.STATE_IDLE)
        else:
            # 继续向目标移动
            self.set_pos(
                self.x + (dx / dist) * self.walk_speed,
                self.y + (dy / dist) * self.walk_speed
            )

    # ========== 拖拽处理 ==========

    def handle_drag(self, mx, my):
        """
        处理拖拽：跟随鼠标移动

        mx, my: 鼠标在窗口中的坐标
        """
        self.change_state(self.STATE_DRAGGED)
        self.boredom_timer = 0
        self.set_pos(mx - self.rect.width // 2, my - self.rect.height // 2)

    def release_drag(self):
        """释放拖拽：回到待机状态"""
        if self.state == self.STATE_DRAGGED:
            self.change_state(self.STATE_IDLE)

    # ========== 绘制与持久化 ==========

    def draw(self, surf):
        """
        绘制宠物到表面

        先绘制精灵，再绘制对话气泡
        """
        sprite = get_sprite(self.state, self.anim_frame)
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        surf.blit(sprite, self.rect)        # 绘制宠物本体
        self.bubble.draw(surf, self.rect)    # 绘制对话气泡

    def get_surface_for_icon(self):
        """
        生成透明背景上的宠物待机图，用于系统托盘图标
        """
        sprite = get_sprite(self.state, self.anim_frame)
        # 创建带透明通道的表面，不填充背景色
        icon_surf = pygame.Surface(
            (sprite.get_width(), sprite.get_height()), pygame.SRCALPHA
        )
        icon_surf.blit(sprite, (0, 0))
        return icon_surf

    def save_state(self):
        """保存当前状态用于持久化"""
        return {
            'pet_x': int(self.x),
            'pet_y': int(self.y),
            'state': self.state,
        }

    def load_state(self, data):
        """
        从保存的数据恢复状态

        data: 从 JSON 读取的配置字典
        状态统一重置为 idle，避免加载到 sleep 等异常状态
        """
        if 'pet_x' in data:
            self.set_pos(data['pet_x'], data['pet_y'])
        self.change_state(self.STATE_IDLE)
