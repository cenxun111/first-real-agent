#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
计算器应用 - 图形界面版本
使用 tkinter 创建桌面计算器
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
from calculator import Calculator, CalculatorError


class CalculatorApp:
    """计算器图形界面应用"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Python 计算器")
        self.root.geometry("400x550")
        self.root.resizable(False, False)
        
        # 设置背景色和字体
        self.root.configure(bg='#f0f0f0')
        self.calc = Calculator()
        
        # 创建界面组件
        self._create_display()
        self._create_buttons()
    
    def _create_display(self):
        """创建显示屏"""
        # 标题标签
        title_frame = tk.Frame(self.root, bg='#333', height=40)
        title_frame.pack(fill=tk.X)
        
        title_label = tk.Label(
            title_frame, 
            text="🔢 Python Calculator",
            font=('Arial', 16, 'bold'),
            fg='white',
            bg='#333'
        )
        title_label.pack(pady=5)
        
        # 显示屏
        self.display = tk.Entry(
            self.root,
            font=('Courier New', 24),
            justify=tk.RIGHT,
            bd=10,
            relief=tk.FLAT,
            bg='#fff',
            fg='#333'
        )
        self.display.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.display.insert(0, "0")
    
    def _create_buttons(self):
        """创建按钮网格"""
        # 定义按钮布局（7 列 x 6 行）
        buttons = [
            ['C', '(', ')', '/'],
            ['7', '8', '9', '*'],
            ['4', '5', '6', '-'],
            ['1', '2', '3', '+'],
            ['0', '.', '=', '√']
        ]
        
        # 创建按钮网格
        for row_idx, row in enumerate(buttons):
            frame = tk.Frame(self.root, bg='#f0f0f0')
            frame.pack(fill=tk.X)
            
            for col_idx, text in enumerate(row):
                button = tk.Button(
                    frame,
                    text=text,
                    font=('Arial', 18),
                    width=3,
                    height=2,
                    bg='#fff',
                    fg='#333',
                    activebackground='#e0e0e0',
                    activeforeground='#555',
                    command=lambda t=text: self._on_button_click(t)
                )
                button.grid(row=row_idx, column=col_idx, padx=2, pady=2)
        
        # 添加功能按钮行
        func_frame = tk.Frame(self.root, bg='#f0f0f0')
        func_frame.pack(fill=tk.X, pady=(5, 0))
        
        func_buttons = [
            ('sin', 'sin'),
            ('cos', 'cos'),
            ('tan', 'tan'),
            ('log', 'log'),
            ('ln', 'ln'),
            ('!', '!')
        ]
        
        for col_idx, (func_name, text) in enumerate(func_buttons):
            button = tk.Button(
                func_frame,
                text=text,
                font=('Arial', 14),
                width=3,
                height=2,
                bg='#e8f4f8',
                fg='#0066cc',
                activebackground='#d0e8f0',
                activeforeground='#0055aa',
                command=lambda f=func_name: self._on_function_click(f)
            )
            button.grid(row=0, column=col_idx, padx=2, pady=2)
    
    def _clear_display(self):
        """清空显示屏"""
        self.display.delete(0, tk.END)
        self.display.insert(0, "0")
    
    def _append_to_display(self, value):
        """在显示屏上添加字符"""
        current = self.display.get()
        if current == '0' or current == 'Error':
            self.display.delete(0, tk.END)
        self.display.insert(tk.END, str(value))
    
    def _on_button_click(self, value):
        """按钮点击事件处理"""
        try:
            if value in ['C']:
                self._clear_display()
            elif value == '=':
                result = self._calculate()
                self.display.delete(0, tk.END)
                self.display.insert(0, str(result))
            else:
                self._append_to_display(value)
        except Exception as e:
            messagebox.showerror("错误", f"操作失败：{str(e)}")
    
    def _on_function_click(self, func_name):
        """函数按钮点击事件处理"""
        try:
            if func_name == 'sin':
                angle = simpledialog.askfloat("输入角度", "请输入角度值（度）:", minvalue=-360, maxvalue=360)
                if angle is not None:
                    result = self.calc.sin(angle)
                    self.display.delete(0, tk.END)
                    self.display.insert(0, f"{result:.4f}")
            
            elif func_name == 'cos':
                angle = simpledialog.askfloat("输入角度", "请输入角度值（度）:", minvalue=-360, maxvalue=360)
                if angle is not None:
                    result = self.calc.cos(angle)
                    self.display.delete(0, tk.END)
                    self.display.insert(0, f"{result:.4f}")
            
            elif func_name == 'tan':
                angle = simpledialog.askfloat("输入角度", "请输入角度值（度）:", minvalue=-360, maxvalue=360)
                if angle is not None:
                    result = self.calc.tan(angle)
                    self.display.delete(0, tk.END)
                    self.display.insert(0, f"{result:.4f}")
            
            elif func_name == 'log':
                number = simpledialog.askfloat("输入数字", "请输入要计算对数的数字:", minvalue=0.01)
                if number is not None:
                    base = 10
                    result = self.calc.log(number, base)
                    self.display.delete(0, tk.END)
                    self.display.insert(0, f"{result:.4f}")
            
            elif func_name == 'ln':
                number = simpledialog.askfloat("输入数字", "请输入要计算自然对数的数字:", minvalue=0.01)
                if number is not None:
                    result = self.calc.ln(number)
                    self.display.delete(0, tk.END)
                    self.display.insert(0, f"{result:.4f}")
            
            elif func_name == '!':
                n = simpledialog.askinteger("输入整数", "请输入要计算阶乘的整数:", minvalue=0)
                if n is not None:
                    result = self.calc.factorial(n)
                    self.display.delete(0, tk.END)
                    self.display.insert(0, str(result))
            
        except CalculatorError as e:
            messagebox.showerror("错误", f"{str(e)}")
        except Exception as e:
            messagebox.showerror("错误", f"操作失败：{str(e)}")
    
    def _calculate(self):
        """执行计算"""
        expression = self.display.get()
        
        try:
            # 处理括号匹配
            if expression.count('(') != expression.count(')'):
                raise CalculatorError("括号不匹配！")
            
            # 基本运算
            result = eval(expression, {"__builtins__": {}}, {
                '+': self.calc.add,
                '-': self.calc.subtract,
                '*': self.calc.multiply,
                '/': self.calc.divide,
                '**': self.calc.power,
                'sqrt': self.calc.square_root,
                'abs': self.calc.abs_value,
                'round': self.calc.round_to,
                'min': lambda *args: self.calc.min_max(*args)['min'],
                'max': lambda *args: self.calc.min_max(*args)['max'],
                'sum': lambda *args: self.calc.sum_all(*args),
                'avg': lambda *args: self.calc.avg(*args)
            })
            
            return result
            
        except CalculatorError as e:
            raise e
        except ZeroDivisionError:
            raise CalculatorError("错误：不能除以零！")
        except Exception as e:
            raise CalculatorError(f"计算错误：{str(e)}")


def main():
    """启动计算器应用"""
    root = tk.Tk()
    app = CalculatorApp(root)
    
    # 设置窗口图标（可选）
    try:
        icon_path = tk.PhotoImage(file='calculator_icon.png')
        root.iconphoto(True, icon_path)
    except:
        pass
    
    root.mainloop()


if __name__ == "__main__":
    main()
