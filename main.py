#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
方块解谜游戏主程序
"""

from game import Game

def main():
    """主函数"""
    print("启动方块解谜游戏...")
    
    try:
        # 创建并运行游戏
        game = Game()
        game.run()
    except Exception as e:
        print(f"游戏运行出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("游戏结束")

if __name__ == "__main__":
    main() 