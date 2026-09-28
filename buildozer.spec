import random
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle

class SnakeGame(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cell_size = 20
        self.snake = [[100, 100], [80, 100], [60, 100]]
        self.direction = 'RIGHT'
        self.food = [200, 200]
        self.bind(size=self.on_size_change)
        Clock.schedule_interval(self.update, 0.15)

    def on_size_change(self, *args):
        self.spawn_food()

    def spawn_food(self):
        max_x = max(1, int(self.width // self.cell_size) - 1)
        max_y = max(1, int(self.height // self.cell_size) - 1)
        self.food = [random.randint(0, max_x) * self.cell_size, random.randint(0, max_y) * self.cell_size]

    def set_direction(self, new_dir):
        opposites = {'UP': 'DOWN', 'DOWN': 'UP', 'LEFT': 'RIGHT', 'RIGHT': 'LEFT'}
        if new_dir != opposites.get(self.direction):
            self.direction = new_dir

    def update(self, dt):
        head = list(self.snake[0])
        if self.direction == 'UP':
            head[1] += self.cell_size
        elif self.direction == 'DOWN':
            head[1] -= self.cell_size
        elif self.direction == 'LEFT':
            head[0] -= self.cell_size
        elif self.direction == 'RIGHT':
            head[0] += self.cell_size

        if head[0] < 0 or head[0] >= self.width or head[1] < 0 or head[1] >= self.height:
            self.reset_game()
            return

        if head in self.snake:
            self.reset_game()
            return

        self.snake.insert(0, head)

        if abs(head[0] - self.food[0]) < self.cell_size and abs(head[1] - self.food[1]) < self.cell_size:
            self.spawn_food()
        else:
            self.snake.pop()

        self.draw()

    def reset_game(self):
        self.snake = [[100, 100], [80, 100], [60, 100]]
        self.direction = 'RIGHT'
        self.spawn_food()

    def draw(self):
        self.canvas.clear()
        with self.canvas:
            Color(0.1, 0.1, 0.1, 1)
            Rectangle(pos=self.pos, size=self.size)

            Color(1, 0, 0, 1)
            Rectangle(pos=(self.food[0], self.food[1]), size=(self.cell_size - 2, self.cell_size - 2))

            Color(0, 1, 0, 1)
            for part in self.snake:
                Rectangle(pos=(part[0], part[1]), size=(self.cell_size - 2, self.cell_size - 2))

class SnakeApp(App):
    def build(self):
        root = BoxLayout(orientation='vertical')
        self.game = SnakeGame()
        root.add_widget(self.game)

        controls = BoxLayout(size_hint_y=0.25)
        btn_left = Button(text='LEFT', on_press=lambda x: self.game.set_direction('LEFT'))
        btn_right = Button(text='RIGHT', on_press=lambda x: self.game.set_direction('RIGHT'))

        vertical_box = BoxLayout(orientation='vertical')
        btn_up = Button(text='UP', on_press=lambda x: self.game.set_direction('UP'))
        btn_down = Button(text='DOWN', on_press=lambda x: self.game.set_direction('DOWN'))
        vertical_box.add_widget(btn_up)
        vertical_box.add_widget(btn_down)

        controls.add_widget(btn_left)
        controls.add_widget(vertical_box)
        controls.add_widget(btn_right)

        root.add_widget(controls)
        return root

if __name__ == '__main__':
    SnakeApp().run()
