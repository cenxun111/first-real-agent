#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
计算器应用 - 核心计算模块
提供基本的数学运算功能
"""

import math


class CalculatorError(Exception):
    """自定义计算器异常类"""
    pass


class Calculator:
    """计算器主类，提供所有计算功能"""
    
    def __init__(self):
        self.history = []
    
    # ==================== 基本运算 ====================
    
    def add(self, a, b):
        """加法运算"""
        return float(a) + float(b)
    
    def subtract(self, a, b):
        """减法运算"""
        return float(a) - float(b)
    
    def multiply(self, a, b):
        """乘法运算"""
        return float(a) * float(b)
    
    def divide(self, a, b):
        """除法运算，处理除零错误"""
        if b == 0:
            raise CalculatorError("错误：不能除以零！")
        return float(a) / float(b)
    
    # ==================== 高级运算 ====================
    
    def power(self, base, exponent):
        """幂运算 (base^exponent)"""
        return math.pow(float(base), float(exponent))
    
    def square_root(self, number):
        """平方根运算"""
        if number < 0:
            raise CalculatorError("错误：负数不能开平方！")
        return math.sqrt(number)
    
    def square(self, number):
        """平方运算"""
        return float(number) ** 2
    
    def factorial(self, n):
        """阶乘运算 (n!)"""
        if not isinstance(n, int):
            raise CalculatorError("错误：阶乘只接受整数！")
        if n < 0:
            raise CalculatorError("错误：负数没有阶乘！")
        if n == 0 or n == 1:
            return 1
        result = 1
        for i in range(2, n + 1):
            result *= i
        return result
    
    def percentage(self, number, percent):
        """百分比运算 (number * percent%)"""
        return float(number) * float(percent) / 100.0
    
    # ==================== 三角函数 ====================
    
    def sin(self, angle_degrees):
        """正弦函数（角度制）"""
        radians = math.radians(angle_degrees)
        return math.sin(radians)
    
    def cos(self, angle_degrees):
        """余弦函数（角度制）"""
        radians = math.radians(angle_degrees)
        return math.cos(radians)
    
    def tan(self, angle_degrees):
        """正切函数（角度制）"""
        radians = math.radians(angle_degrees)
        return math.tan(radians)
    
    def asin(self, value):
        """反正弦函数（返回弧度，可转换为角度）"""
        if abs(value) > 1:
            raise CalculatorError("错误：asin 的参数必须在 [-1, 1] 范围内！")
        return math.asin(value)
    
    def acos(self, value):
        """反余弦函数（返回弧度，可转换为角度）"""
        if abs(value) > 1:
            raise CalculatorError("错误：acos 的参数必须在 [-1, 1] 范围内！")
        return math.acos(value)
    
    def atan(self, value):
        """反正切函数（返回弧度，可转换为角度）"""
        return math.atan(value)
    
    # ==================== 对数运算 ====================
    
    def log(self, number, base=10):
        """对数运算 (log_base(number))"""
        if number <= 0:
            raise CalculatorError("错误：对数的参数必须大于零！")
        return math.log(number, base)
    
    def ln(self, number):
        """自然对数 (ln)"""
        if number <= 0:
            raise CalculatorError("错误：对数的参数必须大于零！")
        return math.log(number)
    
    # ==================== 其他函数 ====================
    
    def abs_value(self, number):
        """绝对值"""
        return abs(float(number))
    
    def round_to(self, number, decimals=2):
        """四舍五入到指定位数"""
        return round(float(number), decimals)
    
    def min_max(self, *numbers):
        """求最小值和最大值"""
        if not numbers:
            raise CalculatorError("错误：至少需要一个数字！")
        return {
            'min': min(numbers),
            'max': max(numbers)
        }
    
    def sum_all(self, *numbers):
        """求和"""
        return sum(float(n) for n in numbers)
    
    def avg(self, *numbers):
        """平均值"""
        if not numbers:
            raise CalculatorError("错误：至少需要一个数字！")
        return self.sum_all(*numbers) / len(numbers)


def main():
    """命令行测试接口"""
    calc = Calculator()
    
    print("=" * 50)
    print("计算器应用 - 欢迎使用！")
    print("=" * 50)
    
    # 示例：基本运算
    print(f"\n1 + 2 = {calc.add(1, 2)}")
    print(f"5 - 3 = {calc.subtract(5, 3)}")
    print(f"4 × 6 = {calc.multiply(4, 6)}")
    print(f"10 ÷ 2 = {calc.divide(10, 2)}")
    
    # 示例：高级运算
    print(f"\n8² = {calc.square(8)}")
    print(f"√9 = {calc.square_root(9)}")
    print(f"5! = {calc.factorial(5)}")
    print(f"20% of 100 = {calc.percentage(100, 20)}")
    
    # 示例：三角函数
    print(f"\nsin(30°) = {calc.sin(30):.4f}")
    print(f"cos(60°) = {calc.cos(60):.4f}")
    
    print("\n使用 GUI 界面可以获得更好的交互体验！")


if __name__ == "__main__":
    main()
