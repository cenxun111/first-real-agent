#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
贪吃蛇游戏 - 蛇类模块
负责蛇的移动、生长和碰撞检测逻辑
"""

import pygame
from constants import GRID_SIZE, INITIAL_DIRECTION


class SnakeSegment:
    """蛇身段类，表示蛇的一个身体部分"""
    
    def __init__(self, x: int, y: int):
        self.x = x  # X 坐标（网格单位）
        self.y = y  # Y 坐标（网格单位）
        self.alive = True  # 是否存活
    
    def get_rect(self) -> pygame.Rect:
        """获取该段对应的矩形区域"""
        return pygame.Rect(
            self.x * GRID_SIZE,
            self.y * GRID_SIZE,
            GRID_SIZE - 2,  # 留 1px 间隙让蛇身看起来有间隔
            GRID_SIZE - 2
        )


class Snake:
    """蛇主类，管理蛇的整体状态和行为"""
    
    def __init__(self):
        self.reset()
    
    def reset(self) -> None:
        """重置蛇到初始状态"""
        # 创建初始蛇身（3 段）
        segments = []
        for i in range(STARTING_LENGTH):
            x = GRID_COUNT_X // 2 - i  # 从中间向左排列
            y = GRID_COUNT_Y // 2
            segment = SnakeSegment(x, y)
            segment.alive = True
            segments.append(segment)
        
        self.segments = segments
        self.direction = INITIAL_DIRECTION.copy()
        self.next_direction = INITIAL_DIRECTION.copy()  # 缓冲下一次转向，防止快速按键导致自杀
        
    def get_head(self) -> SnakeSegment:
        """获取蛇头"""
        return self.segments[0]
    
    def move(self) -> None:
        """移动蛇身"""
        head = self.get_head()
        
        # 计算新头部位置
        new_x = head.x + self.direction[0]
        new_y = head.y + self.direction[1]
        
        # 创建新头部
        new_head = SnakeSegment(new_x, new_y)
        new_head.alive = True
        
        # 将新头部插入最前面
        self.segments.insert(0, new_head)
        
        # 如果蛇没有吃到食物，移除尾部（保持长度不变）
        if not self._just_ate_food:
            tail = self.segments.pop()
            tail.alive = False
    
    def set_direction(self, dx: int, dy: int) -> None:
        """设置移动方向（带防反向保护）"""
        # 防止直接掉头（如正在向右不能立即向左）
        if (dx == -self.direction[0] and dy == -self.direction[1]):
            return
        
        self.next_direction = (dx, dy)
    
    def _apply_direction(self) -> None:
        """应用缓冲的方向"""
        if self.next_direction != self.direction:
            self.direction = self.next_direction
    
    def grow(self) -> None:
        """生长（吃到食物时调用）"""
        self._just_ate_food = True
    
    def _reset_growth_flag(self) -> None:
        """重置生长标志"""
        self._just_ate_food = False
    
    def check_collision_with_self(self) -> bool:
        """检查是否撞到自己的身体"""
        head = self.get_head()
        
        for segment in self.segments[1:]:  # 跳过头部自己
            if not segment.alive:
                continue
            if (head.x == segment.x and head.y == segment.y):
                return True
        
        return False
    
    def check_collision_with_wall(self) -> bool:
        """检查是否撞到墙壁"""
        head = self.get_head()
        
        # 检查边界（留 1px 边距）
        if head.x < 0 or head.x >= GRID_COUNT_X - 1:
            return True
        if head.y < 0 or head.y >= GRID_COUNT_Y - 1:
            return True
        
        return False
    
    def draw(self, screen: pygame.Surface) -> None:
        """绘制蛇"""
        for segment in self.segments:
            rect = segment.get_rect()
            
            # 头部用不同颜色
            if not segment.alive:
                continue
            
            color = COLORS['snake_head'] if len(self.segments) == 1 else COLORS['snake_body']
            
            pygame.draw.rect(screen, color, rect)
        
        # 绘制蛇头眼睛（增加视觉效果）
        head = self.get_head()
        eye_size = GRID_SIZE // 6
        
        # 根据方向计算眼睛位置
        if self.direction[0] == 1:  # 向右
            eye_x1, eye_y1 = head.x * GRID_SIZE + GRID_SIZE - 4, head.y * GRID_SIZE + 4
            eye_x2, eye_y2 = head.x * GRID_SIZE + GRID_SIZE - 4, head.y * GRID_SIZE + GRID_SIZE - 8
        elif self.direction[0] == -1:  # 向左
            eye_x1, eye_y1 = head.x * GRID_SIZE + 4, head.y * GRID_SIZE + 4
            eye_x2, eye_y2 = head.x * GRID_SIZE + 4, head.y * GRID_SIZE + GRID_SIZE - 8
        elif self.direction[1] == -1:  # 向上
            eye_x1, eye_y1 = head.x * GRID_SIZE + 4, head.y * GRID_SIZE + 4
            eye_x2, eye_y2 = head.x * GRID_SIZE + GRID_SIZE - 8, head.y * GRID_SIZE + 4
        else:  # 向下
            eye_x1, eye_y1 = head.x * GRID_SIZE + 4, head.y * GRID_SIZE + GRID_SIZE - 8
            eye_x2, eye_y2 = head.x * GRID_SIZE + GRID_SIZE - 8, head.y * GRID_SIZE + GRID_SIZE - 8
        
        # 绘制眼睛（白色）
        pygame.draw.circle(screen, COLORS['text'], 
                          (eye_x1 // 2 + int(GRID_SIZE/2), eye_y1 // 2 + int(GRID_SIZE/2)), 
                          eye_size)
        pygame.draw.circle(screen, COLORS['text'], 
                          (eye_x2 // 2 + int(GRID_SIZE/2), eye_y2 // 2 + int(GRID_SIZE/2)), 
                          eye_size)


# ==================== 测试代码 ====================
if __name__ == "__main__":
    import sys
    from constants import GRID_COUNT_X, GRID_COUNT_Y
    
    # 创建蛇实例并显示信息
    snake = Snake()
    
    print("=" * 60)
    print("贪吃蛇游戏 - 蛇类测试")
    print("=" * 60)
    print(f"\n初始长度：{len(snake.segments)} 段")
    print(f"初始方向：{snake.direction}")
    print(f"网格尺寸：{GRID_COUNT_X} x {GRID_COUNT_Y}")
    
    # 测试移动
    for i in range(5):
        snake.move()
        head = snake.get_head()
        print(f"移动后位置: ({head.x}, {head.y})")
    
    print("\n蛇类模块测试完成！")
