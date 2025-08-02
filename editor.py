#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关卡编辑器核心类
"""
import pygame
import sys
import os
import re
from typing import List, Tuple, Optional
from block import Block
from level_parser import LevelParser, Level, Scope

class LevelEditor:
    """关卡编辑器类"""
    
    def __init__(self):
        """初始化编辑器"""
        pygame.init()
        self.width = 1200
        self.height = 800
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("关卡编辑器")
        
        # 字体
        font_path = os.path.join("fonts", "Alibaba-PuHuiTi-Regular.ttf")
        self.font = pygame.font.Font(font_path, 24)
        self.title_font = pygame.font.Font(font_path, 36)
        
        # 颜色
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GRAY = (128, 128, 128)
        self.LIGHT_GRAY = (200, 200, 200)
        self.RED = (255, 0, 0)
        self.BLUE = (0, 0, 255)
        
        # 编辑器状态
        self.grid_rows = 14  # 初始行数
        self.grid_cols = 14  # 初始列数
        self.cell_size = 40  # 默认单元格大小
        self.blocks = []  # 当前关卡的方块
        self.anchor = None  # 锚点坐标
        self.current_level_id = None  # 当前编辑的关卡ID
        
        # 工具栏
        self.tools = [
            {"name": "black_block", "display_name": "黑色方块", "type": 1},
            {"name": "blue_block", "display_name": "蓝色方块", "type": 2},
            {"name": "pyramid_block", "display_name": "金字塔方块", "type": 3},
            {"name": "empty_block", "display_name": "空方块", "type": 0},
            {"name": "anchor", "display_name": "设置锚点"},
            {"name": "constraints", "display_name": "设置限制"},
            {"name": "add_row", "display_name": "增加行"},
            {"name": "remove_row", "display_name": "减少行"},
            {"name": "add_col", "display_name": "增加列"},
            {"name": "remove_col", "display_name": "减少列"}
        ]
        
        # 限制条件列表
        self.constraint_options = [
            {"name": "glue", "display_name": "胶水", "abbreviation": "G"},
            {"name": "mirror", "display_name": "镜像", "abbreviation": "M"},
            {"name": "pyramid", "display_name": "金字塔", "abbreviation": "P"},
            {"name": "sail", "display_name": "航行", "abbreviation": "S"}
        ]
        self.selected_constraints = []  # 当前选择的限制条件
        
        # 初始化selected_tool
        self.selected_tool = self.tools[0]  # 当前选择的工具，默认选择第一个工具
        
        # 限制条件
        self.constraints = []
        
        # 提示信息
        self.hints = []
        
        # 待创建的大关ID
        self.pending_scope_id = None
        
        # 左侧工具栏固定宽度
        self.left_toolbar_width = 200
        
        # 计算网格偏移量，使网格居中显示
        self._update_grid_offsets()
        
        # 关卡解析器
        self.level_parser = LevelParser()
        self.level_parser.parse_levels_file("levels.txt")
        
        # 输入框相关
        self.input_active = False
        self.input_text = ""
        
    def _handle_constraint_selection(self):
        """处理限制条件选择"""
        # 显示限制选择界面
        print("请选择限制条件（输入对应数字，多个条件用逗号分隔）：")
        for i, constraint in enumerate(self.constraint_options):
            print(f"{i+1}. {constraint['display_name']} ({constraint['abbreviation']})")
        
        # 解析用户输入
        if self.input_text:
            try:
                selected_indices = [int(x.strip()) - 1 for x in self.input_text.split(",")]
                self.selected_constraints = [self.constraint_options[i]["name"] for i in selected_indices if 0 <= i < len(self.constraint_options)]
                print(f"已选择的限制条件: {', '.join(self.selected_constraints)}")
            except ValueError:
                print("输入格式错误，请输入数字，多个条件用逗号分隔")
        else:
            self.selected_constraints = []
            print("已清空限制条件")
        self.input_mode = ""  # "import", "save_as_scope", "save_as_level"
        
    def _update_grid_offsets(self):
        """更新网格偏移量，实现自适应单元格尺寸和居中布局"""
        # 右侧操作栏宽度
        right_toolbar_width = 200
        
        # 计算可用宽度和高度
        available_width = self.width - self.left_toolbar_width - right_toolbar_width
        available_height = self.height
        
        # 计算自适应单元格尺寸
        # 限制最大单元格尺寸为60
        max_cell_size = 60
        # 计算基于列数的单元格尺寸
        cell_size_by_cols = available_width // self.grid_cols
        # 计算基于行数的单元格尺寸
        cell_size_by_rows = available_height // self.grid_rows
        # 限制最小单元格尺寸为20
        min_cell_size = 20
        
        # 确定最终单元格尺寸，取列和行计算结果的最小值
        self.cell_size = max(min(cell_size_by_cols, cell_size_by_rows, max_cell_size), min_cell_size)
        
        # 计算网格总宽度和高度
        grid_width = self.grid_cols * self.cell_size
        grid_height = self.grid_rows * self.cell_size
        
        # 计算网格偏移量，使网格居中
        self.grid_offset_x = self.left_toolbar_width + (available_width - grid_width) // 2
        self.grid_offset_y = (self.height - grid_height) // 2
        
    def run(self):
        """运行编辑器主循环"""
        clock = pygame.time.Clock()
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # 如果输入框激活，禁止点击其他地方
                    if self.input_active:
                        # 只允许点击输入框区域
                        input_rect = pygame.Rect(self.width // 2 - 150, self.height // 2 - 25, 300, 50)
                        if not input_rect.collidepoint(event.pos):
                            continue
                    self._handle_mouse_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if self.input_active:
                        if event.key == pygame.K_RETURN:
                            self._handle_input_confirm()
                        elif event.key == pygame.K_BACKSPACE:
                            self.input_text = self.input_text[:-1]
                        elif event.key == pygame.K_ESCAPE:
                            # ESC键退出输入框状态
                            self.input_active = False
                            self.input_text = ""
                        else:
                            self.input_text += event.unicode
                
            self._draw_ui()
            pygame.display.flip()
            clock.tick(60)
            
        pygame.quit()
        sys.exit()
        
    def _handle_mouse_click(self, pos: Tuple[int, int]):
        """处理鼠标点击事件"""
        # 检查是否点击了左侧工具栏
        if pos[0] < self.left_toolbar_width:
            self._handle_toolbar_click(pos)
        # 检查是否点击了网格区域
        elif (self.grid_offset_x <= pos[0] < self.grid_offset_x + self.grid_cols * self.cell_size and
              self.grid_offset_y <= pos[1] < self.grid_offset_y + self.grid_rows * self.cell_size):
            self._handle_grid_click(pos)
        # 检查是否点击了右侧操作栏
        elif pos[0] >= self.width - 200:  # 200是操作栏宽度
            self._handle_action_bar_click(pos)
            
    def _handle_toolbar_click(self, pos: Tuple[int, int]):
        """处理工具栏点击事件"""
        # 简单实现，后续可以优化
        tool_height = 60
        tool_width = self.left_toolbar_width - 20
        for i, tool in enumerate(self.tools):
            tool_rect = pygame.Rect(10, 100 + i * tool_height, tool_width, tool_height)
            if tool_rect.collidepoint(pos):
                self.selected_tool = tool
                # 处理增加/减少行和列的点击事件
                if tool["name"] == "add_row":
                    self._add_row()
                elif tool["name"] == "remove_row":
                    self._remove_row()
                elif tool["name"] == "add_col":
                    self._add_col()
                elif tool["name"] == "remove_col":
                    self._remove_col()
                elif tool["name"] == "constraints":
                    # 切换限制选择模式
                    self.input_active = True
                    self.input_mode = "select_constraints"
                    self.input_text = ""
                break
                
    def _add_row(self):
        """增加行"""
        self.grid_rows += 1
        # 重新计算网格偏移量，保持居中
        self._update_grid_offsets()
        
    def _remove_row(self):
        """减少行"""
        if self.grid_rows > 1:
            self.grid_rows -= 1
            # 重新计算网格偏移量，保持居中
            self._update_grid_offsets()
            
    def _add_col(self):
        """增加列"""
        self.grid_cols += 1
        # 重新计算网格偏移量，保持居中
        self._update_grid_offsets()
        
    def _remove_col(self):
        """减少列"""
        if self.grid_cols > 1:
            self.grid_cols -= 1
            # 重新计算网格偏移量，保持居中
            self._update_grid_offsets()
                
    def _handle_action_bar_click(self, pos: Tuple[int, int]):
        """处理操作栏点击事件"""
        action_bar_width = 150
        button_width = action_bar_width - 40
        
        # 导入按钮
        import_button_rect = pygame.Rect(self.width - action_bar_width + 20, 100, button_width, 40)
        if import_button_rect.collidepoint(pos):
            self._import_level()
            
        # 保存按钮
        save_button_rect = pygame.Rect(self.width - action_bar_width + 20, 160, button_width, 40)
        if save_button_rect.collidepoint(pos):
            self._save_level()
            
        # 另存为按钮
        save_as_button_rect = pygame.Rect(self.width - action_bar_width + 20, 220, button_width, 40)
        if save_as_button_rect.collidepoint(pos):
            self._save_as_level()

        # 删除按钮
        delete_button_rect = pygame.Rect(self.width - action_bar_width + 20, 280, button_width, 40)
        if delete_button_rect.collidepoint(pos):
            # 直接触发删除输入流程
            self.input_active = True
            self.input_mode = "delete_level"
            self.input_text = ""
                
    def _handle_grid_click(self, pos: Tuple[int, int]):
        """处理网格点击事件"""
        # 计算点击的网格坐标
        grid_x = (pos[0] - self.grid_offset_x) // self.cell_size
        grid_y = (pos[1] - self.grid_offset_y) // self.cell_size
        
        # 确保坐标在有效范围内
        if 0 <= grid_x < self.grid_cols and 0 <= grid_y < self.grid_rows:
            if self.selected_tool:
                if self.selected_tool["name"] == "anchor":
                    # 设置锚点
                    self.anchor = (grid_x, grid_y)
                elif self.selected_tool["name"] == "pyramid_block":
                    # 放置或修改金字塔方块，需要确定点击的是哪个面
                    # 查找该位置是否已有金字塔方块
                    existing_block = None
                    for i, b in enumerate(self.blocks):
                        if b.pos == (grid_x, grid_y) and b.type == 3:
                            existing_block = b
                            block_index = i
                            break
                    
                    # 计算点击位置相对于方块中心的偏移
                    cell_x = pos[0] - self.grid_offset_x - grid_x * self.cell_size
                    cell_y = pos[1] - self.grid_offset_y - grid_y * self.cell_size
                    
                    # 确定点击的是哪个面
                    center = self.cell_size // 2
                    face_index = None
                    if cell_y < center and abs(cell_x - center) < abs(cell_y - center):
                        # 点击上方
                        face_index = 0
                    elif cell_y > center and abs(cell_x - center) < abs(cell_y - center):
                        # 点击下方
                        face_index = 1
                    elif cell_x < center and abs(cell_x - center) > abs(cell_y - center):
                        # 点击左方
                        face_index = 2
                    elif cell_x > center and abs(cell_x - center) > abs(cell_y - center):
                        # 点击右方
                        face_index = 3
                    
                    if face_index is not None:
                        if existing_block:
                            # 如果已有金字塔方块，修改对应面的状态（0→1→2→0）
                            current_state = existing_block.detailed_information[face_index]
                            new_state = (current_state + 1) % 3
                            existing_block.detailed_information[face_index] = new_state
                        else:
                            self.blocks = [b for b in self.blocks if b.pos != (grid_x, grid_y)]
                            # 如果没有金字塔方块，创建新的（默认状态为[0,0,0,0]）
                            detailed_info = [0, 0, 0, 0]
                            detailed_info[face_index] = 1  # 点击的面设为1
                            block = Block(
                                block_type=self.selected_tool["type"],
                                pos=(grid_x, grid_y),
                                detailed_information=detailed_info
                            )
                            self.blocks.append(block)
                else:
                    # 放置其他方块
                    # 先移除该位置的现有方块
                    self.blocks = [b for b in self.blocks if b.pos != (grid_x, grid_y)]
                    
                    # 添加新方块
                    if "type" in self.selected_tool and self.selected_tool["type"] != 0:  # 不是空方块
                        block = Block(
                            block_type=self.selected_tool["type"],
                            pos=(grid_x, grid_y)
                        )
                        self.blocks.append(block)
                        
    def _draw_ui(self):
        """绘制用户界面"""
        self.screen.fill(self.WHITE)
        
        # 绘制左侧工具栏
        self._draw_toolbar()
        
        # 绘制右侧操作栏
        self._draw_action_bar()
        
        # 绘制网格
        self._draw_grid()
        
        # 绘制方块
        self._draw_blocks()
        
        # 绘制锚点
        if self.anchor:
            self._draw_anchor()
            
        # 绘制输入框
        if self.input_active:
            self._draw_input_box()
            
        # 在右下角显示当前选择的限制条件缩写
        self._draw_selected_constraints()
        
    def _draw_selected_constraints(self):
        """在右下角绘制当前选择的限制条件缩写"""
        if self.selected_constraints:
            # 获取选中限制条件的缩写
            abbreviations = []
            for constraint_name in self.selected_constraints:
                for constraint in self.constraint_options:
                    if constraint["name"] == constraint_name:
                        abbreviations.append(constraint["abbreviation"])
                        break
            
            # 绘制缩写文本
            constraints_text = ", ".join(abbreviations)
            text_surface = self.font.render(f"限制: {constraints_text}", True, self.BLACK)
            # 在右下角绘制
            text_rect = text_surface.get_rect()
            text_rect.bottomright = (self.width - 10, self.height - 10)
            self.screen.blit(text_surface, text_rect)
        
    def _draw_toolbar(self):
        """绘制工具栏"""
        # 绘制工具栏背景
        toolbar_rect = pygame.Rect(0, 0, self.left_toolbar_width, self.height)
        pygame.draw.rect(self.screen, (60, 60, 60), toolbar_rect)
        
        # 绘制工具栏标题
        title = self.title_font.render("工具栏", True, (255, 255, 255))
        self.screen.blit(title, (20, 20))
        
        # 绘制工具按钮
        tool_height = 60
        tool_width = self.left_toolbar_width - 20
        for i, tool in enumerate(self.tools):
            # 按钮位置和大小
            button_rect = pygame.Rect(10, 100 + i * tool_height, tool_width, tool_height)
            
            # 绘制按钮背景
            color = (100, 100, 100) if self.selected_tool != tool else (150, 150, 150)
            pygame.draw.rect(self.screen, color, button_rect)
            pygame.draw.rect(self.screen, (200, 200, 200), button_rect, 2)
            
            # 绘制按钮文字
            text = self.font.render(tool["display_name"], True, (255, 255, 255))
            text_rect = text.get_rect(center=button_rect.center)
            self.screen.blit(text, text_rect)
            
    def _draw_action_bar(self):
        """绘制右侧操作栏"""
        # 操作栏背景
        action_bar_width = 150
        action_bar_rect = pygame.Rect(self.width - action_bar_width, 0, action_bar_width, self.height)
        pygame.draw.rect(self.screen, self.LIGHT_GRAY, action_bar_rect)
        pygame.draw.line(self.screen, self.BLACK, (self.width - action_bar_width, 0), 
                         (self.width - action_bar_width, self.height), 2)
        
        # 操作栏标题
        title = self.title_font.render("操作栏", True, self.BLACK)
        self.screen.blit(title, (self.width - action_bar_width + 10, 20))
        
        # 绘制按钮（简化实现）
        button_width = action_bar_width - 40
        button_rect = pygame.Rect(self.width - action_bar_width + 20, 100, button_width, 40)
        pygame.draw.rect(self.screen, self.GRAY, button_rect)
        pygame.draw.rect(self.screen, self.BLACK, button_rect, 2)
        import_text = self.font.render("导入", True, self.BLACK)
        import_rect = import_text.get_rect(center=button_rect.center)
        self.screen.blit(import_text, import_rect)
        
        button_rect = pygame.Rect(self.width - action_bar_width + 20, 160, button_width, 40)
        pygame.draw.rect(self.screen, self.GRAY, button_rect)
        pygame.draw.rect(self.screen, self.BLACK, button_rect, 2)
        save_text = self.font.render("保存", True, self.BLACK)
        save_rect = save_text.get_rect(center=button_rect.center)
        self.screen.blit(save_text, save_rect)
        
        button_rect = pygame.Rect(self.width - action_bar_width + 20, 220, button_width, 40)
        pygame.draw.rect(self.screen, self.GRAY, button_rect)
        pygame.draw.rect(self.screen, self.BLACK, button_rect, 2)
        save_as_text = self.font.render("另存为", True, self.BLACK)
        save_as_rect = save_as_text.get_rect(center=button_rect.center)
        self.screen.blit(save_as_text, save_as_rect)

        # 删除按钮
        delete_button_rect = pygame.Rect(self.width - action_bar_width + 20, 280, button_width, 40)
        pygame.draw.rect(self.screen, (200, 50, 50), delete_button_rect)
        pygame.draw.rect(self.screen, self.BLACK, delete_button_rect, 2)
        delete_text = self.font.render("删除", True, self.BLACK)
        delete_rect = delete_text.get_rect(center=delete_button_rect.center)
        self.screen.blit(delete_text, delete_rect)
        
    def _draw_grid(self):
        """绘制网格"""
        for x in range(self.grid_cols + 1):
            start_pos = (self.grid_offset_x + x * self.cell_size, self.grid_offset_y)
            end_pos = (self.grid_offset_x + x * self.cell_size, self.grid_offset_y + self.grid_rows * self.cell_size)
            pygame.draw.line(self.screen, self.BLACK, start_pos, end_pos, 1)
            
        for y in range(self.grid_rows + 1):
            start_pos = (self.grid_offset_x, self.grid_offset_y + y * self.cell_size)
            end_pos = (self.grid_offset_x + self.grid_cols * self.cell_size, self.grid_offset_y + y * self.cell_size)
            pygame.draw.line(self.screen, self.BLACK, start_pos, end_pos, 1)
            
    def _draw_blocks(self):
        """绘制方块"""
        for block in self.blocks:
            # 计算屏幕坐标
            screen_x = self.grid_offset_x + block.pos[0] * self.cell_size
            screen_y = self.grid_offset_y + block.pos[1] * self.cell_size
            
            # 绘制方块
            block.draw(self.screen, (self.grid_offset_x, self.grid_offset_y), self.cell_size)
            
    def _draw_anchor(self):
        """绘制锚点"""
        # 计算屏幕坐标
        screen_x = self.grid_offset_x + self.anchor[0] * self.cell_size
        screen_y = self.grid_offset_y + self.anchor[1] * self.cell_size
        
        # 绘制红色十字
        center_x = screen_x + self.cell_size // 2
        center_y = screen_y + self.cell_size // 2
        line_length = self.cell_size // 3
        
        pygame.draw.line(self.screen, self.RED, 
                         (center_x - line_length, center_y), 
                         (center_x + line_length, center_y), 3)
        pygame.draw.line(self.screen, self.RED, 
                         (center_x, center_y - line_length), 
                         (center_x, center_y + line_length), 3)
        
    def _draw_input_box(self):
        """绘制输入框"""
        if self.input_mode == "select_constraints":
            self._draw_constraint_selection()
            return
            
        # 输入框背景
        input_rect = pygame.Rect(self.width // 2 - 150, self.height // 2 - 25, 300, 50)
        pygame.draw.rect(self.screen, self.WHITE, input_rect)
        pygame.draw.rect(self.screen, self.BLACK, input_rect, 2)
        
        # 输入框标题
        title_text = self.font.render(f"请输入{self.input_mode}:", True, self.BLACK)
        self.screen.blit(title_text, (self.width // 2 - 150, self.height // 2 - 50))
        
        # 输入文本
        text_surface = self.font.render(self.input_text, True, self.BLACK)
        self.screen.blit(text_surface, (input_rect.x + 10, input_rect.y + 15))
        
        # 光标
        if pygame.time.get_ticks() % 1000 < 500:  # 闪烁效果
            cursor_x = input_rect.x + 10 + text_surface.get_width()
            pygame.draw.line(self.screen, self.BLACK, (cursor_x, input_rect.y + 10), 
                             (cursor_x, input_rect.y + 40), 2)
                             
    def _draw_constraint_selection(self):
        """绘制限制条件选择界面"""
        # 绘制半透明背景
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # 半透明黑色
        self.screen.blit(overlay, (0, 0))
        
        # 绘制选择框
        box_width, box_height = 400, 300
        box_x, box_y = (self.width - box_width) // 2, (self.height - box_height) // 2
        pygame.draw.rect(self.screen, self.WHITE, (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, self.BLACK, (box_x, box_y, box_width, box_height), 2)
        
        # 标题
        title_text = self.font.render("请选择限制条件：", True, self.BLACK)
        self.screen.blit(title_text, (box_x + 20, box_y + 20))
        
        # 说明文字
        instruction_text = self.font.render("输入数字，多个条件用逗号分隔 (例如: 1,3,4)", True, self.BLACK)
        self.screen.blit(instruction_text, (box_x + 20, box_y + 50))
        
        # 限制条件列表
        for i, constraint in enumerate(self.constraint_options):
            y_pos = box_y + 80 + i * 30
            text = self.font.render(f"{i+1}. {constraint['display_name']} ({constraint['abbreviation']})", True, self.BLACK)
            self.screen.blit(text, (box_x + 40, y_pos))
        
        # 当前已选择的限制条件
        selected_text = self.font.render(f"当前选择: {', '.join(self.selected_constraints)}", True, self.BLACK)
        self.screen.blit(selected_text, (box_x + 20, box_y + box_height - 60))
        
        # 输入框
        input_rect = pygame.Rect(box_x + 20, box_y + box_height - 30, box_width - 40, 25)
        pygame.draw.rect(self.screen, self.WHITE, input_rect)
        pygame.draw.rect(self.screen, self.BLACK, input_rect, 2)
        
        # 输入文本
        text_surface = self.font.render(self.input_text, True, self.BLACK)
        self.screen.blit(text_surface, (input_rect.x + 5, input_rect.y + 5))
        
        # 光标
        if pygame.time.get_ticks() % 1000 < 500:  # 闪烁效果
            cursor_x = input_rect.x + 5 + text_surface.get_width()
            pygame.draw.line(self.screen, self.BLACK, (cursor_x, input_rect.y + 5), 
                             (cursor_x, input_rect.y + 20), 2)
    
    def _import_level(self):
        """导入关卡"""
        self.input_active = True
        self.input_text = ""
        self.input_mode = "import"
        
    def _save_level(self):
        """保存关卡"""
        if not self.current_level_id:
            # 提示暂无导入关卡
            print("暂无导入关卡")
            return
        
        if not self.blocks and not self.anchor:
            # 提示当前内容为空
            print("当前内容为空")
            return
            
        # 保存关卡
        self._save_level_to_file(self.current_level_id)
        
    def _save_as_level(self):
        """另存为关卡"""
        self.input_active = True
        self.input_text = ""
        self.input_mode = "save_as_level"
        
    def _handle_input_confirm(self):
        """处理输入确认"""
        if self.input_mode == "import":
            self._load_level(self.input_text)
        elif self.input_mode == "save_as_level":
            # 传入强制另存为参数
            self._save_level_to_file(self.input_text, save_as=True)
            self.current_level_id = self.input_text  # 更新当前关卡ID
            print(f"已另存为新关卡 {self.input_text}")
        elif self.input_mode == "create_scope":
            # 创建新大关
            try:
                scope_id = int(self.input_text)
                # 保存scope_id以便在create_scope_name模式中使用
                self.pending_scope_id = scope_id
                self.input_mode = "create_scope_name"
                self.input_text = ""
                print("请输入新大关名称：")
                return
            except ValueError:
                print("请输入有效的大关数字")
        elif self.input_mode == "create_scope_name":
            # 输入新大关名称
            scope_name = self.input_text
            # 使用之前保存的scope_id
            if hasattr(self, 'pending_scope_id'):
                if self._create_new_scope(self.pending_scope_id, scope_name):
                    self.input_mode = "save_as_level"
                    self.input_text = ""
                    # 清除pending_scope_id
                    delattr(self, 'pending_scope_id')
                    return
                else:
                    print("大关创建失败")
                    self.input_mode = "save_as_level"
                    # 清除pending_scope_id
                    delattr(self, 'pending_scope_id')
                    return
            else:
                print("未找到待创建的大关ID，请重新输入关卡ID")
                self.input_mode = "save_as_level"
                return
        elif self.input_mode == "select_constraints":
            # 处理限制选择
            self._handle_constraint_selection()
        elif self.input_mode == "delete_level":
            # 增强输入提示
            if re.fullmatch(r'^\d+\s*-\s*\d+$', self.input_text.replace(' ','')):
                clean_id = self.input_text.replace(' ','')
                # 检查关卡是否存在
                # 直接检查文件内容是否存在该关卡
                with open("levels.txt", "r", encoding='utf-8') as f:
                     content = f.read()
                with open("levels.txt", "w", encoding='utf-8') as f:
                    self._delete(content, clean_id, f)
                    print(f"成功删除关卡 {clean_id}")
            else:
                print("无效的关卡格式，请输入如1-2的格式")
            self.level_parser.parse_levels_file("levels.txt")
            
        self.input_active = False
        self.input_text = ""
        
    def _load_level(self, level_id: str):
        """加载关卡"""
        level = self.level_parser.get_level_by_id(level_id)
        if level:
            self.current_level_id = level_id
            self.blocks = level.blocks
            # 计算锚点位置（假设锚点是(0,0)的方块）
            self.anchor = (level.margin_left, level.margin_top)
            for block in self.blocks:
                block.pos = (block.pos[0] + level.margin_left, block.pos[1] + level.margin_top)
            self.grid_cols = level.max_rect[0] + level.margin_left + level.margin_right
            self.grid_rows = level.max_rect[1] + level.margin_top + level.margin_bottom
            # 加载限制条件
            self.selected_constraints = level.constraints.copy()
            # 重新计算网格偏移量和单元格尺寸
            self._update_grid_offsets()
        else:
            print(f"未找到关卡 {level_id}")
            
    def _save_level_to_file(self, level_id: str, save_as: bool = False):
        """实现三种保存模式：
        1. 精确替换（3-2）
        2. 大关内追加（3-*）
        3. 新建大关（[名称]-*）
        """
        # 输入验证
        pattern_a = re.compile(r'^\d+-\d+$')  # 3-2
        pattern_b = re.compile(r'^\d+-\*$')   # 3-*
        pattern_c = re.compile(r'^\[(.+)\]-\*$')  # [新大关]-*

        # 读取文件内容
        try:
            with open("levels.txt", "r+", encoding="utf-8") as f:
                content = f.read()

                # 模式匹配
                if pattern_a.match(level_id):
                    self._handle_case_a(content, level_id, save_as, f)
                    self.level_parser.parse_levels_file("levels.txt")
                elif pattern_b.match(level_id):
                    if not save_as:
                        raise ValueError("B模式需要另存为")
                    self._handle_case_b(content, level_id, f)
                    self.level_parser.parse_levels_file("levels.txt")
                elif match_c := pattern_c.match(level_id):
                    if not save_as:
                        raise ValueError("C模式需要另存为")
                    scope_name = match_c.group(1)
                    self._handle_case_c(content, scope_name, f)
                    self.level_parser.parse_levels_file("levels.txt")
                else:
                    raise ValueError(f"无效关卡ID格式: {level_id}")

        except FileNotFoundError:
            print("关卡文件不存在")

    
    def _delete(self, content, level_id, file_obj):
        """处理精确替换模式"""
        scope_id, level_num = map(int, level_id.split('-'))
        
        # 查找大关范围
        scope_pattern = re.compile(rf'scope={scope_id}\b.*?(total_levels=\d+)', re.DOTALL)
        scope_match = scope_pattern.search(content)
        
        if not scope_match:
            raise ValueError(f"大关 {scope_id} 不存在")

        # 查找具体关卡
        level_pattern = re.compile(
            rf'(begin level {level_num}\n.*?end level {level_num})',
            re.DOTALL
        )
        level_match = level_pattern.search(content, scope_match.start())

        part1 = content[:scope_match.end()+1]  # 包含scope=行及分号
        scope_body_start = scope_match.end()+1
            
            # 查找下一个大关起始位置
        next_scope_match = re.search(r'^\s*scope=\d+', content[scope_match.end():], re.MULTILINE)
        if next_scope_match:
            part2_end = scope_match.end() + next_scope_match.start()
            part2 = content[scope_body_start:part2_end]
            part3 = content[part2_end:]
        else:
            part2 = content[scope_body_start:]
            part3 = []

        # 在part2中递增所有关卡号
        part2_updated = re.sub(
            r'(begin|end) level (\d+)',
            lambda m: f'{m.group(1)} level {0 if int(m.group(2)) == level_num else int(m.group(2))}',
            part2
        )
        part2_updated = re.sub(
            r'(begin|end) level (\d+)',
            lambda m: f'{m.group(1)} level {int(m.group(2)) - 1 if int(m.group(2)) > level_num else int(m.group(2))}',
            part2_updated
        )

        # 删除指定关卡内容
        part2_updated = re.sub(
            r'begin level 0\b.*?end level 0\b',
            '',
            part2_updated,
            flags=re.DOTALL
        )

        part2_updated = '\n' + part2_updated

        # 更新当前大关总关卡数
        part1_updated = re.sub(
            rf'(^\s*scope={scope_id}\b.*?total_levels=)(\d+)',
            lambda m: m.group(1) + str(int(m.group(2)) - 1),
            part1,
            flags=re.DOTALL | re.MULTILINE,
            count=1
        )

        # 从part1提取当前大关总关卡数
        # 精准匹配total_levels值
        scope_pattern = re.compile(rf'scope={scope_id}\b.*?total_levels=(\d+)', re.DOTALL)
        scope_match = scope_pattern.search(part1)
        original_total = int(scope_match.group(1)) if scope_match else 0

        # 添加调试日志
        print(f'当前大关{scope_id}总关卡数:', original_total)

        if original_total == 0:
            # 删除当前大关定义行
            part1_updated = re.sub(rf'scope={scope_id}\b[^;]+;\n', '', part1_updated)
            # 调整后续大关编号
            part3 = re.sub(
                r'scope=(\d+)',
                lambda m: f'scope={int(m.group(1))-1}',
                part3
            )

        # 拼接最终内容
        updated_content = part1_updated + part2_updated + part3

        # 写回文件
        file_obj.seek(0)
        file_obj.write(updated_content)
        file_obj.truncate()


    def _handle_case_a(self, content, level_id, save_as, file_obj):
        """处理精确替换模式"""
        scope_id, level_num = map(int, level_id.split('-'))
        
        # 查找大关范围
        scope_pattern = re.compile(rf'scope={scope_id}\b.*?(total_levels=\d+)', re.DOTALL)
        scope_match = scope_pattern.search(content)
        
        if not scope_match:
            raise ValueError(f"大关 {scope_id} 不存在")

        # 查找具体关卡
        level_pattern = re.compile(
            rf'(begin level {level_num}\n.*?end level {level_num})',
            re.DOTALL
        )
        level_match = level_pattern.search(content, scope_match.start())

        if save_as:
            # 递增所有后续关卡编号
            # 分三部分处理
            # 精确切割大关范围
            part1 = content[:scope_match.end()+1]  # 包含scope=行及分号
            scope_body_start = scope_match.end()+1
             
             # 查找下一个大关起始位置
            next_scope_match = re.search(r'^\s*scope=\d+', content[scope_match.end():], re.MULTILINE)
            if next_scope_match:
                part2_end = scope_match.end() + next_scope_match.start()
                part2 = content[scope_body_start:part2_end]
                part3 = content[part2_end:]
            else:
                part2 = content[scope_body_start:]

            # 在part2中递增所有关卡号
            part2_updated = re.sub(
                r'(begin|end) level (\d+)',
                lambda m: f'{m.group(1)} level {int(m.group(2)) + 1 if int(m.group(2)) >= level_num else int(m.group(2))}',
                part2
            )
            temp_context = self._generate_level_content(f"{scope_id}-{level_num}")

            part2_updated = re.sub(
                r'(begin) level (\d+)',
                lambda m: '\n' + temp_context
                + '\n'
                + f'{m.group(1)} level {int(m.group(2))}' if int(m.group(2)) == level_num + 1 else f'{m.group(1)} level {int(m.group(2))}',
                part2_updated
            )

            part2_updated = '\n' + part2_updated

            # 更新当前大关总关卡数
            part1_updated = re.sub(
                rf'(^\s*scope={scope_id}\b.*?total_levels=)(\d+)',
                lambda m: m.group(1) + str(int(m.group(2)) + 1),
                part1,
                flags=re.DOTALL | re.MULTILINE,
                count=1
            )

            # 拼接最终内容
            
            updated_content = part1_updated + part2_updated + part3 if next_scope_match else part1_updated + part2_updated
            

        else:
            # 直接替换
            updated_content = content[:level_match.start()] + \
                self._generate_level_content(level_id) + \
                content[level_match.end():]

        # 写回文件
        file_obj.seek(0)
        file_obj.write(updated_content)
        file_obj.truncate()

    def _handle_case_b(self, content, level_id, file_obj):
        """处理大关内追加"""
        scope_id = int(level_id.split('-')[0])
        
        # 查找大关并追加
        num_of_levels_pattern = re.compile(rf'scope={scope_id}\b.*?total_levels=(\d+)',
            re.DOTALL)
        last_level = 0
        if match := num_of_levels_pattern.search(content):
            last_level = int(match.group(1))
        
        new_level_content = self._generate_level_content(f"{scope_id}-{last_level+1}")
        
        # 在大关末尾插入
        insert_pos = content.find(f"scope={scope_id+1};") if \
            f"scope={scope_id+1};" in content else len(content)
        
        updated_content = content[:insert_pos] + \
            new_level_content + \
            content[insert_pos:]
        
        # 更新总关卡数
        updated_content = re.sub(
            rf'(^\s*scope={scope_id}\b.*?total_levels=)(\d+)',
            lambda m: m.group(1) + str(int(m.group(2)) + 1),
            updated_content,
            flags=re.DOTALL | re.MULTILINE,
            count=1
        )

        file_obj.seek(0)
        file_obj.write(updated_content)
        file_obj.truncate()

    def _handle_case_c(self, content, scope_name, file_obj):
        """处理新建大关"""
        # 计算新大关ID
        existing_scopes = re.findall(r'scope=(\d+)', content)
        new_scope_id = len(existing_scopes) + 1
        
        # 生成大关头
        new_scope_header = f"scope={new_scope_id}; "
        new_scope_header += f"name={scope_name}; "
        new_scope_header += "total_levels=1;\n"
        
        # 生成首关卡
        new_level_content = self._generate_level_content(f"{new_scope_id}-1")
        
        # 在文件末尾追加
        updated_content = content + "\n\n" + new_scope_header + new_level_content
        
        file_obj.seek(0)
        file_obj.write(updated_content)
        file_obj.truncate()

    def _create_new_scope(self, scope_id: int, scope_name: str = "新大关"):
        """创建新的大关"""
        # 检查大关是否已存在
        if scope_id in [scope.scope_id for scope in self.level_parser.scopes]:
            print(f"大关 {scope_id} 已存在")
            return False
        
        # 读取原文件内容
        try:
            with open("levels.txt", "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            print("未找到levels.txt文件")
            return False
        
        # 找到插入位置（按顺序插入）
        insert_pos = len(content)  # 默认在末尾插入
        for i, scope in enumerate(self.level_parser.scopes):
            if scope.scope_id > scope_id:
                insert_pos = content.find(f"scope={scope.scope_id};")
                break
        
        # 生成新的大关内容
        new_scope_content = f"\nscope={scope_id}; scope_name='{scope_name}'; total_levels=1;\n\n"
        
        # 插入新大关
        content = content[:insert_pos] + new_scope_content + content[insert_pos:]
        
        # 写回文件
        with open("levels.txt", "w", encoding="utf-8") as f:
            f.write(content)
        
        # 重新解析文件
        self.level_parser.parse_levels_file("levels.txt")
        
        print(f"大关 {scope_id} 已创建")
        return True
        
    def _generate_level_content(self, level_id: str) -> str:
        """生成关卡内容字符串"""
        content = f"begin level {level_id.split('-')[1]}\n"
        
        # 添加限制条件
        for constraint in self.selected_constraints:
            content += f"limit {constraint}\n"
        
        # 添加提示信息
        if self.hints:
            content += 'instruction "'
            content += "\n".join(self.hints)
            content += '"\n'
        
        # 计算margin值
        if self.blocks:
            # 计算方块组的边界
            max_x = max(block.pos[0] for block in self.blocks)
            max_y = max(block.pos[1] for block in self.blocks)
            
            # 计算margin值
            if self.anchor:
                left = self.anchor[0]
                top = self.anchor[1]
            else:
                left = min(block.pos[0] for block in self.blocks)
                top = min(block.pos[1] for block in self.blocks)
                self.anchor = (left, top)
            right = self.grid_cols - max_x - 1
            bottom = self.grid_rows - max_y - 1
        else:
            # 如果没有方块或锚点未设置，默认margin值
            max_x = max(block.pos[0] for block in self.blocks)
            max_y = max(block.pos[1] for block in self.blocks)
            left, top, right, bottom = 4, 4, 4, 4
        
        # 添加边界参数
        content += f"margin{{top={top},bottom={bottom},left={left},right={right}}}\n"
        
        # 添加方块
        for block in self.blocks:
            if block.type == 3:  # 金字塔方块
                content += f"block{{type={block.type},pos=({block.pos[0]- self.anchor[0]},{block.pos[1]- self.anchor[1]}),detailed_information=[{','.join(map(str, block.detailed_information))}]}}\n"
            else:
                content += f"block{{type={block.type},pos=({block.pos[0]- self.anchor[0]},{block.pos[1]- self.anchor[1]})}}\n"
        
        # 注意：这里没有处理锚点，因为锚点在游戏逻辑中可能有特殊含义
        # 如果需要保存锚点信息，可以添加额外的标记
        
        content += f"end level {level_id.split('-')[1]}\n"
        return content