from typing import List, Tuple, Dict, Any
from blockset import BlockSet
from block import Block
import math
from typing import List, Dict

class ConstraintChecker:
    """限制条件检查器"""
    
    def __init__(self):
        """初始化限制条件检查器"""
        self.constraints = {
            'glue': self._check_glue,
            'mirror': self._check_mirror,
            'symmetry': self._check_symmetry,
            'pyramid': self._check_pyramid,
            'sail': self._check_sail
        }
        
    def check_constraints(self, blockset: BlockSet, constraint_names: List[str], stage: str) -> Dict[str, bool]:
        """
        检查所有限制条件
        
        Args:
            blockset: 方块集合
            constraint_names: 限制条件名称列表
            stage: 当前阶段，可选值为'selection'或'movement'
            
        Returns:
            Dict[str, bool]: 每个限制条件的检查结果
        """
        results = {}
        for constraint_name in constraint_names:
            # 根据阶段筛选约束检查
            if constraint_name in self.constraints:
                results[constraint_name] = self.constraints[constraint_name](blockset)
            else:
                # 未知的限制条件默认为通过
                results[constraint_name] = True
            if constraint_name == 'mirror' and stage == 'selection':
                results[constraint_name] = True
            if constraint_name == 'glue' and stage == 'movement':
                results[constraint_name] = True
            if constraint_name == 'pyramid' and stage == 'selection':
                results[constraint_name] = self._check_pyramid_selection(blockset)
            if constraint_name == 'pyramid' and stage == 'movement':
                results[constraint_name] = self._check_pyramid_movement(blockset)
            if constraint_name == 'sail' and stage == 'movement':
                results[constraint_name] = self._check_sail(blockset)
            if constraint_name == 'sail' and stage == 'selection':
                results[constraint_name] = True
        return results
        
    def _check_glue(self, blockset: BlockSet) -> bool:
        """
        检查胶水限制：选中的方块需要非空且是连通的
        
        Args:
            blockset: 方块集合
            
        Returns:
            bool: 是否满足胶水限制
        """
        if not blockset.get_all_positions():
            return False
        return blockset.is_connected()
        
    def _check_mirror(self, blockset: BlockSet) -> bool:
        """
        检查镜子限制：所得图形需要是轴对称图形
        
        Args:
            blockset: 方块集合
            
        Returns:
            bool: 是否满足镜子限制
        """
        blocks = blockset.blocks
        if len(blocks) <= 1:
            return True
        
        # 检查所有对称类型
        return (self._is_horizontally_symmetric_blocks(blocks) or
                self._is_vertically_symmetric_blocks(blocks) or
                self._is_diagonal1_symmetric_blocks(blocks) or
                self._is_diagonal2_symmetric_blocks(blocks))
        
    def _is_diagonal1_symmetric_blocks(self, blocks: List[Block]) -> bool:
        """
        检查是否左上-右下斜轴对称（基于方块类型）
        
        Args:
            blocks: 方块列表
            
        Returns:
            bool: 是否斜轴对称
        """
        if not blocks:
            return True
            
        positions = [block.pos for block in blocks]
        
        # 计算对角线中心
        d_values = [x - y for x, y in positions]
        center_d = (min(d_values) + max(d_values)) / 2
        
        # 创建位置到方块的映射
        pos_to_block = {block.pos: block for block in blocks}
        
        for block in blocks:
            x, y = block.pos
            x_sym = y + center_d
            y_sym = x - center_d
            
            # 对称点必须是整数坐标
            if not (x_sym.is_integer() and y_sym.is_integer()):
                return False
                
            sym_pos = (int(x_sym), int(y_sym))
            
            # 检查对称位置是否存在
            if sym_pos not in pos_to_block:
                return False
                
            # 检查方块类型是否匹配
            symmetric_block = pos_to_block[sym_pos]
            if block.type != symmetric_block.type:
                return False
                
        return True
        
    def _is_diagonal2_symmetric_blocks(self, blocks: List[Block]) -> bool:
        """
        检查是否左下-右上斜轴对称（基于方块类型）
        
        Args:
            blocks: 方块列表
            
        Returns:
            bool: 是否斜轴对称
        """
        if not blocks:
            return True
            
        positions = [block.pos for block in blocks]
        
        # 计算对角线中心
        s_values = [x + y for x, y in positions]
        center_s = (min(s_values) + max(s_values)) / 2
        
        # 创建位置到方块的映射
        pos_to_block = {block.pos: block for block in blocks}
        
        for block in blocks:
            x, y = block.pos
            x_sym = center_s - y
            y_sym = center_s - x
            
            # 对称点必须是整数坐标
            if not (x_sym.is_integer() and y_sym.is_integer()):
                return False
                
            sym_pos = (int(x_sym), int(y_sym))
            
            # 检查对称位置是否存在
            if sym_pos not in pos_to_block:
                return False
                
            # 检查方块类型是否匹配
            symmetric_block = pos_to_block[sym_pos]
            if block.type != symmetric_block.type:
                return False
                
        return True
            
        # 检查水平轴对称
        if self._is_horizontally_symmetric(positions):
            return True
            
        # 检查垂直轴对称
        if self._is_vertically_symmetric(positions):
            return True
            
        # 检查左上-右下斜轴对称
        if self._is_diagonal1_symmetric(positions):
            return True
            
        # 检查左下-右上斜轴对称
        if self._is_diagonal2_symmetric(positions):
            return True
            
        return False
        
    def _check_symmetry(self, blockset: BlockSet) -> bool:
        """
        检查对称性限制（与镜子相同）
        
        Args:
            blockset: 方块集合
            
        Returns:
            bool: 是否满足对称性限制
        """
        return self._check_mirror(blockset)
        
    def _is_horizontally_symmetric_blocks(self, blocks: List[Block]) -> bool:
        """
        检查是否水平轴对称（基于方块类型）
        
        Args:
            blocks: 方块列表
            
        Returns:
            bool: 是否水平轴对称
        """
        if not blocks:
            return True
            
        positions = [block.pos for block in blocks]
        
        # 计算中心线
        x_coords = [pos[0] for pos in positions]
        center_x = (min(x_coords) + max(x_coords)) / 2
        
        # 创建位置到方块的映射
        pos_to_block = {block.pos: block for block in blocks}
        
        # 检查每个方块是否有对称的同类型方块
        for block in blocks:
            x, y = block.pos
            symmetric_x = 2 * center_x - x
            symmetric_pos = (int(symmetric_x), y)
            
            # 检查对称位置是否存在
            if symmetric_pos not in pos_to_block:
                return False
                
            # 检查方块类型是否匹配
            symmetric_block = pos_to_block[symmetric_pos]
            if block.type != symmetric_block.type:
                # 对于金字塔方块，需要检查是否是轴对称对应的方块
                if block.type == 3 and symmetric_block.type == 3:
                    # 检查金字塔方块的轴对称对应关系
                    # 水平轴对称时，上下面对调
                    if len(block.detailed_information) >= 4 and len(symmetric_block.detailed_information) >= 4:
                        if block.detailed_information[0] != symmetric_block.detailed_information[1] or \
                           block.detailed_information[1] != symmetric_block.detailed_information[0] or \
                           block.detailed_information[2] != symmetric_block.detailed_information[2] or \
                           block.detailed_information[3] != symmetric_block.detailed_information[3]:
                            return False
                else:
                    return False
                
        return True
        
    def _is_vertically_symmetric_blocks(self, blocks: List[Block]) -> bool:
        """
        检查是否垂直轴对称（基于方块类型）
        
        Args:
            blocks: 方块列表
            
        Returns:
            bool: 是否垂直轴对称
        """
        if not blocks:
            return True
            
        positions = [block.pos for block in blocks]
        
        # 计算中心线
        y_coords = [pos[1] for pos in positions]
        center_y = (min(y_coords) + max(y_coords)) / 2
        
        # 创建位置到方块的映射
        pos_to_block = {block.pos: block for block in blocks}
        
        # 检查每个方块是否有对称的同类型方块
        for block in blocks:
            x, y = block.pos
            symmetric_y = 2 * center_y - y
            symmetric_pos = (x, int(symmetric_y))
            
            # 检查对称位置是否存在
            if symmetric_pos not in pos_to_block:
                return False
                
            # 检查方块类型是否匹配
            symmetric_block = pos_to_block[symmetric_pos]
            if block.type != symmetric_block.type:
                # 对于金字塔方块，需要检查是否是轴对称对应的方块
                if block.type == 3 and symmetric_block.type == 3:
                    # 检查金字塔方块的轴对称对应关系
                    # 垂直轴对称时，左右面对调
                    if len(block.detailed_information) >= 4 and len(symmetric_block.detailed_information) >= 4:
                        if block.detailed_information[0] != symmetric_block.detailed_information[0] or \
                           block.detailed_information[1] != symmetric_block.detailed_information[1] or \
                           block.detailed_information[2] != symmetric_block.detailed_information[3] or \
                           block.detailed_information[3] != symmetric_block.detailed_information[2]:
                            return False
                else:
                    return False
                
        return True
        
    def get_constraint_display_name(self, constraint_name: str) -> str:
        """
        获取限制条件的显示名称
        
        Args:
            constraint_name: 限制条件名称
            
        Returns:
            str: 显示名称
        """
        display_names = {
            'glue': '胶水',
            'mirror': '镜子',
            'symmetry': '对称',
            'pyramid': '金字塔',
            'sail': '航行'
        }
        return display_names.get(constraint_name, constraint_name)
        
    def get_constraint_description(self, constraint_name: str) -> str:
        """
        获取限制条件的详细描述
        
        Args:
            constraint_name: 限制条件名称
            
        Returns:
            str: 详细描述
        """
        descriptions = {
            'glue': '选中的方块需要非空且连通',
            'mirror': '所得图形需要是轴对称图形',
            'symmetry': '所得图形需要是轴对称图形',
            'pyramid': '金字塔方块的每面必须和同\n色内容紧邻',
            'sail': '所有的海洋方块必须连通'
        }
        return descriptions.get(constraint_name, constraint_name)
        
    def _check_sail(self, blockset: BlockSet) -> bool:
        '''航行限制连通性检查（移动阶段专用）'''
        from collections import deque

        # 获取所有相关方块
        nodes = [
            cell for cell in blockset.blocks
            if cell.type == 2 or (cell.type == 3 and any(d == 2 for d in cell.detailed_information))
        ]
        nodes = []
        for cell in blockset.blocks:
            if cell.type == 2:
                nodes.append(cell.pos)
            if cell.type == 3 and cell.detailed_information[0] == 2:
                nodes.append((cell.pos[0] , cell.pos[1] - 0.4))
            if cell.type == 3 and cell.detailed_information[1] == 2:
                nodes.append((cell.pos[0] , cell.pos[1] + 0.4))
            if cell.type == 3 and cell.detailed_information[2] == 2:
                nodes.append((cell.pos[0] - 0.4 , cell.pos[1]))
            if cell.type == 3 and cell.detailed_information[3] == 2:
                nodes.append((cell.pos[0] + 0.4 , cell.pos[1]))
        if len(nodes) < 2:
            return True

        # 构建邻接表
        adjacency = {point: [] for point in nodes}
        for point in nodes:
            for neighbor in nodes:
                if (point[0] - neighbor[0]) ** 2 + (point[1] - neighbor[1]) ** 2 <= 0.61 ** 2:
                    adjacency[point].append(neighbor)
                elif point[0] == int(point[0]) and point[1] == int(point[1]):
                    if (point[0] - neighbor[0]) ** 2 + (point[1] - neighbor[1]) ** 2 == 1:
                        adjacency[point].append(neighbor)
            

        # BFS检查连通性
        visited = set()
        queue = deque([nodes[0]])
        while queue:
            current = queue.popleft()
            if current not in visited:
                visited.add(current)
                queue.extend([n for n in adjacency[current] if n not in visited])

        return len(visited) == len(nodes)

    def _check_pyramid(self, blockset: BlockSet) -> bool:
        """
        检查金字塔限制：金字塔方块的每面必须和同色内容紧邻
        
        Args:
            blockset: 方块集合
            
        Returns:
            bool: 是否满足金字塔限制
        """
        # 这个方法在选择阶段和移动阶段有不同的检查逻辑
        # 在这里我们只实现移动阶段的检查
        return self._check_pyramid_movement(blockset)
    
    def _check_pyramid_selection(self, blockset: BlockSet) -> bool:
        """
        检查金字塔限制（选择阶段）：只检查blockset中被选中的那些方块里，
        是否存在pyramid和一个错误的被选中的方块相邻
        
        Args:
            blockset: 方块集合
            
        Returns:
            bool: 是否满足金字塔限制
        """
        # 获取所有选中的方块
        selected_blocks = [block for block in blockset.blocks if block.selected]
        
        # 如果没有选中的方块或没有金字塔方块，直接返回True
        if not selected_blocks:
            return True
        
        # 创建位置到方块的映射
        pos_to_block = {block.pos: block for block in selected_blocks}
        
        # 检查每个选中的金字塔方块
        for block in selected_blocks:
            if block.type == 3 and len(block.detailed_information) >= 4:
                # 获取金字塔各面的颜色要求
                top_req = block.detailed_information[0]
                bottom_req = block.detailed_information[1]
                left_req = block.detailed_information[2]
                right_req = block.detailed_information[3]
                
                x, y = block.pos
                
                # 检查上方面邻接方块
                top_pos = (x, y - 1)
                if not self._check_pyramid_adjacent(top_pos, top_req, pos_to_block, False, "top"):
                    return False
                
                # 检查下方面邻接方块
                bottom_pos = (x, y + 1)
                if not self._check_pyramid_adjacent(bottom_pos, bottom_req, pos_to_block, False, "bottom"):
                    return False
                
                # 检查左方面邻接方块
                left_pos = (x - 1, y)
                if not self._check_pyramid_adjacent(left_pos, left_req, pos_to_block, False, "left"):
                    return False
                
                # 检查右方面邻接方块
                right_pos = (x + 1, y)
                if not self._check_pyramid_adjacent(right_pos, right_req, pos_to_block, False, "right"):
                    return False
        
        return True
    
    def _check_pyramid_movement(self, blockset: BlockSet) -> bool:
        """
        检查金字塔限制（移动阶段）：检查整个图像是否符合pyramid限制
        
        Args:
            blockset: 方块集合
            
        Returns:
            bool: 是否满足金字塔限制
        """
        # 获取所有方块
        blocks = blockset.blocks
        
        # 如果没有方块或没有金字塔方块，直接返回True
        if not blocks:
            return True
        
        # 创建位置到方块的映射
        pos_to_block = {block.pos: block for block in blocks}
        
        # 检查每个金字塔方块
        for block in blocks:
            if block.type == 3 and len(block.detailed_information) >= 4:
                # 获取金字塔各面的颜色要求
                top_req = block.detailed_information[0]
                bottom_req = block.detailed_information[1]
                left_req = block.detailed_information[2]
                right_req = block.detailed_information[3]
                
                x, y = block.pos
                
                # 检查上方面邻接方块
                top_pos = (x, y - 1)
                if not self._check_pyramid_adjacent(top_pos, top_req, pos_to_block, True, "top"):
                    return False
                
                # 检查下方面邻接方块
                bottom_pos = (x, y + 1)
                if not self._check_pyramid_adjacent(bottom_pos, bottom_req, pos_to_block, True, "bottom"):
                    return False
                
                # 检查左方面邻接方块
                left_pos = (x - 1, y)
                if not self._check_pyramid_adjacent(left_pos, left_req, pos_to_block, True, "left"):
                    return False
                
                # 检查右方面邻接方块
                right_pos = (x + 1, y)
                if not self._check_pyramid_adjacent(right_pos, right_req, pos_to_block, True, "right"):
                    return False
        
        return True
    
    def _check_pyramid_adjacent(self, pos: tuple, requirement: int, pos_to_block: dict, is_movement_stage: bool = False, face_checked: str = "") -> bool:
        """
        检查金字塔某一面的邻接方块是否符合要求
        
        Args:
            pos: 邻接位置
            requirement: 颜色要求（0为白色，1为黑色，2为蓝色）
            pos_to_block: 位置到方块的映射
            is_movement_stage: 是否为移动阶段
            face_checked: 检查的是哪一面（"top", "bottom", "left", "right"）
            
        Returns:
            bool: 是否符合要求
        """
        # 如果要求为0（白色），表示不相邻方块
        if requirement == 0 and pos not in pos_to_block:
            return True
        
        # 如果要求为有色，检查邻接位置是否存在对应颜色的方块或金字塔的同色面
        if pos in pos_to_block:
            adjacent_block = pos_to_block[pos]
            # 如果邻接方块是普通方块，检查类型是否匹配
            if adjacent_block.type in [1, 2]:
                # 1为黑色，2为蓝色
                return (requirement == 1 and adjacent_block.type == 1) or \
                       (requirement == 2 and adjacent_block.type == 2)
            # 如果邻接方块是金字塔方块，检查对应面的颜色
            elif adjacent_block.type == 3 and len(adjacent_block.detailed_information) >= 4:
                # 根据相对位置确定邻接方块的哪一面

                if face_checked == "bottom":  # 当前方块在邻接方块下方
                    adjacent_face_color = adjacent_block.detailed_information[0]  # 上面
                elif face_checked == "top":  # 当前方块在邻接方块上方
                    adjacent_face_color = adjacent_block.detailed_information[1]  # 下面
                elif face_checked == "right":  # 当前方块在邻接方块右方
                    adjacent_face_color = adjacent_block.detailed_information[2]  # 左面
                elif face_checked == "left": # 当前方块在邻接方块左方
                    adjacent_face_color = adjacent_block.detailed_information[3]  # 右面
                else:
                    # 未知的相对位置，返回False
                    return False
                
                # 检查邻接方块的对应面颜色是否与要求一致
                return adjacent_face_color == requirement
        else:
            # 如果邻接位置没有方块（空气），在选择阶段认为是通过的
            # 在移动阶段需要进一步检查
            if is_movement_stage:
                # 在移动阶段，如果检查的是特定面且要求为有色，则需要进一步检查
                if face_checked in ["top", "bottom", "left", "right"] and requirement != 0:
                    return False
            return True
        
        # 其他情况不符合要求
        return False