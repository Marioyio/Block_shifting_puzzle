import pygame
from block import Block
from typing import List, Tuple, Optional, Callable
from level_parser import Scope, Level
from blockset import BlockSet
from constraints import ConstraintChecker

class Button:
    """按钮类"""
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str, 
                 color: Tuple[int, int, int] = (100, 100, 100),
                 hover_color: Tuple[int, int, int] = (150, 150, 150)):
        """
        初始化按钮
        
        Args:
            x, y: 位置
            width, height: 尺寸
            text: 按钮文本
            color: 正常颜色
            hover_color: 悬停颜色
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        
    def draw(self, surface: pygame.Surface, font: pygame.font.Font):
        """绘制按钮"""
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 2)
        
        # 绘制文本
        text_surface = font.render(self.text, True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
        
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        处理事件
        
        Args:
            event: pygame事件
            
        Returns:
            bool: 是否被点击
        """
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False

class UI:
    """用户界面类"""
    
    def __init__(self, width: int = 1200, height: int = 800):
        """
        初始化UI
        
        Args:
            width, height: 窗口尺寸
        """
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("方块解谜游戏")
        
        # 字体 - 尝试使用系统字体以支持中文
        try:
            # 尝试多种中文字体
            font_names = ['simsun', 'simhei', 'microsoftyaheimicrosoftyaheiui', 'arial', 'tahoma']
            font_found = False
            for font_name in font_names:
                try:
                    self.title_font = pygame.font.SysFont(font_name, 48)
                    self.large_font = pygame.font.SysFont(font_name, 36)
                    self.medium_font = pygame.font.SysFont(font_name, 24)
                    self.small_font = pygame.font.SysFont(font_name, 18)
                    # 测试字体是否能渲染中文
                    test_surface = self.title_font.render('测试', True, (0, 0, 0))
                    font_found = True
                    break
                except:
                    continue
            
            if not font_found:
                # 如果所有系统字体都不可用，使用默认字体
                self.title_font = pygame.font.Font(None, 48)
                self.large_font = pygame.font.Font(None, 36)
                self.medium_font = pygame.font.Font(None, 24)
                self.small_font = pygame.font.Font(None, 18)
        except:
            # 如果系统字体不可用，使用默认字体
            self.title_font = pygame.font.Font(None, 48)
            self.large_font = pygame.font.Font(None, 36)
            self.medium_font = pygame.font.Font(None, 24)
            self.small_font = pygame.font.Font(None, 18)
        
        # 颜色
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GRAY = (128, 128, 128)
        self.LIGHT_GRAY = (200, 200, 200)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BLUE = (0, 0, 255)
        
        # 游戏状态
        self.current_state = "start"
        self.scopes: List[Scope] = []
        self.current_scope_index = 0
        self.current_level_index = 0
        self.current_level: Optional[Level] = None
        self.margin_left = 0
        self.margin_top = 0
        self.margin_right = 0
        self.margin_bottom = 0
        self.current_blockset: Optional[BlockSet] = None
        self.constraint_checker = ConstraintChecker()
        self.failed_constraints = []
        
        # 游戏状态变量
        self.dragging = False
        self.drag_start = None
        self.drag_end = None
        self.selection_confirmed = False
        # 重置选中方块状态
        if self.current_blockset and self.current_blockset.selected_blocks:
            for i, block in enumerate(self.current_blockset.selected_blocks):
                block.ghost = False
                # 恢复原始颜色
                block.color = self.original_colors[i]
        self.moving_blocks = False
        self.move_start_pos = None
        self.original_positions = None
        
        # 按钮
        self.buttons = {}
        self._create_buttons()
          
        self.info_width = 260
        self.grid_w = 16
        self.grid_h = 11
        # 动态计算单元格大小（基于窗口尺寸和网格数量，略微调低宽度上限）
        self.available_width = 750  # 略微调低宽度上限
        self.available_height = self.height - 100  # 减去标题栏和底部空间
        self.cell_size = min(self.available_width // self.grid_w, self.available_height // self.grid_h)
        self.button_width = 120
        self.margin_left = 0
        self.margin_top = 0
        self.margin_right = 0
        self.margin_bottom = 0
        self.grid_offset = (0, 0)
        
    def _create_buttons(self):
        """创建按钮"""
        # 主菜单按钮
        self.buttons["start_game"] = Button((self.width - 200) // 2, 300, 200, 50, "开始游戏")  # 确保水平居中
        self.buttons["settings"] = Button((self.width - 200) // 2, 370, 200, 50, "设置")
        self.buttons["quit"] = Button((self.width - 200) // 2, 440, 200, 50, "退出")
        
        # 设置界面按钮
        self.buttons["back_to_menu"] = Button(50, 50, 100, 40, "返回")
        
        # 选大关界面按钮
        self.buttons["prev_scope"] = Button(50, 350, 50, 50, "<")
        self.buttons["next_scope"] = Button(1100, 350, 50, 50, ">")
        
        # 选关卡界面按钮
        self.buttons["prev_page"] = Button(50, 350, 50, 50, "<")
        self.buttons["next_page"] = Button(1100, 350, 50, 50, ">")
        self.buttons["back_to_scopes"] = Button(50, 50, 100, 40, "返回")
        
        # 游戏界面按钮
        self.buttons["reset"] = Button(50, 600, 80, 40, "重置")
        self.buttons["undo"] = Button(150, 600, 80, 40, "撤销")
        self.buttons["redo"] = Button(250, 600, 80, 40, "重做")
        self.buttons["confirm"] = Button(350, 600, 80, 40, "确认")
        self.buttons["back_to_levels"] = Button(450, 600, 100, 40, "返回选关")
        
        # 通关界面按钮
        self.buttons["next_level"] = Button(400, 400, 150, 50, "下一关")
        self.buttons["back_to_level_select"] = Button(400, 470, 150, 50, "返回选关")
        
    def set_scopes(self, scopes: List[Scope]):
        """设置大关列表"""
        self.scopes = scopes
        
    def draw_start_screen(self):
        """绘制开始界面"""
        self.screen.fill(self.WHITE)
        
        # 标题
        title = self.title_font.render("方块解谜游戏", True, self.BLACK)
        title_rect = title.get_rect(center=(self.width // 2, 150))
        self.screen.blit(title, title_rect)
        

        
        # 按钮
        for button in [self.buttons["start_game"], self.buttons["settings"], self.buttons["quit"]]:
            button.draw(self.screen, self.large_font)
            
    def draw_settings_screen(self):
        """绘制设置界面"""
        self.screen.fill(self.WHITE)
        
        # 标题
        title = self.title_font.render("设置", True, self.BLACK)
        title_rect = title.get_rect(center=(self.width // 2, 100))
        self.screen.blit(title, title_rect)
        
        # 提示文本
        text = self.medium_font.render("暂无设置项", True, self.GRAY)
        text_rect = text.get_rect(center=(self.width // 2, 300))
        self.screen.blit(text, text_rect)
        
        # 返回按钮
        self.buttons["back_to_menu"].draw(self.screen, self.medium_font)
        
    def draw_scope_selection_screen(self):
        """绘制选大关界面"""
        self.screen.fill(self.WHITE)
        
        # 标题
        title = self.title_font.render("选择大关", True, self.BLACK)
        title_rect = title.get_rect(center=(self.width // 2, 50))
        self.screen.blit(title, title_rect)
        
        if not self.scopes:
            text = self.medium_font.render("没有可用的大关", True, self.GRAY)
            text_rect = text.get_rect(center=(self.width // 2, 300))
            self.screen.blit(text, text_rect)
            return
            
        # 当前大关
        scope = self.scopes[self.current_scope_index]
        
        # 大关信息
        scope_text = self.large_font.render(f"{scope.scope_id}. {scope.name}", True, self.BLACK)
        scope_rect = scope_text.get_rect(center=(self.width // 2, 200))
        self.screen.blit(scope_text, scope_rect)
        

        
        # 大关选择框
        scope_rect = pygame.Rect(400, 300, 400, 200)
        pygame.draw.rect(self.screen, self.LIGHT_GRAY, scope_rect)
        pygame.draw.rect(self.screen, self.BLACK, scope_rect, 3)
        
        # 导航按钮
        if self.current_scope_index > 0:
            self.buttons["prev_scope"].draw(self.screen, self.large_font)
        if self.current_scope_index < len(self.scopes) - 1:
            self.buttons["next_scope"].draw(self.screen, self.large_font)
        # 绘制返回主菜单按钮
        self.buttons["back_to_start"] = Button(50, 50, 120, 40, "返回主菜单")
        self.buttons["back_to_start"].draw(self.screen, self.medium_font)
            
    def draw_level_selection_screen(self):
        """绘制选关卡界面"""
        self.screen.fill(self.WHITE)
        
        if not self.scopes:
            return
            
        scope = self.scopes[self.current_scope_index]
        
        # 标题
        title = self.large_font.render(f"{scope.scope_id}. {scope.name}", True, self.BLACK)
        title_rect = title.get_rect(center=(self.width // 2, 50))
        self.screen.blit(title, title_rect)
        
        # 显示当前大关的完成进度
        completed, total = self.game.get_completed_levels_in_scope(self.current_scope_index)
        scope_text = f"本大关: {completed}/{total}"
        self.screen.blit(self.medium_font.render(scope_text, True, (0, 0, 0)), (50, 100))
        
        # 关卡网格 (2行4列)
        levels_per_page = 8
        start_index = self.current_level_index * levels_per_page
        
        for i in range(min(levels_per_page, len(scope.levels) - start_index)):
            level = scope.levels[start_index + i]
            row = i // 4
            col = i % 4
            
            x = 200 + col * 200
            y = 150 + row * 150
            
            # 关卡框
            level_rect = pygame.Rect(x, y, 150, 120)
            color = self.GREEN if self.game.is_level_completed(level.level_id) else self.LIGHT_GRAY
            pygame.draw.rect(self.screen, color, level_rect)
            pygame.draw.rect(self.screen, self.BLACK, level_rect, 2)
            
            # 关卡编号
            level_text = self.medium_font.render(level.level_id, True, self.BLACK)
            level_rect_text = level_text.get_rect(center=(x + 75, y + 100))
            self.screen.blit(level_text, level_rect_text)
            
        # 导航按钮
        if self.current_level_index > 0:
            self.buttons["prev_page"].draw(self.screen, self.large_font)
        if (self.current_level_index + 1) * levels_per_page < len(scope.levels):
            self.buttons["next_page"].draw(self.screen, self.large_font)
            
        self.buttons["back_to_scopes"].draw(self.screen, self.medium_font)
        
    def draw_game_screen(self):
        """绘制游戏界面"""
        self.screen.fill(self.WHITE)
        
        if not self.current_level or not self.current_blockset:
            return
        

        # 左侧信息区域（加宽）
        info_rect = pygame.Rect(20, 20, 260, 500)
        pygame.draw.rect(self.screen, self.LIGHT_GRAY, info_rect)
        pygame.draw.rect(self.screen, self.BLACK, info_rect, 2)
        
        # 关卡信息
        level_text = self.large_font.render(self.current_level.name, True, self.BLACK)
        self.screen.blit(level_text, (30, 30))
        
        # 限制条件
        y_offset = 80
        constraint_title = self.medium_font.render("关卡限制:", True, self.BLACK)
        self.screen.blit(constraint_title, (30, y_offset))
        y_offset += 30
        
        for constraint in self.current_level.constraints:
            display_name = self.constraint_checker.get_constraint_display_name(constraint)
            description = self.constraint_checker.get_constraint_description(constraint)
            color = self.RED if constraint in self.failed_constraints else self.BLACK
            constraint_text = self.medium_font.render(f"[{display_name}]", True, color)
            self.screen.blit(constraint_text, (30, y_offset))
            y_offset += 22
            # 自动换行显示描述
            desc_lines = self._wrap_text(description, 22)
            for line in desc_lines:
                desc_text = self.small_font.render(line, True, color)
                self.screen.blit(desc_text, (40, y_offset))
                y_offset += 18
        
        # 显示关卡说明
        if self.current_level.instruction:
            y_offset += 10  # 与限制条件保持一定间距
            instruction_title = self.medium_font.render("[说明]", True, self.BLACK)
            self.screen.blit(instruction_title, (30, y_offset))
            y_offset += 22
            # 自动换行显示说明文字，每12个字换行
            instruction_lines = self._wrap_text(self.current_level.instruction, 12)
            for line in instruction_lines:
                instruction_text = self.small_font.render(line, True, self.BLACK)
                self.screen.blit(instruction_text, (40, y_offset))
                y_offset += 18
        
        # 游戏区域 - 居中显示
        self.cell_size = min(self.available_width // self.grid_w, self.available_height // self.grid_h)
        area_w = self.grid_w * self.cell_size
        area_h = self.grid_h * self.cell_size
        area_x = self.info_width + (self.width - self.info_width - self.button_width - area_w) // 2
        area_y = (self.height - area_h) // 2
        game_area = pygame.Rect(area_x, area_y, area_w, area_h)
        # 不绘制游戏区域上的灰色矩形，只绘制边框
        # pygame.draw.rect(self.screen, self.LIGHT_GRAY, game_area)
        pygame.draw.rect(self.screen, self.BLACK, game_area, 2)
        
        # 绘制网格
        self._draw_grid(game_area, self.cell_size)
        
        # 绘制方块 - 动态偏移量
        offset = (game_area.x + self.margin_left * self.cell_size, game_area.y + self.margin_top * self.cell_size)
        if not self.moving_blocks:
            self.current_blockset.draw(self.screen, offset, self.cell_size)
            # 拖动状态下不绘制选中效果
            if not self.moving_blocks:
                self.current_blockset.draw_selected(self.screen, offset, self.cell_size)
        else:
            # 拖动时只绘制未选中的方块
            if self.current_blockset:
            # 绘制未选中的方块
                for block in self.current_blockset.blocks:
                    if block not in self.current_blockset.selected_blocks:
                        block.draw(self.screen, offset, self.cell_size)
            # 拖拽状态下绘制临时方块集
            if self.moving_blocks and hasattr(self, 'temp_selected_block_set'):
                for block in self.temp_selected_block_set:
                    block.draw(self.screen, offset, self.cell_size)
      
        
        # 绘制选择区域
        if self.dragging and self.drag_start and self.drag_end:
            start_x = min(self.drag_start[0], self.drag_end[0])
            start_y = min(self.drag_start[1], self.drag_end[1])
            end_x = max(self.drag_start[0], self.drag_end[0])
            end_y = max(self.drag_start[1], self.drag_end[1])
            
            selection_rect = pygame.Rect(start_x, start_y, end_x - start_x, end_y - start_y)
            pygame.draw.rect(self.screen, (0, 255, 0, 128), selection_rect, 2)
            
        # 按钮 - 右侧竖排
        button_y = 50
        for button_name in ["reset", "undo", "redo", "confirm", "back_to_levels"]:
            self.buttons[button_name].rect.y = button_y
            self.buttons[button_name].rect.x = 1050  # 进一步向左调整，确保完全可见
            self.buttons[button_name].draw(self.screen, self.medium_font)
            button_y += 60
            
    def draw_congrats_screen(self):
        """绘制通关界面"""
        self.screen.fill(self.WHITE)
        
        # 恭喜文本
        congrats_text = self.title_font.render("恭喜通关！", True, self.GREEN)
        congrats_rect = congrats_text.get_rect(center=(self.width // 2, 200))
        self.screen.blit(congrats_text, congrats_rect)
        
        # 显示当前大关的完成进度
        completed, total = self.game.get_completed_levels_in_scope(self.current_scope_index)
        scope_text = f"本大关: {completed}/{total}"
        text_surface = self.medium_font.render(scope_text, True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=(self.width // 2, 300))
        self.screen.blit(text_surface, text_rect)
        
        # 按钮
        self.buttons["next_level"].draw(self.screen, self.large_font)
        self.buttons["back_to_level_select"].draw(self.screen, self.large_font)
        
    def handle_click(self, pos: Tuple[int, int]) -> Optional[str]:
        """
        处理点击事件
        
        Args:
            pos: 点击位置
            
        Returns:
            Optional[str]: 返回的动作名称
        """
        if self.current_state == "start":
            if self.buttons["start_game"].rect.collidepoint(pos):
                return "start_game"
            elif self.buttons["settings"].rect.collidepoint(pos):
                return "settings"
            elif self.buttons["quit"].rect.collidepoint(pos):
                return "quit"
                
        elif self.current_state == "settings":
            if self.buttons["back_to_menu"].rect.collidepoint(pos):
                return "back_to_menu"
                
        elif self.current_state == "choose_scope":
            if self.buttons["prev_scope"].rect.collidepoint(pos):
                return "prev_scope"
            elif self.buttons["next_scope"].rect.collidepoint(pos):
                return "next_scope"
            elif self.buttons["back_to_start"].rect.collidepoint(pos):
                return "back_to_menu"
            else:
                # 检查是否点击了大关框
                scope_rect = pygame.Rect(400, 300, 400, 200)
                if scope_rect.collidepoint(pos):
                    return "enter_scope"
                    
        elif self.current_state == "choose_level":
            if self.buttons["prev_page"].rect.collidepoint(pos):
                return "prev_page"
            elif self.buttons["next_page"].rect.collidepoint(pos):
                return "next_page"
            elif self.buttons["back_to_scopes"].rect.collidepoint(pos):
                return "back_to_scopes"
            else:
                # 检查是否点击了关卡框
                levels_per_page = 8
                start_index = self.current_level_index * levels_per_page
                scope = self.scopes[self.current_scope_index]
                
                for i in range(min(levels_per_page, len(scope.levels) - start_index)):
                    row = i // 4
                    col = i % 4
                    x = 200 + col * 200
                    y = 150 + row * 150
                    level_rect = pygame.Rect(x, y, 150, 120)
                    
                    if level_rect.collidepoint(pos):
                        return f"select_level_{start_index + i}"
                        
        elif self.current_state == "in_level_chooseblock":
            # 检查按钮点击
            for button_name in ["reset", "undo", "redo", "confirm", "back_to_levels"]:
                if self.buttons[button_name].rect.collidepoint(pos):
                    if button_name == "confirm":
                        # 检查选择阶段的约束
                        results = self.constraint_checker.check_constraints(self.current_blockset, 
                        self.current_level.constraints, 
                        "selection")
                        failed_now_constraints = [name for name, result in results.items() if not result]
                        if failed_now_constraints:
                            self.selection_confirmed = False
                            self.failed_constraints = failed_now_constraints
                            self.selected_blocks = []
                            return "reselection"
                        else:
                            self.selection_confirmed = True
                            self.failed_constraints = []
                            return button_name
                    else:
                        return button_name
                    
        elif self.current_state == "congrats":
            if self.buttons["next_level"].rect.collidepoint(pos):
                return "next_level"
            elif self.buttons["back_to_level_select"].rect.collidepoint(pos):
                return "back_to_level_select"
                
        return None
        
    def start_drag(self, pos: Tuple[int, int]):
        """开始拖拽"""
        self.dragging = True
        self.drag_start = pos
        self.drag_end = pos
        if self.current_blockset and self.current_blockset.selected_blocks:
            self.moving_blocks = True
            self.move_start_pos = pos
            self.original_positions = [block.pos for block in self.current_blockset.selected_blocks]
            # 创建选中方块的深拷贝作为临时集合，保留方块类型信息
            self.temp_selected_block_set = [Block(block_type=block.type, pos=block.pos, color=block.color, size=block.size, detailed_information=block.detailed_information) for block in self.current_blockset.selected_blocks]
            # 存储原始颜色用于恢复
            self.original_colors = [block.color for block in self.current_blockset.selected_blocks]
            # 动态计算游戏区域偏移（边距×单元格大小 + 标题栏高度）
            game_area_offset_x = self.margin_left * self.cell_size
            game_area_offset_y = self.margin_top * self.cell_size + 50  # 50为标题栏固定高度
            game_area_offset = (game_area_offset_x, game_area_offset_y)
            start_grid_x = (pos[0] - game_area_offset[0]) // self.cell_size
            start_grid_y = (pos[1] - game_area_offset[1]) // self.cell_size
            self.start_grid_pos = (start_grid_x, start_grid_y)
            self.start_mouse_pos = pos  # 记录初始鼠标位置
            # 计算最大允许偏移量
            self.min_offset_x = float('inf')
            self.max_offset_x = -float('inf')
            self.min_offset_y = float('inf')
            self.max_offset_y = -float('inf')
            
            for i, block in enumerate(self.current_blockset.selected_blocks):
                orig_x, orig_y = self.original_positions[i]
                # 计算每个方向的最大允许偏移
                left_limit = -self.margin_left - orig_x
                right_limit = (self.grid_w - self.margin_right - 1) - orig_x
                top_limit = -self.margin_top - orig_y
                bottom_limit = (self.grid_h - self.margin_bottom - 1) - orig_y
                
                self.min_offset_x = min(self.min_offset_x, left_limit)
                self.max_offset_x = max(self.max_offset_x, right_limit)
                self.min_offset_y = min(self.min_offset_y, top_limit)
                self.max_offset_y = max(self.max_offset_y, bottom_limit)
            
            self.original_colors = [block.color for block in self.current_blockset.selected_blocks]
            # 初始化选择状态
            for block in self.current_blockset.selected_blocks:
                block.selected = 1  # 1表示已选择(绿色光)
                block.ghost = True
        
    def update_drag(self, pos: Tuple[int, int]):
        """更新拖拽"""
        if not self.moving_blocks or not self.move_start_pos or not self.original_positions:
            return
        # 计算鼠标当前所在格子
        # 动态计算游戏区域偏移（边距×单元格大小 + 标题栏高度）
        game_area_offset_x = self.margin_left * self.cell_size
        game_area_offset_y = self.margin_top * self.cell_size + 50
        game_area_offset = (game_area_offset_x, game_area_offset_y)
        # 使用start_drag中固定的起始鼠标位置计算偏移
        offset_x = pos[0] - self.start_mouse_pos[0]
        offset_y = pos[1] - self.start_mouse_pos[1]
        grid_offset_x = offset_x // self.cell_size
        grid_offset_y = offset_y // self.cell_size
        
        # 使用start_drag中预计算的偏移限制
        grid_offset_x = max(min(grid_offset_x, self.max_offset_x), self.min_offset_x)
        grid_offset_y = max(min(grid_offset_y, self.max_offset_y), self.min_offset_y)
        # 检查位置有效性
        is_valid = True
        new_positions = []
        for i, block in enumerate(self.current_blockset.selected_blocks):
            orig_x, orig_y = self.original_positions[i]
            new_x = orig_x + grid_offset_x
            new_y = orig_y + grid_offset_y
            new_positions.append((new_x, new_y))
            # 边界检查
            if (new_x < -self.margin_left or new_x >= self.grid_w - self.margin_right or
                new_y < -self.margin_top or new_y >= self.grid_h - self.margin_bottom):
                is_valid = False
                break
            # 重叠检查（仅检查与未选中方块的重叠）
            for j, other_block in enumerate(self.current_blockset.blocks):
                if other_block not in self.current_blockset.selected_blocks and other_block.pos == (new_x, new_y):
                    is_valid = False
                    break
            if not is_valid:
                break
        
        # 使用临时方块集计算新位置并更新状态
        for i, temp_block in enumerate(self.temp_selected_block_set):
            orig_x, orig_y = self.original_positions[i]
            temp_block.pos = (orig_x + grid_offset_x, orig_y + grid_offset_y)
            temp_block.selected = 1 if is_valid else 2
            temp_block.color = (144, 238, 144) if is_valid else (255, 182, 193)
            temp_block.ghost = True
            
    def end_drag(self):
        """结束拖拽"""
        is_valid = False  # 初始化is_valid变量
        if self.moving_blocks and self.move_start_pos:
            # 计算最终偏移
            self.move_end_pos = pygame.mouse.get_pos()
            offset_x = self.move_end_pos[0] - self.move_start_pos[0]
            offset_y = self.move_end_pos[1] - self.move_start_pos[1]
            grid_offset_x = offset_x // self.cell_size
            grid_offset_y = offset_y // self.cell_size
            
            # 检查位置有效性
            is_valid = True
            for (orig_x, orig_y) in self.original_positions:
                new_x = orig_x + grid_offset_x
                new_y = orig_y + grid_offset_y
                # 边界检查
                if (new_x < -self.margin_left or new_x >= self.grid_w - self.margin_right or
                    new_y < -self.margin_top or new_y >= self.grid_h - self.margin_bottom):
                    is_valid = False
                    break
                # 重叠检查
                for block in self.current_blockset.blocks:
                    if block not in self.current_blockset.selected_blocks and block.pos == (new_x, new_y):
                        is_valid = False
                        break
                if not is_valid:
                    break
            
            # 应用有效移动或重置位置
        if not is_valid:
            # 位置无效，重置到原始位置
            for i, block in enumerate(self.current_blockset.selected_blocks):
                block.pos = self.original_positions[i]
        elif self.dragging and self.drag_start and self.drag_end and not self.selection_confirmed:
            # 选择区域内的方块（仅在未确认选择时）
            if self.current_blockset:
                start_pos = self._screen_to_grid(self.drag_start)
                end_pos = self._screen_to_grid(self.drag_end)
                self.current_blockset.select_blocks_in_area(start_pos, end_pos)
            
        # 计算最终位置有效性
        is_valid = False
        if self.current_blockset and self.current_blockset.selected_blocks and hasattr(self, 'original_positions'):
            is_valid = True
            for i, block in enumerate(self.current_blockset.selected_blocks):
                orig_x, orig_y = self.original_positions[i]
                new_x = orig_x + grid_offset_x
                new_y = orig_y + grid_offset_y
                # 边界检查
                if (new_x < -self.margin_left or new_x >= self.grid_w - self.margin_right or
                    new_y < -self.margin_top or new_y >= self.grid_h - self.margin_bottom):
                    is_valid = False
                    break
                # 重叠检查
                for j, other_block in enumerate(self.current_blockset.blocks):
                    if other_block not in self.current_blockset.selected_blocks and not other_block.ghost and other_block.pos == (new_x, new_y):
                        is_valid = False
                        break
                if not is_valid:
                    break
        
        # 应用或恢复位置
        if self.current_blockset and self.current_blockset.selected_blocks and hasattr(self, 'original_colors'):
            for i, block in enumerate(self.current_blockset.selected_blocks):
                if i < len(self.original_colors):
                    block.color = self.original_colors[i]
                    if is_valid:
                        # 应用临时方块集的位置
                        block.pos = self.temp_selected_block_set[i].pos
                    else:
                        # 恢复原始位置
                        block.pos = self.original_positions[i]
                    block.selected = 0  # 重置选择状态
                    block.ghost = False
        # 清除临时状态
        self.dragging = False
        self.moving_blocks = False
        self.drag_start = None
        self.drag_end = None
        self.move_start_pos = None
        self.move_end_pos = None
        self.original_positions = None
        self.temp_selected_block_set = None
        
    def _screen_to_grid(self, screen_pos: Tuple[int, int]) -> Tuple[int, int]:
        """将屏幕坐标转换为网格坐标"""
        offset = self.get_grid_offset()
        grid_x = (screen_pos[0] - offset[0]) // self.cell_size
        grid_y = (screen_pos[1] - offset[1]) // self.cell_size
        return (grid_x, grid_y)
        
    def load_level(self, level: Level):
        """加载关卡"""
        self.current_level = level
        if self.current_level:
            self.margin_left = self.current_level.margin_left
            self.margin_top = self.current_level.margin_top
            self.margin_right = self.current_level.margin_right
            self.margin_bottom = self.current_level.margin_bottom
        self.current_blockset = level.create_blockset()
        # 更新所有方块大小以匹配当前网格尺寸
        if self.current_blockset:
            for block in self.current_blockset.blocks:
                block.size = self.cell_size
        self.selection_confirmed = False
        self.moving_blocks = False
        
    def _draw_grid(self, game_area: pygame.Rect, cell_size: int):
        """绘制网格"""
        if not self.current_level:
            return
            
        # 计算网格范围
        start_x = game_area.x + self.margin_left * cell_size
        start_y = game_area.y + self.margin_top * cell_size
        
        # 网格范围严格限制
        for x in range(-self.margin_left, self.grid_w - self.margin_right):
            for y in range(-self.margin_top, self.grid_h - self.margin_bottom):
                grid_x = start_x + x * cell_size
                grid_y = start_y + y * cell_size
                
                # 绘制虚线边框
                for i in range(0, cell_size, 4):  # 虚线效果
                    # 上边
                    if i < cell_size:
                        pygame.draw.line(self.screen, (100, 100, 100), 
                                       (grid_x + i, grid_y), 
                                       (grid_x + min(i + 2, cell_size), grid_y), 1)
                    # 左边
                    if i < cell_size:
                        pygame.draw.line(self.screen, (100, 100, 100), 
                                       (grid_x, grid_y + i), 
                                       (grid_x, grid_y + min(i + 2, cell_size)), 1)
    
    
    def update(self):
        """更新界面"""
        if self.current_state == "start":
            self.draw_start_screen()
        elif self.current_state == "settings":
            self.draw_settings_screen()
        elif self.current_state == "choose_scope":
            self.draw_scope_selection_screen()
        elif self.current_state == "choose_level":
            self.draw_level_selection_screen()
        elif self.current_state == "in_level_chooseblock":
            self.draw_game_screen()
        elif self.current_state == "congrats":
            self.draw_congrats_screen()
            
        pygame.display.flip() 

    def _wrap_text(self, text, max_chars):
        """自动换行"""
        lines = []
        # 按照人工换行符分割文本
        paragraphs = text.split('\n')
        
        for paragraph in paragraphs:
            # 处理每个段落，按max_chars自动换行
            while len(paragraph) > max_chars:
                # 找到合适的换行位置
                split_pos = max_chars
                # 确保不在单词中间换行
                if split_pos < len(paragraph):
                    # 向前查找空格或标点符号作为换行点
                    for i in range(max_chars, max(0, max_chars-10), -1):
                        if paragraph[i] in [' ', '，', '。', '！', '？', '；', '：', ',', '.', '!', '?', ';', ':']:
                            split_pos = i + 1
                            break
                lines.append(paragraph[:split_pos].strip())
                paragraph = paragraph[split_pos:]
            # 添加剩余部分
            if paragraph:
                lines.append(paragraph)
        
        return lines

    def set_level_layout(self, level):
        self.margin_left = level.margin_left
        self.margin_top = level.margin_top
        self.margin_right = level.margin_right
        self.margin_bottom = level.margin_bottom
        max_w, max_h = level.max_rect
        self.grid_w = max_w + self.margin_left + self.margin_right
        self.grid_h = max_h + self.margin_top + self.margin_bottom
        # 自适应cell_size，最大不超过800x600区域
        max_area_w = self.width - self.info_width - self.button_width - 40
        max_area_h = self.height - 40
        self.cell_size = min(max_area_w // self.grid_w, max_area_h // self.grid_h, 60)
        area_w = self.grid_w * self.cell_size
        area_h = self.grid_h * self.cell_size
        area_x = self.info_width + (self.width - self.info_width - self.button_width - area_w) // 2
        area_y = (self.height - area_h) // 2
        self.grid_offset = (area_x + self.margin_left * self.cell_size, area_y + self.margin_top * self.cell_size)

    def get_grid_offset(self):
        return self.grid_offset

    def get_grid_pos(self, screen_pos):
        offset = self.get_grid_offset()
        x = (screen_pos[0] - offset[0]) // self.cell_size
        y = (screen_pos[1] - offset[1]) // self.cell_size
        return (x, y)

    def get_screen_pos(self, grid_pos):
        offset = self.get_grid_offset()
        x = grid_pos[0] * self.cell_size + offset[0]
        y = grid_pos[1] * self.cell_size + offset[1]
        return (x, y)