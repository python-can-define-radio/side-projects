import arcade
import numpy as np
import matplotlib.pyplot as plt
import os
import csv


SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800
SCREEN_TITLE = "Move Sprite with Mouse, Drop points, and Plot FFT"
GRID_COLOR = arcade.color.LIGHT_GRAY
LABEL_COLOR = arcade.color.BLACK


class MyApp(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title)
        arcade.set_background_color(arcade.color.AMAZON)
        self.all_sprites_list = arcade.SpriteList()
        self.sprite = arcade.Sprite(center_x=width // 2, center_y=height // 2)
        self.sprite.color = arcade.color.RED
        self.sprite.width = 20
        self.sprite.height = 20
        self.all_sprites_list.append(self.sprite)
        self.points = []

        self.button_x = SCREEN_WIDTH - 100
        self.button_y = 50
        self.button_width = 90
        self.button_height = 30

        self.save_button_x = 100
        self.save_button_y = 50
        self.save_button_width = 90
        self.save_button_height = 30

    def setup(self):
        pass


    def on_draw(self):
        arcade.start_render()

        for i in range(-10, 11):
            x = SCREEN_WIDTH // 2 + i * (SCREEN_WIDTH // 20)
            y = SCREEN_HEIGHT // 2 + i * (SCREEN_HEIGHT // 20)
            if i != 0:
                arcade.draw_line(x, 0, x, SCREEN_HEIGHT, GRID_COLOR)
            if i != 0:
                arcade.draw_line(0, y, SCREEN_WIDTH, y, GRID_COLOR)
            if i != 0:
                arcade.draw_text(f"{i/10:.1f}", x - 10, SCREEN_HEIGHT // 2 - 20, LABEL_COLOR, 10)

            arcade.draw_text(f"{i/10:.1f}", 10, y - 5, LABEL_COLOR, 10)

        arcade.draw_line(0, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT // 2, arcade.color.BLACK, 2)
        arcade.draw_line(SCREEN_WIDTH // 2, 0, SCREEN_WIDTH // 2, SCREEN_HEIGHT, arcade.color.BLACK, 2)

        self.all_sprites_list.draw()
        
        for dot in self.points:
            arcade.draw_circle_filled(dot[0], dot[1], 5, arcade.color.BLUE)

        arcade.draw_rectangle_filled(self.button_x, self.button_y, self.button_width, self.button_height, arcade.color.GRAY)
        arcade.draw_text("Plot FFT", self.button_x - 30, self.button_y - 5, LABEL_COLOR, 12)
        arcade.draw_rectangle_filled(self.save_button_x, self.save_button_y, self.save_button_width, self.save_button_height, arcade.color.GRAY)
        arcade.draw_text("Save CSV", self.save_button_x - 38, self.save_button_y - 5, LABEL_COLOR, 12)

    def on_mouse_motion(self, x, y, dx, dy):
        self.sprite.center_x = x
        self.sprite.center_y = y


    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            if (self.button_x - self.button_width / 2 < x < self.button_x + self.button_width / 2 and
                    self.button_y - self.button_height / 2 < y < self.button_y + self.button_height / 2):
                self.plot_fft()
            elif (self.save_button_x - self.save_button_width / 2 < x < self.save_button_x + self.save_button_width / 2 and
                  self.save_button_y - self.save_button_height / 2 < y < self.save_button_y + self.save_button_height / 2):
                self.save_to_csv()
            else:
                snapped_x = self.snap_to_grid(x)
                self.points.append((snapped_x, y))
                self.print_grid_coordinates(snapped_x, y)
        elif button == arcade.MOUSE_BUTTON_RIGHT:
            self.clear_screen()


    def snap_to_grid(self, x):
        grid_size = SCREEN_WIDTH // 20  
        center_x = SCREEN_WIDTH // 2
        normalized_x = (x - center_x) / grid_size
        snapped_normalized_x = round(normalized_x)
        snapped_x = snapped_normalized_x * grid_size + center_x
        return snapped_x


    def print_grid_coordinates(self, x, y):
        grid_x = (x - SCREEN_WIDTH // 2) / (SCREEN_WIDTH // 20) / 10
        grid_y = (y - SCREEN_HEIGHT // 2) / (SCREEN_HEIGHT // 20) / 10
        print(f"Grid coordinates: ({grid_x:.2f}, {grid_y:.2f})")


    def clear_screen(self):
        self.points = []
        if os.name == 'nt':
            os.system('cls') 
        else:
            os.system('clear')


    def save_to_csv(self):
        
        grid_coordinates = [(round((dot[0] - SCREEN_WIDTH // 2) / (SCREEN_WIDTH // 20) / 10, 1),
                             round((dot[1] - SCREEN_HEIGHT // 2) / (SCREEN_HEIGHT // 20) / 10, 1)) for dot in self.points]
        
        with open('points.csv', 'w', newline='') as csvfile:
            fieldnames = ['x', 'y']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for coord in grid_coordinates:
                writer.writerow({'x': coord[0], 'y': coord[1]})
        print("Dot coordinates saved to points.csv")


    def plot_fft(self):
        if not self.points:
            return
        
        x_positions = [dot[0] for dot in self.points]
        y_positions = [dot[1] for dot in self.points]
        
        x_positions = np.array(x_positions) - SCREEN_WIDTH / 2
        y_positions = np.array(y_positions) - SCREEN_HEIGHT / 2

        x_fft = np.fft.fft(x_positions)
        y_fft = np.fft.fft(y_positions)

        plt.figure(figsize=(10, 5))

        plt.subplot(1, 2, 1)
        plt.plot(np.abs(x_fft), label="X FFT")
        plt.title("X FFT")
        plt.legend()

        plt.subplot(1, 2, 2)
        plt.plot(np.abs(y_fft), label="Y FFT")
        plt.title("Y FFT")
        plt.legend()

        plt.tight_layout()
        plt.show()

def main():
    window = MyApp(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.setup()
    arcade.run()

if __name__ == "__main__":
    main()
