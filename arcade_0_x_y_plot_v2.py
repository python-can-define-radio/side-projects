import arcade
import arcade.gui
import numpy as np
import csv
import matplotlib.pyplot as plt



SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800
SCREEN_TITLE = "Interactive Plot with Menu"
GRID_STEP = 0.1


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
        for x in np.arange(-1, 1.1, GRID_STEP):
            screen_x = (x + 1) * SCREEN_WIDTH / 2
            if .09 > x > -.1:
                color = arcade.color.BLACK  
            else:
                color = arcade.color.LIGHT_GRAY
            arcade.draw_line(screen_x, 0, screen_x, SCREEN_HEIGHT, color)

        for y in np.arange(-1, 1.1, GRID_STEP):
            screen_y = (y + 1) * SCREEN_HEIGHT / 2
            if .09 > y > -.1:
                color = arcade.color.BLACK  
            else:
                color = arcade.color.LIGHT_GRAY
            arcade.draw_line(0, screen_y, SCREEN_WIDTH, screen_y, color)

        for x in np.arange(-1, 1.1, GRID_STEP):
            screen_x = (x + 1) * SCREEN_WIDTH / 2
            if x != 0:
                arcade.draw_text(f"{x:.1f}", screen_x - 10, SCREEN_HEIGHT / 2 + 5, arcade.color.BLACK, 10)

        for y in np.arange(-1, 1.1, GRID_STEP):
            screen_y = (y + 1) * SCREEN_HEIGHT / 2
            if y != 0:
                arcade.draw_text(f"{y:.1f}", 5, screen_y - 5, arcade.color.BLACK, 10)


    def draw_points(self):
        for point in self.points:
            x, y = point
            screen_x = (x + 1) * SCREEN_WIDTH / 2
            screen_y = (y + 1) * SCREEN_HEIGHT / 2
            arcade.draw_circle_filled(screen_x, screen_y, 5, arcade.color.BLUE)


    def on_mouse_motion(self, x, y, dx, dy):
        grid_x = (x / (SCREEN_WIDTH / 2)) - 1
        grid_y = (y / (SCREEN_HEIGHT / 2)) - 1
        self.current_mouse_x = round(grid_x / GRID_STEP) * GRID_STEP
        self.current_mouse_y = grid_y


    def on_mouse_press(self, x, y, button, modifiers):
        grid_x = (x / (SCREEN_WIDTH / 2)) - 1
        grid_y = (y / (SCREEN_HEIGHT / 2)) - 1
        snapped_x = round(grid_x / GRID_STEP) * GRID_STEP
        snapped_y = grid_y
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.points.append((snapped_x, snapped_y))
            print(f"Added point: {snapped_x}, {snapped_y}")
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
        plot_button = arcade.gui.UIFlatButton(text="Plot FFT", width=150)
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
