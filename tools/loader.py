# tools/loader.py
import os
import importlib
import inspect
from tools.base import BaseTool

class ToolLoader:
    def __init__(self, tools_dir="tools"):
        self.tools_dir = tools_dir
        self.tools = []
        self.handlers = {}
        self.load_all()

    def load_all(self):
        # 1. 遍历 tools 文件夹
        for filename in os.listdir(self.tools_dir):
            if filename.endswith(".py") and filename not in ("base.py", "loader.py"):
                module_name = f"tools.{filename[:-3]}"
                try:
                    # 2. 动态导入模块
                    module = importlib.import_module(module_name)
                    
                    found_tools = 0
                    # 3. 扫描模块中所有继承自 BaseTool 的类
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and issubclass(obj, BaseTool) and obj is not BaseTool:
                            instance = obj() # 实例化工具
                            self.tools.append(instance.to_schema())
                            self.handlers[instance.name] = instance.execute
                            print(f"[Tools] 📦 已自动加载(Class)工具: {instance.name}")
                            found_tools += 1

                    # 4. 兼容加载老格式 TOOLS / TOOL_HANDLERS
                    if hasattr(module, "TOOLS") and hasattr(module, "TOOL_HANDLERS"):
                        legacy_tools = getattr(module, "TOOLS")
                        legacy_handlers = getattr(module, "TOOL_HANDLERS")
                        
                        if isinstance(legacy_tools, list) and isinstance(legacy_handlers, dict):
                            self.tools.extend(legacy_tools)
                            self.handlers.update(legacy_handlers)
                            for t_name in legacy_handlers.keys():
                                print(f"[Tools] 📦 已自动加载(Legacy)工具: {t_name}")
                                found_tools += 1
                                
                    if found_tools == 0:
                        # 既没有找到新架构类，也没有找到兼容旧变量
                        pass
                except Exception as e:
                    print(f"[Tools] ❌ 加载工具模块 {module_name} 失败: {e}")

    def get_tools_schemas(self):
        return self.tools

    def get_handlers(self):
        return self.handlers

# 实例化全局加载器
tool_manager = ToolLoader()