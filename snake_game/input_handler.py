#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
贪吃蛇游戏 - 输入处理模块
负责键盘事件处理和游戏控制逻辑
"""

import pygame
from constants import (
    KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT, 
    INITIAL_DIRECTION, GAME_STATE
)


class InputHandler:
    """输入处理器类，管理所有用户输入"""
    
    def __init__(self):
        self.keys = {}  # 按键状态字典
    
    def handle_events(self) -> bool:
        """处理事件队列，返回是否应该继续游戏循环"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            elif event.type == pygame.KEYDOWN:
                self.keys[event.key] = True
                
                # 处理方向键（防止快速按键导致自杀）
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    GAME_STATE['direction'] = KEY_UP
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    GAME_STATE['direction'] = KEY_DOWN
                elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    GAME_STATE['direction'] = KEY_LEFT
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    GAME_STATE['direction'] = KEY_RIGHT
                
                # 空格键暂停/继续
                if event.key == pygame.K_SPACE and not GAME_STATE['game_over']:
                    GAME_STATE['paused'] = not GAME_STATE['paused']
                
                # ESC 退出游戏
                elif event.key == pygame.K_ESCAPE:
                    return False
            
            elif event.type == pygame.KEYUP:
                self.keys[event.key] = False
        
        return True
    
    def get_pressed_keys(self) -> list:
        """获取当前按下的所有按键"""
        return [key for key, pressed in self.keys.items() if pressed]


# ==================== 测试代码 ====================
if __name__ == "__main__":
    import sys
    
    handler = InputHandler()
    
    print("=" * 60)
    print("贪吃蛇游戏 - 输入处理模块测试")
    print("=" * 60)
    print("\n支持的按键:")
    print("↑ / W - 向上移动")
    print("↓ / S - 向下移动")
    print("← / A - 向左移动")
    print("→ / D - 向右移动")
    print("空格 - 暂停/继续游戏")
    print("ESC - 退出游戏")
