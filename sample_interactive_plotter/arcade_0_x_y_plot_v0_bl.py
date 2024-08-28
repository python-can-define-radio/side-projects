import arcade
import arcade.gui
import numpy as np
import csv
import matplotlib.pyplot as plt



SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Interactive Plot with Menu"

class MainView(arcade.View):
    def __init__(self):
        super().__init__()

        self.points = []

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
        arcade.set_background_color(arcade.color.WHITE)
        self.manager.enable()

    def on_hide_view(self):
        self.manager.disable()

    def on_draw(self):
        self.clear()
        self.draw_grid()
        self.draw_points()
        self.manager.draw()

    def draw_grid(self):
        for x in range(0, SCREEN_WIDTH, 10):
            arcade.draw_line(x, 0, x, SCREEN_HEIGHT, arcade.color.LIGHT_GRAY)
        for y in range(0, SCREEN_HEIGHT, 10):
            arcade.draw_line(0, y, SCREEN_WIDTH, y, arcade.color.LIGHT_GRAY)
        
        for x in range(0, SCREEN_WIDTH, 100):
            arcade.draw_line(x, 0, x, SCREEN_HEIGHT, arcade.color.BLACK)
        for y in range(0, SCREEN_HEIGHT, 100):
            arcade.draw_line(0, y, SCREEN_WIDTH, y, arcade.color.BLACK)

        for y in range(0, SCREEN_HEIGHT, 100):
            arcade.draw_text(f"{(y / 300) - 1:.1f}", 5, y - 5, arcade.color.BLACK, 12)

    def draw_points(self):
        for point in self.points:
            x, y = point
            arcade.draw_circle_filled(x, y, 5, arcade.color.BLUE)

    def on_mouse_motion(self, x, y, dx, dy):
        self.current_mouse_x = round(x, -1)
        self.current_mouse_y = y

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            snapped_x = round(x, -1)
            self.points.append((snapped_x, y))
            print(f"Added point: {snapped_x}, {y}")
        elif button == arcade.MOUSE_BUTTON_RIGHT:
            self.points = []
            print("Cleared all points")

    def save_points_to_csv(self, filename="points.csv"):
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["X", "Y"])
            for point in self.points:
                writer.writerow(point)
        print(f"Points saved to {filename}")

    def plot_fft(self):
        if not self.points:
            print("No points to plot FFT.")
            return
        
        y_values = [point[1] for point in self.points]
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
        plot_button = arcade.gui.UIFlatButton(text="Plot", width=150)
        exit_button = arcade.gui.UIFlatButton(text="Exit", width=150)

        self.layout = arcade.gui.UIBoxLayout(vertical=True, space_between=20)
        self.layout.add(back_button)
        self.layout.add(save_button)
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

        @plot_button.event("on_click")
        def on_click_plot_button(event):
            self.main_view.plot_fft()

        @exit_button.event("on_click")
        def on_click_exit_button(event):
            arcade.exit()

    def on_show_view(self):
        arcade.set_background_color([rgb - 50 for rgb in arcade.color.DARK_BLUE_GRAY])
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
