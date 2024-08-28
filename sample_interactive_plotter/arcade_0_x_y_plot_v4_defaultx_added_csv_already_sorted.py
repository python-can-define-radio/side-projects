import arcade
import arcade.gui
import numpy as np
import csv
import matplotlib.pyplot as plt

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800
SCREEN_TITLE = "Interactive Plot with Menu"
GRID_STEP = 1  # Use integer steps

class MainView(arcade.View):
    def __init__(self):
        super().__init__()

        self.points = {x: 0 for x in range(-10, 11)}

        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        self.menu_button = arcade.gui.UIFlatButton(text="Menu", width=100)
        self.menu_anchor = arcade.gui.UIAnchorWidget(
            anchor_x="right",
            anchor_y="bottom",
            child=self.menu_button
        )
        self.manager.add(self.menu_anchor)

        @self.menu_button.event("on_click")
        def on_click_menu_button(event):
            menu_view = MenuView(self)
            self.window.show_view(menu_view)

    def on_show_view(self):
        arcade.set_background_color(arcade.color.AMAZON)
        self.manager.enable()

    def on_hide_view(self):
        self.manager.disable()

    def on_draw(self):
        self.clear()
        self.draw_grid()
        self.draw_points()
        self.manager.draw()

    def draw_grid(self):
        for x in range(-10, 11):
            screen_x = (x + 10) * (SCREEN_WIDTH / 20)
            if x == 0:
                color = arcade.color.BLACK
            else:
                color = arcade.color.LIGHT_GRAY
            arcade.draw_line(screen_x, 0, screen_x, SCREEN_HEIGHT, color)

        for y in range(-10, 11):
            screen_y = (y + 10) * (SCREEN_HEIGHT / 20)
            if y == 0:
                color = arcade.color.BLACK
            else:
                color = arcade.color.LIGHT_GRAY
            arcade.draw_line(0, screen_y, SCREEN_WIDTH, screen_y, color)

        for x in range(-10, 11):
            screen_x = (x + 10) * (SCREEN_WIDTH / 20)
            if x != 0:
                arcade.draw_text(f"{x}", screen_x - 10, SCREEN_HEIGHT / 2 + 5, arcade.color.BLACK, 10)

        for y in range(-10, 11):
            screen_y = (y + 10) * (SCREEN_HEIGHT / 20)
            if y != 0:
                arcade.draw_text(f"{y}", 5, screen_y - 5, arcade.color.BLACK, 10)

    def draw_points(self):
        for x, y in self.points.items():
            screen_x = (x + 10) * (SCREEN_WIDTH / 20)
            screen_y = (y + 10) * (SCREEN_HEIGHT / 20)
            arcade.draw_circle_filled(screen_x, screen_y, 5, arcade.color.BLUE)


    def on_mouse_press(self, x, y, button, modifiers):
        snapped_x = int(round((x / (SCREEN_WIDTH / 20)) - 10))
        mathed_y = round((y / (SCREEN_HEIGHT / 20)) - 10, 3)

        if button == arcade.MOUSE_BUTTON_LEFT:
            self.points[snapped_x] = mathed_y
            print(f"Updated point: {snapped_x}, {mathed_y}")
        elif button == arcade.MOUSE_BUTTON_RIGHT:
            self.points = {x: 0 for x in range(-10, 11)}
            print("Reset all points to default")

    def save_points_to_csv(self, filename="points.csv"):
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["X", "Y"])
            for x, y in self.points.items():
                writer.writerow([x, y])
        print(f"Points saved to {filename}")

    def load_points_from_csv(self, filename="points.csv"):
        with open(filename, mode='r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip the header
            self.points = {int(row[0]): int(row[1]) for row in reader}
        print(f"Points loaded from {filename}")

    def plot_fft(self):
        if not self.points:
            print("No points to plot FFT.")
            return
        
        y_values = [y for x, y in sorted(self.points.items())]
        y_fft = np.fft.fft(y_values)
        x_values = np.fft.fftfreq(len(y_values))

        plt.figure()
        plt.plot(x_values, np.abs(y_fft))
        plt.title("FFT of Points")
        plt.xlabel("Frequency")
        plt.ylabel("Magnitude")
        plt.show()

class MenuView(arcade.View):
    """Main menu view class."""

    def __init__(self, main_view):
        super().__init__()

        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        back_button = arcade.gui.UIFlatButton(text="Back", width=150)
        save_button = arcade.gui.UIFlatButton(text="Save", width=150)
        load_button = arcade.gui.UIFlatButton(text="Load", width=150)
        plot_button = arcade.gui.UIFlatButton(text="Plot FFT", width=150)
        exit_button = arcade.gui.UIFlatButton(text="Exit", width=150)
        self.layout = arcade.gui.UIBoxLayout(vertical=True, space_between=20)
        self.layout.add(back_button)
        self.layout.add(save_button)
        self.layout.add(load_button)
        self.layout.add(plot_button)
        self.layout.add(exit_button)

        self.anchor = arcade.gui.UIAnchorWidget(
            anchor_x="center_x",
            anchor_y="center_y",
            child=self.layout
        )
        self.manager.add(self.anchor)

        self.main_view = main_view

        @back_button.event("on_click")
        def on_click_back_button(event):
            self.window.show_view(self.main_view)

        @save_button.event("on_click")
        def on_click_save_button(event):
            self.main_view.save_points_to_csv()

        @load_button.event("on_click")
        def on_click_load_button(event):
            self.main_view.load_points_from_csv()

        @plot_button.event("on_click")
        def on_click_plot_button(event):
            self.main_view.plot_fft()

        @exit_button.event("on_click")
        def on_click_exit_button(event):
            arcade.exit()

    def on_show_view(self):
        arcade.set_background_color(arcade.color.DARK_BLUE_GRAY)
        self.manager.enable()

    def on_hide_view(self):
        self.manager.disable()

    def on_draw(self):
        self.clear()
        self.manager.draw()

def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, resizable=True)
    main_view = MainView()
    window.show_view(main_view)
    arcade.run()

if __name__ == "__main__":
    main()
