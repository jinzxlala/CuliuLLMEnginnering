from typing import Dict, List, Optional


def get_rules() -> str:
    return (
        "规则: 同行同列数字不可重复; X 可重复; "
        "仅行/列填满时触发计分; 非当前回合不能落子。"
    )


def evaluate_move(
    grid: List[List[Optional[str]]], row: int, col: int, value: str
) -> Dict:
    if row < 0 or col < 0 or row >= len(grid) or col >= len(grid[0]):
        return {"isLegal": False, "reason": "坐标越界", "reasonCode": "INVALID_POSITION"}
    if grid[row][col] is not None:
        return {"isLegal": False, "reason": "格子已占用", "reasonCode": "CELL_OCCUPIED"}
    if value.lower() == "x":
        return {"isLegal": True, "reason": "合法", "reasonCode": "OK"}
    for c, cell in enumerate(grid[row]):
        if c != col and cell is not None and str(cell) == str(value):
            return {"isLegal": False, "reason": "同行重复", "reasonCode": "ROW_DUPLICATE"}
    for r in range(len(grid)):
        cell = grid[r][col]
        if r != row and cell is not None and str(cell) == str(value):
            return {"isLegal": False, "reason": "同列重复", "reasonCode": "COL_DUPLICATE"}
    return {"isLegal": True, "reason": "合法", "reasonCode": "OK"}
