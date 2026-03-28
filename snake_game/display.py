#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
贪吃蛇游戏 - 显示模块
负责游戏界面的绘制和渲染
"""

import pygame
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, GRID_SIZE, 
    COLORS, FONT_SIZE, SCORE_FONT_SIZE, TITLE_FONT_SIZE
)


class DisplayManager:
    """显示管理器，处理所有界面元素"""
    
    def __init__(self):
        self.screen = None
        self.clock = None
        self.font = None
        self.score_font = None
        self.title_font = None
    
    def initialize(self) -> bool:
        """初始化 pygame 和显示设置"""
        try:
            # 初始化 pygame
            pygame.init()
            
            # 创建全屏窗口（带标题栏）
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.display.set_caption("贪吃蛇游戏 - Snake Game")
            
            # 设置图标（可选）
            icon_size = 32
            icon_surface = pygame.Surface((icon_size, icon_size))
            icon_surface.fill(COLORS['snake_head'])
            pygame.display.set_icon(icon_surface)
            
            # 创建字体
            self.font = pygame.font.Font(None, FONT_SIZE)
            self.score_font = pygame.font.Font(None, SCORE_FONT_SIZE)
            self.title_font = pygame.font.Font(None, TITLE_FONT_SIZE)
            
            # 设置全屏模式（可选，取消注释以启用）
            # pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            
            return True
            
        except Exception as e:
            print(f"初始化失败：{e}")
            return False
    
    def close(self) -> None:
        """关闭游戏"""
        if self.clock:
            self.clock.tick(60)
        pygame.quit()
    
    def draw_background(self) -> None:
        """绘制背景网格"""
        # 填充背景色
        self.screen.fill(COLORS['background'])
        
        # 绘制网格线（可选，增加视觉效果）
        for x in range(0, SCREEN_WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, (30, 30, 35), 
                           (x, 0), (x, SCREEN_HEIGHT), 1)
        
        for y in range(0, SCREEN_HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, (30, 30, 35), 
                           (0, y), (SCREEN_WIDTH, y), 1)
    
    def draw_text(self, text: str, position: tuple, font=None, color=COLORS['text'], 
                  center=False, size_multiplier=1.0) -> None:
        """绘制文本"""
        if font is None:
            font = self.font
        
        # 计算字体大小
        actual_size = int(FONT_SIZE * size_multiplier)
        
        # 创建表面并渲染文字
        surface = font.render(text, True, color)
        
        if center:
            rect = surface.get_rect(center=position)
        else:
            rect = surface.get_rect(topleft=position)
        
        self.screen.blit(surface, rect)
    
    def draw_score(self, score: int, high_score: int = None) -> None:
        """绘制分数"""
        # 当前分数
        score_text = f"得分：{score}"
        self.draw_text(score_text, (10, 10), self.score_font, COLORS['score'])
        
        # 最高分（如果有）
        if high_score is not None:
            high_score_text = f"最高分：{high_score}"
            self.draw_text(high_score_text, (10, SCREEN_HEIGHT - 30), 
                          self.score_font, COLORS['high_score'])
    
    def draw_game_over(self) -> None:
        """绘制游戏结束界面"""
        # 半透明遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(128)
        self.screen.blit(overlay, (0, 0))
        
        # 游戏结束文字
        game_over_text = "游戏结束！"
        self.draw_text(game_over_text, 
                      (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3),
                      self.title_font, COLORS['text'], center=True)
        
        # 最终分数
        final_score_text = f"最终得分：{pygame.display.get_surface().get_rect().center}"
        self.draw_text("最终得分：0", 
                      (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3 + 60),
                      self.font, COLORS['score'], center=True)
        
        # 重新开始提示
        restart_text = "按空格键重新开始"
        self.draw_text(restart_text, 
                      (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3 + 120),
                      self.font, (255, 255, 200), center=True)
    
    def draw_pause(self) -> None:
        """绘制暂停界面"""
        # 半透明遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(128)
        self.screen.blit(overlay, (0, 0))
        
        # 暂停文字
        pause_text = "游戏已暂停"
        self.draw_text(pause_text, 
                      (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2),
                      self.title_font, COLORS['text'], center=True)
        
        # 继续提示
        continue_text = "按空格键继续"
        self.draw_text(continue_text, 
                      (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60),
                      self.font, (255, 255, 200), center=True)


# ==================== 测试代码 ====================
if __name__ == "__main__":
    import sys
    
    display = DisplayManager()
    
    if display.initialize():
        print("=" * 60)
        print("贪吃蛇游戏 - 显示模块测试")
        print("=" * 60)
        
        # 绘制背景
        display.draw_background()
        
        # 绘制分数
        display.draw_score(100, high_score=500)
        
        # 显示窗口
        pygame.display.flip()
        
        print("\n显示模块初始化成功！")
        print("窗口已打开，按 ESC 退出...")
        
        # 等待用户关闭窗口
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
        
        display.close()
    else:
        print("显示模块初始化失败！")
