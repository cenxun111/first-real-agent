#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
贪吃蛇游戏 - 食物模块
负责食物的生成、显示和碰撞检测
"""

import pygame
import random
from constants import GRID_SIZE, GRID_COUNT_X, GRID_COUNT_Y, COLORS


class Food:
    """食物类，表示游戏中的食物"""
    
    def __init__(self):
        self.x = 0
        self.y = 0
        self.spawn()
    
    def spawn(self) -> None:
        """在随机位置生成食物（避开蛇身）"""
        # 简单随机生成，实际游戏中会检查是否撞到蛇
        self.x = random.randint(1, GRID_COUNT_X - 2)
        self.y = random.randint(1, GRID_COUNT_Y - 2)
    
    def get_rect(self) -> tuple:
        """获取食物的矩形区域"""
        return (self.x * GRID_SIZE + GRID_SIZE // 2, 
                self.y * GRID_SIZE + GRID_SIZE // 2,
                GRID_SIZE - 4,
                GRID_SIZE - 4)
    
    def draw(self, screen: pygame.Surface) -> None:
        """绘制食物（使用圆形和渐变色）"""
        center_x, center_y = self.get_rect()[:2]
        
        # 绘制红色圆形食物
        radius = (GRID_SIZE - 4) // 2
        
        # 创建渐变效果
        for angle in range(360):
            rad = angle * 3.14159 / 180
            x_offset = int(radius * 0.7 * (rad % (2 * 3.14159)))
            y_offset = int(radius * 0.7)
            
            # 绘制小圆点形成渐变效果
            color_val = int(255 * (1 - angle / 360))
            color = (color_val, 100, 100)
            
            pygame.draw.circle(screen, color, 
                             (center_x + x_offset % GRID_SIZE, center_y + y_offset),
                             2)
    
    def check_collision(self, head: tuple) -> bool:
        """检查是否与蛇头碰撞"""
        return (head[0] == self.x and head[1] == self.y)


# ==================== 测试代码 ====================
if __name__ == "__main__":
    food = Food()
    
    print("=" * 60)
    print("贪吃蛇游戏 - 食物模块测试")
    print("=" * 60)
    print(f"\n初始位置: ({food.x}, {food.y})")
    print(f"矩形区域：{food.get_rect()}")
    
    # 生成几个不同位置的食物
    for i in range(3):
        food.spawn()
        print(f"第{i+1}次生成位置: ({food.x}, {food.y})")
