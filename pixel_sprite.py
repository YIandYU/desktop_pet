"""
像素精灵绘制模块 - Q 版像素钢铁侠

通过 Pygame 逐像素绘制所有动画帧，不依赖外部图片文件。
每个动画函数接收 frame 参数控制动画进度。
精灵实际尺寸: 24x32 逻辑像素 * 4 缩放 = 96x128 物理像素
"""
import pygame


# 钢铁侠配色调色板
COLORS = {
    "body_red": (180, 30, 30),         # 装甲主体红色
    "body_red_dark": (130, 20, 20),    # 暗红色（阴影）
    "body_red_light": (220, 60, 60),   # 亮红色（高光）
    "gold": (200, 170, 50),            # 金色（面罩、手臂、腿）
    "gold_light": (230, 200, 80),      # 亮金色
    "gold_dark": (150, 120, 30),       # 暗金色
    "reactor": (60, 200, 255),         # 方舟反应炉 - 蓝色
    "reactor_light": (150, 230, 255),  # 反应炉高光
    "eye": (60, 200, 255),             # 眼睛发光蓝色
    "eye_off": (40, 40, 60),           # 闭眼
    "eye_happy": (255, 200, 100),      # 开心时眼睛暖色
    "eye_angry": (255, 30, 30),        # 生气时眼睛红色
    "mouth": (100, 100, 100),          # 嘴巴缝隙
    "shadow": (50, 100, 220, 80),      # 蓝色阴影
    "bg_key": (0, 0, 0),              # 背景色（黑色作为透明色）
}

# 像素缩放倍数
PIXEL_SCALE = 4

# 精灵逻辑尺寸
SPRITE_W = 24
SPRITE_H = 32


def _set_pixel(surf, x, y, color):
    """在表面上绘制一个像素块（逻辑坐标转物理坐标）"""
    pygame.draw.rect(surf, color, (x * PIXEL_SCALE, y * PIXEL_SCALE, PIXEL_SCALE, PIXEL_SCALE))


def _fill_bg(surf):
    """填充背景色（黑色=透明）"""
    surf.fill(COLORS["bg_key"])


def draw_ironman_idle(frame=0):
    """
    待机动画 - 呼吸/反应炉闪烁

    帧循环规律:
    - 呼吸: 每 60 帧上下浮动 1 像素
    - 反应炉: 每 20 帧闪烁一次
    """
    surf = pygame.Surface((SPRITE_W * PIXEL_SCALE, SPRITE_H * PIXEL_SCALE))
    _fill_bg(surf)

    breath = -1 if (frame % 60) < 30 else 0

    # ----- 头部（金色面罩）-----
    for y in range(2, 11):
        for x in range(7, 17):
            if y == 2 and x not in range(8, 16): continue
            if y == 10 and x not in range(8, 16): continue
            _set_pixel(surf, x, y + breath, COLORS["gold"])

    # 头部红色部分（头顶两侧）
    for x in range(7, 9):
        for y in range(3, 5):
            _set_pixel(surf, x, y + breath, COLORS["body_red"])
    for x in range(15, 17):
        for y in range(3, 5):
            _set_pixel(surf, x, y + breath, COLORS["body_red"])

    # 眼睛（发光蓝色）
    if (frame // 40) % 4 != 0:  # 偶尔眨眼
        _set_pixel(surf, 9, 5 + breath, COLORS["eye"])
        _set_pixel(surf, 10, 5 + breath, COLORS["eye"])
        _set_pixel(surf, 14, 5 + breath, COLORS["eye"])
        _set_pixel(surf, 15, 5 + breath, COLORS["eye"])
    else:
        _set_pixel(surf, 9, 5 + breath, COLORS["eye_off"])
        _set_pixel(surf, 10, 5 + breath, COLORS["eye_off"])
        _set_pixel(surf, 14, 5 + breath, COLORS["eye_off"])
        _set_pixel(surf, 15, 5 + breath, COLORS["eye_off"])

    # 嘴巴金色线条
    for x in range(11, 13):
        _set_pixel(surf, x, 8 + breath, COLORS["mouth"])

    # ----- 身体（红色装甲）-----
    for y in range(11, 21):
        for x in range(6, 18):
            _set_pixel(surf, x, y, COLORS["body_red"])

    # 身体左右两侧高光
    for y in range(12, 17):
        for x in range(7, 10):
            _set_pixel(surf, x, y, COLORS["body_red_light"])
        for x in range(14, 17):
            _set_pixel(surf, x, y, COLORS["body_red_light"])

    # 金色腰带
    for y in range(18, 20):
        for x in range(7, 17):
            _set_pixel(surf, x, y, COLORS["gold"])

    # ----- 方舟反应炉（胸口）-----
    if (frame // 20) % 2 == 0:
        for x in range(11, 13):
            for y in range(13, 15):
                _set_pixel(surf, x, y, COLORS["reactor_light"])
    for x in range(11, 13):
        _set_pixel(surf, x, 13, COLORS["reactor"])
        _set_pixel(surf, x, 14, COLORS["reactor"])

    # ----- 手臂（红色+金色）-----
    for y in range(12, 18):
        for x in range(4, 6):
            _set_pixel(surf, x, y, COLORS["gold"])
        for x in range(18, 20):
            _set_pixel(surf, x, y, COLORS["gold"])
    # 肩部金色
    for y in range(11, 13):
        for x in range(4, 6):
            _set_pixel(surf, x, y, COLORS["body_red"])
        for x in range(18, 20):
            _set_pixel(surf, x, y, COLORS["body_red"])

    # ----- 腿（红色+金色）-----
    for y in range(21, 27):
        for x in range(8, 11):
            _set_pixel(surf, x, y, COLORS["body_red"])
        for x in range(13, 16):
            _set_pixel(surf, x, y, COLORS["body_red"])
    # 小腿金色
    for y in range(24, 27):
        for x in range(8, 11):
            _set_pixel(surf, x, y, COLORS["gold"])
        for x in range(13, 16):
            _set_pixel(surf, x, y, COLORS["gold"])

    # 脚（金色）
    for x in range(7, 12):
        _set_pixel(surf, x, 27, COLORS["gold"])
    for x in range(12, 17):
        _set_pixel(surf, x, 27, COLORS["gold"])

    surf.set_colorkey(COLORS["bg_key"])
    return surf


def draw_ironman_walk(frame=0):
    """
    走路动画 - 手臂和腿交替摆动
    """
    surf = pygame.Surface((SPRITE_W * PIXEL_SCALE, SPRITE_H * PIXEL_SCALE))
    _fill_bg(surf)

    offset = 1 if (frame // 8) % 4 < 2 else -1

    # ----- 头部（金色面罩）-----
    for y in range(2, 10):
        for x in range(7, 17):
            if y == 2 and x not in range(8, 16): continue
            if y == 9 and x not in range(8, 16): continue
            _set_pixel(surf, x, y, COLORS["gold"])
    for x in range(7, 9):
        for y in range(3, 5):
            _set_pixel(surf, x, y, COLORS["body_red"])
    for x in range(15, 17):
        for y in range(3, 5):
            _set_pixel(surf, x, y, COLORS["body_red"])

    for x in (9, 10, 14, 15):
        _set_pixel(surf, x, 5, COLORS["eye"])
    for x in range(11, 13):
        _set_pixel(surf, x, 7, COLORS["mouth"])

    # ----- 身体（红色装甲）-----
    for y in range(10, 20):
        for x in range(6, 18):
            _set_pixel(surf, x, y, COLORS["body_red"])
    for y in range(11, 16):
        for x in range(7, 10):
            _set_pixel(surf, x, y, COLORS["body_red_light"])
        for x in range(14, 17):
            _set_pixel(surf, x, y, COLORS["body_red_light"])

    # 腰带金色
    for y in range(17, 19):
        for x in range(7, 17):
            _set_pixel(surf, x, y, COLORS["gold"])

    # 反应炉
    for x in range(11, 13):
        for y in range(12, 14):
            _set_pixel(surf, x, y, COLORS["reactor"])

    # 手臂摆动
    arm = offset
    for y in range(11, 18):
        _set_pixel(surf, 4 + arm, y, COLORS["gold"])
        _set_pixel(surf, 5 + arm, y, COLORS["gold"])
        _set_pixel(surf, 18 - arm, y, COLORS["gold"])
        _set_pixel(surf, 19 - arm, y, COLORS["gold"])
    for y in range(11, 13):
        _set_pixel(surf, 4 + arm, y, COLORS["body_red"])
        _set_pixel(surf, 5 + arm, y, COLORS["body_red"])
        _set_pixel(surf, 18 - arm, y, COLORS["body_red"])
        _set_pixel(surf, 19 - arm, y, COLORS["body_red"])

    # 腿交替
    leg = offset
    for y in range(20, 26):
        for x in range(8, 11):
            _set_pixel(surf, x + leg, y, COLORS["body_red"])
        for x in range(13, 16):
            _set_pixel(surf, x - leg, y, COLORS["body_red"])
    # 小腿金色
    for y in range(23, 26):
        for x in range(8, 11):
            _set_pixel(surf, x + leg, y, COLORS["gold"])
        for x in range(13, 16):
            _set_pixel(surf, x - leg, y, COLORS["gold"])

    for x in range(7, 12):
        _set_pixel(surf, x + leg, 26, COLORS["gold"])
    for x in range(12, 17):
        _set_pixel(surf, x - leg, 26, COLORS["gold"])

    surf.set_colorkey(COLORS["bg_key"])
    return surf


def draw_ironman_sleep(frame=0):
    """
    睡觉动画 - 闭眼打坐，反应炉微弱发光
    """
    surf = pygame.Surface((SPRITE_W * PIXEL_SCALE, SPRITE_H * PIXEL_SCALE))
    _fill_bg(surf)

    breath = -1 if (frame % 90) < 45 else 0

    # 头部（金色变暗表示待机）
    for y in range(3, 11):
        for x in range(7, 17):
            if y == 3 and x not in range(8, 16): continue
            if y == 10 and x not in range(8, 16): continue
            _set_pixel(surf, x, y + breath, COLORS["gold_dark"])

    # 闭眼
    for x in (9, 10, 14, 15):
        _set_pixel(surf, x, 6 + breath, COLORS["eye_off"])

    # Zzz
    zf = (frame // 30) % 3
    if zf >= 0:
        _set_pixel(surf, 18, 3, (200, 200, 255))
        _set_pixel(surf, 18, 2, (200, 200, 255))
    if zf >= 1:
        _set_pixel(surf, 20, 1, (200, 200, 255))
    if zf >= 2:
        _set_pixel(surf, 22, 0, (200, 200, 255))

    # 身体（盘腿）
    for y in range(11, 19):
        for x in range(6, 18):
            _set_pixel(surf, x, y + breath, COLORS["body_red_dark"])

    # 反应炉微弱发光
    if (frame // 30) % 2 == 0:
        for x in range(11, 13):
            for y_pos in range(13, 15):
                _set_pixel(surf, x, y_pos + breath, COLORS["reactor"])

    # 交叉手臂
    for x in range(8, 16):
        for y in range(13, 15):
            _set_pixel(surf, x, y + breath, COLORS["gold_dark"])

    # 盘腿
    for y in range(19, 24):
        for x in range(7, 17):
            _set_pixel(surf, x, y + breath, COLORS["body_red_dark"])

    surf.set_colorkey(COLORS["bg_key"])
    return surf


def draw_ironman_happy(frame=0):
    """
    开心动画 - 跳跃 + 掌心炮特效
    """
    surf = pygame.Surface((SPRITE_W * PIXEL_SCALE, SPRITE_H * PIXEL_SCALE))
    _fill_bg(surf)

    phase = (frame // 4) % 8
    jump = -phase if phase < 4 else -(8 - phase)

    # 头部
    for y in range(2, 10):
        for x in range(7, 17):
            if y == 2 and x not in range(8, 16): continue
            if y == 9 and x not in range(8, 16): continue
            _set_pixel(surf, x, y + jump, COLORS["gold"])

    # 开心眼睛（暖色发光）
    for x in (9, 10, 14, 15):
        _set_pixel(surf, x, 5 + jump, COLORS["eye_happy"])
    _set_pixel(surf, 9, 6 + jump, COLORS["eye_happy"])
    _set_pixel(surf, 15, 6 + jump, COLORS["eye_happy"])

    # 张嘴笑
    for x in range(11, 14):
        _set_pixel(surf, x, 7 + jump, COLORS["mouth"])
    _set_pixel(surf, 11, 8 + jump, COLORS["mouth"])
    _set_pixel(surf, 13, 8 + jump, COLORS["mouth"])

    # 身体
    for y in range(10, 20):
        for x in range(6, 18):
            _set_pixel(surf, x, y + jump, COLORS["body_red"])

    for y in range(11, 15):
        for x in range(7, 10):
            _set_pixel(surf, x, y + jump, COLORS["body_red_light"])
        for x in range(14, 17):
            _set_pixel(surf, x, y + jump, COLORS["body_red_light"])

    # 腰带
    for y in range(17, 19):
        for x in range(7, 17):
            _set_pixel(surf, x, y + jump, COLORS["gold"])

    # 反应炉发光（强光）
    for x in range(10, 14):
        for y_pos in range(12, 15):
            _set_pixel(surf, x, y_pos + jump, COLORS["reactor_light"])

    # 手臂举起（掌心朝上，带蓝色光效）
    for y in range(8, 11):
        for x in range(3, 6):
            _set_pixel(surf, x, y + jump, COLORS["gold"])
        for x in range(18, 21):
            _set_pixel(surf, x, y + jump, COLORS["gold"])
    # 掌心炮光效
    hp = (frame // 6) % 2
    for x in range(3, 4):
        for y_pos in range(7, 8):
            _set_pixel(surf, x, y_pos + jump - hp, COLORS["reactor_light"])
    for x in range(20, 21):
        for y_pos in range(7, 8):
            _set_pixel(surf, x, y_pos + jump - hp, COLORS["reactor_light"])

    # 腿
    for y in range(20, 26):
        for x in range(8, 11):
            _set_pixel(surf, x, y + jump, COLORS["body_red"])
        for x in range(13, 16):
            _set_pixel(surf, x, y + jump, COLORS["body_red"])
    for y in range(23, 26):
        for x in range(8, 11):
            _set_pixel(surf, x, y + jump, COLORS["gold"])
        for x in range(13, 16):
            _set_pixel(surf, x, y + jump, COLORS["gold"])

    for x in range(7, 12):
        _set_pixel(surf, x, 26 + jump, COLORS["gold"])
    for x in range(12, 17):
        _set_pixel(surf, x, 26 + jump, COLORS["gold"])

    surf.set_colorkey(COLORS["bg_key"])
    return surf


def draw_ironman_dragged(frame=0):
    """
    被拖拽动画 - 被提起的惊讶姿态
    """
    surf = pygame.Surface((SPRITE_W * PIXEL_SCALE, SPRITE_H * PIXEL_SCALE))
    _fill_bg(surf)

    tilt = 1

    # 头部歪斜
    for y in range(2, 10):
        for x in range(7, 17):
            if y == 2 and x not in range(8, 16): continue
            if y == 9 and x not in range(8, 16): continue
            _set_pixel(surf, x + tilt, y, COLORS["gold"])

    # 惊讶眼睛（放大发光）
    for pair in [(9, 10), (14, 15)]:
        for px in pair:
            _set_pixel(surf, px + tilt, 5, COLORS["reactor_light"])
            _set_pixel(surf, px + tilt, 6, COLORS["reactor_light"])
            _set_pixel(surf, px + tilt, 5, COLORS["eye"])

    # 嘴巴（O形）
    for x in range(11, 14):
        _set_pixel(surf, x + tilt, 8, COLORS["mouth"])

    # 身体
    for y in range(10, 20):
        for x in range(6, 18):
            _set_pixel(surf, x, y, COLORS["body_red"])

    # 手臂下垂
    for y in range(12, 20):
        for x in (4, 5):
            _set_pixel(surf, x, y, COLORS["gold"])
        for x in (18, 19):
            _set_pixel(surf, x, y, COLORS["gold"])
    for y in range(12, 14):
        for x in (4, 5):
            _set_pixel(surf, x, y, COLORS["body_red"])
        for x in (18, 19):
            _set_pixel(surf, x, y, COLORS["body_red"])

    # 腿
    for y in range(20, 27):
        for x in range(8, 11):
            _set_pixel(surf, x, y, COLORS["body_red"])
        for x in range(13, 16):
            _set_pixel(surf, x, y, COLORS["body_red"])
    for y in range(24, 27):
        for x in range(8, 11):
            _set_pixel(surf, x, y, COLORS["gold"])
        for x in range(13, 16):
            _set_pixel(surf, x, y, COLORS["gold"])

    for x in range(7, 12):
        _set_pixel(surf, x, 27, COLORS["gold"])
    for x in range(12, 17):
        _set_pixel(surf, x, 27, COLORS["gold"])

    surf.set_colorkey(COLORS["bg_key"])
    return surf



def _add_blue_shadow(surf):
    """给精灵表面添加 1 像素蓝色右下投影阴影"""
    w, h = surf.get_size()
    # 在下方建一个带阴影的新表面
    shadowed = pygame.Surface((w + 2, h + 2), pygame.SRCALPHA)
    shadowed.fill((0, 0, 0, 0))
    # 在偏移 (1,1) 处绘制蓝色阴影（将非透明像素复制为蓝色阴影）
    blue = (50, 100, 220, 100)
    for dx in (0, 1):
        for dy in (0, 1):
            for x in range(w):
                for y in range(h):
                    r, g, b, a = surf.get_at((x, y))
                    if a > 0 and r + g + b > 0:  # 非透明且非黑色
                        if x + dx < w + 2 and y + dy < h + 2:
                            shadowed.set_at((x + 1 + dx, y + 1 + dy), blue)
    # 在 (0,0) 绘制原图
    shadowed.blit(surf, (0, 0))
    return shadowed


def draw_ironman_anger(frame=0):
    """
    生气动画 - 红色怒视双眼 + 蓝色阴影轮廓

    长按触发，眼睛变为红色，眉毛倒竖
    """
    surf = pygame.Surface((SPRITE_W * PIXEL_SCALE, SPRITE_H * PIXEL_SCALE))
    _fill_bg(surf)

    tilt_val = 1 if (frame // 6) % 2 == 0 else -1  # 微微左右晃动

    # 天线（闪烁红光）
    if (frame // 8) % 2 == 0:
        _set_pixel(surf, 12, 1, COLORS["eye_angry"])
    for x in range(11, 14):
        _set_pixel(surf, x, 2, COLORS["gold_dark"])

    # 头部（金色面罩）
    for y in range(2, 10):
        for x in range(7, 17):
            if y == 2 and x not in range(8, 16): continue
            if y == 9 and x not in range(8, 16): continue
            _set_pixel(surf, x, y, COLORS["gold"])

    # 红色怒视眼睛（红色发光）
    for x in (9, 10, 14, 15):
        _set_pixel(surf, x, 5, COLORS["eye_angry"])
    # 眉眼倒竖（生气皱眉）
    _set_pixel(surf, 8, 4, COLORS["eye_angry"])
    _set_pixel(surf, 11, 4, COLORS["eye_angry"])
    _set_pixel(surf, 16, 4, COLORS["eye_angry"])
    _set_pixel(surf, 13, 4, COLORS["eye_angry"])

    # 咬牙表情
    _set_pixel(surf, 11, 8, COLORS["mouth"])
    _set_pixel(surf, 12, 8, COLORS["mouth"])
    _set_pixel(surf, 13, 8, COLORS["mouth"])
    _set_pixel(surf, 11, 7, COLORS["mouth"])
    _set_pixel(surf, 13, 7, COLORS["mouth"])

    # 身体（红色装甲）
    for y in range(10, 20):
        for x in range(6, 18):
            _set_pixel(surf, x, y, COLORS["body_red"])
    # 身体左右两侧高光
    for y in range(12, 16):
        for x in range(7, 10):
            _set_pixel(surf, x, y, COLORS["body_red_light"])
        for x in range(14, 17):
            _set_pixel(surf, x, y, COLORS["body_red_light"])
    # 腰带
    for y in range(17, 19):
        for x in range(7, 17):
            _set_pixel(surf, x, y, COLORS["gold"])
    # 反应炉（闪烁更强）
    if (frame // 4) % 2 == 0:
        for x in range(10, 14):
            for y_p in range(12, 15):
                _set_pixel(surf, x, y_p, COLORS["reactor_light"])
    for x in range(11, 13):
        for y_p in range(13, 15):
            _set_pixel(surf, x, y_p, COLORS["reactor"])

    # 握拳手臂
    for y in range(12, 18):
        for x in (4, 5):
            _set_pixel(surf, x, y, COLORS["gold"])
        for x in (18, 19):
            _set_pixel(surf, x, y, COLORS["gold"])
    for y in range(11, 13):
        for x in (4, 5):
            _set_pixel(surf, x, y, COLORS["body_red"])
        for x in (18, 19):
            _set_pixel(surf, x, y, COLORS["body_red"])

    # 腿
    for y in range(20, 27):
        for x in range(8, 11):
            _set_pixel(surf, x, y, COLORS["body_red"])
        for x in range(13, 16):
            _set_pixel(surf, x, y, COLORS["body_red"])
    for y in range(24, 27):
        for x in range(8, 11):
            _set_pixel(surf, x, y, COLORS["gold"])
        for x in range(13, 16):
            _set_pixel(surf, x, y, COLORS["gold"])
    for x in range(7, 12):
        _set_pixel(surf, x, 27, COLORS["gold"])
    for x in range(12, 17):
        _set_pixel(surf, x, 27, COLORS["gold"])

    surf.set_colorkey(COLORS["bg_key"])
    return surf


# 动画帧生成器映射
ANIMATION_GENERATORS = {
    "idle": lambda f: _add_blue_shadow(draw_ironman_idle(f)),
    "walk": lambda f: _add_blue_shadow(draw_ironman_walk(f)),
    "sleep": lambda f: _add_blue_shadow(draw_ironman_sleep(f)),
    "happy": lambda f: _add_blue_shadow(draw_ironman_happy(f)),
    "clicked": lambda f: _add_blue_shadow(draw_ironman_happy(f)),
    "dragged": lambda f: _add_blue_shadow(draw_ironman_dragged(f)),
    "angry": lambda f: _add_blue_shadow(draw_ironman_anger(f)),
}


def get_sprite(state, frame=0):
    """
    根据状态名称和帧号获取对应的精灵表面

    state: 状态名称（idle/walk/sleep/happy/clicked/dragged）
    frame: 当前动画帧号，用于控制动画进度
    """
    return ANIMATION_GENERATORS.get(state, draw_ironman_idle)(frame)


def get_sprite_size():
    """获取精灵的物理像素尺寸 (宽, 高)"""
    return (SPRITE_W * PIXEL_SCALE, SPRITE_H * PIXEL_SCALE)
