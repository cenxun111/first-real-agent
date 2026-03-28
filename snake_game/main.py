#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
贪吃蛇游戏 - 主程序入口
整合所有模块，提供完整的游戏体验
"""

import pygame
from constants import *
from snake import Snake
from food import Food
from input_handler import InputHandler
from display import DisplayManager
from game_logic import GameLogic


class SnakeGame:
    """贪吃蛇游戏主类"""
    
    def __init__(self):
        self.display = None
        self.snake = None
        self.input_handler = None
        self.game_logic = None
        
        # 初始化所有组件
        if not self._initialize():
            print("游戏初始化失败！")
            return
    
    def _initialize(self) -> bool:
        """初始化游戏"""
        try:
            # 创建显示管理器并初始化
            self.display = DisplayManager()
            
            # 检查 pygame 是否成功初始化
            if not self.display.initialize():
                return False
            
            # 创建蛇、输入处理器和游戏逻辑
            self.snake = Snake()
            self.input_handler = InputHandler()
            self.game_logic = GameLogic()
            
            # 生成初始食物
            head = self.snake.get_head()
            self.game_logic.spawn_food(head)
            
            return True
            
        except Exception as e:
            print(f"初始化错误：{e}")
            return False
    
    def run(self) -> None:
        """运行游戏主循环"""
        running = True
        
        while running:
            # 处理输入事件
            if not self.input_handler.handle_events():
                running = False
                continue
            
            # 如果暂停，跳过本帧更新
            if GAME_STATE['paused']:
                pygame.time.wait(100)  # 暂停时降低刷新率
                continue
            
            # 处理游戏逻辑（每帧）
            self._update_game_logic()
            
            # 绘制所有元素
            self._draw_game()
            
            # 控制游戏速度
            clock_speed = int(60 / self.speed) if self.speed > 0 else 1
            pygame.time.wait(clock_speed)
        
        # 清理资源
        self.display.close()
    
    def _update_game_logic(self) -> None:
        """更新游戏逻辑"""
        try:
            # 应用缓冲的方向（防止快速按键导致自杀）
            if not GAME_STATE['paused']:
                self.snake._apply_direction()
            
            # 移动蛇
            self.snake.move()
            
            # 检查碰撞
            head = self.snake.get_head()
            
            # 撞墙检测
            if self.game_logic.check_wall_collision(head):
                self._game_over("撞墙了！")
                return
            
            # 撞自己检测
            if self.game_logic.check_self_collision(self.snake):
                self._game_over("撞到自己的身体了！")
                return
            
            # 吃食物检测
            if self.game_logic.check_food_collision(head):
                self.snake.grow()
                self.game_logic.handle_food_collision()
            
        except Exception as e:
            print(f"游戏更新错误：{e}")
    
    def _draw_game(self) -> None:
        """绘制游戏画面"""
        try:
            # 绘制背景网格
            self.display.draw_background()
            
            # 绘制食物
            if self.game_logic.food is not None:
                food_rect = (self.game_logic.food.x * GRID_SIZE, 
                            self.game_logic.food.y * GRID_SIZE)
                pygame.draw.rect(self.display.screen, COLORS['food'], 
                               food_rect, GRID_SIZE - 4)
            
            # 绘制蛇
            if self.snake is not None:
                self.snake.draw(self.display.screen)
            
            # 绘制分数
            self.display.draw_score(
                self.game_logic.score, 
                high_score=self.game_logic.high_score
            )
            
            # 更新显示
            pygame.display.flip()
            
        except Exception as e:
            print(f"绘制错误：{e}")
    
    def _game_over(self, reason: str) -> None:
        """游戏结束处理"""
        GAME_STATE['game_over'] = True
        self.game_logic.game_over_reason = reason
        
        # 更新最高分
        self.game_logic.update_high_score()
        
        # 绘制游戏结束界面
        self.display.draw_game_over()


def main():
    """主函数"""
    print("=" * 60)
    print("贪吃蛇游戏 - 欢迎！")
    print("=" * 60)
    print("\n游戏规则:")
    print("- 使用方向键或 WASD 控制蛇的移动")
    print("- 吃到红色食物得分，每 50 分速度提升一次")
    print("- 避免撞墙或撞到自己的身体")
    print("- 空格键暂停/继续游戏")
    print("- ESC 退出游戏\n")
    
    # 创建并运行游戏
    game = SnakeGame()
    
    if game:
        try:
            game.run()
        except KeyboardInterrupt:
            print("\n用户中断，正在退出...")
        finally:
            pygame.quit()


if __name__ == "__main__":
    main()
