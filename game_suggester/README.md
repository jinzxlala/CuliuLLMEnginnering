# game_suggester

基于 `game_coach_game` 的课堂实验项目：输入房间号，读取快照，生成并验证“下一步建议”。

## 1. 已实现功能

- 输入游戏服务地址、账号、密码、房间号后，一键生成建议。
- 后端先调用 `GET /api/coach/snapshot/<room_code>` 获取对局快照。
- 使用 Prompt + Ollama（默认 `qwen3.5:0.8b`）生成候选走法。
- 对每条候选调用 `POST /api/coach/evaluate_move` 验证合法性与影响。
- 输出最终建议（位置、输入值、理由、风险、置信度）与备选建议。
- 当模型不可用或输出异常时，自动切换到规则启发式兜底。

## 2. 游戏机制总结（基于源码与接口）

- 棋盘为 `rows x cols`，轮流在空格子输入数字或 `X`。
- 合法性：同一行/列的数字不能重复；`X` 可重复。
- 计分触发：只有当某一整行或整列填满时才触发计分。
- 计分逻辑：令该线非 `X` 数字个数为 `n`，若线中存在值等于 `n` 的格子，则该格所属玩家可得 `n` 分（每玩家每线最多一次）。
- 教练评估接口会返回：`isLegal`、`reason`、`scoreDelta`、`nextTurn`、`turnSkipped`。

## 3. 目录结构

```text
game_suggester/
├─ app.py
├─ templates/
│  └─ index.html
├─ static/
│  └─ app.js
├─ prompts/
│  └─ suggest_prompt.md
├─ logs/
│  └─ test_log.md
└─ README.md
```

## 4. 运行方式

在仓库根目录执行：

```bash
python game_suggester/app.py
```

打开：

- `http://127.0.0.1:5001`

默认页面已预填：

- 服务地址：`http://127.0.0.1:5000`
- 房间号：`1E4E9F`
- 模型：`qwen3.5:0.8b`

## 5. API

### `POST /api/suggest`

请求体示例：

```json
{
  "gameBaseUrl": "http://127.0.0.1:5000",
  "username": "test1",
  "password": "1111",
  "roomCode": "1E4E9F",
  "model": "qwen3.5:0.8b",
  "maxCandidates": 6
}
```

返回字段包含：

- `snapshotMeta`
- `bestSuggestion`（含位置/输入值/理由/风险/置信度/验证结果）
- `alternatives`
- `warnings`

## 6. Prompt 设计要点

- 角色：游戏建议助手。
- 任务：给出下一步候选。
- 状态输入：来自 `snapshot`。
- 固定输出：严格 JSON `candidates`。
- 展示前：每条候选都经过 `evaluate_move` 二次验证。

详细 Prompt 见：`prompts/suggest_prompt.md`。

