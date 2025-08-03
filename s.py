# server.py
import socket
import threading
import random
import time

snakes = {98: 79, 95: 75, 93: 73, 87: 24, 64: 60, 62: 19, 54: 34, 17: 7}
ladders = {1: 38, 4: 14, 9: 31, 21: 42, 28: 84, 51: 67, 71: 91, 80: 99}
positions = []
clients = []
turn = 0
lock = threading.Lock()

MIN_PLAYERS = 2
MAX_PLAYERS = 4
game_started = False
finished_players = set()

def broadcast(message):
    for client in clients:
        try:
            client.sendall(message.encode())
        except:
            pass  # Client might have disconnected

def handle_client(conn, player_id):#handles dice roll
    global turn, finished_players

    conn.sendall(f"Welcome Player {player_id + 1}!\n".encode())

    while not game_started:
        time.sleep(1)

    while True:
        with lock:
            if player_id in finished_players or turn != player_id:
                continue

            conn.sendall("Your turn! Press Roll Dice to continue.\n".encode())

        try:
            msg = conn.recv(1024)
            if not msg:
                break
        except:
            break

        with lock:
            if player_id in finished_players:
                continue

            dice = random.randint(1, 6)
            new_pos = positions[player_id] + dice
            msg_text = f"\nPlayer {player_id + 1} rolled a {dice}.\n"

            if new_pos > 100:
                msg_text += "You need exact number to reach 100.\n"
                new_pos = positions[player_id]
            else:
                if new_pos in snakes:
                    msg_text += f"Oh no! Snake at {new_pos}. Go to {snakes[new_pos]}.\n"
                    new_pos = snakes[new_pos]
                elif new_pos in ladders:
                    msg_text += f"Yay! Ladder at {new_pos}. Climb to {ladders[new_pos]}.\n"
                    new_pos = ladders[new_pos]

            positions[player_id] = new_pos

            board = "\nBoard Status:\n" + "\n".join(
                [f"Player {i+1}: {positions[i]}" for i in range(len(clients))]
            ) + "\n"

            broadcast(msg_text + board)

            if new_pos == 100:
                broadcast(f"\n🎉 Player {player_id + 1} has finished the game! 🎉\n")
                finished_players.add(player_id)

                if len(finished_players) == len(clients) - 1:
                    for i in range(len(clients)):
                        if i not in finished_players:
                            broadcast(f"\n🏁 Player {i + 1} is the last one left!\n")
                    broadcast("Game Over. Thanks for playing!\n")
                    break

            while True:
                turn = (turn + 1) % len(clients)
                if turn not in finished_players:
                    break

    conn.close()


def start_server():#binds server to the host on port 5555
    global game_started

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 5555))
    server.listen(MAX_PLAYERS)
    print(f"Server started. Waiting for {MIN_PLAYERS}-{MAX_PLAYERS} players...")

    def wait_for_players():            #One separate thread runs to wait for the game to start
        global game_started
        start_time = None

        while not game_started:
            if len(clients) >= MIN_PLAYERS:
                if start_time is None:
                    print("Minimum players reached. Starting 10s countdown...")
                    broadcast("Minimum players joined. Waiting 10 seconds for more players...\n")
                    start_time = time.time()

                if time.time() - start_time > 15 or len(clients) == MAX_PLAYERS:
                    game_started = True
                    print("Game starting now!")
                    broadcast("Game is starting now!\n")
                    break
            time.sleep(1)

    threading.Thread(target=wait_for_players).start()#server starts a new thread for each connected player

    while not game_started:
        conn, addr = server.accept()
        player_id = len(clients)
        print(f"Player {player_id + 1} connected from {addr}")
        clients.append(conn)
        positions.append(0)
        threading.Thread(target=handle_client, args=(conn, player_id)).start()

start_server()
