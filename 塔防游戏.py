import pygame
import sys
import random
import math
import os

# 初始化 Pygame
pygame.init()

# 游戏窗口大小
WIDTH, HEIGHT = 800, 600
CELL_SIZE = 80
COLS = WIDTH // CELL_SIZE          # 10
ROWS = 7                           # 格子行数
GRID_WIDTH = COLS * CELL_SIZE      # 800
GRID_HEIGHT = ROWS * CELL_SIZE     # 560

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
BROWN = (139, 69, 19)

# 游戏设置
FPS = 60
INIT_SCORE = 631
TARGET_SCORE = 2104
INIT_LIVES = 3
PATH_WIDTH = 2

# 路径点（格子坐标）
waypoints_grid = [
    (0, 3), (1, 3), (2, 3), (3, 2), (4, 2),
    (5, 2), (6, 3), (7, 3), (8, 3), (9, 3)
]

def grid_to_pixel(col, row):
    """格子坐标转像素中心点"""
    return (col * CELL_SIZE + CELL_SIZE // 2, row * CELL_SIZE + CELL_SIZE // 2)

def is_path_cell(col, row):
    """判断是否为路径格子"""
    return (col, row) in waypoints_grid

# 敌人初始生命值池
ENemy_HP_POOL = [20, 25, 30, 33, 29, 46, 20]

# 塔属性
TOWER_RANGE = 150
TOWER_COOLDOWN = 30
TOWER_DAMAGE = 10
TOWER_COST = 50

# 子弹属性
BULLET_SPEED = 5
BULLET_RADIUS = 5

# 敌人属性
ENEMY_SPEED = 1.2
ENEMY_RADIUS = 15

# ---------- 改进的字体加载函数 ----------
def init_chinese_font(size):
    """优先从Windows字体目录加载中文字体，确保中文显示"""
    # 常见中文字体文件路径（按优先顺序）
    font_paths = [
        "C:/Windows/Fonts/simhei.ttf",      # 黑体
        "C:/Windows/Fonts/msyh.ttc",        # 微软雅黑
        "C:/Windows/Fonts/simsun.ttc",      # 宋体
        "C:/Windows/Fonts/STHeiti.ttf",     # 华文黑体（Mac兼容）
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                font = pygame.font.Font(path, size)
                # 简单测试渲染一个中文字符（不会实际显示）
                font.render("中", True, WHITE)
                print(f"成功加载字体: {path}")
                return font
            except Exception as e:
                print(f"字体文件加载失败 {path}: {e}")
                continue
    # 如果文件加载失败，回退到SysFont
    try:
        font = pygame.font.SysFont('simhei', size)
        font.render("中", True, WHITE)
        print("回退到SysFont simhei")
        return font
    except:
        pass
    # 最后使用默认字体（可能无法显示中文，但至少不崩溃）
    print("警告：使用默认字体，中文可能显示为方框")
    return pygame.font.Font(None, size)

# 初始化字体
font = init_chinese_font(24)
small_font = init_chinese_font(18)
big_font = init_chinese_font(36)

# 初始化窗口
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("王者来打龙 · 塔防原型")
clock = pygame.time.Clock()

# ------------------ 游戏类定义 ------------------
class Enemy:
    def __init__(self, path, hp):
        self.path = path
        self.hp = hp
        self.max_hp = hp
        self.target_index = 1
        self.pos = list(self.path[0])
        self.speed = ENEMY_SPEED
        self.radius = ENEMY_RADIUS
        self.reached_end = False

    def update(self):
        if self.reached_end:
            return
        target = self.path[self.target_index]
        dx = target[0] - self.pos[0]
        dy = target[1] - self.pos[1]
        dist = math.hypot(dx, dy)
        if dist < self.speed:
            self.pos[0], self.pos[1] = target
            if self.target_index == len(self.path) - 1:
                self.reached_end = True
            else:
                self.target_index += 1
        else:
            self.pos[0] += (dx / dist) * self.speed
            self.pos[1] += (dy / dist) * self.speed

    def draw(self, surface):
        pygame.draw.circle(surface, RED, (int(self.pos[0]), int(self.pos[1])), self.radius)
        bar_width = 40
        bar_height = 6
        bar_x = self.pos[0] - bar_width // 2
        bar_y = self.pos[1] - self.radius - 12
        pygame.draw.rect(surface, BLACK, (bar_x, bar_y, bar_width, bar_height))
        hp_width = int(bar_width * (self.hp / self.max_hp))
        pygame.draw.rect(surface, GREEN, (bar_x, bar_y, hp_width, bar_height))
        hp_text = small_font.render(str(self.hp), True, WHITE)
        surface.blit(hp_text, (self.pos[0] - 10, self.pos[1] - self.radius - 25))

class Tower:
    def __init__(self, col, row):
        self.col = col
        self.row = row
        self.x, self.y = grid_to_pixel(col, row)
        self.range = TOWER_RANGE
        self.cooldown = 0
        self.attack_cooldown = TOWER_COOLDOWN
        self.damage = TOWER_DAMAGE

    def update(self, enemies, bullets):
        if self.cooldown > 0:
            self.cooldown -= 1
            return
        target_enemy = None
        min_dist = float('inf')
        for enemy in enemies:
            if enemy.reached_end:
                continue
            dist = math.hypot(enemy.pos[0] - self.x, enemy.pos[1] - self.y)
            if dist <= self.range and dist < min_dist:
                min_dist = dist
                target_enemy = enemy
        if target_enemy:
            bullet = Bullet((self.x, self.y), target_enemy, self.damage)
            bullets.append(bullet)
            self.cooldown = self.attack_cooldown

    def draw(self, surface):
        pygame.draw.circle(surface, BLUE, (self.x, self.y), 20)
        pygame.draw.rect(surface, DARK_GRAY, (self.x-10, self.y-10, 20, 20))

class Bullet:
    def __init__(self, start_pos, target_enemy, damage):
        self.pos = list(start_pos)
        self.target = target_enemy
        self.damage = damage
        self.speed = BULLET_SPEED
        self.radius = BULLET_RADIUS
        self.active = True

    def update(self, enemies):
        if self.target not in enemies or self.target.hp <= 0:
            return False
        dx = self.target.pos[0] - self.pos[0]
        dy = self.target.pos[1] - self.pos[1]
        dist = math.hypot(dx, dy)
        if dist < self.speed:
            self.target.hp -= self.damage
            return False
        else:
            self.pos[0] += (dx / dist) * self.speed
            self.pos[1] += (dy / dist) * self.speed
            return True

    def draw(self, surface):
        pygame.draw.circle(surface, YELLOW, (int(self.pos[0]), int(self.pos[1])), self.radius)

# ------------------ 游戏状态 ------------------
class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        self.score = INIT_SCORE
        self.lives = INIT_LIVES
        self.game_over = False
        self.win = False
        self.enemies = []
        self.bullets = []
        self.towers = []
        # 放置两个固定塔（避开路径）
        if not is_path_cell(2, 1):
            self.towers.append(Tower(2, 1))
        if not is_path_cell(7, 4):
            self.towers.append(Tower(7, 4))
        self.spawn_counter = 0
        self.spawn_interval = 90
        self.path_pixels = [grid_to_pixel(col, row) for col, row in waypoints_grid]

    def spawn_enemy(self):
        if len(self.enemies) >= 8:
            return
        hp = random.choice(ENemy_HP_POOL)
        enemy = Enemy(self.path_pixels, hp)
        self.enemies.append(enemy)

    def update(self):
        if self.game_over or self.win:
            return

        if self.score >= TARGET_SCORE:
            self.win = True

        self.spawn_counter += 1
        if self.spawn_counter >= self.spawn_interval:
            self.spawn_counter = 0
            self.spawn_enemy()

        for enemy in self.enemies[:]:
            enemy.update()
            if enemy.reached_end:
                self.enemies.remove(enemy)
                self.lives -= 1
                if self.lives <= 0:
                    self.game_over = True
                continue
            if enemy.hp <= 0:
                self.enemies.remove(enemy)
                self.score += enemy.max_hp
                continue

        for bullet in self.bullets[:]:
            if not bullet.update(self.enemies):
                self.bullets.remove(bullet)

        for tower in self.towers:
            tower.update(self.enemies, self.bullets)

    def draw(self, surface):
        surface.fill((50, 50, 50))
        for row in range(ROWS):
            for col in range(COLS):
                rect = pygame.Rect(col*CELL_SIZE, row*CELL_SIZE, CELL_SIZE, CELL_SIZE)
                color = (34, 139, 34) if not is_path_cell(col, row) else (139, 69, 19)
                pygame.draw.rect(surface, color, rect)
                pygame.draw.rect(surface, BLACK, rect, 1)

        for px, py in self.path_pixels:
            pygame.draw.circle(surface, WHITE, (px, py), 5)

        for tower in self.towers:
            tower.draw(surface)

        for enemy in self.enemies:
            enemy.draw(surface)

        for bullet in self.bullets:
            bullet.draw(surface)

        ui_y = GRID_HEIGHT
        title_surf = big_font.render("王者来打龙", True, YELLOW)
        surface.blit(title_surf, (20, 10))

        score_text = font.render(f"得分: {self.score}/{TARGET_SCORE}", True, WHITE)
        surface.blit(score_text, (WIDTH - 220, 15))

        lives_text = font.render(f"生命: {self.lives}", True, RED)
        surface.blit(lives_text, (WIDTH - 120, 50))

        prompt1 = small_font.render("你厉害你来把第二关过了", True, GREEN)
        prompt2 = small_font.render("点击格子建造新塔 (消耗50分)", True, WHITE)
        surface.blit(prompt1, (20, ui_y + 10))
        surface.blit(prompt2, (20, ui_y + 35))

        wx_text = small_font.render("打开微信小游戏", True, GRAY)
        surface.blit(wx_text, (WIDTH - 200, ui_y + 10))
        wx_text2 = small_font.render("发现更多精彩游戏>", True, GRAY)
        surface.blit(wx_text2, (WIDTH - 200, ui_y + 35))

        if self.game_over:
            over_surf = big_font.render("游戏结束 按R重新开始", True, RED)
            surface.blit(over_surf, (WIDTH//2-200, HEIGHT//2))
        if self.win:
            win_surf = big_font.render("胜利! 按R重新开始", True, GREEN)
            surface.blit(win_surf, (WIDTH//2-180, HEIGHT//2))

    def handle_click(self, pos):
        if self.game_over or self.win:
            return
        x, y = pos
        col = x // CELL_SIZE
        row = y // CELL_SIZE
        if col >= COLS or row >= ROWS:
            return
        if is_path_cell(col, row):
            return
        for t in self.towers:
            if t.col == col and t.row == row:
                return
        if self.score >= TOWER_COST:
            self.score -= TOWER_COST
            self.towers.append(Tower(col, row))

# ------------------ 主循环 ------------------
def main():
    game = Game()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game.reset()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    game.handle_click(pygame.mouse.get_pos())

        game.update()
        game.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()