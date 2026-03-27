
import pygame
import random
import sys

# FARBEN (aus main.py übernommen + erweitert)
GREEN      = (80, 255, 80)
GREEN_SOFT = (120, 255, 120)
DIM_GREEN  = (18, 55, 18)
BLACK      = (0, 0, 0)
WHITE      = (255, 255, 255)
br_green   = (0, 255, 0)

class HackingGame:
    def __init__(self, surface, font_large, font_small):
        self.screen = surface
        self.font = font_small
        self.header_font = font_large
        self.W, self.H = surface.get_size()
        
        self.words = ["VAULT", "NUCLEAR", "ATOMIC", "RADS", "PIPBOY", "STIMPAK", "MUTANT", "GHOUL", "WASTELAND", "POWER", "ARMOR", "LASER", "PLASMA", "DEATH", "CLAW", "ROBOT", "SYSTEM", "HACK", "ACCESS", "DENIED", "GRANT", "USER", "ADMIN", "ROOT"]
        self.word_length = 5
        self.attempts = 4
        self.grid_width = 12
        self.grid_height = 16
        
        self.reset_game()

    def reset_game(self):
        self.attempts = 4
        self.locked_out = False
        self.won = False
        self.history = []  # Log of attempts
        
        # 1. Wähle eine Wortlänge
        self.current_words = [w for w in self.words if abs(len(w) - self.word_length) <= 1]
        if len(self.current_words) < 10:
             self.current_words = self.words # Fallback
             
        # Filtere auf exakte Länge für dieses Spiel (optional, einfacher)
        # Nimm zufällige Länge aus verfügbaren
        chosen_len = len(random.choice(self.current_words))
        self.game_words = [w for w in self.current_words if len(w) == chosen_len]
        if len(self.game_words) > 15:
            self.game_words = random.sample(self.game_words, 15)
            
        self.password = random.choice(self.game_words)
        self.word_len = len(self.password)
        
        # 2. Grid generieren
        self.chars = [] # Liste von (char, is_word_ref, word_obj)
        # Wir brauchen ca grid_width * grid_height * 2 (zwei spalten) Zeichen
        total_chars = self.grid_width * self.grid_height * 2
        
        # Fülle mit Müll
        garbage = "!@#$%^&*()_+-=[]{}|;':,./<>?"
        self.grid_data = [] # (text, is_word, original_word_str)
        
        # Platziere Wörter
        occupied_indices = set()
        
        # Versuche Wörter zufällig zu platzieren
        self.placed_words = []
        for w in self.game_words:
            # Versuche 100 mal einen Platz zu finden
            for _ in range(100):
                idx = random.randint(0, total_chars - len(w))
                # Check ob frei (und nicht über Zeilenumbruch, wenn wir streng wären, aber hier ist es ein endlos stream visual)
                # Vereinfachung: Linearer Speicher, Zeilenumbruch egal für Logik, nur für Render
                collision = False
                for i in range(len(w)):
                    if (idx + i) in occupied_indices:
                        collision = True
                        break
                if not collision:
                    for i, char in enumerate(w):
                        occupied_indices.add(idx + i)
                    self.placed_words.append({'word': w, 'start': idx, 'len': len(w)})
                    break
        
        # Baue das finale Grid-Array
        for i in range(total_chars):
            if i in occupied_indices:
                # Finde welches Wort (ineffizient aber egal bei der Größe)
                char = '-'
                my_word = None
                for pw in self.placed_words:
                    if i >= pw['start'] and i < pw['start'] + pw['len']:
                        char = pw['word'][i - pw['start']]
                        my_word = pw['word']
                        break
                self.grid_data.append({'char': char, 'word': my_word, 'hl': False})
            else:
                self.grid_data.append({'char': random.choice(garbage), 'word': None, 'hl': False})

    def get_likeness(self, word):
        count = 0
        for i in range(min(len(word), len(self.password))):
            if word[i] == self.password[i]:
                count += 1
        return count

    def draw(self, mouse_pos):
        self.screen.fill(BLACK)
        
        # Header
        header = f"ROBCO INDUSTRIES (TM) TERMLINK PROTOCOL"
        self.screen.blit(self.header_font.render(header, True, GREEN), (20, 10))
        
        sub = f"ENTER PASSWORD NOW"
        self.screen.blit(self.font.render(sub, True, GREEN_SOFT), (20, 50))
        
        attempts_str = f"{self.attempts} ATTEMPT(S) LEFT: " + ("[] " * self.attempts)
        self.screen.blit(self.font.render(attempts_str, True, GREEN_SOFT), (20, 75))

        # Grid Setup
        col_w = 20  # Breite pro Zeichen
        line_h = 24 # Höhe pro Zeile
        start_y = 110
        col1_x = 20
        col2_x = 340
        
        hover_word = None
        
        # Render Loop
        # Wir haben grid_height Zeilen pro Spalte
        # Spalte 1: Indizes 0 bis grid_width * grid_height - 1
        # Spalte 2: Rest
        
        split_idx = self.grid_width * self.grid_height
        
        for i, item in enumerate(self.grid_data):
            # Berechne Position
            if i < split_idx:
                col = 0
                row = i // self.grid_width
                local_col = i % self.grid_width
                x = col1_x + 80 + local_col * col_w # 80px für Hex-Adresse
                y = start_y + row * line_h
                
                # Hex Address nur am Anfang der Zeile
                if local_col == 0:
                    addr = f"0x{0xF000 + i:04X}"
                    self.screen.blit(self.font.render(addr, True, GREEN_SOFT), (col1_x, y))
                    
            else:
                col = 1
                adj_i = i - split_idx
                row = adj_i // self.grid_width
                local_col = adj_i % self.grid_width
                x = col2_x + 80 + local_col * col_w
                y = start_y + row * line_h
                
                if local_col == 0:
                    addr = f"0x{0xF000 + i:04X}"
                    self.screen.blit(self.font.render(addr, True, GREEN_SOFT), (col2_x, y))

            # Maus Hover Check Logic
            # Bounding Box für das Zeichen
            char_rect = pygame.Rect(x, y, col_w, line_h)
            is_hover = char_rect.collidepoint(mouse_pos)
            
            # Farbe bestimmen
            color = GREEN
            if item['word'] and is_hover:
                 hover_word = item['word'] # Merken für späteres Highlight
            
            # Zeichnen später, damit wir wissen ob das ganze Wort gehighlighted werden muss
            item['rect'] = char_rect
        
        # Zweiter Pass für Draw (mit Word Highlight)
        for i, item in enumerate(self.grid_data):
            color = GREEN
            bg_color = None
            
            if self.locked_out:
                color = DIM_GREEN
            elif self.won:
                if item['word'] == self.password:
                    color = BLACK
                    bg_color = GREEN
                else:
                    color = DIM_GREEN

            elif not self.won and not self.locked_out:
                # Highlight logic
                if item['word'] and item['word'] == hover_word:
                    color = BLACK
                    bg_color = GREEN
                elif item['rect'].collidepoint(mouse_pos) and not item['word']:
                    color = BLACK
                    bg_color = GREEN
            
            char_s = self.font.render(item['char'], True, color)
            if bg_color:
                pygame.draw.rect(self.screen, bg_color, item['rect'])
            self.screen.blit(char_s, item['rect'].topleft)

        # Feedback Area unten rechts
        fb_x = self.W - 200
        fb_y = self.H - 150
        
        if hover_word:
            txt = f"> {hover_word}"
        else:
            # Finde Zeichen unter Maus
            mouse_char = ""
            for item in self.grid_data:
                if item['rect'].collidepoint(mouse_pos):
                     mouse_char = item['char']
                     break
            txt = f"> {mouse_char}" if mouse_char else ">"
            
        self.screen.blit(self.font.render(txt, True, GREEN), (fb_x - 50, fb_y))
        
        # History
        hist_y = fb_y + 30
        for entry in self.history[-4:]:
            self.screen.blit(self.font.render(entry, True, GREEN_SOFT), (fb_x - 50, hist_y))
            hist_y += 24
            
        if self.won:
             res_txt = "LOGIN SUCCESS"
             self.screen.blit(self.header_font.render(res_txt, True, WHITE), (fb_x - 100, self.H - 50))
        elif self.locked_out:
             res_txt = "TERMINAL LOCKED"
             self.screen.blit(self.header_font.render(res_txt, True, (255, 0, 0)), (fb_x - 100, self.H - 50))

    def handle_click(self, mouse_pos):
        if self.locked_out or self.won:
            return "EXIT" # Click ends game
            
        for item in self.grid_data:
            if item['rect'].collidepoint(mouse_pos):
                if item['word']:
                    clicked = item['word']
                    likeness = self.get_likeness(clicked)
                    self.history.append(f"{clicked} : {likeness}/{self.word_len}")
                    
                    if clicked == self.password:
                        self.won = True
                        self.history.append("!! GRANTED !!")
                    else:
                        self.attempts -= 1
                        if self.attempts <= 0:
                            self.locked_out = True
                            self.history.append("!! LOCKED !!")
                else:
                    self.history.append(f"{item['char']} : ERROR")
                return

# Standalone Test
if __name__ == "__main__":
    pygame.init()
    W, H = 640, 480
    screen = pygame.display.set_mode((W, H))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 20, bold=True)
    font_lg = pygame.font.SysFont("monospace", 30, bold=True)
    
    game = HackingGame(screen, font_lg, font)
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                res = game.handle_click(mouse_pos)
                if res == "EXIT":
                    game.reset_game() # Restart in standalone
                    
        game.draw(mouse_pos)
        pygame.display.flip()
        clock.tick(30)
    pygame.quit()
