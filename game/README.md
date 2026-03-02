# 数字预言家课堂版

本目录用于课堂实操，支持学生联机对战与规则验证。

## 1. 运行方式

## 环境要求
- Python 3.9+
- 依赖：`flask`

## 安装依赖
```bash
pip install flask
```

## 启动服务
在当前目录运行：
```bash
python app.py
```

启动后可访问：
- 本地：`http://127.0.0.1:5000`
- 局域网：终端会打印对应地址

## 默认账号
- `player1 / a`
- `player2 / b`
- `player3 / c`

---

## 2. 目录说明

- `app.py`：后端服务
- `templates/index.html`：页面模板
- `static/`：前端脚本与样式
- `game_data.json`：用户积分/战绩数据

---

## 3. API 说明

说明：
- 大部分接口需要先登录
- 返回格式统一为：
  - 成功：`{ "success": true, ... }`
  - 失败：`{ "success": false, "errorCode": "ERR_XXX", "message": "..." }`

## 3.1 用户相关

### `POST /api/login`
- 功能：登录
- 请求体：
```json
{
  "username": "player1",
  "password": "a"
}
```

### `POST /api/register`
- 功能：注册
- 请求体：
```json
{
  "username": "new_user",
  "password": "123456",
  "confirmPassword": "123456"
}
```

### `POST /api/logout`
- 功能：退出登录

### `GET /api/current_user`
- 功能：获取当前登录用户

### `GET /api/user_points`
- 功能：查询当前用户积分

### `POST /api/update_points`
- 功能：设置当前用户积分
- 请求体：
```json
{
  "points": 1000
}
```

### `POST /api/deduct_points`
- 功能：扣除积分
- 请求体：
```json
{
  "amount": 50
}
```

---

## 3.2 房间相关

### `POST /api/create_room`
- 功能：创建房间
- 请求体：
```json
{
  "roomCode": "ABC123",
  "rows": 5,
  "cols": 8
}
```
- `roomCode` 可留空自动生成，且必须为 6 位

### `POST /api/join_room`
- 功能：加入房间
- 请求体：
```json
{
  "roomCode": "ABC123"
}
```

### `GET /api/room_status/<room_code>`
- 功能：查看房间状态

### `GET /api/room_info/<room_code>`
- 功能：查看房间玩家信息

### `POST /api/cancel_room/<room_code>`
- 功能：房主取消房间

---

## 3.3 颜色与游戏状态

### `POST /api/select_color`
- 功能：选择玩家颜色
- 请求体：
```json
{
  "roomCode": "ABC123",
  "color": "red"
}
```

### `GET /api/color_status/<room_code>`
- 功能：查看双方颜色选择状态

### `GET /api/game/<room_code>`
- 功能：获取当前对局状态

---

## 3.4 对局动作

### `POST /api/game/<room_code>/move`
- 功能：落子
- 请求体：
```json
{
  "row": 0,
  "col": 1,
  "value": "5",
  "color": "red"
}
```
- 规则要点：
  - 同一行/列数字不可重复
  - `X` 可重复
  - 非当前回合无法落子

### `POST /api/game/<room_code>/apply_card`
- 功能：使用卡牌
- 请求体：
```json
{
  "card_type": "double_score"
}
```
- 可选：`double_score` / `skip_turn` / `change_number`

### `POST /api/game/<room_code>/change_move`
- 功能：修改自己已落子的格子
- 请求体：
```json
{
  "row": 0,
  "col": 1,
  "value": "6"
}
```

### `POST /api/game/<room_code>/end`
- 功能：手动结束游戏

### `GET /api/leaderboard`
- 功能：查看排行榜

### `GET /api/replay/<game_id>`
- 功能：查看某局事件回放

---

## 3.5 教练接口

### `GET /api/coach/snapshot/<room_code>`
- 功能：导出教练输入快照

### `POST /api/coach/evaluate_move`
- 功能：评估某步是否合法与可能影响
- 请求体：
```json
{
  "roomCode": "ABC123",
  "row": 0,
  "col": 1,
  "value": "5"
}
```

---

## 4. Agent/MCP 扩展说明

本 Demo 默认只用于纯游戏和基础教练评估。

- `agent_mcp_extension.py` 不在本目录
- 即使你设置了 `ENABLE_AGENT_MCP_EXTENSION=1`，主服务也会保持可启动；扩展缺失只会告警，不阻断运行

---

## 5. 常见错误码
- `ERR_NOT_LOGGED_IN`：未登录
- `ERR_ROOM_NOT_FOUND`：房间不存在
- `ERR_GAME_NOT_FOUND`：游戏不存在
- `ERR_NOT_YOUR_TURN`：不是你的回合
- `ERR_CELL_OCCUPIED`：格子已被填充
- `ERR_INVALID_MOVE_RULE`：违反行/列数字规则
- `ERR_INVALID_POSITION`：坐标越界或非法
- `ERR_INVALID_VALUE`：输入值非法

