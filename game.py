from typing import List, Optional, Tuple
from ui import UI
from level_parser import LevelParser, Scope, Level
from blockset import BlockSet
from constraints import ConstraintChecker
import pygame

class Game:
    """主游戏类"""
    
    def __init__(self):
        """初始化游戏"""
        self.ui = UI()
        self.ui.game = self  # 将Game实例传递给UI
        self.level_parser = LevelParser()
        self.constraint_checker = ConstraintChecker()
        
        # 游戏状态
        self.running = True
        self.scopes: List[Scope] = []
        self.current_scope_index = 0
        self.current_level_index = 0
        self.current_level: Optional[Level] = None
        
        # 存档数据
        self.save_data = self.load_save_data()
        
        # 历史记录（用于撤销/重做）
        self.history = []
        self.history_index = -1
        
        # 加载关卡
        self._load_levels()
        
    def _load_levels(self):
        """加载关卡"""
        try:
            self.scopes = self.level_parser.parse_levels_file("levels.txt")
        except FileNotFoundError:
            print("未找到levels.txt文件，使用默认关卡")
            self.scopes = self.level_parser.parse_levels_file("")
            
        self.ui.set_scopes(self.scopes)
        
    def run(self):
        """运行游戏主循环"""
        clock = pygame.time.Clock()
        
        while self.running:
            # 处理事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self._handle_event(event)
                    
            # 更新界面
            self.ui.update()
            
            # 控制帧率
            clock.tick(60)
            
        pygame.quit()
        
    def _handle_event(self, event: pygame.event.Event):
        """处理事件"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左键
                self._handle_mouse_down(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # 左键
                self._handle_mouse_up(event.pos)
        elif event.type == pygame.MOUSEMOTION:
            self._handle_mouse_motion(event.pos)
            
    def _handle_mouse_down(self, pos: Tuple[int, int]):
        """处理鼠标按下事件"""
        if self.ui.current_state == "in_level_chooseblock":
            # 在游戏界面中，先检查是否点击了按钮
            action = self.ui.handle_click(pos)
            if action:
                self._handle_action(action)
                return
            
            if not self.ui.selection_confirmed:
                # 选择阶段
                if self.ui.current_blockset:
                    # 检查是否点击了方块
                    grid_pos = self.ui.get_grid_pos(pos)
                    clicked_block = None
                    for block in self.ui.current_blockset.blocks:
                        if block.pos == grid_pos:
                            clicked_block = block
                            break
                    
                    # 如果点击的是已选择的方块，则取消选择
                    if clicked_block and clicked_block in self.ui.current_blockset.selected_blocks:
                        self.ui.current_blockset.deselect_block(clicked_block)
                        if self.ui.failed_constraints:
                            self.ui.failed_constraints = []
                    # 如果点击的是未选择的方块，则选中它
                    elif clicked_block:
                        self.ui.current_blockset.select_block(clicked_block)
                        if self.ui.failed_constraints:
                            self.ui.failed_constraints = []
                    return
            else:
                # 移动阶段
                if self.ui.current_blockset:
                    grid_pos = self.ui.get_grid_pos(pos)
                    for block in self.ui.current_blockset.selected_blocks:
                        if block.pos == grid_pos:
                            self.ui.moving_blocks = True
                            self.ui.move_start_pos = pos
                            self.ui.original_positions = [(b.pos[0], b.pos[1]) for b in self.ui.current_blockset.selected_blocks]
                            break
                self.ui.start_drag(pos)
        else:
            # 处理其他界面的点击
            action = self.ui.handle_click(pos)
            if action:
                self._handle_action(action)
                
    def _handle_mouse_up(self, pos: Tuple[int, int]):
        """处理鼠标释放事件"""
        if self.ui.current_state == "in_level_chooseblock":
            if self.ui.dragging:
                self.ui.end_drag()

                self.ui.move_start_pos = None
                self.ui.original_positions = []
                # 仅在选择确认后才检查最终限制条件
                if self.ui.selection_confirmed and self.ui.current_blockset and self.current_level:
                    results = self.constraint_checker.check_constraints(
                        self.ui.current_blockset, 
                        self.current_level.constraints, 
                        "movement"
                    )
                    failed_constraints = [name for name, result in results.items() if not result]
                    self.ui.failed_constraints = failed_constraints
                    if failed_constraints:
                        self._reset_level()
                        self.ui.failed_constraints = failed_constraints
                    else:
                        self.current_level.completed = True
                        if self.current_level is not None:
                            self.complete_level(self.current_level.level_id)
                        self.ui.current_state = "congrats"
                        self.ui.failed_constraints = []
            
    def _handle_mouse_motion(self, pos: Tuple[int, int]):
        """处理鼠标移动事件"""
        if self.ui.current_state == "in_level_chooseblock":
            if self.ui.dragging:
                self.ui.update_drag(pos)
            # elif self.ui.moving_blocks and self.ui.move_start_pos:
            #     self._move_selected_blocks(pos)
            
    def _handle_action(self, action: str):
        """处理动作"""
        if action == "start_game":
            self.ui.current_state = "choose_scope"
            
        elif action == "settings":
            previous_state = self.ui.current_state 
            self.ui.current_state = "settings"
            if previous_state == "in_level_chooseblock":
                self._reload_current_level()  # 重新加载关卡而非设为None
            
        elif action == "quit":
            previous_state = self.ui.current_state
            self.running = False
            if previous_state == "in_level_chooseblock":
                self._reload_current_level()  # 重新加载关卡而非设为None
            
        elif action == "back_to_menu":
            if self.ui.current_state == "choose_level":
                self.ui.current_state = "choose_scope"
            else:
                self.ui.current_state = "start"
            self._reload_current_level()  # 重新加载关卡而非设为None
        elif action == "back_to_scopes":
            self.ui.current_state = "choose_scope"
        elif action == "back_to_start":
            self.ui.current_state = "start"
        elif action == "replay_level":
            # 重新加载当前关卡
            self.current_level = self.level_parser.get_level(self.current_level.level_id)
            self.current_level.completed = False
            self.ui.load_level(self.current_level)
            self.ui.current_state = "in_level_chooseblock"
        elif action.startswith("level_"):
            level_index = int(action.split("_")[1])
            self.current_level = self.level_parser.parse_level(level_index)
            self.current_level.completed = False
            self._reload_current_level()
            self.ui.load_level(self.current_level)
            self.ui.current_state = "in_level_chooseblock"
            
        elif action == "prev_scope":
            if self.ui.current_scope_index > 0:
                self.ui.current_scope_index -= 1
                
        elif action == "next_scope":
            if self.ui.current_scope_index < len(self.scopes) - 1:
                self.ui.current_scope_index += 1
                
        elif action == "enter_scope":
            self.ui.current_state = "choose_level"
            self._reload_current_level()  # 重新加载关卡
            self.ui.current_level_index = 0
            
        elif action == "prev_page":
            if self.ui.current_level_index > 0:
                self.ui.current_level_index -= 1
                
        elif action == "next_page":
            scope = self.scopes[self.ui.current_scope_index]
            levels_per_page = 8
            if (self.ui.current_level_index + 1) * levels_per_page < len(scope.levels):
                self.ui.current_level_index += 1
                
        elif action == "start_game":
            previous_state = self.ui.current_state
            self.ui.current_state = "choose_scope"
            if previous_state == "in_level_chooseblock":
                self._reload_current_level()  # 重新加载关卡而非设为None
            
        elif action.startswith("select_level_"):
            level_id = f"{self.ui.current_scope_index+1}-{int(action.split('_')[-1])+1}"
            level = self.level_parser.get_level(level_id)
            if level:
                self._load_level(level)
                
        elif action == "reset":
            self._reset_level()
            
        elif action == "undo":
            self._undo()
            
        elif action == "redo":
            self._redo()
            
        elif action == "confirm":
            self._confirm_selection()
            
        elif action == "back_to_levels":
            self.ui.current_state = "choose_level"
            
        elif action == "next_level":
            self._next_level()
            
        elif action == "back_to_level_select":
            if self.ui.current_state == "choose_level":
                self.ui.current_state = "choose_scope"
            else:
                self.ui.current_state = "choose_level"
            
    def _load_level(self, level: Level):
        """加载关卡"""
        self.current_level = level
        self.ui.load_level(level)
        self.ui.set_level_layout(level)
        self.ui.current_state = "in_level_chooseblock"
        self.history = []
        self.history_index = -1
        # 注册选中状态变更回调
        if self.ui.current_blockset:
            self.ui.current_blockset.on_selection_change = self._save_state
            
    def load_save_data(self):
        """加载存档数据"""
        import json
        import os
        try:
            if os.path.exists('save_data.json'):
                with open('save_data.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"加载存档失败: {e}")
            return {}

    def save_save_data(self):
        """保存存档数据"""
        import json
        try:
            with open('save_data.json', 'w', encoding='utf-8') as f:
                json.dump(self.save_data, f, indent=2)
        except Exception as e:
            print(f"保存存档失败: {e}")

    def is_level_completed(self, level_id):
        """检查关卡是否已完成"""
        return self.save_data.get(level_id, False)

    def check_selection_constraints(self):
        """检查选择阶段的约束"""
        if self.current_level:
            results = self.constraint_checker.check_constraints(
                self.ui.current_blockset, 
                self.current_level.constraints, 
                "selection"
            )
            return all(results.values())
        return False

    def complete_level(self, level_id):
        """标记关卡为已完成并保存存档"""
        if level_id not in self.save_data or not self.save_data[level_id]:
            self.save_data[level_id] = True
            self.save_save_data()

    def get_completed_level_count(self):
        """从存档中获取已完成关卡总数"""
        return sum(1 for completed in self.save_data.values() if completed)

    def get_completed_levels_in_scope(self, scope_index):
        """获取指定大关内已完成的关卡数和总关卡数"""
        scope_id = scope_index + 1
        completed = 0
        total = 0
        if 0 <= scope_index < len(self.scopes):
            total = len(self.scopes[scope_index].levels)
            for level in self.scopes[scope_index].levels:
                if self.is_level_completed(level.level_id):
                    completed += 1
        return completed, total

    def _reload_current_level(self):
        """重新加载当前关卡"""
        if self.current_level:
            level_id = self.current_level.level_id
            self.current_level = self.level_parser.get_level(level_id)
            self.current_level.completed = False
            self.ui.load_level(self.current_level)
            
    def _reset_level(self):
        """重置关卡"""
        if self.current_level and self.ui.current_blockset:
            # 重置所有方块位置
            for block in self.ui.current_blockset.blocks:
                block.reset_position()
                
            # 清除选择
            self.ui.current_blockset.clear_selection()
            self.ui.selection_confirmed = False
            self.ui.moving_blocks = False
            
            # 清空历史
            self.history = []
            self.history_index = -1
            # 重置失败的限制条件
            self.ui.failed_constraints = []
            
    def _undo(self):
        """撤销操作"""
        if self.history_index > 0:
            self.history_index -= 1
            self._restore_state(self.history[self.history_index])
            # 重置选择状态
            self.ui.selection_confirmed = False
            self.ui.failed_constraints = []
            
    def _redo(self):
        """重做操作"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self._restore_state(self.history[self.history_index])
            # 重置选择状态
            self.ui.selection_confirmed = False
            self.ui.failed_constraints = []
            
    def _save_state(self):
        """保存当前状态"""
        if not self.ui.current_blockset:
            return
        # 保存所有方块的位置和选中状态
        state = []
        for block in self.ui.current_blockset.blocks:
            state.append((block.pos, block.selected))
        # 保存selection_confirmed状态
        state_confirmed = self.ui.selection_confirmed
        # 删除当前状态之后的历史
        self.history = self.history[:self.history_index + 1]
        self.history.append((state, state_confirmed))
        self.history_index = len(self.history) - 1
        # 限制历史记录数量
        if len(self.history) > 20:
            self.history = self.history[-20:]
            self.history_index = len(self.history) - 1

    def _restore_state(self, state):
        """恢复状态"""
        if not self.ui.current_blockset:
            return
        state_blocks, state_confirmed = state
        for i, (pos, selected) in enumerate(state_blocks):
            if i < len(self.ui.current_blockset.blocks):
                block = self.ui.current_blockset.blocks[i]
                block.pos = pos
                block.selected = selected
                if selected:
                    self.ui.current_blockset.selected_blocks.add(block)
                else:
                    self.ui.current_blockset.selected_blocks.discard(block)
        self.ui.selection_confirmed = state_confirmed
        self.ui.failed_constraints = []
            
    def _confirm_selection(self):
        """
        确认选择
        """
        if not self.ui.current_blockset or not self.ui.current_blockset.selected_blocks:
            return
        self.ui.selection_confirmed = True
        self._save_state()
        self.ui.failed_constraints = []
            
    def _next_level(self):
        """进入下一关"""
        if not self.current_level:
            return
            
        # 标记当前关卡为完成
        self.current_level.completed = True
        
        # 查找下一关
        next_level = self._find_next_level()
        
        if next_level:
            self._load_level(next_level)
        else:
            # 没有下一关，显示通关界面
            self.ui.current_state = "choose_level"
            
    def _find_next_level(self) -> Optional[Level]:
        """查找下一关"""
        if not self.current_level:
            return None
            
        current_scope_id, current_level_num = map(int, self.current_level.level_id.split('-'))
        
        # 先尝试在当前大关中找下一关
        current_scope = self.scopes[current_scope_id - 1]
        if current_level_num < len(current_scope.levels):
            return current_scope.levels[current_level_num]
            
        # 当前大关没有下一关，尝试下一个大关的第一关
        if current_scope_id < len(self.scopes):
            next_scope = self.scopes[current_scope_id]
            if next_scope.levels:
                return next_scope.levels[0]
                
        return None
        
    def _move_selected_blocks(self, pos: Tuple[int, int]):
        """移动选中的方块"""
        if not self.ui.move_start_pos or not self.ui.original_positions:
            return
            
        # 计算移动偏移量
        offset_x = pos[0] - self.ui.move_start_pos[0]
        offset_y = pos[1] - self.ui.move_start_pos[1]
        
        # 转换为网格偏移（网格吸附）
        grid_offset_x = round(offset_x / 40)
        grid_offset_y = round(offset_y / 40)
        
        # 检查边界限制
        if self.current_level:
            # 计算新的位置
            new_positions = []
            for i, (orig_x, orig_y) in enumerate(self.ui.original_positions):
                new_x = orig_x + grid_offset_x
                new_y = orig_y + grid_offset_y
                
                # 检查边界（网格限制）
                if (new_x < -self.current_level.margin_left or 
                    new_x > 15 + self.current_level.margin_right or
                    new_y < -self.current_level.margin_top or 
                    new_y > 10 + self.current_level.margin_bottom):
                    return  # 超出边界，不移动
                    
                new_positions.append((new_x, new_y))
            
            # 检查是否与其他方块重叠
            all_positions = set()
            for block in self.ui.current_blockset.blocks:
                if block not in self.ui.current_blockset.selected_blocks:
                    all_positions.add(block.pos)
            
            for new_pos in new_positions:
                if new_pos in all_positions:
                    return  # 有重叠，不移动
            
            # 应用移动
            for i, block in enumerate(self.ui.current_blockset.selected_blocks):
                if i < len(new_positions):
                    block.pos = new_positions[i]