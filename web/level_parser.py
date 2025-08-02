from typing import List, Dict, Any, Tuple
from block import Block
from blockset import BlockSet
import re

class Level:
    """关卡类"""
    
    def __init__(self, level_id: str, name: str, constraints: List[str], blocks: List[Block], 
                 instruction: str = "", margin_top: int = 4, margin_bottom: int = 4, 
                 margin_left: int = 4, margin_right: int = 4):
        """
        初始化关卡
        
        Args:
            level_id: 关卡ID (如 "1-1")
            name: 关卡名称
            constraints: 限制条件列表
            blocks: 方块列表
            instruction: 关卡说明
            margin_top: 上方预留空白
            margin_bottom: 下方预留空白
            margin_left: 左侧预留空白
            margin_right: 右侧预留空白
        """
        self.level_id = level_id
        self.name = name
        self.constraints = constraints
        self.blocks = blocks
        self.instruction = instruction
        self.completed = False
        self.margin_top = margin_top
        self.margin_bottom = margin_bottom
        self.margin_left = margin_left
        self.margin_right = margin_right
        self.max_rect = self._calc_max_rect()
        
    def create_blockset(self) -> BlockSet:
        """
        创建关卡对应的方块集合
        
        Returns:
            BlockSet: 方块集合
        """
        blockset = BlockSet()
        for block in self.blocks:
            blockset.add_block(block)
        return blockset

    def _calc_max_rect(self):
        if not self.blocks:
            return (1, 1)
        min_x = min(b.pos[0] for b in self.blocks)
        max_x = max(b.pos[0] for b in self.blocks)
        min_y = min(b.pos[1] for b in self.blocks)
        max_y = max(b.pos[1] for b in self.blocks)
        width = max_x - min_x + 1
        height = max_y - min_y + 1
        return (width, height)

class Scope:
    """大关类"""
    
    def __init__(self, scope_id: int, name: str, total_levels: int):
        """
        初始化大关
        
        Args:
            scope_id: 大关ID
            name: 大关名称
            total_levels: 总关卡数
        """
        self.scope_id = scope_id
        self.name = name
        self.total_levels = total_levels
        self.levels: List[Level] = []
        self.completed_levels = 0
        
    def add_level(self, level: Level):
        """
        添加关卡
        
        Args:
            level: 关卡对象
        """
        self.levels.append(level)
        
    def get_completion_ratio(self) -> Tuple[int, int]:
        """
        获取完成比例
        
        Returns:
            Tuple[int, int]: (已完成关卡数, 总关卡数)
        """
        completed = sum(1 for level in self.levels if level.completed)
        return completed, len(self.levels)

class LevelParser:
    """关卡解析器"""
    
    def __init__(self):
        """初始化关卡解析器"""
        self.scopes: List[Scope] = []
        self.level_contents = {}  # 缓存关卡原始内容
        
    def parse_levels_file(self, file_path: str) -> List[Scope]:
        """
        解析levels.txt文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            List[Scope]: 大关列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"警告: 找不到文件 {file_path}")
            return self._create_default_levels()
            
        # 分割大关
        scope_sections = re.split(r'scope=\d+;', content)[1:]  # 跳过第一个空字符串
        scope_headers = re.findall(r'scope=(\d+);', content)
        
        for i, (header, section) in enumerate(zip(scope_headers, scope_sections)):
            scope_id = int(header)
            
            # 解析大关信息
            scope_info_match = re.search(r"scope_name='([^']+)'; total_levels=(\d+);", section)
            if scope_info_match:
                scope_name = scope_info_match.group(1)
                total_levels = int(scope_info_match.group(2))
                
                scope = Scope(scope_id, scope_name, total_levels)
                
                # 解析关卡
                level_sections = re.findall(r'begin level (\d+)\n(.*?)end level \d+', section, re.DOTALL)
                
                for level_num, level_content in level_sections:
                    level = self._parse_level(scope_id, int(level_num), level_content)
                    if level:
                        scope.add_level(level)
                        
                self.scopes.append(scope)
                
        return self.scopes
        
    def _parse_level(self, scope_id: int, level_num: int, content: str) -> Level:
        """
        解析单个关卡
        
        Args:
            scope_id: 大关ID
            level_num: 关卡编号
            content: 关卡内容
            
        Returns:
            Level: 关卡对象
        """
        level_id = f"{scope_id}-{level_num}"
        self.level_contents[level_id] = content  # 缓存关卡内容

        # 解析限制条件
        constraints = []
        constraint_matches = re.findall(r'limit (\w+)', content)
        constraints.extend(constraint_matches)
        
        # 解析关卡说明
        instruction = ""
        instruction_match = re.search(r'instruction "(.*?)"', content, re.DOTALL)
        if instruction_match:
            instruction = instruction_match.group(1).replace('\\n', '\n')
        
        # 解析边界参数
        margin_top = 4
        margin_bottom = 4
        margin_left = 4
        margin_right = 4
        
        margin_match = re.search(r'margin\{top=(\d+),bottom=(\d+),left=(\d+),right=(\d+)\}', content)
        if margin_match:
            margin_top = int(margin_match.group(1))
            margin_bottom = int(margin_match.group(2))
            margin_left = int(margin_match.group(3))
            margin_right = int(margin_match.group(4))
        
        # 解析方块
        blocks = []
        block_matches = re.findall(r'block\{type=(\d+),pos=\(([^)]+)\)(?:,detailed_information=\[([\d, ]*)\])?\}', content)
        
        for block_match in block_matches:
            block_type_str, pos_str = block_match[0], block_match[1]
            detailed_info_str = block_match[2] if len(block_match) > 2 and block_match[2] else ""
            
            block_type = int(block_type_str)
            pos_parts = pos_str.split(',')
            pos = (int(pos_parts[0]), int(pos_parts[1]))
            
            # 解析详细信息
            detailed_information = []
            if detailed_info_str:
                try:
                    detailed_information = [int(x.strip()) for x in detailed_info_str.split(',') if x.strip()]
                except ValueError:
                    # 如果解析失败，使用空列表
                    detailed_information = []
            
            block = Block(block_type=block_type, pos=pos, detailed_information=detailed_information)
            blocks.append(block)
            
        return Level(level_id, f"关卡 {level_id}", constraints, blocks, instruction,
                    margin_top, margin_bottom, margin_left, margin_right)
        
    def get_level(self, level_id: str) -> Level:
        """通过关卡ID获取新的关卡实例"""
        if level_id not in self.level_contents:
            return None
        scope_id, level_num = map(int, level_id.split('-'))
        return self._parse_level(scope_id, level_num, self.level_contents[level_id])

    def _create_default_levels(self) -> List[Scope]:
        """
        创建默认关卡（当文件不存在时）
        
        Returns:
            List[Scope]: 默认大关列表
        """
        # 创建示例关卡
        scope1 = Scope(1, "基础关卡", 3)
        
        # 关卡1-1：简单方块
        blocks_1_1 = [
            Block(1, (0, 0)), Block(1, (1, 0)), Block(1, (2, 0)),
            Block(1, (0, 1)), Block(1, (1, 1)), Block(1, (2, 1))
        ]
        level_1_1 = Level("1-1", "关卡 1-1", ["glue"], blocks_1_1)
        scope1.add_level(level_1_1)
        
        # 关卡1-2：对称图形
        blocks_1_2 = [
            Block(1, (0, 0)), Block(1, (1, 0)), Block(1, (2, 0)),
            Block(1, (0, 1)), Block(1, (2, 1))
        ]
        level_1_2 = Level("1-2", "关卡 1-2", ["mirror"], blocks_1_2)
        scope1.add_level(level_1_2)
        
        # 关卡1-3：复杂图形
        blocks_1_3 = [
            Block(1, (0, 0)), Block(1, (1, 0)), Block(1, (2, 0)),
            Block(1, (0, 1)), Block(1, (1, 1)), Block(1, (2, 1)),
            Block(1, (1, 2))
        ]
        level_1_3 = Level("1-3", "关卡 1-3", ["glue", "mirror"], blocks_1_3)
        scope1.add_level(level_1_3)
        
        return [scope1]
        
    def get_scope_by_id(self, scope_id: int) -> Scope:
        """
        根据ID获取大关
        
        Args:
            scope_id: 大关ID
            
        Returns:
            Scope: 大关对象
        """
        for scope in self.scopes:
            if scope.scope_id == scope_id:
                return scope
        return None
        
    def get_level_by_id(self, level_id: str) -> Level:
        """
        根据ID获取关卡
        
        Args:
            level_id: 关卡ID (如 "1-1")
            
        Returns:
            Level: 关卡对象
        """
        scope_id, level_num = map(int, level_id.split('-'))
        scope = self.get_scope_by_id(scope_id)
        if scope and 0 <= level_num - 1 < len(scope.levels):
            return scope.levels[level_num - 1]
        return None