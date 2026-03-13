from flask import jsonify, request, session
import os
import json
import time


def register_agent_mcp_routes(app, deps):
    games_db = deps['games_db']
    rules_version = deps['RULES_VERSION']
    error_response = deps['error_response']
    build_game_snapshot = deps['build_game_snapshot']
    ensure_game_meta = deps['ensure_game_meta']
    validate_position = deps['validate_position']
    validate_move = deps['validate_move']
    score_move_simulation = deps['score_move_simulation']

    reports_dir = "reports"
    os.makedirs(reports_dir, exist_ok=True)
    runtime_metrics_file = os.path.join(reports_dir, "runtime_metrics.json")
    tool_whitelist = {
        'get_game_state',
        'evaluate_move',
        'list_legal_moves',
        'explain_scoring'
    }

    def _default_runtime_metrics():
        return {
            'rulesVersion': rules_version,
            'updatedAt': time.time(),
            'counters': {
                'coachToolCalls': 0,
                'coachToolFailures': 0,
                'coachEvalTotal': 0,
                'coachEvalLegal': 0
            },
            'derived': {
                'coachLegalRate': 0.0,
                'coachToolFailureRate': 0.0
            },
            'perTool': {}
        }

    runtime_metrics = _default_runtime_metrics()
    if os.path.exists(runtime_metrics_file):
        try:
            with open(runtime_metrics_file, 'r', encoding='utf-8') as f:
                runtime_metrics = json.load(f)
        except Exception:
            runtime_metrics = _default_runtime_metrics()

    def save_runtime_metrics():
        runtime_metrics['updatedAt'] = time.time()
        counters = runtime_metrics['counters']
        eval_total = counters.get('coachEvalTotal', 0)
        tool_calls = counters.get('coachToolCalls', 0)
        runtime_metrics['derived']['coachLegalRate'] = (
            counters.get('coachEvalLegal', 0) / eval_total if eval_total else 0.0
        )
        runtime_metrics['derived']['coachToolFailureRate'] = (
            counters.get('coachToolFailures', 0) / tool_calls if tool_calls else 0.0
        )
        with open(runtime_metrics_file, 'w', encoding='utf-8') as f:
            json.dump(runtime_metrics, f, ensure_ascii=False, indent=2)

    def record_tool_call(tool_name, success=True):
        counters = runtime_metrics['counters']
        counters['coachToolCalls'] = counters.get('coachToolCalls', 0) + 1
        if not success:
            counters['coachToolFailures'] = counters.get('coachToolFailures', 0) + 1
        per_tool = runtime_metrics.setdefault('perTool', {}).setdefault(
            tool_name,
            {'calls': 0, 'failures': 0}
        )
        per_tool['calls'] += 1
        if not success:
            per_tool['failures'] += 1
        save_runtime_metrics()

    def record_eval_result(is_legal):
        counters = runtime_metrics['counters']
        counters['coachEvalTotal'] = counters.get('coachEvalTotal', 0) + 1
        if is_legal:
            counters['coachEvalLegal'] = counters.get('coachEvalLegal', 0) + 1
        save_runtime_metrics()

    def get_player_turn_by_username(game, username):
        if username == game['player1']:
            return 'player1'
        if username == game['player2']:
            return 'player2'
        return None

    def list_legal_moves_for_player(game, player_turn, limit=20):
        candidate_values = [str(i) for i in range(1, 10)] + ['X']
        results = []
        rows = len(game['grid'])
        cols = len(game['grid'][0])
        for r in range(rows):
            for c in range(cols):
                if game['grid'][r][c] is not None:
                    continue
                for value in candidate_values:
                    is_valid, _ = validate_move(game, r, c, value, player_turn)
                    if not is_valid:
                        continue
                    score_delta, _, skipped = score_move_simulation(game, r, c, value, player_turn)
                    results.append({
                        'row': r,
                        'col': c,
                        'value': value,
                        'scoreDelta': score_delta,
                        'turnSkipped': skipped
                    })
                    if len(results) >= limit:
                        return results
        return results

    @app.route('/api/coach/tools', methods=['GET'])
    def coach_tools():
        username = session.get('username')
        if not username:
            return error_response('ERR_NOT_LOGGED_IN', '请先登录')
        return jsonify({
            'success': True,
            'tools': sorted(list(tool_whitelist)),
            'rulesVersion': rules_version
        })

    @app.route('/api/coach/tool_call', methods=['POST'])
    def coach_tool_call():
        username = session.get('username')
        if not username:
            return error_response('ERR_NOT_LOGGED_IN', '请先登录')

        data = request.json or {}
        tool = data.get('tool')
        args = data.get('args', {})
        if tool not in tool_whitelist:
            record_tool_call(tool or 'unknown', success=False)
            return error_response('ERR_TOOL_NOT_ALLOWED', '该工具不在白名单中')

        room_code = args.get('roomCode')
        if not room_code:
            record_tool_call(tool, success=False)
            return error_response('ERR_MISSING_ROOM_CODE', '缺少 roomCode')
        if room_code not in games_db:
            record_tool_call(tool, success=False)
            return error_response('ERR_GAME_NOT_FOUND', '游戏不存在')

        game = games_db[room_code]
        ensure_game_meta(game, room_code)
        player_turn = get_player_turn_by_username(game, username)
        if not player_turn:
            record_tool_call(tool, success=False)
            return error_response('ERR_NOT_ROOM_PLAYER', '你不是该房间的玩家')

        if tool == 'get_game_state':
            snapshot = build_game_snapshot(room_code, game)
            record_tool_call(tool, success=True)
            return jsonify({'success': True, 'result': snapshot})

        if tool == 'list_legal_moves':
            limit = args.get('limit', 20)
            try:
                limit = max(1, min(int(limit), 100))
            except (TypeError, ValueError):
                limit = 20
            moves = list_legal_moves_for_player(game, player_turn, limit=limit)
            record_tool_call(tool, success=True)
            return jsonify({'success': True, 'result': {'moves': moves, 'count': len(moves)}})

        if tool == 'evaluate_move':
            row = args.get('row')
            col = args.get('col')
            value = args.get('value')
            if not validate_position(game, row, col):
                record_tool_call(tool, success=False)
                return error_response('ERR_INVALID_POSITION', '无效的落子坐标')
            if value is None or str(value).strip() == '':
                record_tool_call(tool, success=False)
                return error_response('ERR_INVALID_VALUE', '请输入有效数字或 X')
            if game['grid'][row][col] is not None:
                result = {
                    'isLegal': False,
                    'reasonCode': 'CELL_OCCUPIED',
                    'reason': '该格子已被填充'
                }
                record_eval_result(False)
                record_tool_call(tool, success=True)
                return jsonify({'success': True, 'result': result})
            is_valid, error_msg = validate_move(game, row, col, value, player_turn)
            if not is_valid:
                result = {
                    'isLegal': False,
                    'reasonCode': 'INVALID_MOVE_RULE',
                    'reason': error_msg
                }
                record_eval_result(False)
                record_tool_call(tool, success=True)
                return jsonify({'success': True, 'result': result})
            score_delta, next_turn, skipped = score_move_simulation(game, row, col, value, player_turn)
            result = {
                'isLegal': True,
                'reasonCode': 'OK',
                'reason': '落子合法',
                'scoreDelta': score_delta,
                'nextTurn': next_turn,
                'turnSkipped': skipped
            }
            record_eval_result(True)
            record_tool_call(tool, success=True)
            return jsonify({'success': True, 'result': result})

        if tool == 'explain_scoring':
            row = args.get('row')
            col = args.get('col')
            value = args.get('value')
            if not validate_position(game, row, col):
                record_tool_call(tool, success=False)
                return error_response('ERR_INVALID_POSITION', '无效的落子坐标')
            if value is None or str(value).strip() == '':
                record_tool_call(tool, success=False)
                return error_response('ERR_INVALID_VALUE', '请输入有效数字或 X')
            if game['grid'][row][col] is not None:
                record_tool_call(tool, success=False)
                return error_response('ERR_CELL_OCCUPIED', '该格子已被填充')
            is_valid, error_msg = validate_move(game, row, col, value, player_turn)
            if not is_valid:
                record_tool_call(tool, success=False)
                return error_response('ERR_INVALID_MOVE_RULE', error_msg)
            score_delta, next_turn, skipped = score_move_simulation(game, row, col, value, player_turn)
            explanation = {
                'row': row,
                'col': col,
                'value': value,
                'scoreDelta': score_delta,
                'nextTurn': next_turn,
                'turnSkipped': skipped,
                'explanation': '该步先进行行列唯一性校验，再按行/列满线规则触发计分计算。'
            }
            record_tool_call(tool, success=True)
            return jsonify({'success': True, 'result': explanation})

        record_tool_call(tool, success=False)
        return error_response('ERR_TOOL_NOT_IMPLEMENTED', '工具尚未实现')

    @app.route('/api/metrics/runtime', methods=['GET'])
    def get_runtime_metrics():
        username = session.get('username')
        if not username:
            return error_response('ERR_NOT_LOGGED_IN', '请先登录')
        return jsonify({'success': True, 'metrics': runtime_metrics})
