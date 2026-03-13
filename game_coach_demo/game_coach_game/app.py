from flask import Flask, render_template, request, jsonify, session
import uuid
import time
import json
import os
from copy import deepcopy

app = Flask(__name__)
app.secret_key = 'grid_game_secret_key_2024'

# 数据文件路径
DATA_FILE = 'game_data.json'

# 服务器端数据存储
users_db = {}
rooms_db = {}
games_db = {}
colors_db = {}

# 可用颜色
AVAILABLE_COLORS = ['red', 'blue', 'gray', 'yellow', 'green', 'purple', 'gold', 'silver', 'pink', 'aurora', 'neon']
RULES_VERSION = "v1.0"
GAME_LOG_DIR = "game_logs"
os.makedirs(GAME_LOG_DIR, exist_ok=True)
ENABLE_AGENT_MCP_EXTENSION = os.getenv('ENABLE_AGENT_MCP_EXTENSION', '0') == '1'


def error_response(error_code, message, extra=None):
    payload = {'success': False, 'errorCode': error_code, 'message': message}
    if extra:
        payload.update(extra)
    return jsonify(payload)


def other_player(player_turn):
    return 'player2' if player_turn == 'player1' else 'player1'


def ensure_game_meta(game, room_code):
    if 'gameId' not in game:
        game['gameId'] = f"{room_code}-{uuid.uuid4().hex[:8]}"
    if 'events' not in game:
        game['events'] = []
    if 'skipNextTurnFor' not in game:
        game['skipNextTurnFor'] = None
    if 'rulesVersion' not in game:
        game['rulesVersion'] = RULES_VERSION


def log_game_event(game, room_code, event_type, actor=None, payload=None, score_delta=None):
    ensure_game_meta(game, room_code)
    event = {
        'eventId': len(game['events']) + 1,
        'timestamp': time.time(),
        'type': event_type,
        'actor': actor,
        'payload': payload or {},
        'scoreDelta': score_delta or {'player1': 0, 'player2': 0},
        'gameState': serialize_game(game)
    }
    game['events'].append(event)
    log_file = os.path.join(GAME_LOG_DIR, f"{game['gameId']}.jsonl")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')


def resolve_next_turn(game, player_turn):
    next_turn = other_player(player_turn)
    if game.get('skipNextTurnFor') == next_turn:
        return player_turn, True
    return next_turn, False


def apply_turn_transition(game, player_turn):
    next_turn, skipped = resolve_next_turn(game, player_turn)
    if skipped:
        game['skipNextTurnFor'] = None
    game['currentTurn'] = next_turn
    return skipped


def serialize_game(game):
    return {
        'grid': game['grid'],
        'player1': game['player1'],
        'player2': game['player2'],
        'player1Color': game['player1Color'],
        'player2Color': game['player2Color'],
        'player1Score': game['player1Score'],
        'player2Score': game['player2Score'],
        'player1Multiplier': game.get('player1Multiplier', 1),
        'player2Multiplier': game.get('player2Multiplier', 1),
        'currentTurn': game['currentTurn'],
        'status': game['status'],
        'lastUpdate': game['lastUpdate'],
        'rowScores': game.get('rowScores', {}),
        'colScores': game.get('colScores', {}),
        'skipNextTurnFor': game.get('skipNextTurnFor'),
        'gameId': game.get('gameId'),
        'rulesVersion': game.get('rulesVersion', RULES_VERSION)
    }


def validate_position(game, row, col):
    if not isinstance(row, int) or not isinstance(col, int):
        return False
    rows = len(game['grid'])
    cols = len(game['grid'][0])
    return 0 <= row < rows and 0 <= col < cols


def recompute_affected_scores(game, row, col):
    row_scores = game.setdefault('rowScores', {})
    col_scores = game.setdefault('colScores', {})
    old_row = row_scores.pop(row, {'player1': 0, 'player2': 0})
    old_col = col_scores.pop(col, {'player1': 0, 'player2': 0})

    game['player1Score'] -= old_row.get('player1', 0) + old_col.get('player1', 0)
    game['player2Score'] -= old_row.get('player2', 0) + old_col.get('player2', 0)

    game['player1Score'] = max(0, game['player1Score'])
    game['player2Score'] = max(0, game['player2Score'])

    new_scores = check_and_score(game, row, col)
    game['player1Score'] += new_scores['player1']
    game['player2Score'] += new_scores['player2']
    return {
        'oldRow': old_row,
        'oldCol': old_col,
        'newDelta': new_scores
    }


def build_game_snapshot(room_code, game):
    return {
        'snapshotId': uuid.uuid4().hex[:12],
        'roomCode': room_code,
        'gameId': game.get('gameId'),
        'rulesVersion': game.get('rulesVersion', RULES_VERSION),
        'grid': game['grid'],
        'currentTurn': game['currentTurn'],
        'status': game['status'],
        'player1': game['player1'],
        'player2': game['player2'],
        'player1Score': game['player1Score'],
        'player2Score': game['player2Score'],
        'player1Multiplier': game.get('player1Multiplier', 1),
        'player2Multiplier': game.get('player2Multiplier', 1),
        'skipNextTurnFor': game.get('skipNextTurnFor'),
        'rowScores': game.get('rowScores', {}),
        'colScores': game.get('colScores', {}),
        'lastUpdate': game['lastUpdate']
    }



# ==================== 数据持久化 ====================
def load_data():
    global users_db, rooms_db, games_db, colors_db
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                users_db = data.get('users', {})
                rooms_db = data.get('rooms', {})
                games_db = data.get('games', {})
                colors_db = data.get('colors', {})
    except Exception as e:
        print(f"加载数据失败：{e}")
        init_users()

def save_data():
    try:
        data = {
            'users': users_db,
            'rooms': {},
            'games': {},
            'colors': {}
        }
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存数据失败：{e}")

# 初始化默认用户
def init_users():
    global users_db
    if not users_db:
        users_db = {
            'player1': {'password': 'a', 'wins': 0, 'losses': 0, 'draws': 0, 'totalScore': 1000},
            'player2': {'password': 'b', 'wins': 0, 'losses': 0, 'draws': 0, 'totalScore': 1000},
            'player3': {'password': 'c', 'wins': 0, 'losses': 0, 'draws': 0, 'totalScore': 1000}
        }
        save_data()

# 加载数据
load_data()
if not users_db:
    init_users()

# ==================== 用户系统 ====================
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return error_response('ERR_MISSING_CREDENTIALS', '请输入用户名和密码')
    
    if username in users_db and users_db[username]['password'] == password:
        session['username'] = username
        save_data()
        return jsonify({'success': True, 'username': username})
    
    return error_response('ERR_INVALID_CREDENTIALS', '用户名或密码错误')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    confirm_password = data.get('confirmPassword', '').strip()
    
    if not username or not password:
        return error_response('ERR_MISSING_CREDENTIALS', '请输入用户名和密码')
    
    if password != confirm_password:
        return error_response('ERR_PASSWORD_MISMATCH', '两次输入的密码不一致')
    
    if username in users_db:
        return error_response('ERR_USERNAME_EXISTS', '用户名已存在')
    
    users_db[username] = {'password': password, 'wins': 0, 'losses': 0, 'draws': 0, 'totalScore': 1000}
    save_data()
    return jsonify({'success': True, 'message': '注册成功'})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/current_user', methods=['GET'])
def get_current_user():
    username = session.get('username')
    if username:
        return jsonify({'success': True, 'username': username})
    return jsonify({'success': False})

@app.route('/api/user_points', methods=['GET'])
def get_user_points():
    username = session.get('username')
    if not username:
        return error_response('ERR_NOT_LOGGED_IN', '请先登录')
    if username in users_db:
        return jsonify({'success': True, 'points': users_db[username]['totalScore']})
    return error_response('ERR_USER_NOT_FOUND', '用户不存在')

@app.route('/api/update_points', methods=['POST'])
def update_points():
    username = session.get('username')
    if not username:
        return error_response('ERR_NOT_LOGGED_IN', '请先登录')
    data = request.json
    points = data.get('points', 0)
    if username in users_db:
        users_db[username]['totalScore'] = points
        save_data()
        return jsonify({'success': True, 'points': points})
    return error_response('ERR_USER_NOT_FOUND', '用户不存在')

@app.route('/api/deduct_points', methods=['POST'])
def deduct_points():
    username = session.get('username')
    if not username:
        return error_response('ERR_NOT_LOGGED_IN', '请先登录')
    data = request.json
    amount = data.get('amount', 0)
    if username in users_db:
        if users_db[username]['totalScore'] >= amount:
            users_db[username]['totalScore'] -= amount
            save_data()
            return jsonify({'success': True, 'points': users_db[username]['totalScore']})
        return error_response('ERR_INSUFFICIENT_POINTS', '积分不足')
    return error_response('ERR_USER_NOT_FOUND', '用户不存在')

# ==================== 房间系统 ====================
@app.route('/api/create_room', methods=['POST'])
def create_room():
    username = session.get('username')
    if not username:
        return error_response('ERR_NOT_LOGGED_IN', '请先登录')
    
    data = request.json
    room_code = data.get('roomCode', '').strip()
    rows = data.get('rows', 5)
    cols = data.get('cols', 8)
    
    if not room_code:
        room_code = str(uuid.uuid4())[:6].upper()
    
    if len(room_code) != 6:
        return error_response('ERR_INVALID_ROOM_CODE', '房间号必须是 6 位')
    
    if room_code in rooms_db:
        return error_response('ERR_ROOM_EXISTS', '房间号已存在')
    
    rooms_db[room_code] = {
        'host': username,
        'player1': username,
        'player2': None,
        'rows': rows,
        'cols': cols,
        'status': 'waiting',
        'created_at': time.time()
    }
    
    games_db[room_code] = {
        'grid': [[None for _ in range(cols)] for _ in range(rows)],
        'player1': username,
        'player2': None,
        'player1Color': None,
        'player2Color': None,
        'player1Score': 0,
        'player2Score': 0,
        'player1Multiplier': 1,
        'player2Multiplier': 1,
        'currentTurn': 'player1',
        'status': 'waiting',
        'lastUpdate': time.time(),
        'rowScores': {},
        'colScores': {},
        'rulesVersion': RULES_VERSION,
        'skipNextTurnFor': None
    }
    ensure_game_meta(games_db[room_code], room_code)
    log_game_event(games_db[room_code], room_code, 'ROOM_CREATED', actor=username, payload={'rows': rows, 'cols': cols})
    
    colors_db[room_code] = {
        'player1': None,
        'player2': None,
        'taken_colors': []
    }
    
    return jsonify({'success': True, 'roomCode': room_code, 'rulesVersion': RULES_VERSION, 'gameId': games_db[room_code]['gameId']})

@app.route('/api/join_room', methods=['POST'])
def join_room():
    username = session.get('username')
    if not username:
        return error_response('ERR_NOT_LOGGED_IN', '请先登录')
    
    data = request.json
    room_code = data.get('roomCode', '').strip()
    
    if room_code not in rooms_db:
        return error_response('ERR_ROOM_NOT_FOUND', '房间不存在')
    
    room = rooms_db[room_code]
    
    if room['status'] != 'waiting':
        return error_response('ERR_ROOM_UNAVAILABLE', '房间已满或游戏已开始')
    
    if room['player1'] == username:
        return error_response('ERR_JOIN_OWN_ROOM', '不能加入自己的房间')
    
    room['player2'] = username
    room['status'] = 'playing'
    
    game = games_db[room_code]
    ensure_game_meta(game, room_code)
    game['player2'] = username
    game['status'] = 'playing'
    game['lastUpdate'] = time.time()
    log_game_event(game, room_code, 'PLAYER_JOINED', actor=username, payload={'roomCode': room_code})
    
    return jsonify({'success': True, 'roomCode': room_code, 'rulesVersion': game.get('rulesVersion', RULES_VERSION), 'gameId': game.get('gameId')})

@app.route('/api/room_status/<room_code>', methods=['GET'])
def get_room_status(room_code):
    username = session.get('username')
    if not username:
        return jsonify({'success': False})
    
    if room_code not in rooms_db:
        return jsonify({'success': False, 'message': '房间不存在'})
    
    room = rooms_db[room_code]
    return jsonify({
        'success': True,
        'room': {
            'code': room_code,
            'host': room['player1'],
            'player2': room['player2'],
            'status': room['status']
        }
    })

@app.route('/api/room_info/<room_code>', methods=['GET'])
def get_room_info(room_code):
    username = session.get('username')
    if not username:
        return jsonify({'success': False})
    
    if room_code not in rooms_db:
        return jsonify({'success': False, 'message': '房间不存在'})
    
    room = rooms_db[room_code]
    return jsonify({
        'success': True,
        'room': {
            'player1': room['player1'],
            'player2': room['player2'],
            'status': room['status']
        }
    })

@app.route('/api/cancel_room/<room_code>', methods=['POST'])
def cancel_room(room_code):
    username = session.get('username')
    if not username:
        return jsonify({'success': False})
    
    if room_code in rooms_db:
        if rooms_db[room_code]['player1'] == username:
            del rooms_db[room_code]
            if room_code in games_db:
                del games_db[room_code]
            if room_code in colors_db:
                del colors_db[room_code]
    
    return jsonify({'success': True})

# ==================== 颜色选择系统 ====================
@app.route('/api/select_color', methods=['POST'])
def select_color():
    username = session.get('username')
    if not username:
        return error_response('ERR_NOT_LOGGED_IN', '请先登录')
    
    data = request.json
    room_code = data.get('roomCode')
    color = data.get('color')
    
    if room_code not in colors_db:
        return error_response('ERR_ROOM_NOT_FOUND', '房间不存在')
    
    if color not in AVAILABLE_COLORS:
        return error_response('ERR_INVALID_COLOR', '无效的颜色')
    
    colors = colors_db[room_code]
    room = rooms_db[room_code]
    game = games_db[room_code]
    
    if username == room['player1']:
        player_num = 1
        if colors['player1']:
            return error_response('ERR_COLOR_ALREADY_SELECTED', '你已经选择过颜色了')
    elif username == room['player2']:
        player_num = 2
        if colors['player2']:
            return error_response('ERR_COLOR_ALREADY_SELECTED', '你已经选择过颜色了')
    else:
        return error_response('ERR_NOT_ROOM_PLAYER', '你不是该房间的玩家')
    
    if color in colors['taken_colors']:
        return error_response('ERR_COLOR_TAKEN', '该颜色已被选择')
    
    if player_num == 1:
        colors['player1'] = color
        game['player1Color'] = color
    else:
        colors['player2'] = color
        game['player2Color'] = color
    
    colors['taken_colors'].append(color)
    game['lastUpdate'] = time.time()
    log_game_event(game, room_code, 'COLOR_SELECTED', actor=username, payload={'player': player_num, 'color': color})
    
    return jsonify({'success': True, 'playerNumber': player_num, 'rulesVersion': game.get('rulesVersion', RULES_VERSION)})

@app.route('/api/color_status/<room_code>', methods=['GET'])
def get_color_status(room_code):
    username = session.get('username')
    if not username:
        return jsonify({'success': False})
    
    if room_code not in colors_db:
        return jsonify({'success': False, 'message': '房间不存在'})
    
    colors = colors_db[room_code]
    return jsonify({
        'success': True,
        'colors': {
            'player1': colors['player1'],
            'player2': colors['player2']
        }
    })

# ==================== 游戏系统 ====================
@app.route('/api/game/<room_code>', methods=['GET'])
def get_game(room_code):
    username = session.get('username')
    if not username:
        return error_response('ERR_NOT_LOGGED_IN', '请先登录')
    
    if room_code not in games_db:
        return error_response('ERR_GAME_NOT_FOUND', '游戏不存在')
    
    game = games_db[room_code]
    ensure_game_meta(game, room_code)
    return jsonify({'success': True, 'game': serialize_game(game)})

# ✅ 修复：正确的路由定义
@app.route('/api/game/<room_code>/apply_card', methods=['POST'])
def apply_card(room_code):
    username = session.get('username')
    if not username:
        return error_response('ERR_NOT_LOGGED_IN', '请先登录')
    
    if room_code not in games_db:
        return error_response('ERR_GAME_NOT_FOUND', '游戏不存在')
    
    data = request.json
    card_type = data.get('card_type')
    
    game = games_db[room_code]
    ensure_game_meta(game, room_code)
    
    if username == game['player1']:
        player_turn = 'player1'
    elif username == game['player2']:
        player_turn = 'player2'
    else:
        return error_response('ERR_NOT_ROOM_PLAYER', '你不是该房间的玩家')
    
    if game['currentTurn'] != player_turn:
        return error_response('ERR_NOT_YOUR_TURN', '不是你的回合')
    
    if card_type == 'double_score':
        if player_turn == 'player1':
            game['player1Multiplier'] = 2
        else:
            game['player2Multiplier'] = 2
        game['lastUpdate'] = time.time()
        log_game_event(game, room_code, 'CARD_APPLIED', actor=username, payload={'cardType': card_type})
        return jsonify({'success': True, 'message': '双重预言已激活！', 'game': serialize_game(game)})
    
    elif card_type == 'skip_turn':
        target = other_player(player_turn)
        if game.get('skipNextTurnFor') is not None:
            return error_response('ERR_SKIP_ALREADY_ACTIVE', '已有待跳过回合，请先完成当前效果')
        game['skipNextTurnFor'] = target
        game['lastUpdate'] = time.time()
        log_game_event(game, room_code, 'CARD_APPLIED', actor=username, payload={'cardType': card_type, 'target': target})
        return jsonify({'success': True, 'message': '时间禁锢已激活！对方回合将被跳过', 'game': serialize_game(game)})
    
    elif card_type == 'change_number':
        game['lastUpdate'] = time.time()
        log_game_event(game, room_code, 'CARD_APPLIED', actor=username, payload={'cardType': card_type})
        return jsonify({'success': True, 'message': '命运改写已激活！请选择要修改的格子', 'game': serialize_game(game)})
    
    return error_response('ERR_INVALID_CARD_TYPE', '无效的卡牌类型')

# ✅ 修复：正确的路由定义（这里是出错的地方）
@app.route('/api/game/<room_code>/change_move', methods=['POST'])
def change_move(room_code):
    username = session.get('username')
    if not username:
        return error_response('ERR_NOT_LOGGED_IN', '请先登录')
    
    if room_code not in games_db:
        return error_response('ERR_GAME_NOT_FOUND', '游戏不存在')
    
    data = request.json
    row = data.get('row')
    col = data.get('col')
    new_value = data.get('value')
    
    game = games_db[room_code]
    ensure_game_meta(game, room_code)

    if game['status'] != 'playing':
        return error_response('ERR_GAME_NOT_PLAYING', '游戏未开始或已结束')
    if not validate_position(game, row, col):
        return error_response('ERR_INVALID_POSITION', '无效的落子坐标')
    if new_value is None or str(new_value).strip() == '':
        return error_response('ERR_INVALID_VALUE', '请输入有效数字或 X')
    
    if username == game['player1']:
        player_turn = 'player1'
        player_color = game['player1Color']
    elif username == game['player2']:
        player_turn = 'player2'
        player_color = game['player2Color']
    else:
        return error_response('ERR_NOT_ROOM_PLAYER', '你不是该房间的玩家')

    if game['currentTurn'] != player_turn:
        return error_response('ERR_NOT_YOUR_TURN', '不是你的回合')
    
    if game['grid'][row][col] is None:
        return error_response('ERR_EMPTY_CELL', '该格子为空')
    
    if game['grid'][row][col].get('turn') != player_turn:
        return error_response('ERR_NOT_YOUR_CELL', '只能修改自己填写的格子')

    is_valid, error_msg = validate_move(game, row, col, new_value, player_turn)
    if not is_valid:
        return error_response('ERR_INVALID_MOVE_RULE', error_msg)
    
    old_value = game['grid'][row][col]['value']
    game['grid'][row][col] = {'value': new_value, 'color': player_color, 'turn': player_turn}

    score_recalc = recompute_affected_scores(game, row, col)
    skipped = apply_turn_transition(game, player_turn)
    game['lastUpdate'] = time.time()

    log_game_event(
        game,
        room_code,
        'MOVE_CHANGED',
        actor=username,
        payload={'row': row, 'col': col, 'oldValue': old_value, 'newValue': new_value, 'turnSkipped': skipped},
        score_delta=score_recalc['newDelta']
    )
    return jsonify({'success': True, 'game': serialize_game(game)})

def validate_move(game, row, col, value, player_turn):
    if value == 'X' or value == 'x':
        return True, None
    
    for c in range(len(game['grid'][row])):
        cell = game['grid'][row][c]
        if cell and str(cell.get('value')) == str(value) and c != col:
            return False, f'第{row+1}行已有数字{value}'
    
    for r in range(len(game['grid'])):
        cell = game['grid'][r][col]
        if cell and str(cell.get('value')) == str(value) and r != row:
            return False, f'第{col+1}列已有数字{value}'
    
    return True, None

def calculate_line_score(line, player_turn, scored_players):
    numbers = [cell['value'] for cell in line if cell and cell.get('value') != 'X' and cell.get('value') != 'x']
    n = len(numbers)
    if n == 0:
        return 0, False
    score = 0
    for cell in line:
        if cell and str(cell.get('value')) == str(n):
            if cell['turn'] == player_turn and player_turn not in scored_players:
                score = n
                scored_players.add(player_turn)
    return score, len(numbers) == len(line)

def check_and_score(game, row, col):
    scores = {'player1': 0, 'player2': 0}
    rows = len(game['grid'])
    cols = len(game['grid'][0])
    
    if row not in game.get('rowScores', {}):
        line = game['grid'][row]
        is_full = all(cell is not None for cell in line)
        if is_full:
            p1_scored = set()
            p2_scored = set()
            p1_score, _ = calculate_line_score(line, 'player1', p1_scored)
            p2_score, _ = calculate_line_score(line, 'player2', p2_scored)
            scores['player1'] += p1_score
            scores['player2'] += p2_score
            if 'rowScores' not in game:
                game['rowScores'] = {}
            game['rowScores'][row] = {'player1': p1_score, 'player2': p2_score}
    
    if col not in game.get('colScores', {}):
        line = [game['grid'][r][col] for r in range(rows)]
        is_full = all(cell is not None for cell in line)
        if is_full:
            p1_scored = set()
            p2_scored = set()
            p1_score, _ = calculate_line_score(line, 'player1', p1_scored)
            p2_score, _ = calculate_line_score(line, 'player2', p2_scored)
            scores['player1'] += p1_score
            scores['player2'] += p2_score
            if 'colScores' not in game:
                game['colScores'] = {}
            game['colScores'][col] = {'player1': p1_score, 'player2': p2_score}
    
    return scores


def score_move_simulation(game, row, col, value, player_turn):
    simulated = deepcopy(game)
    simulated['grid'][row][col] = {'value': value, 'color': 'simulated', 'turn': player_turn}
    score_delta = check_and_score(simulated, row, col)
    next_turn, skipped = resolve_next_turn(simulated, player_turn)
    return score_delta, next_turn, skipped

@app.route('/api/game/<room_code>/move', methods=['POST'])
def make_move(room_code):
    username = session.get('username')
    if not username:
        return error_response('ERR_NOT_LOGGED_IN', '请先登录')
    
    if room_code not in games_db:
        return error_response('ERR_GAME_NOT_FOUND', '游戏不存在')
    
    data = request.json
    row = data.get('row')
    col = data.get('col')
    value = data.get('value')
    
    game = games_db[room_code]
    ensure_game_meta(game, room_code)
    
    if game['status'] != 'playing':
        return error_response('ERR_GAME_NOT_PLAYING', '游戏未开始或已结束')
    if not validate_position(game, row, col):
        return error_response('ERR_INVALID_POSITION', '无效的落子坐标')
    if value is None or str(value).strip() == '':
        return error_response('ERR_INVALID_VALUE', '请输入有效数字或 X')
    
    if username == game['player1']:
        player_turn = 'player1'
        player_color = game['player1Color']
    elif username == game['player2']:
        player_turn = 'player2'
        player_color = game['player2Color']
    else:
        return error_response('ERR_NOT_ROOM_PLAYER', '你不是该房间的玩家')
    
    if game['currentTurn'] != player_turn:
        return error_response('ERR_NOT_YOUR_TURN', '不是你的回合')
    
    if game['grid'][row][col] is not None:
        return error_response('ERR_CELL_OCCUPIED', '该格子已被填充')
    
    is_valid, error_msg = validate_move(game, row, col, value, player_turn)
    if not is_valid:
        return error_response('ERR_INVALID_MOVE_RULE', error_msg)
    
    game['grid'][row][col] = {'value': value, 'color': player_color, 'turn': player_turn}
    
    scores = check_and_score(game, row, col)
    game['player1Score'] += scores['player1']
    game['player2Score'] += scores['player2']

    skipped = apply_turn_transition(game, player_turn)
    game['lastUpdate'] = time.time()
    log_game_event(
        game,
        room_code,
        'MOVE_MADE',
        actor=username,
        payload={'row': row, 'col': col, 'value': value, 'turnSkipped': skipped},
        score_delta=scores
    )
    
    is_full = all(cell is not None for row in game['grid'] for cell in row)
    if is_full:
        game['status'] = 'ended'
        log_game_event(game, room_code, 'GAME_ENDED_AUTO', actor='system')
        update_leaderboard(game)
        cleanup_finished_room(room_code)
    
    return jsonify({'success': True, 'game': serialize_game(game)})

@app.route('/api/game/<room_code>/end', methods=['POST'])
def end_game(room_code):
    username = session.get('username')
    if not username:
        return error_response('ERR_NOT_LOGGED_IN', '请先登录')
    
    if room_code not in games_db:
        return error_response('ERR_GAME_NOT_FOUND', '游戏不存在')
    
    game = games_db[room_code]
    ensure_game_meta(game, room_code)
    game['status'] = 'ended'
    game['lastUpdate'] = time.time()
    log_game_event(game, room_code, 'GAME_ENDED_MANUAL', actor=username)
    update_leaderboard(game)
    cleanup_finished_room(room_code)
    
    return jsonify({'success': True, 'rulesVersion': game.get('rulesVersion', RULES_VERSION), 'gameId': game.get('gameId')})

def update_leaderboard(game):
    p1_final_score = game['player1Score'] * game.get('player1Multiplier', 1)
    p2_final_score = game['player2Score'] * game.get('player2Multiplier', 1)
    
    if game['player1'] in users_db:
        users_db[game['player1']]['totalScore'] += p1_final_score
    if game['player2'] in users_db:
        users_db[game['player2']]['totalScore'] += p2_final_score
    
    if p1_final_score > p2_final_score:
        if game['player1'] in users_db:
            users_db[game['player1']]['wins'] += 1
        if game['player2'] in users_db:
            users_db[game['player2']]['losses'] += 1
    elif p2_final_score > p1_final_score:
        if game['player2'] in users_db:
            users_db[game['player2']]['wins'] += 1
        if game['player1'] in users_db:
            users_db[game['player1']]['losses'] += 1
    else:
        if game['player1'] in users_db:
            users_db[game['player1']]['draws'] += 1
        if game['player2'] in users_db:
            users_db[game['player2']]['draws'] += 1
    
    save_data()

def cleanup_finished_room(room_code):
    if room_code in rooms_db:
        del rooms_db[room_code]
    if room_code in games_db:
        del games_db[room_code]
    if room_code in colors_db:
        del colors_db[room_code]


@app.route('/api/coach/snapshot/<room_code>', methods=['GET'])
def coach_snapshot(room_code):
    username = session.get('username')
    if not username:
        return error_response('ERR_NOT_LOGGED_IN', '请先登录')
    if room_code not in games_db:
        return error_response('ERR_GAME_NOT_FOUND', '游戏不存在')

    game = games_db[room_code]
    ensure_game_meta(game, room_code)
    snapshot = build_game_snapshot(room_code, game)
    log_game_event(game, room_code, 'COACH_SNAPSHOT_REQUESTED', actor=username, payload={'snapshotId': snapshot['snapshotId']})
    return jsonify({'success': True, 'snapshot': snapshot})


@app.route('/api/coach/evaluate_move', methods=['POST'])
def coach_evaluate_move():
    username = session.get('username')
    if not username:
        return error_response('ERR_NOT_LOGGED_IN', '请先登录')

    data = request.json or {}
    room_code = data.get('roomCode')
    row = data.get('row')
    col = data.get('col')
    value = data.get('value')

    if not room_code:
        return error_response('ERR_MISSING_ROOM_CODE', '缺少 roomCode')
    if room_code not in games_db:
        return error_response('ERR_GAME_NOT_FOUND', '游戏不存在')

    game = games_db[room_code]
    ensure_game_meta(game, room_code)
    if not validate_position(game, row, col):
        return error_response('ERR_INVALID_POSITION', '无效的落子坐标')
    if value is None or str(value).strip() == '':
        return error_response('ERR_INVALID_VALUE', '请输入有效数字或 X')

    if username == game['player1']:
        player_turn = 'player1'
    elif username == game['player2']:
        player_turn = 'player2'
    else:
        return error_response('ERR_NOT_ROOM_PLAYER', '你不是该房间的玩家')

    if game['grid'][row][col] is not None:
        return jsonify({
            'success': True,
            'evaluation': {
                'isLegal': False,
                'reason': '该格子已被填充',
                'reasonCode': 'CELL_OCCUPIED',
                'scoreDelta': {'player1': 0, 'player2': 0},
                'nextTurn': game['currentTurn'],
                'turnSkipped': False,
                'citationsHint': ['rules/placement.md#cell-occupied']
            }
        })

    is_valid, error_msg = validate_move(game, row, col, value, player_turn)
    if not is_valid:
        return jsonify({
            'success': True,
            'evaluation': {
                'isLegal': False,
                'reason': error_msg,
                'reasonCode': 'INVALID_MOVE_RULE',
                'scoreDelta': {'player1': 0, 'player2': 0},
                'nextTurn': game['currentTurn'],
                'turnSkipped': False,
                'citationsHint': ['rules/validation.md#row-col-unique']
            }
        })

    score_delta, next_turn, skipped = score_move_simulation(game, row, col, value, player_turn)

    evaluation = {
        'isLegal': True,
        'reason': '落子合法',
        'reasonCode': 'OK',
        'scoreDelta': score_delta,
        'nextTurn': next_turn,
        'turnSkipped': skipped,
        'citationsHint': [
            'rules/validation.md#row-col-unique',
            'rules/scoring.md#line-score-trigger'
        ]
    }
    log_game_event(
        game,
        room_code,
        'COACH_EVALUATE_MOVE',
        actor=username,
        payload={'row': row, 'col': col, 'value': value, 'isLegal': True},
        score_delta=score_delta
    )
    return jsonify({'success': True, 'evaluation': evaluation})


@app.route('/api/replay/<game_id>', methods=['GET'])
def get_replay(game_id):
    username = session.get('username')
    if not username:
        return error_response('ERR_NOT_LOGGED_IN', '请先登录')
    path = os.path.join(GAME_LOG_DIR, f"{game_id}.jsonl")
    if not os.path.exists(path):
        return error_response('ERR_REPLAY_NOT_FOUND', '未找到对应对局日志')

    events = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    states = [e.get('gameState') for e in events if e.get('gameState')]
    return jsonify({
        'success': True,
        'gameId': game_id,
        'eventCount': len(events),
        'events': events,
        'states': states
    })


if ENABLE_AGENT_MCP_EXTENSION:
    try:
        from agent_mcp_extension import register_agent_mcp_routes

        register_agent_mcp_routes(
            app=app,
            deps={
                'games_db': games_db,
                'RULES_VERSION': RULES_VERSION,
                'error_response': error_response,
                'build_game_snapshot': build_game_snapshot,
                'ensure_game_meta': ensure_game_meta,
                'validate_position': validate_position,
                'validate_move': validate_move,
                'score_move_simulation': score_move_simulation
            }
        )
        print("[extension] agent_mcp_extension loaded")
    except Exception as e:
        # 保证主游戏服务可启动：扩展失败仅告警，不阻断运行
        print(f"[extension] agent_mcp_extension failed to load: {e}")


@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    save_data()
    users_list = []
    # 修复⑥：确保所有注册玩家都显示在排行榜上
    for name, data in users_db.items():
        users_list.append({
            'name': name,
            'wins': data['wins'],
            'losses': data['losses'],
            'draws': data['draws'],
            'totalScore': data.get('totalScore', 0)
        })
    users_list.sort(key=lambda x: -x['totalScore'])
    return jsonify({'success': True, 'leaderboard': users_list})

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "127.0.0.1"
    
    print("\n" + "="*60)
    print("🔮 预言家小游戏服务器已启动")
    print("="*60)
    print(f"📍 本地访问：http://127.0.0.1:5000")
    print(f"🌐 局域网访问：http://{local_ip}:5000")
    print("="*60)
    print("📋 默认账号:")
    print("   player1 - 密码：a (积分：1000)")
    print("   player2 - 密码：b (积分：1000)")
    print("   player3 - 密码：c (积分：1000)")
    print("="*60)
    print("🎴 抽卡消耗：50 积分/次，十连 500 积分")
    print("📊 计分规则：每局得分直接计入总积分（不论输赢）")
    print("💾 数据已保存到 game_data.json")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)