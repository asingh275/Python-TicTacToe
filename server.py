import socketio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn
import random
import string
import os
from dotenv import load_dotenv
from azure.messaging.webpubsub.socketio import WebPubSubManager

load_dotenv()

# 1. Create a Socket.io server
connection_string = os.getenv('AZURE_WEB_PUBSUB_CONNECTION_STRING')
if connection_string:
    print("Using Azure Web PubSub for Socket.IO")
    sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*', 
                               client_manager=WebPubSubManager(connection_string))
else:
    print("Using local Socket.IO")
    sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

# 2. Wrap it in an ASGI application
app = FastAPI()
socket_app = socketio.ASGIApp(sio, app)

# 3. Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Game State ---
# lobbies = { "CODE": { "board": [...], "turn": "X", "players": {sid: "X"}, "nicknames": {sid: "Name"}, "winner": None } }
lobbies = {}

def generate_lobby_code():
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if code not in lobbies:
            return code

def check_winner(board):
    win_combinations = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8), # rows
        (0, 3, 6), (1, 4, 7), (2, 5, 8), # columns
        (0, 4, 8), (2, 4, 6)             # diagonals
    ]
    for a, b, c in win_combinations:
        if board[a] == board[b] == board[c] != "":
            return board[a]
    return None

def is_board_full(board):
    return "" not in board

def get_best_move(board, ai_player):
    opponent = "O" if ai_player == "X" else "X"

    def minimax(board, is_maximizing):
        winner = check_winner(board)
        if winner == ai_player: return 1
        if winner == opponent: return -1
        if is_board_full(board): return 0

        if is_maximizing:
            best_score = -float('inf')
            for i in range(9):
                if board[i] == "":
                    board[i] = ai_player
                    score = minimax(board, False)
                    board[i] = ""
                    best_score = max(score, best_score)
            return best_score
        else:
            best_score = float('inf')
            for i in range(9):
                if board[i] == "":
                    board[i] = opponent
                    score = minimax(board, True)
                    board[i] = ""
                    best_score = min(score, best_score)
            return best_score

    best_score = -float('inf')
    move = -1
    for i in range(9):
        if board[i] == "":
            board[i] = ai_player
            score = minimax(board, False)
            board[i] = ""
            if score > best_score:
                best_score = score
                move = i
    return move

    return move

def get_random_move(board):
    import random
    empty_cells = [i for i, cell in enumerate(board) if cell == ""]
    return random.choice(empty_cells) if empty_cells else -1

@sio.event
async def connect(sid, environ):
    print(f"Connection attempt: {sid}")

async def _cleanup_player(sid):
    # Find which lobby the user was in and remove them
    for code, game in list(lobbies.items()):
        if sid in game["players"]:
            role = game["players"].pop(sid)
            game["nicknames"].pop(sid, None)
            await sio.leave_room(sid, code)
            print(f"Player {role} ({sid}) cleaned up from lobby {code}")
            # If lobby empty, delete it
            if not game["players"]:
                if code in lobbies:
                    del lobbies[code]
                    print(f"Lobby {code} deleted as it became empty")
            else:
                await sio.emit('player_left', {'role': role}, room=code)

@sio.event
async def disconnect(sid):
    await _cleanup_player(sid)

@sio.event
async def create_lobby(sid, data=None):
    await _cleanup_player(sid)
    nickname = data.get('nickname', 'Player X') if data else 'Player X'
    code = generate_lobby_code()
    lobbies[code] = {
        "board": [""] * 9,
        "current_turn": "X",
        "players": {sid: "X"},
        "nicknames": {sid: nickname},
        "winner": None
    }
    await sio.enter_room(sid, code)
    print(f"Lobby {code} created by {sid} ({nickname})")
    return {"code": code, "role": "X"}

@sio.event
async def play_ai(sid, data=None):
    await _cleanup_player(sid)
    difficulty = data.get('difficulty', 'hard') if data else 'hard'
    nickname = data.get('nickname', 'Player X') if data else 'Player X'
    code = generate_lobby_code()
    lobbies[code] = {
        "board": [""] * 9,
        "current_turn": "X",
        "players": {sid: "X", "ai": "O"},
        "nicknames": {sid: nickname, "ai": "CPU 🤖"},
        "winner": None,
        "is_ai": True,
        "difficulty": difficulty
    }
    await sio.enter_room(sid, code)
    print(f"AI Lobby {code} ({difficulty}) created by {sid}")
    return {"code": code, "role": "X", "nicknames": {"X": nickname, "O": "CPU 🤖"}}

@sio.event
async def join_lobby(sid, data):
    await _cleanup_player(sid)
    code = data.get('code', '').upper()
    nickname = data.get('nickname', 'Player O')
    if code not in lobbies:
        return {"error": "Lobby not found"}
    
    game = lobbies[code]
    if len(game["players"]) >= 2:
        return {"error": "Lobby is full"}
    
    # Assign O to the second player
    game["players"][sid] = "O"
    game["nicknames"][sid] = nickname
    await sio.enter_room(sid, code)
    print(f"Player {sid} ({nickname}) joined lobby {code} as O")
    
    # Map roles to names for the client
    nick_map = {game["players"][s]: game["nicknames"][s] for s in game["players"]}

    # Notify both players game is starting
    await sio.emit('game_start', {
        'board': game["board"],
        'turn': game["current_turn"],
        'role': "O",
        'nicknames': nick_map
    }, room=sid)
    
    await sio.emit('opponent_joined', {
        'role': "O",
        'nicknames': nick_map
    }, room=code, skip_sid=sid)
    
    return {"code": code, "role": "O"}

@sio.event
async def make_move(sid, data):
    code = data.get('code')
    index = data.get('index')
    
    if not code or code not in lobbies:
        return
    
    game = lobbies[code]
    role = game["players"].get(sid)
    
    if not role or role != game["current_turn"] or game["winner"] or game["board"][index] != "":
        return 

    game["board"][index] = role
    winner = check_winner(game["board"])
    draw = is_board_full(game["board"]) and not winner
    
    if winner:
        game["winner"] = winner
    
    game["current_turn"] = "O" if role == "X" else "X"
    
    await sio.emit('game_update', {
        'board': game["board"],
        'turn': game["current_turn"],
        'winner': winner,
        'draw': draw
    }, room=code)

    # --- AI Move ---
    if game.get("is_ai") and not winner and not draw and game["current_turn"] == "O":
        import asyncio
        await asyncio.sleep(0.6) # Add a slight delay for realism
        
        difficulty = game.get("difficulty", "hard")
        if difficulty == "easy":
            ai_move = get_random_move(game["board"])
        else:
            ai_move = get_best_move(game["board"], "O")
            
        if ai_move != -1:
            game["board"][ai_move] = "O"
            winner = check_winner(game["board"])
            draw = is_board_full(game["board"]) and not winner
            game["current_turn"] = "X"
            
            if winner: game["winner"] = winner
            
            await sio.emit('game_update', {
                'board': game["board"],
                'turn': game["current_turn"],
                'winner': winner,
                'draw': draw
            }, room=code)

@sio.event
async def turn_timeout(sid, data):
    code = data.get('code')
    if not code or code not in lobbies:
        return
    
    game = lobbies[code]
    
    # Feature ONLY for multiplayer (ignore if it's an AI game)
    if game.get("is_ai"):
        return

    role = game["players"].get(sid)
    
    # Only the current player can trigger their own timeout
    if role and role == game["current_turn"] and not game["winner"]:
        game["current_turn"] = "O" if role == "X" else "X"
        print(f"Turn timeout in lobby {code}: {role} forfeited turn")
        
        await sio.emit('game_update', {
            'board': game["board"],
            'turn': game["current_turn"],
            'winner': None,
            'draw': False,
            'timeout': True
        }, room=code)

@sio.event
async def reset_game(sid, data):
    code = data.get('code')
    if not code or code not in lobbies:
        return
        
    game = lobbies[code]
    game["board"] = [""] * 9
    game["current_turn"] = "X"
    game["winner"] = None
    
    await sio.emit('game_update', {
        'board': game["board"],
        'turn': game["current_turn"],
        'winner': None,
        'draw': False
    }, room=code)

@sio.event
async def send_chat(sid, data):
    code = data.get('code')
    message = data.get('message')
    if code in lobbies and sid in lobbies[code]["players"]:
        role = lobbies[code]["players"][sid]
        name = lobbies[code]["nicknames"][sid]
        await sio.emit('new_chat', {
            'role': role,
            'name': name,
            'message': message
        }, room=code)

@sio.event
async def send_reaction(sid, data):
    code = data.get('code')
    emoji = data.get('emoji')
    if code in lobbies and sid in lobbies[code]["players"]:
        role = lobbies[code]["players"][sid]
        await sio.emit('new_reaction', {
            'role': role,
            'emoji': emoji
        }, room=code)

@app.get("/")
async def get_index():
    from fastapi.responses import FileResponse
    return FileResponse("static/index.html")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(socket_app, host="0.0.0.0", port=port)
