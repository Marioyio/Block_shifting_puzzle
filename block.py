import pygame
from typing import Tuple, Optional

class Block:
    """方块对象类"""
    
    def __init__(self, block_type: int = 1, pos: Tuple[int, int] = (0, 0), 
                 size: int = 40, color: Tuple[int, int, int] = (0, 0, 0),
                 detailed_information = None):
        """
        初始化方块
        
        Args:
            block_type: 方块类型（不小于1的正整数）
            pos: 方块位置 (x, y)
            size: 方块大小
            color: 方块颜色
            detailed_information: 方块详细信息，在type不同时有不同意义
                type为1,2时默认为空
                type为3时，为一个0,1,2构成的四维数组表示其上下左右的颜色（0为白色，1为黑色，2为蓝色）
        """
        self.type = block_type
        self.pos = pos
        self.size = size
        self.color = color
        self.detailed_information = detailed_information if detailed_information is not None else []
        self.selected = False
        self.ghost = False
        self.original_pos = pos  # 保存原始位置用于重置
        
    def draw(self, surface: pygame.Surface, offset: Tuple[int, int] = (0, 0), size: int = 40):
        """
        绘制方块
        
        Args:
            surface: 绘制表面
            offset: 偏移量 (x, y)
            size: 方块大小
        """
        x, y = self.pos
        rect_x = offset[0] + x * size
        rect_y = offset[1] + y * size
        rect = pygame.Rect(rect_x, rect_y, size, size)
        
        # 绘制方块边框
        pygame.draw.rect(surface, (50, 50, 50), rect, 1)
        
        # 根据方块类型绘制中心图案
        if self.type == 1:  # 黑色方块
            # 绘制黑色方块中心的黑色小方块
            center_size = size // 1.4
            center_x = rect_x + (size - center_size) // 2
            center_y = rect_y + (size - center_size) // 2
            center_rect = pygame.Rect(center_x, center_y, center_size, center_size)
            pygame.draw.rect(surface, (0, 0, 0), center_rect)
        elif self.type == 2:  # 深蓝色方块
            # 绘制深蓝色方块中心的深蓝色小方块，大小与黑色方块一致
            center_size = size // 1.8
            center_x = rect_x + (size - center_size) // 2
            center_y = rect_y + (size - center_size) // 2
            center_rect = pygame.Rect(center_x, center_y, center_size, center_size)
            pygame.draw.rect(surface, (0, 0, 139), center_rect)  # 深蓝色 RGB(0, 0, 139)
        elif self.type == 3:  # 金字塔方块
            # 绘制金字塔方块：中心正方形分为四个三角形区域
            center_x = rect_x + size // 2
            center_y = rect_y + size // 2
            half_size = size // 3  # 调整大小，使其不占满整个格子
            shrinkage_size = size // 6
            
            # 定义颜色映射
            color_map = {0: (255, 255, 255), 1: (0, 0, 0), 2: (0, 0, 139)}
            
            # 获取金字塔各面的颜色信息
            if len(self.detailed_information) >= 4:
                top_color = color_map.get(self.detailed_information[0], (255, 255, 255))
                bottom_color = color_map.get(self.detailed_information[1], (255, 255, 255))
                left_color = color_map.get(self.detailed_information[2], (255, 255, 255))
                right_color = color_map.get(self.detailed_information[3], (255, 255, 255))
            else:
                # 默认颜色
                top_color = bottom_color = left_color = right_color = (255, 255, 255)
            
            if self.detailed_information[0]==2:
                top_coords = [
                (center_x, center_y - shrinkage_size),  
                (center_x - half_size + shrinkage_size, center_y - half_size),  
                (center_x + half_size - shrinkage_size, center_y - half_size)   
            ]
            else:
                top_coords = [
                (center_x, center_y),  
                (center_x - half_size, center_y - half_size),  
                (center_x + half_size, center_y - half_size)   
            ]
            pygame.draw.polygon(surface, top_color, top_coords)
            pygame.draw.polygon(surface, (50, 50, 50), top_coords, 1)
            
            if self.detailed_information[1]==2:
                bottom_coords = [
                (center_x, center_y + shrinkage_size),  
                (center_x - half_size + shrinkage_size, center_y + half_size),  
                (center_x + half_size - shrinkage_size, center_y + half_size)   
            ]
            else:
                bottom_coords = [
                (center_x, center_y),  
                (center_x - half_size, center_y + half_size),  
                (center_x + half_size, center_y + half_size)   
            ]
            pygame.draw.polygon(surface, bottom_color, bottom_coords)
            pygame.draw.polygon(surface, (50, 50, 50), bottom_coords, 1)
            
            if self.detailed_information[2]==2:
                left_coords = [
                (center_x - shrinkage_size, center_y),  
                (center_x - half_size, center_y - half_size + shrinkage_size),  
                (center_x - half_size, center_y + half_size - shrinkage_size)   
            ]
            else:
                left_coords = [
                (center_x, center_y),  
                (center_x - half_size, center_y - half_size),  
                (center_x - half_size, center_y + half_size)     
            ]
            pygame.draw.polygon(surface, left_color, left_coords)
            pygame.draw.polygon(surface, (50, 50, 50), left_coords, 1)
            
            if self.detailed_information[3]==2:
                right_coords = [
                (center_x + shrinkage_size, center_y),  
                (center_x + half_size, center_y - half_size + shrinkage_size),  
                (center_x + half_size, center_y + half_size - shrinkage_size)   
            ]
            else:
                right_coords = [
                (center_x, center_y),  
                (center_x + half_size, center_y - half_size),  
                (center_x + half_size, center_y + half_size)     
            ]
            pygame.draw.polygon(surface, right_color, right_coords)
            pygame.draw.polygon(surface, (50, 50, 50), right_coords, 1)
        
    def draw_selected(self, surface: pygame.Surface, offset: Tuple[int, int] = (0, 0), size: int = 40):
        """
        绘制选中状态的方块（绿色半透明）
        
        Args:
            surface: 绘制表面
            offset: 偏移量
        """
        if not self.selected:
            return
            
        x, y = self.pos[0] * size + offset[0], self.pos[1] * size + offset[1]
        
        # 创建半透明绿色表面
        overlay = pygame.Surface((size, size))
        overlay.set_alpha(128)  # 半透明
        overlay.fill((0, 255, 0))  # 绿色
        surface.blit(overlay, (x, y))
        
    def is_point_inside(self, point: Tuple[int, int], offset: Tuple[int, int] = (0, 0), size: int = 40) -> bool:
        """
        检查点是否在方块内
        
        Args:
            point: 要检查的点 (x, y)
            offset: 偏移量
            
        Returns:
            bool: 点是否在方块内
        """
        x, y = self.pos[0] * size + offset[0], self.pos[1] * size + offset[1]
        px, py = point
        return (x <= px < x + size) and (y <= py < y + size)
        
    def move(self, new_pos: Tuple[int, int]):
        """
        移动方块到新位置
        
        Args:
            new_pos: 新位置 (x, y)
        """
        self.pos = new_pos
        
    def reset_position(self):
        """重置到原始位置"""
        self.pos = self.original_pos
        
    def __eq__(self, other):
        if not isinstance(other, Block):
            return False
        return self.type == other.type and self.pos == other.pos
        
    def __hash__(self):
        return hash((self.type, self.pos))