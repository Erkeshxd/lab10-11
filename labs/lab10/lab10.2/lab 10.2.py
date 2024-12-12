import psycopg2
from config import config
from os import scandir
from select import select
import pygame
import random
import sys
from pygame.locals import *
import time
import threading
import os

# Constants and global variables
BLACK = (0, 0, 0)
LINE_COLOR = (50, 50, 50)
HEIGHT = 400
WIDTH = 400
SPEED = 5
BLOCK_SIZE = 20
MAX_LEVEL = 2
SCORE = 0
LEVEL = 1

# Database-related functions
def get_player(nickname):
    sql = "SELECT * FROM Snake WHERE NickName = %s"
    conn = None
    try:
        params = config()
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        cur.execute(sql, (nickname,))
        row = cur.fetchone()
        return (row[1], row[2]) if row else (None, None)
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn:
            conn.close()

def insert_player(players):
    conn = None
    try:
        params = config()
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        for nickname, level, score in players:
            cur.execute("SELECT * FROM Snake WHERE NickName = %s", (nickname,))
            if cur.fetchone():
                cur.execute("UPDATE Snake SET Level = %s, Score = %s WHERE NickName = %s", (level, score, nickname))
            else:
                cur.execute("INSERT INTO Snake(NickName, Level, Score) VALUES(%s, %s, %s)", (nickname, level, score))
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn:
            conn.close()

# Classes for game components
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Wall:
    def __init__(self, level):
        self.body = []
        level = level % MAX_LEVEL
        try:
            with open(f"levels/level{level}.txt", "r") as f:
                for y, line in enumerate(f):
                    for x, char in enumerate(line.strip()):
                        if char == '#':
                            self.body.append(Point(x, y))
        except FileNotFoundError:
            print(f"Level file level{level}.txt not found.")
            sys.exit()
    
    def draw(self):
        for point in self.body:
            rect = pygame.Rect(BLOCK_SIZE * point.x, BLOCK_SIZE * point.y, BLOCK_SIZE, BLOCK_SIZE)
            pygame.draw.rect(SCREEN, (255, 255, 255), rect)

class Food:
    def __init__(self, wall):
        self.body = None
        self.wall = wall
        self.lock = threading.Lock()
        self.update_location()

    def update_location(self):
        self.lock.acquire()
        while True:
            self.body = Point(random.randint(0, WIDTH//BLOCK_SIZE - 1), random.randint(0, HEIGHT//BLOCK_SIZE - 1))
            if not any(p.x == self.body.x and p.y == self.body.y for p in self.wall.body):
                break
        self.lock.release()

    def draw(self):
        rect = pygame.Rect(BLOCK_SIZE * self.body.x, BLOCK_SIZE * self.body.y, BLOCK_SIZE, BLOCK_SIZE)
        pygame.draw.rect(SCREEN, (0, 255, 0), rect)

class Snake:
    def __init__(self):
        self.body = [Point(10, 11)]
        self.dx = 0
        self.dy = 0

    def move(self, wall):
        for i in range(len(self.body) - 1, 0, -1):
            self.body[i] = Point(self.body[i-1].x, self.body[i-1].y)

        self.body[0].x += self.dx
        self.body[0].y += self.dy

        if self.body[0].x * BLOCK_SIZE >= WIDTH:
            self.body[0].x = 0
        if self.body[0].y * BLOCK_SIZE >= HEIGHT:
            self.body[0].y = 0
        if self.body[0].x < 0:
            self.body[0].x = WIDTH // BLOCK_SIZE - 1
        if self.body[0].y < 0:
            self.body[0].y = HEIGHT // BLOCK_SIZE - 1

        for point in wall.body:
            if self.body[0].x == point.x and self.body[0].y == point.y:
                self.game_over()

    def game_over(self):
        global LEVEL, SCORE
        insert_player([(Nickname, LEVEL, SCORE)])
        font = pygame.font.SysFont("Verdana", 30)
        text = font.render("GAME OVER", True, (255, 255, 255))
        SCREEN.blit(text, text.get_rect(center=(WIDTH//2, HEIGHT//2)))
        pygame.display.flip()
        time.sleep(2)
        pygame.quit()
        sys.exit()

    def draw(self):
        for point in self.body:
            rect = pygame.Rect(BLOCK_SIZE * point.x, BLOCK_SIZE * point.y, BLOCK_SIZE, BLOCK_SIZE)
            pygame.draw.rect(SCREEN, (0, 255, 0) if point != self.body[0] else (255, 0, 0), rect)

    def check_collision(self, food):
        if self.body[0].x == food.body.x and self.body[0].y == food.body.y:
            global SCORE
            SCORE += random.randint(1, 4)
            self.body.append(Point(self.body[-1].x, self.body[-1].y))
            food.update_location()

# Main function
def main():
    global SCREEN, CLOCK
    pygame.init()
    SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
    CLOCK = pygame.time.Clock()

    snake = Snake()
    wall = Wall(LEVEL)
    food = Food(wall)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                insert_player([(Nickname, LEVEL, SCORE)])
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT and snake.dx == 0:
                    snake.dx, snake.dy = 1, 0
                if event.key == pygame.K_LEFT and snake.dx == 0:
                    snake.dx, snake.dy = -1, 0
                if event.key == pygame.K_UP and snake.dy == 0:
                    snake.dx, snake.dy = 0, -1
                if event.key == pygame.K_DOWN and snake.dy == 0:
                    snake.dx, snake.dy = 0, 1

        snake.move(wall)
        snake.check_collision(food)

        SCREEN.fill(BLACK)
        wall.draw()
        food.draw()
        snake.draw()
        draw_grid()

        pygame.display.flip()
        CLOCK.tick(SPEED)

def draw_grid():
    for x in range(0, WIDTH, BLOCK_SIZE):
        for y in range(0, HEIGHT, BLOCK_SIZE):
            rect = pygame.Rect(x, y, BLOCK_SIZE, BLOCK_SIZE)
            pygame.draw.rect(SCREEN, LINE_COLOR, rect, 1)

if __name__ == "__main__":
    main()
