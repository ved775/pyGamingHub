import pygame
import random
import sys
import os
import pyodbc

conn = pyodbc.connect('DRIVER={SQL Server};SERVER=ved;DATABASE=pygaming')
cursor = conn.cursor()
user_id = int(sys.argv[1])
cursor.execute("INSERT INTO game_session (user_id,game_id,outcome) VALUES (?,?,?)", (user_id,2,'win'))
conn.commit()

# Initialize pygame
pygame.init()

# Screen setup
WIDTH, HEIGHT = 1000, 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Rock Paper Scissors")

# Colors
DARK_BLUE = (10, 25, 50)
WHITE = (255, 255, 255)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)

# Load images
ASSET_PATH = os.path.join("static", "assets")
rock_img = pygame.image.load(os.path.join(ASSET_PATH, "rock.png"))
paper_img = pygame.image.load(os.path.join(ASSET_PATH, "paper.png"))
scissor_img = pygame.image.load(os.path.join(ASSET_PATH, "scissor.png"))

# Resize images
IMG_SIZE = 200
rock_img = pygame.transform.scale(rock_img, (IMG_SIZE, IMG_SIZE))
paper_img = pygame.transform.scale(paper_img, (IMG_SIZE, IMG_SIZE))
scissor_img = pygame.transform.scale(scissor_img, (IMG_SIZE, IMG_SIZE))

# Positions and rects
choices = ["rock", "paper", "scissor"]
img_dict = {"rock": rock_img, "paper": paper_img, "scissor": scissor_img}
rects = {
    "rock": pygame.Rect(150, 100, IMG_SIZE, IMG_SIZE),
    "paper": pygame.Rect(400, 100, IMG_SIZE, IMG_SIZE),
    "scissor": pygame.Rect(650, 100, IMG_SIZE, IMG_SIZE)
}

# Fonts
font_small = pygame.font.SysFont(None, 36)
font_large = pygame.font.SysFont(None, 48)

def show_text(text, y, font, color=WHITE):
    txt = font.render(text, True, color)
    text_rect = txt.get_rect(center=(WIDTH // 2, y))
    screen.blit(txt, text_rect)

def draw_button(text, rect, font, mouse_pos):
    color = LIGHT_GRAY if rect.collidepoint(mouse_pos) else DARK_GRAY
    pygame.draw.rect(screen, color, rect)
    txt = font.render(text, True, WHITE)
    txt_rect = txt.get_rect(center=rect.center)
    screen.blit(txt, txt_rect)

def main():
    running = True
    user_choice = None
    computer_choice = None
    result = None
    round_result = ""
    user_score = 0
    round_num = 1
    max_rounds = 3

    # Buttons for Restart and Quit
    restart_btn = pygame.Rect(WIDTH // 2 - 160, 690, 140, 40)
    quit_btn = pygame.Rect(WIDTH // 2 + 20, 690, 140, 40)

    while running:
        screen.fill(DARK_BLUE)
        mouse_pos = pygame.mouse.get_pos()

        # Show round and score
        show_text(f"Round: {min(round_num, max_rounds)} / {max_rounds}", 30, font_small)
        show_text(f"Score: {user_score}", 70, font_small)

        # Draw choice images
        for choice, rect in rects.items():
            pygame.draw.rect(screen, WHITE, rect, 4)
            screen.blit(img_dict[choice], (rect.x, rect.y))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()

                if result is None and round_num <= max_rounds:
                    for choice, rect in rects.items():
                        if rect.collidepoint(pos):
                            user_choice = choice
                            computer_choice = random.choice(choices)

                            if user_choice == computer_choice:
                                round_result = "Draw!"
                            elif ((user_choice == "rock" and computer_choice == "scissor") or
                                  (user_choice == "paper" and computer_choice == "rock") or
                                  (user_choice == "scissor" and computer_choice == "paper")):
                                round_result = "You Win!"
                                user_score += 50
                            else:
                                round_result = "Computer Wins!"

                            round_num += 1
                            if round_num > max_rounds:
                                cursor.execute("INSERT INTO score (user_id,game_id,score) VALUES (?,?,?)", (user_id,2,user_score))
                                conn.commit()
                                result = f"Your score is {user_score}"

                elif result:  # When game is over
                    if restart_btn.collidepoint(pos):
                        # Reset game
                        user_choice = None
                        computer_choice = None
                        result = None
                        round_result = ""
                        user_score = 0
                        round_num = 1
                    elif quit_btn.collidepoint(pos):
                        cursor.execute("UPDATE game_session SET end_at = SYSDATETIME() WHERE user_id = ? AND end_at IS NULL",(user_id))
                        # Check existing leaderboard score
                        cursor.execute("SELECT score FROM leaderboard WHERE user_id = ? AND game_id = ?", (user_id, 2))
                        result = cursor.fetchone()

                        if result is None:
                           # No existing record, insert new one
                           cursor.execute("INSERT INTO leaderboard (user_id, game_id, score) VALUES (?, ?, ?)", (user_id, 2, user_score))
                        elif user_score > result[0]:
                           # Score is higher, update record
                           cursor.execute("UPDATE leaderboard SET score = ? WHERE user_id = ? AND game_id = ?", (user_score, user_id, 2))
                        conn.commit()
                        conn.close()
                        pygame.quit()
                        sys.exit()

        # Display user vs computer selections
        if user_choice and computer_choice and round_num <= max_rounds + 1:
            screen.blit(img_dict[user_choice], (250, 360))
            screen.blit(img_dict[computer_choice], (550, 360))
            show_text(f"You: {user_choice.capitalize()}  vs  Computer: {computer_choice.capitalize()}", 570, font_small)
            show_text(round_result, 610, font_small)

        # Final result + buttons
        if result:
            show_text(result, 660, font_large)
            draw_button("Restart", restart_btn, font_small, mouse_pos)
            draw_button("Quit", quit_btn, font_small, mouse_pos)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
