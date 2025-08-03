import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from PIL import Image, ImageTk

# ---- SOCKET SETUP ----
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)#tcp connection
client_socket.connect(('192.168.63.206', 5555))  #connecting to different clients

# ---- GLOBAL VARIABLES ----
player_positions = [0, 0, 0, 0]
player_id = None
max_players = 4
cell_size = 60
colors = ["red", "blue", "green", "purple"]

# ---- GUI SETUP ----
window = tk.Tk()
window.title("Snake & Ladder - Multiplayer")

top_frame = tk.Frame(window)
top_frame.pack()

canvas = tk.Canvas(top_frame, width=10 * cell_size, height=10 * cell_size)
canvas.pack(side=tk.LEFT)

right_frame = tk.Frame(top_frame)
right_frame.pack(padx=10)

chat_area = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, width=40, height=20)
chat_area.pack()
chat_area.config(state='disabled')

# Add colored tags for each player
for i in range(max_players):
    chat_area.tag_config(f"player{i+1}", foreground=colors[i])

dice_button = tk.Button(right_frame, text="Roll Dice (Your Turn)", state='disabled')
dice_button.pack(pady=5)

# ---- DICE IMAGE ----
dice_images = {}
for i in range(1, 7):
    img = Image.open(f"{i}.png")
    img = img.resize((60, 60))
    dice_images[i] = ImageTk.PhotoImage(img)

dice_label = tk.Label(right_frame, image=dice_images[1])  # Default face
dice_label.pack(pady=10)

# ---- BOARD IMAGE ----
board_img = Image.open("board2.jpeg")
board_img = board_img.resize((10 * cell_size, 10 * cell_size))
board_photo = ImageTk.PhotoImage(board_img)
canvas.create_image(0, 0, anchor=tk.NW, image=board_photo)

# ---- FUNCTIONS ----
def get_coordinates(pos):
    if pos == 0:
        return None
    pos -= 1
    row = pos // 10
    col = pos % 10
    if row % 2 == 1:
        col = 9 - col
    x = col * cell_size + cell_size // 4 - 2
    y = (9 - row) * cell_size + cell_size // 4 - 2  # shift upward
    return x, y

def draw_board():
    pass 

def update_tokens():
    canvas.delete("token")
    for i in range(max_players):
        pos = player_positions[i]
        coords = get_coordinates(pos)
        if coords:
            x, y = coords
            offset_x = (i % 2) * 20 + 2
            offset_y = (i // 2) * 20 - 10
            canvas.create_oval(
                x + offset_x, y + offset_y,
                x + offset_x + 15, y + offset_y + 15,
                fill=colors[i], tags="token"
            )

def update_chat(message, tag=None):
    chat_area.config(state='normal')
    if tag:
        chat_area.insert(tk.END, message + "\n", tag)
    else:
        chat_area.insert(tk.END, message + "\n")
    chat_area.yview(tk.END)
    chat_area.config(state='disabled')

def roll_dice():
    client_socket.sendall(b'ROLL')#sending data
    dice_button.config(state='disabled')

dice_button.config(command=roll_dice)

def listen_to_server():#Constantly listens to messages from the server.
    global player_id
    while True:
        try:
            msg = client_socket.recv(1024).decode()
            if msg.startswith("Welcome"):
                player_id = int(msg.split(" ")[2].replace("!", "")) - 1
                update_chat(msg)
            elif "Your turn" in msg:#message passing
                dice_button.config(state='normal')
                update_chat(msg)
            elif "Board Status:" in msg:
                # Check for dice roll in the message
                if "rolled a" in msg:
                    try:
                        roll_num = int(msg.split("rolled a")[1].split(".")[0].strip())
                        if roll_num in dice_images:
                            dice_label.config(image=dice_images[roll_num])
                    except:
                        pass

                # Process the message to display with colored player information
                formatted_msg = ""
                roll_info = ""
                ladder_snake_info = ""
                board_status_info = []
                
                lines = msg.split("\n")
                for line in lines:
                    line = line.strip()
                    if "Game is starting" in line:
                        formatted_msg += line + "\n"
                    elif "rolled a" in line and "Player" in line:
                        roll_info = line
                    elif "Ladder at" in line or "Snake at" in line:
                        ladder_snake_info = line
                    elif "Board Status:" in line:
                        formatted_msg += line + "\n"
                    elif line.startswith("Player") and ":" in line:
                        # Add to board status for later colored processing
                        board_status_info.append(line)
                
                # Display the roll information
                if roll_info:
                    try:
                        player_num = int(roll_info.split("Player")[1].split("rolled")[0].strip())
                        update_chat(roll_info, f"player{player_num}")
                    except:
                        update_chat(roll_info)
                
                # Display ladder/snake information
                if ladder_snake_info:
                    update_chat(ladder_snake_info)
                
                # Display board status with player positions in their respective colors
                for status_line in board_status_info:
                    try:
                        player_num = int(status_line.split("Player")[1].split(":")[0].strip())
                        update_chat(status_line, f"player{player_num}")
                    except:
                        update_chat(status_line)
                
                # Update board positions
                for line in board_status_info:
                    if "Player" in line:
                        parts = line.strip().split(":")
                        p_num = int(parts[0].split(" ")[1]) - 1
                        pos = int(parts[1])
                        player_positions[p_num] = pos
                update_tokens()
            else:
                update_chat(msg)
        except Exception as e:
            print(f"Error: {e}")
            break

# ---- START GUI ----
draw_board()
threading.Thread(target=listen_to_server, daemon=True).start()
window.mainloop()