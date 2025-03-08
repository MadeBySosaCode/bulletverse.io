import pygame
import math
import random
import time
import socket
import threading
import pickle
from pypresence import Presence
import numpy as np
from typing import Dict, List, Tuple, Any, Optional, Union
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('bulletverse')

WIDTH, HEIGHT = 0, 0
FPS = 60
COLORS = {
    "WHITE": (255, 255, 255),
    "BLUE": (50, 100, 255),
    "RED": (255, 50, 50),
    "GREEN": (50, 255, 50),
    "BLACK": (0, 0, 0),
    "GRAY": (200, 200, 200),
    "DARK_GRAY": (100, 100, 100),
    "YELLOW": (255, 255, 0),
    "PURPLE": (128, 0, 128),
    "ORANGE": (255, 128, 0),
    "CYAN": (0, 255, 255),
    "MAGENTA": (255, 0, 255)
}

BULLET_SPEED = 7
ENEMY_BULLET_SPEED = 5
ENEMY_FIRE_RATE = 80
NUM_ENEMIES = 6
MAX_STAT_LEVEL = 8
PLAYER_COLORS = [
    COLORS["BLUE"], COLORS["GREEN"], COLORS["PURPLE"], COLORS["YELLOW"],
    COLORS["ORANGE"], COLORS["CYAN"], COLORS["MAGENTA"]
]

SERVER_HOST = "localhost"
SERVER_PORT = 5555
BUFFER_SIZE = 8192

DIFFICULTY_SETTINGS = {
    "easy": {
        "enemy_speed": 1.5,
        "enemy_health": 25,
        "enemy_damage": 8,
        "xp_multiplier": 1.2
    },
    "normal": {
        "enemy_speed": 2,
        "enemy_health": 30,
        "enemy_damage": 10,
        "xp_multiplier": 1.0
    },
    "hard": {
        "enemy_speed": 2.5,
        "enemy_health": 40,
        "enemy_damage": 15,
        "xp_multiplier": 0.8
    }
}


class LoadingScreen:

    def __init__(self, screen, screen_width, screen_height, font, title_font):
        self.screen = screen
        self.width = screen_width
        self.height = screen_height
        self.font = font
        self.title_font = title_font
        self.progress = 0
        self.max_progress = 100
        self.loading_tasks = []
        self.current_task_index = 0
        self.current_task_text = ""
        self.loading_complete = False
        self.start_time = 0
        self.animation_dots = 0
        self.dot_timer = 0
        self.colors = {
            "WHITE": (255, 255, 255),
            "BLUE": (50, 100, 255),
            "DARK_BLUE": (20, 60, 180),
            "BLACK": (0, 0, 0),
            "GRAY": (200, 200, 200),
            "DARK_GRAY": (100, 100, 100),
        }
        self.particles = []

        self.tips = self.generate_tips()
        self.current_tip = random.choice(self.tips)
        self.tip_change_timer = 0

    def generate_tips(self):
        """Returns a list of useful gameplay tips to show during loading"""
        return [
            "Upgrade your Health Max for longer survival in difficult levels.",
            "Bullet Penetration lets you hit multiple enemies with a single shot.",
            "Shield powerups can save your life in a tough situation.",
            "The Speed powerup helps you dodge enemy bullets more easily.",
            "Green tanks are faster, purple tanks are tougher.",
            "Maintain distance from enemies to give yourself more reaction time.",
            "Customizing your tank color is more than cosmetic - find what works for you!",
            "In multiplayer, coordinate with teammates to take down tough enemies.",
            "XP powerups give you points toward your next upgrade faster.",
            "Higher difficulty means tougher enemies but better rewards.",
            "Health regeneration is crucial for long-term survival.",
            "Press U during gameplay to open the upgrade menu.",
            "Enemies will pursue you more aggressively at higher levels.",
            "The reload speed upgrade can dramatically increase your firepower.",
            "Press ESC at any time to return to the main menu.",
            "Particles can be turned off in settings to improve performance.",
            "Try different upgrade combinations to find your preferred playstyle.",
            "Enemies drop powerups more often when you're at low health.",
            "Your score increases faster on higher difficulty settings.",
            "Use obstacles in the environment to block enemy line of sight."
        ]

    def add_task(self, task_function, task_text, weight=1):
        """Add a task to the loading queue"""
        self.loading_tasks.append({
            "function": task_function,
            "text": task_text,
            "weight": weight
        })
        self.max_progress = sum(task["weight"] for task in self.loading_tasks)

    def update(self, dt):
        """Update loading animation"""
        self.dot_timer += dt
        if self.dot_timer > 0.5:
            self.animation_dots = (self.animation_dots + 1) % 4
            self.dot_timer = 0

        self.tip_change_timer += dt
        if self.tip_change_timer > 3.0:
            self.current_tip = random.choice(self.tips)
            self.tip_change_timer = 0

        for particle in list(self.particles):
            particle["pos"][0] += particle["velocity"][0] * dt
            particle["pos"][1] += particle["velocity"][1] * dt
            particle["life"] -= dt

            if particle["life"] <= 0:
                self.particles.remove(particle)

        if len(self.particles) < 30 and pygame.time.get_ticks() % 100 < 10:
            self.add_particle()

        if self.current_task_index < len(
                self.loading_tasks) and not self.loading_complete:
            current_task = self.loading_tasks[self.current_task_index]
            self.current_task_text = current_task["text"]

            try:
                current_task["function"]()
                self.progress += current_task["weight"]
                self.current_task_index += 1

                if self.current_task_index >= len(self.loading_tasks):
                    self.loading_complete = True
                    self.current_task_text = "Loading complete!"
            except Exception as e:
                logger.error(f"Error in loading task: {e}")
                self.current_task_text = f"Error: {str(e)}"

    def draw(self):
        """Draw the loading screen"""
        self.screen.fill(self.colors["WHITE"])

        for particle in self.particles:
            alpha = int(255 * (particle["life"] / particle["max_life"]))
            color = (*particle["color"], alpha)
            pos = (int(particle["pos"][0]), int(particle["pos"][1]))

            particle_surface = pygame.Surface(
                (int(particle["size"]) * 2, int(particle["size"]) * 2),
                pygame.SRCALPHA)
            pygame.draw.circle(particle_surface, color,
                               (int(particle["size"]), int(particle["size"])),
                               int(particle["size"]))
            self.screen.blit(particle_surface,
                             (pos[0] - int(particle["size"]),
                              pos[1] - int(particle["size"])))

        title = self.title_font.render("BULLETVERSE.IO", True,
                                       self.colors["BLUE"])
        title_rect = title.get_rect(center=(self.width // 2, self.height // 3))
        self.screen.blit(title, title_rect)

        dots = "." * self.animation_dots
        loading_text = self.font.render(f"{self.current_task_text}{dots}",
                                        True, self.colors["BLACK"])
        text_rect = loading_text.get_rect(center=(self.width // 2,
                                                  self.height // 2 + 50))
        self.screen.blit(loading_text, text_rect)

        bar_width = self.width // 2
        bar_height = 20
        bar_x = (self.width - bar_width) // 2
        bar_y = self.height // 2 + 100
        pygame.draw.rect(self.screen,
                         self.colors["GRAY"],
                         (bar_x, bar_y, bar_width, bar_height),
                         border_radius=10)

        if self.max_progress > 0:
            fill_width = int(bar_width * (self.progress / self.max_progress))
            pygame.draw.rect(self.screen,
                             self.colors["BLUE"],
                             (bar_x, bar_y, fill_width, bar_height),
                             border_radius=10)

        percentage = int((self.progress / self.max_progress) *
                         100) if self.max_progress > 0 else 0
        percentage_text = self.font.render(f"{percentage}%", True,
                                           self.colors["WHITE"])
        percentage_rect = percentage_text.get_rect(
            center=(bar_x + bar_width // 2, bar_y + bar_height // 2))
        self.screen.blit(percentage_text, percentage_rect)

        tip = self.font.render(f"Tip: {self.current_tip}", True,
                               self.colors["DARK_GRAY"])
        tip_rect = tip.get_rect(center=(self.width // 2, self.height - 50))
        self.screen.blit(tip, tip_rect)

        pygame.display.flip()

    def add_particle(self):
        """Add decorative particles to the loading screen"""
        pos_x = random.randint(0, self.width)
        pos_y = random.randint(0, self.height)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(5, 20)
        velocity = [speed * math.cos(angle), speed * math.sin(angle)]
        size = random.uniform(2, 5)
        life = random.uniform(1, 3)

        blue_value = random.randint(180, 255)
        color = (50, 100, blue_value)

        self.particles.append({
            "pos": [pos_x, pos_y],
            "velocity": velocity,
            "color": color,
            "life": life,
            "max_life": life,
            "size": size
        })


class ParticleSystem:

    def __init__(self):
        self.particles = []

    def add_particles(self,
                      pos: Tuple[float, float],
                      color: Tuple[int, int, int],
                      count: int = 10,
                      speed: float = 2.0,
                      life: int = 30):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            velocity = [speed * math.cos(angle), speed * math.sin(angle)]
            size = random.uniform(1, 3)
            self.particles.append({
                "pos": [pos[0], pos[1]],
                "velocity": velocity,
                "color": color,
                "life": life,
                "max_life": life,
                "size": size
            })
            self.available_colors = {
                "Blue": COLORS["BLUE"],
                "Green": COLORS["GREEN"],
                "Purple": COLORS["PURPLE"],
                "Yellow": COLORS["YELLOW"],
                "Orange": COLORS["ORANGE"],
                "Cyan": COLORS["CYAN"],
                "Magenta": COLORS["MAGENTA"],
                "Red": COLORS["RED"]
            }
        self.player_color_name = "Blue"
        self.player_color = self.available_colors[self.player_color_name]
        self.show_cosmetics_menu = False

    def update(self):
        for particle in list(self.particles):
            particle["pos"][0] += particle["velocity"][0]
            particle["pos"][1] += particle["velocity"][1]
            particle["life"] -= 1

            if particle["life"] <= 0:
                self.particles.remove(particle)

    def draw(self, screen):
        for particle in self.particles:
            alpha = int(255 * (particle["life"] / particle["max_life"]))
            color = (*particle["color"], alpha)
            pos = (int(particle["pos"][0]), int(particle["pos"][1]))

            particle_surface = pygame.Surface(
                (int(particle["size"]) * 2, int(particle["size"]) * 2),
                pygame.SRCALPHA)
            pygame.draw.circle(particle_surface, color,
                               (int(particle["size"]), int(particle["size"])),
                               int(particle["size"]))
            screen.blit(particle_surface, (pos[0] - int(particle["size"]),
                                           pos[1] - int(particle["size"])))


class PowerUp:

    def __init__(self, pos: Tuple[float, float], type_name: str):
        self.pos = pos
        self.type = type_name
        self.radius = 15
        self.active = True
        self.creation_time = time.time()
        self.pulse_size = 0
        self.pulse_growing = True

        if self.type == "health":
            self.color = COLORS["RED"]
            self.effect = {"health": 25}
        elif self.type == "shield":
            self.color = COLORS["BLUE"]
            self.effect = {"shield": 30, "shield_duration": 10}
        elif self.type == "speed":
            self.color = COLORS["GREEN"]
            self.effect = {"movement_speed": 1.5, "speed_duration": 5}
        elif self.type == "damage":
            self.color = COLORS["YELLOW"]
            self.effect = {"bullet_damage": 5, "damage_duration": 8}
        else:
            self.type = "xp"
            self.color = COLORS["PURPLE"]
            self.effect = {"xp": 30}

    def update(self):
        if self.pulse_growing:
            self.pulse_size += 0.2
            if self.pulse_size >= 5:
                self.pulse_growing = False
        else:
            self.pulse_size -= 0.2
            if self.pulse_size <= 0:
                self.pulse_growing = True

    def draw(self, screen):
        pygame.draw.circle(screen, self.color,
                           (int(self.pos[0]), int(self.pos[1])),
                           int(self.radius + self.pulse_size), 2)

        pygame.draw.circle(screen, self.color,
                           (int(self.pos[0]), int(self.pos[1])), self.radius)

        if self.type == "health":
            pygame.draw.line(screen, COLORS["WHITE"],
                             (self.pos[0] - 8, self.pos[1]),
                             (self.pos[0] + 8, self.pos[1]), 3)
            pygame.draw.line(screen, COLORS["WHITE"],
                             (self.pos[0], self.pos[1] - 8),
                             (self.pos[0], self.pos[1] + 8), 3)
        elif self.type == "shield":
            pygame.draw.arc(screen, COLORS["WHITE"],
                            (self.pos[0] - 8, self.pos[1] - 8, 16, 16),
                            math.pi / 4, math.pi * 7 / 4, 3)
        elif self.type == "speed":
            points = [(self.pos[0] - 5, self.pos[1] - 8),
                      (self.pos[0], self.pos[1]),
                      (self.pos[0] - 2, self.pos[1]),
                      (self.pos[0] + 5, self.pos[1] + 8),
                      (self.pos[0], self.pos[1]),
                      (self.pos[0] + 2, self.pos[1])]
            pygame.draw.lines(screen, COLORS["WHITE"], False, points, 2)
        elif self.type == "damage":
            pygame.draw.polygon(screen, COLORS["WHITE"],
                                [(self.pos[0], self.pos[1] - 8),
                                 (self.pos[0] + 3, self.pos[1] - 3),
                                 (self.pos[0] + 8, self.pos[1] - 3),
                                 (self.pos[0] + 4, self.pos[1] + 2),
                                 (self.pos[0] + 6, self.pos[1] + 8),
                                 (self.pos[0], self.pos[1] + 5),
                                 (self.pos[0] - 6, self.pos[1] + 8),
                                 (self.pos[0] - 4, self.pos[1] + 2),
                                 (self.pos[0] - 8, self.pos[1] - 3),
                                 (self.pos[0] - 3, self.pos[1] - 3)])
        else:
            font = pygame.font.Font(None, 20)
            text = font.render("XP", True, COLORS["WHITE"])
            text_rect = text.get_rect(center=(self.pos[0], self.pos[1]))
            screen.blit(text, text_rect)


def spawn_enemy(difficulty: str = "normal") -> Dict:
    settings = DIFFICULTY_SETTINGS[difficulty]

    return {
        "pos":
        [random.randint(50, WIDTH - 50),
         random.randint(50, HEIGHT - 50)],
        "angle": random.uniform(0, 2 * math.pi),
        "speed": settings["enemy_speed"] * random.uniform(0.8, 1.2),
        "health": settings["enemy_health"],
        "max_health": settings["enemy_health"],
        "fire_timer": random.randint(0, ENEMY_FIRE_RATE),
        "type": random.choice(["normal", "fast", "tank"]),
        "size": random.uniform(0.8, 1.2) * 20
    }


class Button:

    def __init__(self,
                 x: int,
                 y: int,
                 width: int,
                 height: int,
                 text: str,
                 color=COLORS["GRAY"],
                 hover_color=(220, 220, 220),
                 text_color=COLORS["BLACK"],
                 border_radius: int = 0,
                 font_size: int = 24,
                 border_width: int = 2):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.hovered = False
        self.font = pygame.font.Font(None, font_size)
        self.border_radius = border_radius
        self.border_width = border_width
        self.clicked = False

    def draw(self, screen):
        color = self.hover_color if self.hovered else self.color

        if self.border_radius > 0:
            pygame.draw.rect(screen,
                             color,
                             self.rect,
                             border_radius=self.border_radius)
            pygame.draw.rect(screen,
                             COLORS["BLACK"],
                             self.rect,
                             self.border_width,
                             border_radius=self.border_radius)
        else:
            pygame.draw.rect(screen, color, self.rect)
            pygame.draw.rect(screen, COLORS["BLACK"], self.rect,
                             self.border_width)

        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def update(self, mouse_pos: Tuple[int, int]):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered:
                self.clicked = True
                return True
        return False


class Slider:

    def __init__(self,
                 x: int,
                 y: int,
                 width: int,
                 height: int,
                 min_value: float,
                 max_value: float,
                 start_value: float,
                 label: str,
                 color=COLORS["GRAY"]):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_value = min_value
        self.max_value = max_value
        self.value = start_value
        self.label = label
        self.color = color
        self.handle_radius = height * 1.5
        self.dragging = False
        self.font = pygame.font.Font(None, 20)

        self.handle_pos = self.get_handle_pos()

    def get_handle_pos(self) -> int:
        ratio = (self.value - self.min_value) / (self.max_value -
                                                 self.min_value)
        return int(self.rect.x + (self.rect.width * ratio))

    def draw(self, screen):
        pygame.draw.rect(screen, COLORS["DARK_GRAY"], self.rect)

        filled_width = self.handle_pos - self.rect.x
        filled_rect = pygame.Rect(self.rect.x, self.rect.y, filled_width,
                                  self.rect.height)
        pygame.draw.rect(screen, self.color, filled_rect)

        pygame.draw.circle(
            screen, COLORS["WHITE"],
            (self.handle_pos, self.rect.y + self.rect.height // 2),
            self.handle_radius)
        pygame.draw.circle(
            screen, COLORS["BLACK"],
            (self.handle_pos, self.rect.y + self.rect.height // 2),
            self.handle_radius, 2)

        label_surface = self.font.render(f"{self.label}: {self.value:.1f}",
                                         True, COLORS["BLACK"])
        label_rect = label_surface.get_rect(midleft=(self.rect.x,
                                                     self.rect.y - 10))
        screen.blit(label_surface, label_rect)

    def update(self, mouse_pos: Tuple[int, int],
               mouse_pressed: Tuple[bool, bool, bool]):
        handle_rect = pygame.Rect(
            self.handle_pos - self.handle_radius,
            self.rect.y + self.rect.height // 2 - self.handle_radius,
            self.handle_radius * 2, self.handle_radius * 2)

        if mouse_pressed[0] and handle_rect.collidepoint(mouse_pos):
            self.dragging = True

        if not mouse_pressed[0]:
            self.dragging = False

        if self.dragging:
            x = max(self.rect.x,
                    min(mouse_pos[0], self.rect.x + self.rect.width))
            self.handle_pos = x

            ratio = (self.handle_pos - self.rect.x) / self.rect.width
            self.value = self.min_value + ratio * (self.max_value -
                                                   self.min_value)

        return self.value


class NetworkClient:

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.player_id = str(random.randint(1000, 9999))
        self.game_state = {
            "players": {},
            "enemies": [],
            "bullets": [],
            "powerups": []
        }
        self.receive_thread = None
        self.last_received = time.time()
        self.ping = 0

    def connect(self) -> bool:
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True

            self.socket.send(self.player_id.encode())

            self.receive_thread = threading.Thread(target=self.receive_data)
            self.receive_thread.daemon = True
            self.receive_thread.start()

            logger.info(f"Client connected to {self.host}:{self.port}")
            return True

        except Exception as e:
            logger.error(f"Connection error: {e}")
            self.connected = False
            return False

    def send_data(self, data: Dict):
        if not self.connected:
            return

        try:
            send_time = time.time()
            data["send_time"] = send_time
            self.socket.send(pickle.dumps(data))
        except Exception as e:
            logger.error(f"Send error: {e}")
            self.connected = False

    def receive_data(self):
        while self.connected:
            try:
                data = self.socket.recv(BUFFER_SIZE)
                if not data:
                    self.connected = False
                    logger.warning("Connection closed by server")
                    break

                receive_time = time.time()
                self.last_received = receive_time

                self.game_state = pickle.loads(data)

                if "send_time" in self.game_state:
                    self.ping = int(
                        (receive_time - self.game_state["send_time"]) * 1000)

            except Exception as e:
                logger.error(f"Receive error: {e}")
                self.connected = False
                break

    def close(self):
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
                logger.info("Client connection closed")
            except:
                pass


class GameServer:

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.clients = {}
        self.game_state = {
            "players": {},
            "enemies": [spawn_enemy() for _ in range(NUM_ENEMIES)],
            "bullets": [],
            "powerups": [],
            "send_time": time.time()
        }
        self.last_powerup_time = time.time()
        self.powerup_interval = 10
        self.difficulty = "normal"

    def start(self) -> bool:
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.socket.settimeout(0.5)
            self.running = True

            logger.info(f"Server started on {self.host}:{self.port}")

            server_thread = threading.Thread(target=self.run)
            server_thread.daemon = True
            server_thread.start()

            return True

        except Exception as e:
            logger.error(f"Server start error: {e}")
            return False

    def run(self):
        while self.running:
            try:
                client_socket, addr = self.socket.accept()
                logger.info(f"New connection from {addr}")

                player_id = client_socket.recv(1024).decode()

                client_thread = threading.Thread(target=self.handle_client,
                                                 args=(client_socket,
                                                       player_id))
                client_thread.daemon = True
                client_thread.start()

                self.clients[player_id] = client_socket

            except socket.timeout:
                pass
            except Exception as e:
                logger.error(f"Accept error: {e}")

            self.update_game_state()

            time.sleep(0.01)

    def handle_client(self, client_socket, player_id: str):
        try:
            client_socket.send(pickle.dumps(self.game_state))

            while self.running:
                try:
                    data = client_socket.recv(BUFFER_SIZE)
                    if not data:
                        break

                    player_data = pickle.loads(data)

                    self.game_state["players"][player_id] = player_data

                    if "new_bullets" in player_data and player_data[
                            "new_bullets"]:
                        for bullet in player_data["new_bullets"]:
                            self.game_state["bullets"].append({
                                "pos":
                                bullet[:2],
                                "angle":
                                bullet[2],
                                "penetration":
                                bullet[3],
                                "damage":
                                bullet[4],
                                "owner":
                                player_id
                            })

                    self.game_state["send_time"] = time.time()
                    if "send_time" in player_data:
                        self.game_state["last_ping"] = time.time(
                        ) - player_data["send_time"]

                    client_socket.send(pickle.dumps(self.game_state))

                except Exception as e:
                    logger.error(f"Client handler error: {e}")
                    break

        except Exception as e:
            logger.error(f"Client handler error: {e}")
        finally:
            if player_id in self.clients:
                del self.clients[player_id]
            if player_id in self.game_state["players"]:
                del self.game_state["players"][player_id]
            try:
                client_socket.close()
            except:
                pass
            logger.info(f"Client {player_id} disconnected")

    def spawn_powerup(self):
        if len(self.game_state["powerups"]) >= 5:
            return

        pos = [random.randint(50, WIDTH - 50), random.randint(50, HEIGHT - 50)]

        types = ["health", "shield", "speed", "damage", "xp"]
        weights = [0.25, 0.2, 0.2, 0.2, 0.15]
        powerup_type = random.choices(types, weights=weights)[0]

        self.game_state["powerups"].append({
            "pos": pos,
            "type": powerup_type,
            "creation_time": time.time()
        })

    def update_game_state(self):
        current_time = time.time()
        self.game_state["send_time"] = current_time

        if current_time - self.last_powerup_time > self.powerup_interval:
            self.spawn_powerup()
            self.last_powerup_time = current_time

        for powerup in list(self.game_state["powerups"]):
            if current_time - powerup["creation_time"] > 30:
                self.game_state["powerups"].remove(powerup)

        for enemy in self.game_state["enemies"]:
            enemy["pos"][0] += enemy["speed"] * math.cos(enemy["angle"])
            enemy["pos"][1] += enemy["speed"] * math.sin(enemy["angle"])

            if enemy["pos"][0] <= 20 or enemy["pos"][0] >= WIDTH - 20:
                enemy["angle"] = math.pi - enemy["angle"]
            if enemy["pos"][1] <= 20 or enemy["pos"][1] >= HEIGHT - 20:
                enemy["angle"] = -enemy["angle"]

            if random.random() < 0.01:
                enemy["angle"] += random.uniform(-0.5, 0.5)

            if self.game_state["players"] and random.random() < 0.05:
                closest_player = None
                min_dist = float('inf')

                for player_id, player in self.game_state["players"].items():
                    dist = math.hypot(player["pos"][0] - enemy["pos"][0],
                                      player["pos"][1] - enemy["pos"][1])
                    if dist < min_dist:
                        min_dist = dist
                        closest_player = player

                if closest_player:
                    target_angle = math.atan2(
                        closest_player["pos"][1] - enemy["pos"][1],
                        closest_player["pos"][0] - enemy["pos"][0])
                    angle_diff = (target_angle - enemy["angle"] +
                                  math.pi) % (2 * math.pi) - math.pi
                    enemy["angle"] += angle_diff * 0.1

            enemy["fire_timer"] -= 1

            if enemy["fire_timer"] <= 0:
                enemy["fire_timer"] = ENEMY_FIRE_RATE * random.uniform(
                    0.8, 1.2)

                if self.game_state["players"]:
                    closest_player = None
                    min_dist = float('inf')

                    for player_id, player in self.game_state["players"].items(
                    ):
                        dist = math.hypot(player["pos"][0] - enemy["pos"][0],
                                          player["pos"][1] - enemy["pos"][1])
                        if dist < min_dist:
                            min_dist = dist
                            closest_player = player

                    if closest_player and min_dist < 400:
                        angle_to_player = math.atan2(
                            closest_player["pos"][1] - enemy["pos"][1],
                            closest_player["pos"][0] - enemy["pos"][0])

                        inaccuracy = min(0.2, min_dist / 2000)
                        angle_to_player += random.uniform(
                            -inaccuracy, inaccuracy)

                        self.game_state["bullets"].append({
                            "pos": [enemy["pos"][0], enemy["pos"][1]],
                            "angle":
                            angle_to_player,
                            "penetration":
                            1,
                            "damage":
                            DIFFICULTY_SETTINGS[self.difficulty]
                            ["enemy_damage"],
                            "owner":
                            "enemy"
                        })

        for bullet in list(self.game_state["bullets"]):
            speed = ENEMY_BULLET_SPEED if bullet[
                "owner"] == "enemy" else BULLET_SPEED
            bullet["pos"][0] += speed * math.cos(bullet["angle"])
            bullet["pos"][1] += speed * math.sin(bullet["angle"])

            if (bullet["pos"][0] < 0 or bullet["pos"][0] > WIDTH
                    or bullet["pos"][1] < 0 or bullet["pos"][1] > HEIGHT):
                self.game_state["bullets"].remove(bullet)
                continue

            if bullet["owner"] != "enemy":
                for enemy in list(self.game_state["enemies"]):
                    if math.hypot(bullet["pos"][0] - enemy["pos"][0],
                                  bullet["pos"][1] -
                                  enemy["pos"][1]) < enemy["size"]:
                        enemy["health"] -= bullet["damage"]
                        bullet["penetration"] -= 1

                        if bullet["penetration"] <= 0:
                            if bullet in self.game_state["bullets"]:
                                self.game_state["bullets"].remove(bullet)

                        if enemy["health"] <= 0:
                            if random.random() < 0.1:
                                self.game_state["powerups"].append({
                                    "pos": [enemy["pos"][0], enemy["pos"][1]],
                                    "type":
                                    random.choice([
                                        "health", "shield", "speed", "damage",
                                        "xp"
                                    ]),
                                    "creation_time":
                                    time.time()
                                })

                            self.game_state["enemies"].remove(enemy)
                            self.game_state["enemies"].append(
                                spawn_enemy(self.difficulty))

                            if bullet["owner"] in self.game_state["players"]:
                                player = self.game_state["players"][
                                    bullet["owner"]]
                                xp_gain = 10 * DIFFICULTY_SETTINGS[
                                    self.difficulty]["xp_multiplier"]

                                if "xp" not in player:
                                    player["xp"] = 0
                                if "xp_to_next_level" not in player:
                                    player["xp_to_next_level"] = 100
                                if "level" not in player:
                                    player["level"] = 1

                                player["xp"] += xp_gain

                                if player["xp"] >= player["xp_to_next_level"]:
                                    player["level"] += 1
                                    player["xp"] -= player["xp_to_next_level"]
                                    player["xp_to_next_level"] = int(
                                        player["xp_to_next_level"] * 1.5)

                                    if "upgrade_points" not in player:
                                        player["upgrade_points"] = 0
                                    player["upgrade_points"] += 1

                        break

            if bullet["owner"] == "enemy":
                for player_id, player in self.game_state["players"].items():
                    if math.hypot(bullet["pos"][0] - player["pos"][0],
                                  bullet["pos"][1] - player["pos"][1]) < 20:
                        if "shield" in player and player["shield"] > 0:
                            player["shield"] -= bullet["damage"]
                            if player["shield"] < 0:
                                player["health"] += player["shield"]
                                player["shield"] = 0
                        else:
                            player["health"] -= bullet["damage"]

                        if bullet in self.game_state["bullets"]:
                            self.game_state["bullets"].remove(bullet)
                        break

            for powerup in list(self.game_state["powerups"]):
                for player_id, player in self.game_state["players"].items():
                    if math.hypot(powerup["pos"][0] - player["pos"][0],
                                  powerup["pos"][1] - player["pos"][1]) < 25:
                        if powerup["type"] == "health":
                            player["health"] = min(
                                player["health"] + 25,
                                player.get("max_health", 100))
                        elif powerup["type"] == "shield":
                            player["shield"] = 30
                            player["shield_end_time"] = time.time() + 10
                        elif powerup["type"] == "speed":
                            player["movement_speed_boost"] = 1.5
                            player["speed_end_time"] = time.time() + 5
                        elif powerup["type"] == "damage":
                            player["damage_boost"] = 5
                            player["damage_end_time"] = time.time() + 8
                        elif powerup["type"] == "xp":
                            xp_gain = 30
                            if "xp" not in player:
                                player["xp"] = 0
                            if "xp_to_next_level" not in player:
                                player["xp_to_next_level"] = 100

                            player["xp"] += xp_gain

                            if player["xp"] >= player["xp_to_next_level"]:
                                player["level"] += 1
                                player["xp"] -= player["xp_to_next_level"]
                                player["xp_to_next_level"] = int(
                                    player["xp_to_next_level"] * 1.5)

                                if "upgrade_points" not in player:
                                    player["upgrade_points"] = 0
                                player["upgrade_points"] += 1

                        self.game_state["powerups"].remove(powerup)
                        break

    def close(self):
        self.running = False

        for client_socket in self.clients.values():
            try:
                client_socket.close()
            except:
                pass

        if self.socket:
            try:
                self.socket.close()
            except:
                pass

        logger.info("Server stopped")


class Game:

    def __init__(self):
        pygame.init()

        self.available_colors = {
            "Blue": COLORS["BLUE"],
            "Green": COLORS["GREEN"],
            "Purple": COLORS["PURPLE"],
            "Yellow": COLORS["YELLOW"],
            "Orange": COLORS["ORANGE"],
            "Cyan": COLORS["CYAN"],
            "Magenta": COLORS["MAGENTA"],
            "Red": COLORS["RED"]
        }
        self.player_color_name = "Blue"
        self.player_color = self.available_colors[self.player_color_name]
        self.show_cosmetics_menu = False

        info = pygame.display.Info()
        global WIDTH, HEIGHT
        WIDTH, HEIGHT = info.current_w, info.current_h

        self.fullscreen = True
        if self.fullscreen:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT),
                                                  pygame.FULLSCREEN)
        else:
            WIDTH, HEIGHT = 1280, 720
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))

        pygame.display.set_caption("Bulletverse.io")
        self.icon = pygame.Surface((32, 32))
        self.icon.fill(COLORS["BLUE"])
        pygame.draw.circle(self.icon, COLORS["WHITE"], (16, 16), 8)
        pygame.display.set_icon(self.icon)

        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 48)
        self.subtitle_font = pygame.font.Font(None, 36)

        self.running = True
        self.current_screen = "loading"
        self.show_upgrade_menu = False
        self.show_settings_menu = False
        self.show_help_menu = False
        self.clock = pygame.time.Clock()
        self.fps_display = True
        self.mouse_sensitivity = 1.0
        self.sound_volume = 0.7
        self.music_volume = 0.5
        self.particle_effects = True

        self.setup_loading_screen()

        self.frame_times = []
        self.last_update_time = time.time()
        self.update_interval = 1.0

    def setup_loading_screen(self):
        """Set up the loading screen and queue tasks"""
        self.loading_screen = LoadingScreen(self.screen, WIDTH, HEIGHT,
                                            self.font, self.title_font)

        self.loading_screen.add_task(self.load_settings, "Loading settings",
                                     10)
        self.loading_screen.add_task(self.initialize_particles,
                                     "Initializing particles", 5)
        self.loading_screen.add_task(self.load_sounds, "Loading game sounds",
                                     20)
        self.loading_screen.add_task(self.initialize_menus, "Setting up menus",
                                     15)
        self.loading_screen.add_task(self.setup_discord_rpc,
                                     "Connecting to Discord", 20)
        self.loading_screen.add_task(self.prepare_network, "Preparing network",
                                     10)
        self.loading_screen.add_task(self.reset_game,
                                     "Initializing game state", 15)

    def initialize_particles(self):
        """Initialize the particle system"""
        self.particles = ParticleSystem()
        self.powerups = []
        self.active_effects = {}
        self.difficulty = "normal"
        time.sleep(0.1)

    def initialize_menus(self):
        """Initialize all menus"""
        menu_width = 450
        menu_height = 600
        button_width = 350
        button_height = 60
        menu_x = (WIDTH - menu_width) // 2
        menu_y = (HEIGHT - menu_height) // 2

        self.menu_buttons = {
            "singleplayer":
            Button(menu_x + (menu_width - button_width) // 2,
                   menu_y + 120,
                   button_width,
                   button_height,
                   "Singleplayer",
                   border_radius=10,
                   font_size=30),
            "host":
            Button(menu_x + (menu_width - button_width) // 2,
                   menu_y + 200,
                   button_width,
                   button_height,
                   "Host Game (soon)",
                   border_radius=10,
                   font_size=30),
            "join":
            Button(menu_x + (menu_width - button_width) // 2,
                   menu_y + 280,
                   button_width,
                   button_height,
                   "Join Game (soon)",
                   border_radius=10,
                   font_size=30),
            "cosmetics":
            Button(menu_x + (menu_width - button_width) // 2,
                   menu_y + 360,
                   button_width,
                   button_height,
                   "Customize Tank",
                   border_radius=10,
                   font_size=30),
            "settings":
            Button(menu_x + (menu_width - button_width) // 2,
                   menu_y + 440,
                   button_width,
                   button_height,
                   "Settings",
                   border_radius=10,
                   font_size=30),
            "quit":
            Button(menu_x + (menu_width - button_width) // 2,
                   menu_y + 520,
                   button_width,
                   button_height,
                   "Quit",
                   border_radius=10,
                   font_size=30,
                   color=COLORS["RED"],
                   hover_color=(255, 100, 100))
        }

        left_column_x = WIDTH // 2 - 220
        right_column_x = WIDTH // 2 + 20
        row_height = 70

        self.settings_sliders = {
            "sensitivity":
            Slider(left_column_x, HEIGHT // 2 - 100, 200, 20, 0.1, 3.0,
                   self.mouse_sensitivity, "Mouse Sensitivity",
                   COLORS["BLUE"]),
            "sound":
            Slider(left_column_x, HEIGHT // 2 - 100 + row_height, 200, 20, 0.0,
                   1.0, self.sound_volume, "Sound Volume", COLORS["GREEN"]),
            "music":
            Slider(left_column_x, HEIGHT // 2 - 100 + row_height * 2, 200, 20,
                   0.0, 1.0, self.music_volume, "Music Volume",
                   COLORS["PURPLE"])
        }

        self.settings_buttons = {
            "fullscreen":
            Button(right_column_x,
                   HEIGHT // 2 - 100,
                   200,
                   40,
                   f"Fullscreen: {'ON' if self.fullscreen else 'OFF'}",
                   border_radius=5),
            "particles":
            Button(
                right_column_x,
                HEIGHT // 2 - 100 + row_height,
                200,
                40,
                f"Particle Effects: {'ON' if self.particle_effects else 'OFF'}",
                border_radius=5),
            "fps":
            Button(right_column_x,
                   HEIGHT // 2 - 100 + row_height * 2,
                   200,
                   40,
                   f"FPS Display: {'ON' if self.fps_display else 'OFF'}",
                   border_radius=5),
            "music":
            Button(right_column_x,
                   HEIGHT // 2 - 100 + row_height * 3,
                   200,
                   40,
                   "Toggle Music",
                   color=COLORS["BLUE"],
                   hover_color=(100, 150, 255),
                   border_radius=5),
            "back":
            Button(WIDTH // 2 - 100,
                   HEIGHT // 2 + 180,
                   200,
                   50,
                   "Back",
                   color=COLORS["RED"],
                   hover_color=(255, 100, 100),
                   border_radius=5)
        }

        self.difficulty_buttons = {
            "easy":
            Button(WIDTH // 2 - 200,
                   HEIGHT // 2 - 50,
                   120,
                   40,
                   "Easy",
                   color=COLORS["GREEN"],
                   hover_color=(100, 255, 100),
                   border_radius=5),
            "normal":
            Button(WIDTH // 2 - 60,
                   HEIGHT // 2 - 50,
                   120,
                   40,
                   "Normal",
                   color=COLORS["BLUE"],
                   hover_color=(100, 150, 255),
                   border_radius=5),
            "hard":
            Button(WIDTH // 2 + 80,
                   HEIGHT // 2 - 50,
                   120,
                   40,
                   "Hard",
                   color=COLORS["RED"],
                   hover_color=(255, 100, 100),
                   border_radius=5)
        }

        self.host_buttons = {
            "start":
            Button(WIDTH // 2 - 100,
                   HEIGHT // 2 + 50,
                   200,
                   50,
                   "Start Server",
                   color=COLORS["GREEN"],
                   hover_color=(100, 255, 100),
                   border_radius=5),
            "back":
            Button(WIDTH // 2 - 100,
                   HEIGHT // 2 + 120,
                   200,
                   50,
                   "Back",
                   color=COLORS["RED"],
                   hover_color=(255, 100, 100),
                   border_radius=5)
        }

        self.join_buttons = {
            "connect":
            Button(WIDTH // 2 - 100,
                   HEIGHT // 2 + 50,
                   200,
                   50,
                   "Connect",
                   color=COLORS["GREEN"],
                   hover_color=(100, 255, 100),
                   border_radius=5),
            "back":
            Button(WIDTH // 2 - 100,
                   HEIGHT // 2 + 120,
                   200,
                   50,
                   "Back",
                   color=COLORS["RED"],
                   hover_color=(255, 100, 100),
                   border_radius=5)
        }

        self.game_buttons = {
            "upgrade":
            Button(WIDTH - 210,
                   10,
                   200,
                   50,
                   "Upgrade Stats [U]",
                   border_radius=5),
            "menu":
            Button(WIDTH - 210,
                   70,
                   200,
                   50,
                   "Main Menu [ESC]",
                   border_radius=5)
        }

        self.host_port = SERVER_PORT
        self.join_ip = SERVER_HOST
        self.join_port = SERVER_PORT

        self.setup_cosmetics_menu()

        time.sleep(0.3)

        menu_width, menu_height = 500, 500
        menu_x, menu_y = (WIDTH - menu_width) // 2, (HEIGHT - menu_height) // 2

        self.color_buttons = {}
        button_width = 60
        button_height = 60
        button_margin = 20
        buttons_per_row = 4

        color_names = list(self.available_colors.keys())
        rows = (len(color_names) + buttons_per_row - 1) // buttons_per_row

        for i, color_name in enumerate(color_names):
            row = i // buttons_per_row
            col = i % buttons_per_row

            x = menu_x + 50 + col * (button_width + button_margin)
            y = menu_y + 120 + row * (button_height + button_margin)

            self.color_buttons[color_name] = Button(
                x,
                y,
                button_width,
                button_height,
                "",
                color=self.available_colors[color_name],
                hover_color=self.available_colors[color_name],
                border_radius=10)

        self.cosmetics_back_button = Button(menu_x + (menu_width - 200) // 2,
                                            menu_y + menu_height - 80,
                                            200,
                                            50,
                                            "Back",
                                            color=COLORS["RED"],
                                            hover_color=(255, 100, 100),
                                            border_radius=10)

        time.sleep(0.3)

    def prepare_network(self):
        """Initialize network components"""
        self.client = NetworkClient(SERVER_HOST, SERVER_PORT)
        self.server = None
        self.multiplayer_mode = False
        self.is_host = False
        self.new_bullets = []
        time.sleep(0.2)

    def load_settings(self):
        try:
            with open('settings.pkl', 'rb') as f:
                settings = pickle.load(f)
                self.fullscreen = settings.get('fullscreen', True)
                self.mouse_sensitivity = settings.get('mouse_sensitivity', 1.0)
                self.sound_volume = settings.get('sound_volume', 0.7)
                self.music_volume = settings.get('music_volume', 0.5)
                self.particle_effects = settings.get('particle_effects', True)
                self.fps_display = settings.get('fps_display', True)

                color_name = settings.get('player_color_name', 'Blue')
                if color_name in self.available_colors:
                    self.player_color_name = color_name
                    self.player_color = self.available_colors[
                        self.player_color_name]
        except:
            pass
        time.sleep(0.2)

    def save_settings(self):
        settings = {
            'fullscreen': self.fullscreen,
            'mouse_sensitivity': self.mouse_sensitivity,
            'sound_volume': self.sound_volume,
            'music_volume': self.music_volume,
            'particle_effects': self.particle_effects,
            'fps_display': self.fps_display,
            'player_color_name': self.player_color_name
        }

        try:
            with open('settings.pkl', 'wb') as f:
                pickle.dump(settings, f)
        except Exception as e:
            logger.error(f"Error saving settings: {e}")

    def load_sounds(self):
        try:
            pygame.mixer.quit()
            pygame.mixer.init(frequency=44100,
                              size=-16,
                              channels=2,
                              buffer=4096)
            logger.info("Sound mixer initialized with custom parameters")
        except Exception as e:
            logger.warning(f"Could not initialize mixer: {e}")

        self.sounds = {
            'shoot': None,
            'hit': None,
            'powerup': None,
            'level_up': None,
            'death': None,
            'button': None
        }

        if pygame.mixer.get_init():
            try:
                import os
                sounds_dir = 'assets/sounds'
                if not os.path.exists('assets'):
                    os.makedirs('assets')
                if not os.path.exists(sounds_dir):
                    os.makedirs(sounds_dir)
                    logger.warning(
                        f"Created missing sounds directory: {sounds_dir}")

                sound_files = {
                    'shoot': os.path.join(sounds_dir, 'shoot.wav'),
                    'hit': os.path.join(sounds_dir, 'hit.wav'),
                    'powerup': os.path.join(sounds_dir, 'powerup.wav'),
                    'level_up': os.path.join(sounds_dir, 'levelup.wav'),
                    'death': os.path.join(sounds_dir, 'death.wav'),
                    'button': os.path.join(sounds_dir, 'button.wav')
                }

                for sound_name, file_path in sound_files.items():
                    try:
                        if os.path.exists(file_path):
                            self.sounds[sound_name] = pygame.mixer.Sound(
                                file_path)
                        else:
                            logger.warning(
                                f"Sound file not found: {file_path}")
                    except Exception as e:
                        logger.warning(
                            f"Failed to load sound {sound_name}: {e}")

                for sound in self.sounds.values():
                    if sound:
                        sound.set_volume(self.sound_volume)

                logger.info(
                    f"Loaded {sum(1 for s in self.sounds.values() if s is not None)} sound files"
                )
            except Exception as e:
                logger.warning(f"Error initializing sounds: {e}")
        else:
            logger.warning(
                "Sound mixer not initialized, continuing without sound")

        self.load_and_play_background_music()

        time.sleep(0.5)

    def load_and_play_background_music(self):
        """Dedicated method to handle background music with robust error handling"""
        try:
            import os

            possible_paths = [
                'assets/sounds/background.mp3',
            ]

            music_file = None
            for path in possible_paths:
                if os.path.exists(path):
                    music_file = path
                    logger.info(f"Found music file at: {path}")
                    break

            if not pygame.mixer.get_init():
                logger.warning("Cannot play music: mixer not initialized")
                return

            if not music_file:
                logger.warning(
                    f"No background music file found. Checked paths: {possible_paths}"
                )
                os.makedirs('assets/sounds', exist_ok=True)
                return

            try:
                pygame.mixer.music.load(music_file)
                pygame.mixer.music.set_volume(self.music_volume)
                pygame.mixer.music.play(-1)
                logger.info(
                    f"Background music started from {music_file} (standard method)"
                )

                self.music_file_path = music_file
            except Exception as e:
                logger.warning(f"Standard music loading failed: {e}")
                try:
                    music_sound = pygame.mixer.Sound(music_file)
                    music_sound.set_volume(self.music_volume)
                    music_sound.play(-1)
                    self.music_sound = music_sound
                    self.music_file_path = music_file
                    logger.info(
                        f"Background music started from {music_file} (alternative method)"
                    )
                except Exception as e2:
                    logger.warning(f"Alternative music loading failed: {e2}")

        except Exception as e:
            logger.error(f"Music initialization failed: {e}")

    def toggle_music(self):
        """Toggle background music on/off"""
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.pause()
                logger.info("Music paused")
            else:
                pygame.mixer.music.unpause()
                if not pygame.mixer.music.get_busy():
                    pygame.mixer.music.play(-1)
                logger.info("Music resumed")
        except Exception as e:
            logger.warning(f"Error toggling music: {e}")
            if hasattr(self, 'music_sound'):
                try:
                    self.music_sound.stop()
                    self.music_sound.play(-1)
                    logger.info("Music toggled (alternative method)")
                except Exception as e2:
                    logger.warning(f"Alternative music toggle failed: {e2}")

            time.sleep(0.5)

    def play_sound(self, sound_name):
        if sound_name in self.sounds and self.sounds[sound_name]:
            try:
                self.sounds[sound_name].play()
            except Exception as e:
                logger.warning(f"Error playing sound {sound_name}: {e}")

    def setup_discord_rpc(self):
        try:
            client_id = '1345600362706374717'
            self.rpc = Presence(client_id)
            self.rpc.connect()
            self.rpc.update(
                details="Game was created here:",
                state=".gg/XVN6mYv5AJ",
                large_image="https://i.imgur.com/vn4pYBH.png",
                large_text="Bulletverse.io",
                small_image=
                "https://th.bing.com/th/id/R.da61fa152c102c46c16786b9f79402f8?rik=l5kvYddcePaDtw&pid=ImgRaw&r=0",
                small_text="https://discord.gg/XVN6mYv5AJ",
                start=int(time.time()))
            logger.info("Discord RPC connected")
        except:
            self.rpc = None
            logger.warning("Discord RPC failed to connect")
        time.sleep(0.3)

    def setup_cosmetics_menu(self):
        menu_width, menu_height = 500, 500
        menu_x, menu_y = (WIDTH - menu_width) // 2, (HEIGHT - menu_height) // 2

        self.color_buttons = {}
        button_width = 60
        button_height = 60
        button_margin = 20
        buttons_per_row = 4

        color_names = list(self.available_colors.keys())
        rows = (len(color_names) + buttons_per_row - 1) // buttons_per_row

        for i, color_name in enumerate(color_names):
            row = i // buttons_per_row
            col = i % buttons_per_row

            x = menu_x + 50 + col * (button_width + button_margin)
            y = menu_y + 120 + row * (button_height + button_margin)

            self.color_buttons[color_name] = Button(
                x,
                y,
                button_width,
                button_height,
                "",
                color=self.available_colors[color_name],
                hover_color=self.available_colors[color_name],
                border_radius=10)

        self.cosmetics_back_button = Button(menu_x + (menu_width - 200) // 2,
                                            menu_y + menu_height - 80,
                                            200,
                                            50,
                                            "Back",
                                            color=COLORS["RED"],
                                            hover_color=(255, 100, 100),
                                            border_radius=10)
        time.sleep(0.2)

    def draw_cosmetics_menu(self):
        if not self.show_cosmetics_menu:
            return

        if not hasattr(self, 'cosmetics_overlay'):
            self.cosmetics_overlay = pygame.Surface((WIDTH, HEIGHT),
                                                    pygame.SRCALPHA)
            self.cosmetics_overlay.fill((0, 0, 0, 128))
        self.screen.blit(self.cosmetics_overlay, (0, 0))

        menu_width, menu_height = 500, 500
        menu_x, menu_y = (WIDTH - menu_width) // 2, (HEIGHT - menu_height) // 2

        pygame.draw.rect(self.screen,
                         COLORS["WHITE"],
                         (menu_x, menu_y, menu_width, menu_height),
                         border_radius=15)
        pygame.draw.rect(self.screen,
                         COLORS["BLACK"],
                         (menu_x, menu_y, menu_width, menu_height),
                         3,
                         border_radius=15)

        title = self.title_font.render("Tank Customization", True,
                                       COLORS["BLACK"])
        title_rect = title.get_rect(center=(menu_x + menu_width // 2,
                                            menu_y + 40))
        self.screen.blit(title, title_rect)

        subtitle = self.font.render("Select Tank Color:", True,
                                    COLORS["BLACK"])
        subtitle_rect = subtitle.get_rect(midleft=(menu_x + 50, menu_y + 90))
        self.screen.blit(subtitle, subtitle_rect)

        mouse_pos = pygame.mouse.get_pos()
        for color_name, button in self.color_buttons.items():
            button.update(mouse_pos)
            button.draw(self.screen)

            if color_name == self.player_color_name:
                rect = button.rect.copy()
                rect.inflate_ip(10, 10)
                pygame.draw.rect(self.screen,
                                 COLORS["BLACK"],
                                 rect,
                                 3,
                                 border_radius=10)

        self.cosmetics_back_button.update(mouse_pos)
        self.cosmetics_back_button.draw(self.screen)

        preview_x = menu_x + menu_width // 2
        preview_y = menu_y + 350
        preview_text = self.font.render("Preview:", True, COLORS["BLACK"])
        self.screen.blit(preview_text, (preview_x - 80, preview_y - 40))

        self.draw_tank((preview_x, preview_y), 0, self.player_color, False, 30)

    def reset_game(self):
        self.player_pos = [WIDTH // 2, HEIGHT // 2]
        self.player_angle = 0
        self.player_health = 100
        self.player_shield = 0
        self.player_xp = 0
        self.player_level = 1
        self.xp_to_next_level = 100
        self.player_upgrade_points = 3
        self.score = 0
        self.kills = 0

        self.bullets = []
        self.enemy_bullets = []
        self.enemies = [
            spawn_enemy(self.difficulty) for _ in range(NUM_ENEMIES)
        ]
        self.powerups = []
        self.particles = ParticleSystem()

        self.player_stats = {
            "max_health": 100,
            "regen": 0,
            "bullet_damage": 10,
            "bullet_speed": BULLET_SPEED,
            "bullet_penetration": 1,
            "bullet_reload": 10,
            "movement_speed": 4,
        }

        self.active_effects = {
            "shield": {
                "active": False,
                "end_time": 0
            },
            "speed_boost": {
                "active": False,
                "end_time": 0
            },
            "damage_boost": {
                "active": False,
                "end_time": 0
            }
        }

        self.reload_timer = 0
        self.respawn_time = 0
        self.is_dead = False
        self.game_start_time = time.time()
        self.last_powerup_time = time.time()
        self.last_regen_time = time.time()

        self.new_bullets = []

        time.sleep(0.3)

    def draw_tank(self,
                  pos,
                  angle,
                  color=COLORS["BLUE"],
                  shield=False,
                  size=20):
        outline_size = size + 2
        pygame.draw.circle(self.screen, COLORS["BLACK"],
                           (int(pos[0]), int(pos[1])), outline_size)

        pygame.draw.circle(self.screen, color, (int(pos[0]), int(pos[1])),
                           size)

        barrel_length = size * 1.25
        barrel_width = int(size / 4)
        outline_width = barrel_width + 2

        barrel_x = pos[0] + barrel_length * math.cos(angle)
        barrel_y = pos[1] + barrel_length * math.sin(angle)

        pygame.draw.line(self.screen, COLORS["BLACK"],
                         (int(pos[0]), int(pos[1])),
                         (int(barrel_x), int(barrel_y)), outline_width)

        pygame.draw.line(self.screen, color, (int(pos[0]), int(pos[1])),
                         (int(barrel_x), int(barrel_y)), barrel_width)

        if shield:
            shield_radius = size + 5
            for i in range(3):
                pulse_offset = (time.time() * 3) % 1.0
                pulse_size = shield_radius + i * 2 + pulse_offset * 2
                pygame.draw.circle(self.screen, (100, 150, 255, 100),
                                   (int(pos[0]), int(pos[1])), int(pulse_size),
                                   2)

    def draw_bullets(self):
        for bullet in self.bullets:
            pygame.draw.circle(self.screen, COLORS["BLUE"],
                               (int(bullet[0]), int(bullet[1])), 5)

        for bullet in self.enemy_bullets:
            pygame.draw.circle(self.screen, COLORS["RED"],
                               (int(bullet[0]), int(bullet[1])), 5)

        if self.multiplayer_mode and "bullets" in self.client.game_state:
            for bullet in self.client.game_state["bullets"]:
                if "owner" in bullet and bullet[
                        "owner"] == self.client.player_id:
                    continue

                color = COLORS["YELLOW"] if bullet[
                    "owner"] != "enemy" else COLORS["RED"]
                pygame.draw.circle(
                    self.screen, color,
                    (int(bullet["pos"][0]), int(bullet["pos"][1])), 5)

    def draw_enemies(self):
        enemy_list = self.client.game_state[
            "enemies"] if self.multiplayer_mode else self.enemies

        for enemy in enemy_list:
            enemy_type = enemy.get("type", "normal")
            if enemy_type == "normal":
                color = COLORS["RED"]
            elif enemy_type == "fast":
                color = COLORS["ORANGE"]
            elif enemy_type == "tank":
                color = COLORS["MAGENTA"]
            else:
                color = COLORS["RED"]

            size = enemy.get("size", 20)
            self.draw_tank((enemy["pos"][0], enemy["pos"][1]),
                           enemy.get("angle", 0), color, False, size)

            max_health = enemy.get("max_health", 30)
            health_pct = enemy["health"] / max_health
            health_width = int(size * 2 * health_pct)

            health_bar_y = enemy["pos"][1] - size - 10
            pygame.draw.rect(
                self.screen, COLORS["DARK_GRAY"],
                (enemy["pos"][0] - size, health_bar_y, size * 2, 5))
            pygame.draw.rect(
                self.screen, COLORS["GREEN"],
                (enemy["pos"][0] - size, health_bar_y, health_width, 5))

    def draw_players(self):
        if not self.is_dead:
            has_shield = self.player_shield > 0 or (
                self.active_effects["shield"]["active"]
                and time.time() < self.active_effects["shield"]["end_time"])
            self.draw_tank(self.player_pos, self.player_angle,
                           self.player_color, has_shield)

        if self.multiplayer_mode:
            color_idx = 0
            for player_id, player_data in self.client.game_state[
                    "players"].items():
                if player_id != self.client.player_id:
                    color = PLAYER_COLORS[color_idx % len(PLAYER_COLORS)]
                    has_shield = "shield" in player_data and player_data[
                        "shield"] > 0
                    self.draw_tank(player_data["pos"], player_data["angle"],
                                   color, has_shield)

                    name_text = self.font.render(
                        f"Player {player_id} [Lv.{player_data.get('level', 1)}]",
                        True, COLORS["BLACK"])
                    self.screen.blit(name_text, (player_data["pos"][0] - 50,
                                                 player_data["pos"][1] - 40))

                    color_idx += 1

    def draw_powerups(self):
        if self.multiplayer_mode and "powerups" in self.client.game_state:
            for powerup_data in self.client.game_state["powerups"]:
                pos = powerup_data.get("pos", [0, 0])
                powerup_type = powerup_data.get("type", "xp")

                powerup = PowerUp((pos[0], pos[1]), powerup_type)
                powerup.update()
                powerup.draw(self.screen)
        else:
            for powerup in self.powerups:
                powerup.update()
                powerup.draw(self.screen)

    def draw_particles(self):
        if self.particle_effects:
            self.particles.draw(self.screen)

    def draw_ui(self):
        health_text = self.font.render(
            f"Health: {int(self.player_health)}/{self.player_stats['max_health']}",
            True, COLORS["RED"])
        shield_text = self.font.render(f"Shield: {int(self.player_shield)}",
                                       True, COLORS["BLUE"])
        xp_text = self.font.render(
            f"XP: {self.player_xp}/{self.xp_to_next_level}", True,
            COLORS["BLUE"])
        level_text = self.font.render(f"Level: {self.player_level}", True,
                                      COLORS["BLACK"])
        points_text = self.font.render(
            f"Upgrade Points: {self.player_upgrade_points}", True,
            COLORS["GREEN"])
        score_text = self.font.render(f"Score: {self.score}", True,
                                      COLORS["PURPLE"])
        kills_text = self.font.render(f"Kills: {self.kills}", True,
                                      COLORS["RED"])

        seconds_played = int(time.time() - self.game_start_time)
        minutes = seconds_played // 60
        seconds = seconds_played % 60
        time_text = self.font.render(f"Time: {minutes:02d}:{seconds:02d}",
                                     True, COLORS["BLACK"])

        panel_height = 180
        pygame.draw.rect(self.screen, (240, 240, 240, 200),
                         (0, 0, 220, panel_height))
        pygame.draw.rect(self.screen, COLORS["DARK_GRAY"],
                         (0, 0, 220, panel_height), 2)

        self.screen.blit(health_text, (10, 10))
        self.screen.blit(shield_text, (10, 35))
        self.screen.blit(xp_text, (10, 60))
        self.screen.blit(level_text, (10, 85))
        self.screen.blit(points_text, (10, 110))
        self.screen.blit(score_text, (10, 135))
        self.screen.blit(kills_text, (10, 160))
        self.screen.blit(time_text, (WIDTH - 120, 10))

        effect_y = 200
        for effect_name, effect_data in self.active_effects.items():
            if effect_data["active"] and time.time() < effect_data["end_time"]:
                remaining = int(effect_data["end_time"] - time.time())
                effect_text = self.font.render(
                    f"{effect_name.replace('_', ' ').title()}: {remaining}s",
                    True, COLORS["BLUE"])
                self.screen.blit(effect_text, (10, effect_y))
                effect_y += 25

        pygame.draw.rect(self.screen, COLORS["DARK_GRAY"], (230, 10, 200, 15))
        xp_width = int((self.player_xp / self.xp_to_next_level) * 200)
        pygame.draw.rect(self.screen, COLORS["BLUE"], (230, 10, xp_width, 15))

        pygame.draw.rect(self.screen, COLORS["DARK_GRAY"], (230, 35, 200, 15))
        health_width = int(
            (self.player_health / self.player_stats["max_health"]) * 200)
        pygame.draw.rect(self.screen, COLORS["RED"],
                         (230, 35, health_width, 15))

        if self.player_shield > 0:
            pygame.draw.rect(self.screen, COLORS["DARK_GRAY"],
                             (230, 60, 200, 10))
            shield_width = int((self.player_shield / 30) * 200)
            pygame.draw.rect(self.screen, (100, 150, 255),
                             (230, 60, shield_width, 10))

        if self.multiplayer_mode:
            players_text = self.font.render(
                f"Players: {len(self.client.game_state['players'])}", True,
                COLORS["BLACK"])
            ping_text = self.font.render(f"Ping: {self.client.ping} ms", True,
                                         COLORS["BLACK"])
            self.screen.blit(players_text, (WIDTH - 120, 35))
            self.screen.blit(ping_text, (WIDTH - 120, 60))

        if self.fps_display:
            current_time = time.time()
            elapsed = current_time - self.last_update_time

            self.frame_times.append(self.clock.get_time())

            if len(self.frame_times) > 60:
                self.frame_times.pop(0)

            if elapsed >= self.update_interval:
                self.last_update_time = current_time

            avg_frame_time = sum(self.frame_times) / len(
                self.frame_times) if self.frame_times else 0
            fps = 0 if avg_frame_time == 0 else 1000 / avg_frame_time

            fps_text = self.font.render(
                f"FPS: {int(fps)}", True, COLORS["GREEN"] if fps >= 55 else
                COLORS["YELLOW"] if fps >= 30 else COLORS["RED"])
            self.screen.blit(fps_text, (WIDTH - 100, HEIGHT - 30))

        mouse_pos = pygame.mouse.get_pos()
        for button in self.game_buttons.values():
            button.update(mouse_pos)
            button.draw(self.screen)

    def draw_upgrade_menu(self):
        if not self.show_upgrade_menu:
            return

        menu_width, menu_height = 500, 600
        menu_x, menu_y = (WIDTH - menu_width) // 2, (HEIGHT - menu_height) // 2

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))

        pygame.draw.rect(self.screen,
                         COLORS["WHITE"],
                         (menu_x, menu_y, menu_width, menu_height),
                         border_radius=15)
        pygame.draw.rect(self.screen,
                         COLORS["BLACK"],
                         (menu_x, menu_y, menu_width, menu_height),
                         3,
                         border_radius=15)

        title = self.title_font.render("Upgrade Stats", True, COLORS["BLACK"])
        title_rect = title.get_rect(center=(menu_x + menu_width // 2,
                                            menu_y + 40))
        self.screen.blit(title, title_rect)

        points_text = self.subtitle_font.render(
            f"Upgrade Points: {self.player_upgrade_points}", True,
            COLORS["GREEN"])
        points_rect = points_text.get_rect(center=(menu_x + menu_width // 2,
                                                   menu_y + 80))
        self.screen.blit(points_text, points_rect)

        y_offset = 130
        button_width, button_height = 40, 40

        stats_info = [
            ("Health Max", "max_health", 10),
            ("Health Regen", "regen", 0.5),
            ("Bullet Damage", "bullet_damage", 2),
            ("Bullet Speed", "bullet_speed", 0.5),
            ("Bullet Penetration", "bullet_penetration", 1),
            ("Reload Speed", "bullet_reload", -1),
            ("Movement Speed", "movement_speed", 0.2),
        ]

        for name, stat_key, increment in stats_info:
            stat_text = self.font.render(name, True, COLORS["BLACK"])
            self.screen.blit(stat_text, (menu_x + 30, menu_y + y_offset))

            stat_level = self.get_stat_level(stat_key)
            for i in range(MAX_STAT_LEVEL):
                rect = pygame.Rect(menu_x + 220 + i * 20, menu_y + y_offset,
                                   15, 20)
                color = COLORS["BLUE"] if i < stat_level else COLORS["GRAY"]
                pygame.draw.rect(self.screen, color, rect, border_radius=3)
                pygame.draw.rect(self.screen,
                                 COLORS["BLACK"],
                                 rect,
                                 1,
                                 border_radius=3)

            upgrade_button = pygame.Rect(menu_x + menu_width - 90,
                                         menu_y + y_offset - 5, button_width,
                                         button_height)
            color = COLORS[
                "GREEN"] if self.player_upgrade_points > 0 and stat_level < MAX_STAT_LEVEL else COLORS[
                    "GRAY"]
            pygame.draw.rect(self.screen,
                             color,
                             upgrade_button,
                             border_radius=5)
            pygame.draw.rect(self.screen,
                             COLORS["BLACK"],
                             upgrade_button,
                             2,
                             border_radius=5)

            plus_text = self.font.render("+", True, COLORS["BLACK"])
            plus_rect = plus_text.get_rect(center=upgrade_button.center)
            self.screen.blit(plus_text, plus_rect)

            value_text = self.font.render(f"{self.player_stats[stat_key]}",
                                          True, COLORS["BLACK"])
            self.screen.blit(value_text, (menu_x + 390, menu_y + y_offset))

            y_offset += 60

        close_button = pygame.Rect(menu_x + (menu_width - 200) // 2,
                                   menu_y + menu_height - 80, 200, 50)
        pygame.draw.rect(self.screen,
                         COLORS["GRAY"],
                         close_button,
                         border_radius=10)
        pygame.draw.rect(self.screen,
                         COLORS["BLACK"],
                         close_button,
                         2,
                         border_radius=10)

        close_text = self.font.render("Close [U]", True, COLORS["BLACK"])
        close_rect = close_text.get_rect(center=close_button.center)
        self.screen.blit(close_text, close_rect)

    def draw_settings_menu(self):
        if not self.show_settings_menu:
            return

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))

        menu_width, menu_height = 500, 600
        menu_x, menu_y = (WIDTH - menu_width) // 2, (HEIGHT - menu_height) // 2

        pygame.draw.rect(self.screen,
                         COLORS["WHITE"],
                         (menu_x, menu_y, menu_width, menu_height),
                         border_radius=15)
        pygame.draw.rect(self.screen,
                         COLORS["BLACK"],
                         (menu_x, menu_y, menu_width, menu_height),
                         3,
                         border_radius=15)

        title = self.title_font.render("Settings", True, COLORS["BLACK"])
        title_rect = title.get_rect(center=(menu_x + menu_width // 2,
                                            menu_y + 40))
        self.screen.blit(title, title_rect)

        sliders_header = self.font.render("Controls", True, COLORS["BLACK"])
        buttons_header = self.font.render("Options", True, COLORS["BLACK"])

        sliders_header_rect = sliders_header.get_rect(center=(menu_x +
                                                              menu_width // 4,
                                                              menu_y + 80))
        buttons_header_rect = buttons_header.get_rect(
            center=(menu_x + menu_width * 3 // 4, menu_y + 80))

        self.screen.blit(sliders_header, sliders_header_rect)
        self.screen.blit(buttons_header, buttons_header_rect)

        pygame.draw.line(
            self.screen, COLORS["GRAY"],
            (menu_x + menu_width // 2, menu_y + 100),
            (menu_x + menu_width // 2, menu_y + menu_height - 100), 2)

        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()

        for slider in self.settings_sliders.values():
            slider.value = slider.update(mouse_pos, mouse_pressed)
            slider.draw(self.screen)

        self.settings_buttons[
            "fullscreen"].text = f"Fullscreen: {'ON' if self.fullscreen else 'OFF'}"
        self.settings_buttons[
            "particles"].text = f"Particle Effects: {'ON' if self.particle_effects else 'OFF'}"
        self.settings_buttons[
            "fps"].text = f"FPS Display: {'ON' if self.fps_display else 'OFF'}"

        for button in self.settings_buttons.values():
            button.update(mouse_pos)
            button.draw(self.screen)

    def draw_host_menu(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))

        menu_width, menu_height = 500, 300
        menu_x, menu_y = (WIDTH - menu_width) // 2, (HEIGHT - menu_height) // 2

        pygame.draw.rect(self.screen,
                         COLORS["WHITE"],
                         (menu_x, menu_y, menu_width, menu_height),
                         border_radius=15)
        pygame.draw.rect(self.screen,
                         COLORS["BLACK"],
                         (menu_x, menu_y, menu_width, menu_height),
                         3,
                         border_radius=15)

        title = self.title_font.render("Host Game", True, COLORS["BLACK"])
        title_rect = title.get_rect(center=(menu_x + menu_width // 2,
                                            menu_y + 40))
        self.screen.blit(title, title_rect)

        info_text = self.font.render(
            f"Server will start on localhost:{self.host_port}", True,
            COLORS["BLACK"])
        info_rect = info_text.get_rect(center=(menu_x + menu_width // 2,
                                               menu_y + 100))
        self.screen.blit(info_text, info_rect)

        mouse_pos = pygame.mouse.get_pos()

        diff_text = self.font.render("Difficulty:", True, COLORS["BLACK"])
        diff_rect = diff_text.get_rect(topleft=(menu_x + 50, menu_y + 150))
        self.screen.blit(diff_text, diff_rect)

        for name, button in self.difficulty_buttons.items():
            color_boost = 50 if name == self.difficulty else 0
            original_color = button.color
            if name == self.difficulty:
                r, g, b = original_color
                button.color = (min(255, r + color_boost),
                                min(255, g + color_boost),
                                min(255, b + color_boost))

            button.update(mouse_pos)
            button.draw(self.screen)

            button.color = original_color

        for button in self.host_buttons.values():
            button.update(mouse_pos)
            button.draw(self.screen)

    def draw_join_menu(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))

        menu_width, menu_height = 500, 300
        menu_x, menu_y = (WIDTH - menu_width) // 2, (HEIGHT - menu_height) // 2

        pygame.draw.rect(self.screen,
                         COLORS["WHITE"],
                         (menu_x, menu_y, menu_width, menu_height),
                         border_radius=15)
        pygame.draw.rect(self.screen,
                         COLORS["BLACK"],
                         (menu_x, menu_y, menu_width, menu_height),
                         3,
                         border_radius=15)

        title = self.title_font.render("Join Game", True, COLORS["BLACK"])
        title_rect = title.get_rect(center=(menu_x + menu_width // 2,
                                            menu_y + 40))
        self.screen.blit(title, title_rect)

        info_text = self.font.render(
            f"Connect to: {self.join_ip}:{self.join_port}", True,
            COLORS["BLACK"])
        info_rect = info_text.get_rect(center=(menu_x + menu_width // 2,
                                               menu_y + 100))
        self.screen.blit(info_text, info_rect)

        note_text = self.font.render("(Edit server.py to change IP/port)",
                                     True, COLORS["DARK_GRAY"])
        note_rect = note_text.get_rect(center=(menu_x + menu_width // 2,
                                               menu_y + 130))
        self.screen.blit(note_text, note_rect)

        mouse_pos = pygame.mouse.get_pos()
        for button in self.join_buttons.values():
            button.update(mouse_pos)
            button.draw(self.screen)

    def draw_main_menu(self):
        self.screen.fill(COLORS["WHITE"])

        current_time = time.time()
        for i in range(20):
            x = (WIDTH //
                 2) + math.cos(current_time * 0.5 + i * 0.5) * (WIDTH // 3)
            y = (HEIGHT //
                 2) + math.sin(current_time * 0.5 + i * 0.7) * (HEIGHT // 3)
            size = 20 + 10 * math.sin(current_time + i)
            alpha = int(128 + 64 * math.sin(current_time * 0.3 + i * 0.2))

            circle_surf = pygame.Surface((int(size * 2), int(size * 2)),
                                         pygame.SRCALPHA)
            color = (*PLAYER_COLORS[i % len(PLAYER_COLORS)][:3], alpha)
            pygame.draw.circle(circle_surf, color, (int(size), int(size)),
                               int(size))
            self.screen.blit(circle_surf, (int(x - size), int(y - size)))

        menu_width = 450
        menu_height = 600
        menu_x = (WIDTH - menu_width) // 2
        menu_y = (HEIGHT - menu_height) // 2

        pygame.draw.rect(self.screen, (255, 255, 255, 230),
                         (menu_x, menu_y, menu_width, menu_height),
                         border_radius=20)
        pygame.draw.rect(self.screen,
                         COLORS["BLACK"],
                         (menu_x, menu_y, menu_width, menu_height),
                         3,
                         border_radius=20)

        title = self.title_font.render("BULLETVERSE.IO", True, COLORS["BLUE"])
        subtitle = self.font.render("Multiplayer Tank Battle", True,
                                    COLORS["BLACK"])

        title_rect = title.get_rect(center=(menu_x + menu_width // 2,
                                            menu_y + 60))
        subtitle_rect = subtitle.get_rect(center=(menu_x + menu_width // 2,
                                                  menu_y + 90))

        self.screen.blit(title, title_rect)
        self.screen.blit(subtitle, subtitle_rect)

        mouse_pos = pygame.mouse.get_pos()
        for button in self.menu_buttons.values():
            button.update(mouse_pos)
            button.draw(self.screen)

        version_text = self.font.render("Version 2.0", True,
                                        COLORS["DARK_GRAY"])
        self.screen.blit(version_text, (WIDTH - 120, HEIGHT - 30))

        if self.show_cosmetics_menu:
            self.draw_cosmetics_menu()

    def draw_death_screen(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        death_text = self.title_font.render("You Died!", True, COLORS["RED"])
        death_rect = death_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        self.screen.blit(death_text, death_rect)

        remaining = max(0, int(self.respawn_time - time.time()))
        respawn_text = self.subtitle_font.render(
            f"Respawning in {remaining}...", True, COLORS["WHITE"])
        respawn_rect = respawn_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.screen.blit(respawn_text, respawn_rect)

        stats_text = self.font.render(
            f"Score: {self.score}   Kills: {self.kills}   Level: {self.player_level}",
            True, COLORS["WHITE"])
        stats_rect = stats_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
        self.screen.blit(stats_text, stats_rect)

    def get_stat_level(self, stat_key):
        base_values = {
            "max_health": 100,
            "regen": 0,
            "bullet_damage": 10,
            "bullet_speed": BULLET_SPEED,
            "bullet_penetration": 1,
            "bullet_reload": 10,
            "movement_speed": 4,
        }

        increments = {
            "max_health": 10,
            "regen": 0.5,
            "bullet_damage": 2,
            "bullet_speed": 0.5,
            "bullet_penetration": 1,
            "bullet_reload": -1,
            "movement_speed": 0.2,
        }

        current = self.player_stats[stat_key]
        base = base_values[stat_key]
        increment = increments[stat_key]

        if increment > 0:
            return int((current - base) / increment)
        else:
            return int((base - current) / abs(increment))

    def handle_upgrade_click(self, pos):
        if not self.show_upgrade_menu or self.player_upgrade_points <= 0:
            return

        menu_width, menu_height = 500, 600
        menu_x, menu_y = (WIDTH - menu_width) // 2, (HEIGHT - menu_height) // 2
        button_width, button_height = 40, 40

        stats_info = [
            ("Health Max", "max_health", 10),
            ("Health Regen", "regen", 0.5),
            ("Bullet Damage", "bullet_damage", 2),
            ("Bullet Speed", "bullet_speed", 0.5),
            ("Bullet Penetration", "bullet_penetration", 1),
            ("Reload Speed", "bullet_reload", -1),
            ("Movement Speed", "movement_speed", 0.2),
        ]

        y_offset = 130
        for _, stat_key, increment in stats_info:
            upgrade_button = pygame.Rect(menu_x + menu_width - 90,
                                         menu_y + y_offset - 5, button_width,
                                         button_height)
            stat_level = self.get_stat_level(stat_key)

            if upgrade_button.collidepoint(
                    pos) and stat_level < MAX_STAT_LEVEL:
                self.player_stats[stat_key] += increment
                self.player_upgrade_points -= 1
                self.play_sound('button')
                break

            y_offset += 60

        close_button = pygame.Rect(menu_x + (menu_width - 200) // 2,
                                   menu_y + menu_height - 80, 200, 50)
        if close_button.collidepoint(pos):
            self.show_upgrade_menu = False
            self.play_sound('button')

    def handle_settings_click(self, pos, event):

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.settings_buttons["fullscreen"].is_clicked(event):
                self.fullscreen = not self.fullscreen
                self.apply_display_mode()
                self.play_sound('button')
                return True

            elif self.settings_buttons["particles"].is_clicked(event):
                self.particle_effects = not self.particle_effects
                self.play_sound('button')
                return True

            elif self.settings_buttons["music"].is_clicked(event):
                self.toggle_music()
                self.play_sound('button')
                return True

            elif self.settings_buttons["fps"].is_clicked(event):
                self.fps_display = not self.fps_display
                self.play_sound('button')
                return True

            elif self.settings_buttons["back"].is_clicked(event):
                self.show_settings_menu = False
                self.save_settings()
                self.play_sound('button')
                return True

        return False

    def apply_display_mode(self):
        global WIDTH, HEIGHT

        pygame.display.quit()
        pygame.display.init()

        if self.fullscreen:
            info = pygame.display.Info()
            WIDTH, HEIGHT = info.current_w, info.current_h
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT),
                                                  pygame.FULLSCREEN)
        else:
            WIDTH, HEIGHT = 1280, 720
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))

        self.initialize_menus()

    def update_settings(self):
        self.mouse_sensitivity = self.settings_sliders["sensitivity"].value

        new_sound_volume = self.settings_sliders["sound"].value
        if new_sound_volume != self.sound_volume:
            self.sound_volume = new_sound_volume
            for sound in self.sounds.values():
                if sound:
                    sound.set_volume(self.sound_volume)

        new_music_volume = self.settings_sliders["music"].value
        if new_music_volume != self.music_volume:
            self.music_volume = new_music_volume
            pygame.mixer.music.set_volume(self.music_volume)

    def handle_menu_events(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.show_settings_menu:
                self.show_settings_menu = False
                self.save_settings()
                return True

        if self.current_screen == "main_menu" and not self.show_settings_menu and not self.show_cosmetics_menu:
            if self.menu_buttons["singleplayer"].is_clicked(event):
                self.current_screen = "game"
                self.multiplayer_mode = False
                self.reset_game()
                self.play_sound('button')
                return True

            if self.menu_buttons["host"].is_clicked(event):
                self.current_screen = "host"
                self.play_sound('button')
                return True

            if self.menu_buttons["join"].is_clicked(event):
                self.current_screen = "join"
                self.play_sound('button')
                return True

            if self.menu_buttons["cosmetics"].is_clicked(event):
                self.show_cosmetics_menu = True
                self.play_sound('button')
                return True

            if self.menu_buttons["settings"].is_clicked(event):
                self.show_settings_menu = True
                self.play_sound('button')
                return True

            if self.menu_buttons["quit"].is_clicked(event):
                self.running = False
                self.play_sound('button')
                return True

        if self.show_settings_menu:
            return self.handle_settings_click(pygame.mouse.get_pos(), event)

        if self.current_screen == "host":
            for name, button in self.difficulty_buttons.items():
                if button.is_clicked(event):
                    self.difficulty = name
                    self.play_sound('button')
                    return True

            if self.host_buttons["start"].is_clicked(event):
                self.server = GameServer(SERVER_HOST, self.host_port)
                if self.server.start():
                    time.sleep(0.5)

                    self.server.difficulty = self.difficulty

                    if self.client.connect():
                        self.current_screen = "game"
                        self.multiplayer_mode = True
                        self.is_host = True
                        self.reset_game()
                        self.play_sound('button')
                        return True
                else:
                    self.server = None
                return False

            if self.host_buttons["back"].is_clicked(event):
                self.current_screen = "main_menu"
                self.play_sound('button')
                return True

        if self.show_cosmetics_menu:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for color_name, button in self.color_buttons.items():
                    if button.is_clicked(event):
                        self.player_color_name = color_name
                        self.player_color = self.available_colors[color_name]
                        self.play_sound('button')
                        return True

                if self.cosmetics_back_button.is_clicked(event):
                    self.show_cosmetics_menu = False
                    self.save_settings()
                    self.play_sound('button')
                    return True

        if self.current_screen == "join":
            if self.join_buttons["connect"].is_clicked(event):
                if self.client.connect():
                    self.current_screen = "game"
                    self.multiplayer_mode = True
                    self.is_host = False
                    self.reset_game()
                    self.play_sound('button')
                    return True
                return False

            if self.join_buttons["back"].is_clicked(event):
                self.current_screen = "main_menu"
                self.play_sound('button')
                return True

        return False

    def handle_game_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.show_upgrade_menu:
                    self.show_upgrade_menu = False
                else:
                    self.current_screen = "main_menu"

                    if self.multiplayer_mode:
                        if self.client:
                            self.client.close()
                        if self.server:
                            self.server.close()
                            self.server = None
                        self.multiplayer_mode = False
                        self.is_host = False

            elif event.key == pygame.K_u:
                self.show_upgrade_menu = not self.show_upgrade_menu
                self.play_sound('button')

            elif event.key == pygame.K_m:
                self.toggle_music()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()

            if self.game_buttons["upgrade"].rect.collidepoint(mouse_pos):
                self.show_upgrade_menu = not self.show_upgrade_menu
                self.play_sound('button')
                return

            if self.game_buttons["menu"].rect.collidepoint(mouse_pos):
                self.current_screen = "main_menu"

                if self.multiplayer_mode:
                    if self.client:
                        self.client.close()
                    if self.server:
                        self.server.close()
                        self.server = None
                    self.multiplayer_mode = False
                    self.is_host = False
                return

            if self.show_upgrade_menu:
                self.handle_upgrade_click(mouse_pos)
            elif not self.is_dead and self.reload_timer <= 0:
                angle = math.atan2(mouse_pos[1] - self.player_pos[1],
                                   mouse_pos[0] - self.player_pos[0])

                damage = self.player_stats["bullet_damage"]
                if self.active_effects["damage_boost"]["active"] and time.time(
                ) < self.active_effects["damage_boost"]["end_time"]:
                    damage += 5

                bullet = [
                    self.player_pos[0] + 25 * math.cos(angle),
                    self.player_pos[1] + 25 * math.sin(angle), angle,
                    self.player_stats["bullet_penetration"], damage
                ]
                self.bullets.append(bullet)

                self.play_sound('shoot')

                if self.particle_effects:
                    bullet_pos = (self.player_pos[0] + 25 * math.cos(angle),
                                  self.player_pos[1] + 25 * math.sin(angle))
                    self.particles.add_particles(bullet_pos, COLORS["BLUE"], 5,
                                                 1.0, 20)

                if self.multiplayer_mode:
                    self.new_bullets.append(bullet)

                self.reload_timer = self.player_stats["bullet_reload"]

    def update_player_position(self):
        if self.is_dead:
            return

        keys = pygame.key.get_pressed()
        speed = self.player_stats["movement_speed"]

        if self.active_effects["speed_boost"]["active"] and time.time(
        ) < self.active_effects["speed_boost"]["end_time"]:
            speed *= 1.5

        dx, dy = 0, 0
        if keys[pygame.K_w]:
            dy -= speed
        if keys[pygame.K_s]:
            dy += speed
        if keys[pygame.K_a]:
            dx -= speed
        if keys[pygame.K_d]:
            dx += speed

        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071

        self.player_pos[0] += dx
        self.player_pos[1] += dy

        self.player_pos[0] = max(20, min(WIDTH - 20, self.player_pos[0]))
        self.player_pos[1] = max(20, min(HEIGHT - 20, self.player_pos[1]))

        mouse_pos = pygame.mouse.get_pos()
        target_angle = math.atan2(mouse_pos[1] - self.player_pos[1],
                                  mouse_pos[0] - self.player_pos[0])

        angle_diff = (target_angle - self.player_angle +
                      math.pi) % (2 * math.pi) - math.pi
        self.player_angle += angle_diff * min(1.0,
                                              0.2 * self.mouse_sensitivity * 2)

        self.player_angle = (self.player_angle + 2 * math.pi) % (2 * math.pi)

    def update_active_effects(self):
        current_time = time.time()

        if self.active_effects["shield"][
                "active"] and current_time >= self.active_effects["shield"][
                    "end_time"]:
            self.active_effects["shield"]["active"] = False
            self.player_shield = 0

        if self.active_effects["speed_boost"][
                "active"] and current_time >= self.active_effects[
                    "speed_boost"]["end_time"]:
            self.active_effects["speed_boost"]["active"] = False

        if self.active_effects["damage_boost"][
                "active"] and current_time >= self.active_effects[
                    "damage_boost"]["end_time"]:
            self.active_effects["damage_boost"]["active"] = False

    def update_discord_rpc(self):
        if self.rpc:
            try:
                mode = "Multiplayer" if self.multiplayer_mode else "Singleplayer"
                difficulty = self.difficulty.capitalize()

                self.rpc.update(
                    details=
                    f"{mode} ({difficulty}) | Level: {self.player_level}",
                    state=f"Score: {self.score} | Kills: {self.kills}",
                    large_image="https://i.imgur.com/vn4pYBH.png",
                    large_text="Bulletverse.io",
                    small_image=
                    "https://th.bing.com/th/id/R.da61fa152c102c46c16786b9f79402f8?rik=l5kvYddcePaDtw&pid=ImgRaw&r=0",
                    small_text="https://discord.gg/XVN6mYv5AJ",
                    start=int(time.time()))
            except:
                pass

    def update_multiplayer(self):
        if not self.multiplayer_mode:
            return

        player_data = {
            "pos": self.player_pos,
            "angle": self.player_angle,
            "health": self.player_health,
            "shield": self.player_shield,
            "level": self.player_level,
            "xp": self.player_xp,
            "xp_to_next_level": self.xp_to_next_level,
            "new_bullets": self.new_bullets,
            "upgrade_points": self.player_upgrade_points,
            "send_time": time.time()
        }

        self.client.send_data(player_data)

        self.new_bullets = []

        if "powerups" in self.client.game_state:
            for powerup in self.client.game_state["powerups"]:
                if math.hypot(powerup["pos"][0] - self.player_pos[0],
                              powerup["pos"][1] - self.player_pos[1]) < 25:
                    self.apply_powerup(powerup["type"])

    def apply_powerup(self, powerup_type):
        self.play_sound('powerup')

        if self.particle_effects:
            self.particles.add_particles(self.player_pos, COLORS["PURPLE"], 15,
                                         2.0, 40)

        if powerup_type == "health":
            self.player_health = min(self.player_health + 25,
                                     self.player_stats["max_health"])
        elif powerup_type == "shield":
            self.player_shield = 30
            self.active_effects["shield"]["active"] = True
            self.active_effects["shield"]["end_time"] = time.time() + 10
        elif powerup_type == "speed":
            self.active_effects["speed_boost"]["active"] = True
            self.active_effects["speed_boost"]["end_time"] = time.time() + 5
        elif powerup_type == "damage":
            self.active_effects["damage_boost"]["active"] = True
            self.active_effects["damage_boost"]["end_time"] = time.time() + 8
        elif powerup_type == "xp":
            self.add_xp(30)

    def add_xp(self, amount):
        self.player_xp += amount

        if self.player_xp >= self.xp_to_next_level:
            self.player_level += 1
            self.player_upgrade_points += 1
            self.player_xp -= self.xp_to_next_level
            self.xp_to_next_level = int(self.xp_to_next_level * 1.5)

            self.play_sound('level_up')

            if self.particle_effects:
                self.particles.add_particles(self.player_pos, COLORS["YELLOW"],
                                             20, 3.0, 60)

    def update_singleplayer(self):
        current_time = time.time()

        if current_time - self.last_powerup_time > random.uniform(15, 30):
            if len(self.powerups) < 5:
                pos = (random.randint(50, WIDTH - 50),
                       random.randint(50, HEIGHT - 50))

                types = ["health", "shield", "speed", "damage", "xp"]
                weights = [0.25, 0.2, 0.2, 0.2, 0.15]
                powerup_type = random.choices(types, weights=weights)[0]

                self.powerups.append(PowerUp(pos, powerup_type))
                self.last_powerup_time = current_time

        for powerup in list(self.powerups):
            powerup.update()

            if math.hypot(powerup.pos[0] - self.player_pos[0],
                          powerup.pos[1] - self.player_pos[1]) < 25:
                self.apply_powerup(powerup.type)

                self.powerups.remove(powerup)

        self.move_enemies()

        self.move_bullets()

        if current_time - self.last_regen_time >= 1.0:
            self.health_regeneration()
            self.last_regen_time = current_time

    def move_enemies(self):
        for enemy in self.enemies:
            enemy["pos"][0] += enemy["speed"] * math.cos(enemy["angle"])
            enemy["pos"][1] += enemy["speed"] * math.sin(enemy["angle"])

            if enemy["pos"][0] <= 20 or enemy["pos"][0] >= WIDTH - 20:
                enemy["angle"] = math.pi - enemy["angle"]
            if enemy["pos"][1] <= 20 or enemy["pos"][1] >= HEIGHT - 20:
                enemy["angle"] = -enemy["angle"]

            if random.random() < 0.01:
                enemy["angle"] += random.uniform(-0.5, 0.5)

            if random.random() < 0.05:
                target_angle = math.atan2(self.player_pos[1] - enemy["pos"][1],
                                          self.player_pos[0] - enemy["pos"][0])

                angle_diff = (target_angle - enemy["angle"] +
                              math.pi) % (2 * math.pi) - math.pi
                enemy["angle"] += angle_diff * 0.1

            enemy["fire_timer"] -= 1
            if enemy["fire_timer"] <= 0:
                enemy["fire_timer"] = ENEMY_FIRE_RATE * random.uniform(
                    0.8, 1.2)

                dist = math.hypot(self.player_pos[0] - enemy["pos"][0],
                                  self.player_pos[1] - enemy["pos"][1])

                if dist < 400:
                    angle_to_player = math.atan2(
                        self.player_pos[1] - enemy["pos"][1],
                        self.player_pos[0] - enemy["pos"][0])

                    inaccuracy = min(0.2, dist / 2000)
                    angle_to_player += random.uniform(-inaccuracy, inaccuracy)

                    self.enemy_bullets.append(
                        [enemy["pos"][0], enemy["pos"][1], angle_to_player])

                    if self.particle_effects:
                        bullet_pos = (enemy["pos"][0], enemy["pos"][1])
                        self.particles.add_particles(bullet_pos, COLORS["RED"],
                                                     3, 1.0, 10)

    def move_bullets(self):
        for bullet in list(self.bullets):
            bullet[0] += self.player_stats["bullet_speed"] * math.cos(
                bullet[2])
            bullet[1] += self.player_stats["bullet_speed"] * math.sin(
                bullet[2])

            if bullet[0] < 0 or bullet[0] > WIDTH or bullet[1] < 0 or bullet[
                    1] > HEIGHT:
                self.bullets.remove(bullet)
                continue

            for enemy in list(self.enemies):
                if math.hypot(bullet[0] - enemy["pos"][0],
                              bullet[1] - enemy["pos"][1]) < enemy.get(
                                  "size", 20):
                    damage = bullet[4] if len(
                        bullet) > 4 else self.player_stats["bullet_damage"]
                    enemy["health"] -= damage

                    self.play_sound('hit')

                    if self.particle_effects:
                        hit_pos = (bullet[0], bullet[1])
                        self.particles.add_particles(hit_pos, COLORS["RED"], 8,
                                                     1.5, 20)

                    bullet[3] -= 1

                    if bullet[3] <= 0:
                        if bullet in self.bullets:
                            self.bullets.remove(bullet)

                    if enemy["health"] <= 0:
                        self.score += 100
                        self.kills += 1

                        xp_gain = 10
                        if hasattr(
                                self, 'difficulty'
                        ) and self.difficulty in DIFFICULTY_SETTINGS:
                            xp_gain *= DIFFICULTY_SETTINGS[
                                self.difficulty]["xp_multiplier"]
                        self.add_xp(xp_gain)

                        if random.random() < 0.1:
                            powerup_type = random.choice(
                                ["health", "shield", "speed", "damage", "xp"])
                            self.powerups.append(
                                PowerUp((enemy["pos"][0], enemy["pos"][1]),
                                        powerup_type))

                        if self.particle_effects:
                            explosion_pos = (enemy["pos"][0], enemy["pos"][1])
                            self.particles.add_particles(
                                explosion_pos, COLORS["RED"], 20, 2.5, 40)

                        self.enemies.remove(enemy)
                        self.enemies.append(
                            spawn_enemy(self.difficulty if hasattr(
                                self, 'difficulty') else "normal"))

                    break

        for bullet in list(self.enemy_bullets):
            bullet[0] += ENEMY_BULLET_SPEED * math.cos(bullet[2])
            bullet[1] += ENEMY_BULLET_SPEED * math.sin(bullet[2])

            if bullet[0] < 0 or bullet[0] > WIDTH or bullet[1] < 0 or bullet[
                    1] > HEIGHT:
                self.enemy_bullets.remove(bullet)
                continue

            if not self.is_dead and math.hypot(
                    bullet[0] - self.player_pos[0],
                    bullet[1] - self.player_pos[1]) < 20:
                damage = 10
                if hasattr(self, 'difficulty'
                           ) and self.difficulty in DIFFICULTY_SETTINGS:
                    damage = DIFFICULTY_SETTINGS[
                        self.difficulty]["enemy_damage"]

                if hasattr(self, 'player_shield') and self.player_shield > 0:
                    self.player_shield -= damage
                    if self.player_shield < 0:
                        self.player_health += self.player_shield
                        self.player_shield = 0
                else:
                    self.player_health -= damage

                self.play_sound('hit')

                if self.particle_effects:
                    hit_pos = (self.player_pos[0] + random.uniform(-10, 10),
                               self.player_pos[1] + random.uniform(-10, 10))
                    self.particles.add_particles(hit_pos, COLORS["RED"], 8,
                                                 1.5, 20)

                self.enemy_bullets.remove(bullet)

                if self.player_health <= 0:
                    self.player_died()

    def health_regeneration(self):
        if self.player_stats[
                "regen"] > 0 and self.player_health < self.player_stats[
                    "max_health"]:
            regen_amount = self.player_stats["regen"]
            self.player_health = min(self.player_stats["max_health"],
                                     self.player_health + regen_amount)

    def player_died(self):
        self.is_dead = True

        self.respawn_time = time.time() + 5

        self.play_sound('death')

        if self.particle_effects:
            self.particles.add_particles(self.player_pos, COLORS["BLUE"], 30,
                                         3.0, 60)

    def check_respawn(self):
        if self.is_dead and time.time() >= self.respawn_time:
            self.is_dead = False
            self.player_health = self.player_stats["max_health"]
            self.player_shield = 0

            safe_respawn = False
            tries = 0
            while not safe_respawn and tries < 10:
                self.player_pos = [
                    random.randint(100, WIDTH - 100),
                    random.randint(100, HEIGHT - 100)
                ]

                safe_respawn = True
                for enemy in self.enemies:
                    if math.hypot(self.player_pos[0] - enemy["pos"][0],
                                  self.player_pos[1] - enemy["pos"][1]) < 200:
                        safe_respawn = False
                        break

                tries += 1

    def update_settings_menu(self):
        self.update_settings()

    def update_game(self):
        if self.show_upgrade_menu:
            return

        self.update_player_position()

        self.update_active_effects()

        self.particles.update()

        self.check_respawn()

        if self.multiplayer_mode:
            self.update_multiplayer()
        else:
            self.update_singleplayer()

        if self.reload_timer > 0:
            self.reload_timer -= 1

        if time.time() % 15 < 0.1:
            self.update_discord_rpc()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break

                if self.current_screen == "loading":
                    continue

                if self.current_screen == "main_menu" or self.current_screen == "host" or self.current_screen == "join":
                    self.handle_menu_events(event)
                else:
                    self.handle_game_events(event)

            if self.current_screen == "loading":
                self.loading_screen.update(dt)
                self.loading_screen.draw()

                if self.loading_screen.loading_complete:
                    if not hasattr(self, 'completion_delay'):
                        self.completion_delay = time.time() + 0.7

                    if time.time() >= self.completion_delay:
                        self.current_screen = "main_menu"
                        self.load_and_play_background_music()
                        delattr(self, 'completion_delay')

            elif self.current_screen == "game":
                self.update_game()

                self.screen.fill(COLORS["WHITE"])
                self.draw_players()
                self.draw_powerups()
                self.draw_bullets()
                self.draw_enemies()
                self.draw_particles()
                self.draw_ui()

                if self.show_upgrade_menu:
                    self.draw_upgrade_menu()

                if self.is_dead:
                    self.draw_death_screen()
                if self.show_cosmetics_menu:
                    self.draw_cosmetics_menu()

                pygame.display.flip()

            elif self.current_screen == "main_menu":
                self.draw_main_menu()

                if self.show_settings_menu:
                    self.draw_settings_menu()

                pygame.display.flip()

            elif self.current_screen == "host":
                self.draw_host_menu()
                pygame.display.flip()

            elif self.current_screen == "join":
                self.draw_join_menu()
                pygame.display.flip()

            elif self.show_settings_menu:
                self.update_settings_menu()
                self.draw_settings_menu()
                pygame.display.flip()

        self.save_settings()

        if self.rpc:
            self.rpc.close()

        if self.client:
            self.client.close()

        if self.server:
            self.server.close()

        pygame.quit()

    def run_dedicated_server():
        server = GameServer(SERVER_HOST, SERVER_PORT)
        if server.start():
            logger.info("Dedicated server started. Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Server shutdown requested.")
            finally:
                server.close()
        else:
            logger.error("Failed to start dedicated server.")


if __name__ == "__main__":
    import sys
    import os

    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        run_dedicated_server()
    else:
        try:
            if not os.path.exists('assets'):
                os.makedirs('assets')
                logger.info("Created assets directory")
            if not os.path.exists('assets/sounds'):
                os.makedirs('assets/sounds')
                logger.info("Created sounds directory")

            game = Game()
            game.run()
        except Exception as e:
            logger.critical(f"Unhandled error: {e}", exc_info=True)
            pygame.quit()
