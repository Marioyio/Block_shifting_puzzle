#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关卡编辑器主程序
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from editor import LevelEditor

def main():
    """主函数"""
    editor = LevelEditor()
    editor.run()

if __name__ == "__main__":
    main()