def print_board(board):
    print(f"\n {board[0]} | {board[1]} | {board[2]} ")
    print("-----------")
    print(f" {board[3]} | {board[4]} | {board[5]} ")
    print("-----------")
    print(f" {board[6]} | {board[7]} | {board[8]} \n")

def check_winner(board):
    win_combinations = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8), # rows
        (0, 3, 6), (1, 4, 7), (2, 5, 8), # columns
        (0, 4, 8), (2, 4, 6)             # diagonals
    ]
    for a, b, c in win_combinations:
        if board[a] == board[b] == board[c] != " ":
            return board[a]
    return None

def is_board_full(board):
    return " " not in board

def main():
    board = [" "] * 9
    current_player = "X"
    
    print("Welcome to Simple Tic-Tac-Toe!")
    print("Positions are 1-9, starting from top-left.")
    
    while True:
        print_board(board)
        
        try:
            move = int(input(f"Player {current_player}, enter your move (1-9): ")) - 1
            if move < 0 or move > 8 or board[move] != " ":
                print("Invalid move. Try again.")
                continue
        except ValueError:
            print("Please enter a number between 1 and 9.")
            continue
            
        board[move] = current_player
        
        winner = check_winner(board)
        if winner:
            print_board(board)
            print(f"Congratulations! Player {winner} wins!")
            break
            
        if is_board_full(board):
            print_board(board)
            print("It's a draw!")
            break
            
        current_player = "O" if current_player == "X" else "X"

if __name__ == "__main__":
    main()