"""
对话气泡模块

在宠物头顶显示带有文字的对话气泡，类似漫画中的对白框。
支持多种情境文案，气泡显示约 3 秒后自动消失。
"""
import random
import pygame


class Bubble:
    """对话气泡类"""

    # 不同情境下的随机文案列表
    MESSAGES = {
        "click": ["嘿嘿~", "别摸我啦~", "好舒服~", "嘬嘬！", "再摸会~"],
        "double_click": ["哇哦！", "讨厌啦~", "害羞啦>///<", "别这样~"],
        "long_press": ["喂！！", "生气啦！", "放开我！！", "哼！(\u2567\u00b0\u25e1\u00b0\uff09\u2567"],
        "bored": ["好无聊啊…", "陪我玩嘛~", "没人理我…", "好想有人陪我…"],
        "wake": ["唔…早上了？", "再睡五分钟…", "哈欠~~", "早上好~"],
        "monitor": ["让我看看你的电脑~", "监测中…", "嗯嗯，状态不错~"],
        "morning": ["早上好！新的一天~", "早安哟~", "今天也要加油！"],
        "night": ["晚安啦~", "好困…", "要睡了…zzZ"],
    }

    def __init__(self):
        self.text = ''           # 当前显示的文字
        self.timer = 0           # 剩余显示时间（帧数）
        self.duration = 90       # 总持续时间（约 3 秒，60FPS）
        self.active = False      # 是否正在显示
        self.font = None         # 文字字体
        self.need_init = True    # 是否需要初始化字体

    def _init_font(self):
        """初始化字体（首次使用延迟初始化）"""
        try:
            self.font = pygame.font.SysFont('simhei', 14)
        except:
            pass
        if self.font is None:
            self.font = pygame.font.Font(None, 16)
        self.need_init = False

    def show(self, category='click'):
        """从指定情境类别中随机选一句文案显示"""
        if self.need_init:
            self._init_font()
        if category in self.MESSAGES:
            self.text = random.choice(self.MESSAGES[category])
        else:
            self.text = '...'
        self.timer = self.duration
        self.active = True

    def show_text(self, text):
        """显示自定义文字"""
        if self.need_init:
            self._init_font()
        self.text = text
        self.timer = self.duration
        self.active = True
        self.text_color = (50, 50, 50)
        # 确保字体已初始化
        if self.font is None:
            self.font = pygame.font.Font(None, 16)

    def show_text_color(self, text, color):
        """显示自定义文字（带颜色）"""
        if self.need_init:
            self._init_font()
        self.text = text
        self.timer = self.duration * 2  # 硬件数据展示久一点（6秒）
        self.active = True
        self.text_color = color

    def update(self):
        """每帧更新，计时归零时自动隐藏"""
        if self.active:
            self.timer -= 1
            if self.timer <= 0:
                self.active = False

    def draw(self, surf, pet_rect):
        """
        在宠物头顶绘制气泡

        surf: 要绘制到的 Pygame 表面
        pet_rect: 宠物的位置矩形，用于定位气泡
        """
        if not self.active or not self.text:
            return
        if self.need_init:
            self._init_font()

        # 渲染文字并计算气泡尺寸
        color = getattr(self, 'text_color', (50, 50, 50))
        text_surf = self.font.render(self.text, True, color)
        tw = text_surf.get_width() + 16   # 气泡宽度（带内边距）
        th = text_surf.get_height() + 8   # 气泡高度（带内边距）
        tw = max(tw, 40)                  # 最小宽度

        # 气泡位置：宠物头顶居中
        bx = pet_rect.centerx - tw // 2
        by = pet_rect.top - th - 8

        # 确保气泡不超出屏幕边界
        sw = surf.get_width()
        bx = max(4, min(bx, sw - tw - 4))
        by = max(4, by)

        # 绘制白色圆角矩形背景
        br = pygame.Rect(bx, by, tw, th)
        pygame.draw.rect(surf, (255, 255, 255), br, border_radius=5)
        pygame.draw.rect(surf, (100, 100, 100), br, width=1, border_radius=5)

        # 绘制气泡下方的三角尾巴（指向宠物头顶）
        tail = [
            (pet_rect.centerx - 4, by + th),
            (pet_rect.centerx + 4, by + th),
            (pet_rect.centerx, by + th + 6),
        ]
        pygame.draw.polygon(surf, (255, 255, 255), tail)

        # 绘制文字
        tx = bx + (tw - text_surf.get_width()) // 2
        ty = by + (th - text_surf.get_height()) // 2
        surf.blit(text_surf, (tx, ty))
