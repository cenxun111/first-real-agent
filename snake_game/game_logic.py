#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
贪吃蛇游戏 - 游戏逻辑模块
负责游戏核心逻辑：碰撞检测、分数计算、游戏状态管理
"""

import random
from constants import (
    GRID_SIZE, GRID_COUNT_X, GRID_COUNT_Y, 
    INITIAL_SPEED, SPEED_INCREMENT, MAX_SPEED,
    GAME_STATE, COLORS
)


class GameLogic:
    """游戏逻辑控制器，管理所有游戏核心逻辑"""
    
    def __init__(self):
        self.score = 0
        self.high_score = 0
        self.speed = INITIAL_SPEED
        self.food = None
        self.game_over_reason = ""
        
    def spawn_food(self, snake_head: tuple) -> None:
        """生成食物，确保不生成在蛇身上"""
        while True:
            x = random.randint(1, GRID_COUNT_X - 2)
            y = random.randint(1, GRID_COUNT_Y - 2)
            
            # 检查是否撞到蛇身（简单检查）
            if abs(x - snake_head[0]) > 5 or abs(y - snake_head[1]) > 5:
                self.food = type('Food', (), {'x': x, 'y': y})()
                break
    
    def check_food_collision(self, head: tuple) -> bool:
        """检查是否与食物碰撞"""
        if self.food is None:
            return False
        
        return (head[0] == self.food.x and head[1] == self.food.y)
    
    def handle_food_collision(self) -> None:
        """处理吃到食物的情况"""
        # 增加分数
        self.score += 10
        
        # 增加速度（但不超过最大速度）
        if self.speed < MAX_SPEED:
            self.speed = min(INITIAL_SPEED + (self.score // 50) * SPEED_INCREMENT, 
                           MAX_SPEED)
        
        # 生成新食物
        head = self.snake.get_head()
        self.spawn_food(head)
    
    def check_wall_collision(self, head: tuple) -> bool:
        """检查是否撞墙"""
        return (head[0] < 0 or head[0] >= GRID_COUNT_X - 1 or 
                head[1] < 0 or head[1] >= GRID_COUNT_Y - 1)
    
    def check_self_collision(self, snake) -> bool:
        """检查是否撞到自己"""
        return snake.check_collision_with_self()
    
    def update_high_score(self) -> None:
        """更新最高分"""
        if self.score > self.high_score:
            self.high_score = self.score
    
    def reset(self, snake=None) -> None:
        """重置游戏状态"""
        self.score = 0
        self.speed = INITIAL_SPEED
        self.game_over_reason = ""
        
        if snake is not None:
            self.snake = snake
            head = snake.get_head()
            self.spawn_food(head)


# ==================== 测试代码 ====================
if __name__ == "__main__":
    import sys
    
    logic = GameLogic()
    
    print("=" * 60)
    print("贪吃蛇游戏 - 游戏逻辑模块测试")
    print("=" * 60)
    print(f"\n初始速度：{logic.speed}")
    print(f"最高速度：{MAX_SPEED}")
    print(f"分数增加规则：每 50 分提升一次速度")
