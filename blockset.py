from typing import List, Tuple, Set, Optional
from block import Block
import pygame

class BlockSet:
    """方块集合类"""
    
    def __init__(self):
        """初始化方块集合"""
        self.blocks: List[Block] = []
        self.selected_blocks: Set[Block] = set()
        self.on_selection_change = None  # 回调
        
    def add_block(self, block: Block):
        """
        添加方块到集合
        
        Args:
            block: 要添加的方块
        """
        self.blocks.append(block)
        
    def remove_block(self, block: Block):
        """
        从集合中移除方块
        
        Args:
            block: 要移除的方块
        """
        if block in self.blocks:
            self.blocks.remove(block)
        if block in self.selected_blocks:
            self.selected_blocks.remove(block)
            
    def get_block_at_position(self, pos: Tuple[int, int]) -> Optional[Block]:
        """
        获取指定位置的方块
        
        Args:
            pos: 位置 (x, y)
            
        Returns:
            Block: 该位置的方块，如果没有则返回None
        """
        for block in self.blocks:
            if block.pos == pos:
                return block
        return None
        
    def select_block(self, block: Block):
        """
        选中方块
        
        Args:
            block: 要选中的方块
        """
        if block in self.blocks:
            block.selected = True
            self.selected_blocks.add(block)
            if self.on_selection_change:
                self.on_selection_change()
            
    def deselect_block(self, block: Block):
        """
        取消选中方块
        
        Args:
            block: 要取消选中的方块
        """
        if block in self.selected_blocks:
            block.selected = False
            self.selected_blocks.remove(block)
            if self.on_selection_change:
                self.on_selection_change()
            
    def select_blocks_in_area(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int]):
        """
        选择区域内的方块
        
        Args:
            start_pos: 起始位置
            end_pos: 结束位置
        """
        min_x, min_y = min(start_pos[0], end_pos[0]), min(start_pos[1], end_pos[1])
        max_x, max_y = max(start_pos[0], end_pos[0]), max(start_pos[1], end_pos[1])
        
        for block in self.blocks:
            if min_x <= block.pos[0] <= max_x and min_y <= block.pos[1] <= max_y:
                self.select_block(block)
                
    def clear_selection(self):
        """清除所有选中状态"""
        for block in self.selected_blocks:
            block.selected = False
        self.selected_blocks.clear()
        if self.on_selection_change:
            self.on_selection_change()
        
    def move_selected_blocks(self, offset: Tuple[int, int]):
        """
        移动所有选中的方块
        
        Args:
            offset: 移动偏移量 (dx, dy)
        """
        for block in self.selected_blocks:
            new_pos = (block.pos[0] + offset[0], block.pos[1] + offset[1])
            block.move(new_pos)
            
    def reset_selected_blocks(self):
        """重置所有选中方块的位置"""
        for block in self.selected_blocks:
            block.reset_position()
            
    def get_selected_positions(self) -> List[Tuple[int, int]]:
        """
        获取所有选中方块的位置
        
        Returns:
            List[Tuple[int, int]]: 选中方块的位置列表
        """
        return [block.pos for block in self.selected_blocks]
        
    def get_all_positions(self) -> List[Tuple[int, int]]:
        """
        获取所有方块的位置
        
        Returns:
            List[Tuple[int, int]]: 所有方块的位置列表
        """
        return [block.pos for block in self.blocks]
        
    def has_overlap(self, other_blockset: 'BlockSet') -> bool:
        """
        检查是否与其他方块集合重叠
        
        Args:
            other_blockset: 其他方块集合
            
        Returns:
            bool: 是否有重叠
        """
        self_positions = set(self.get_all_positions())
        other_positions = set(other_blockset.get_all_positions())
        return bool(self_positions & other_positions)
        
    def is_connected(self) -> bool:
        """
        检查选中的方块是否连通
        
        Returns:
            bool: 是否连通
        """
        if len(self.selected_blocks) <= 1:
            return True
            
        # 使用BFS检查连通性
        selected_positions = set(self.get_selected_positions())
        if not selected_positions:
            return True
            
        start_pos = list(selected_positions)[0]
        visited = set()
        queue = [start_pos]
        visited.add(start_pos)
        
        while queue:
            current = queue.pop(0)
            x, y = current
            
            # 检查四个方向的相邻方块
            neighbors = [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
            for neighbor in neighbors:
                if neighbor in selected_positions and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
                    
        return len(visited) == len(selected_positions)
        
    def draw(self, surface: pygame.Surface, offset: Tuple[int, int] = (0, 0), size: int = 40):
        """
        绘制所有方块
        
        Args:
            surface: 绘制表面
            offset: 偏移量
        """
        for block in self.blocks:
            block.draw(surface, offset, size)
            
    def draw_selected(self, surface: pygame.Surface, offset: Tuple[int, int] = (0, 0), size: int = 40):
        """
        绘制选中状态的方块
        
        Args:
            surface: 绘制表面
            offset: 偏移量
        """
        for block in self.selected_blocks:
            block.draw_selected(surface, offset, size)