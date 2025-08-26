import arcade
import pyglet

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

AVATAR_IMAGES = [
    ":resources:images/animated_characters/female_person/femalePerson_idle.png",
    ":resources:images/animated_characters/male_person/malePerson_idle.png",
    ":resources:images/animated_characters/zombie/zombie_idle.png"
]

class Username_Selection(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Username Selection")
        self.button_text = "Submit"
        arcade.set_background_color(arcade.color.DARK_MIDNIGHT_BLUE)

        # ✳️ Submit Button (Moved further down)
        self.button_x = SCREEN_WIDTH // 2
        self.button_y = SCREEN_HEIGHT // 4  # ⬅️ Moved down by 100 pixels
        self.button_width = 200
        self.button_height = 50

        # ✳️ Textbox
        self.username = ""
        self.textbox_x = SCREEN_WIDTH // 2 + 40
        self.textbox_y = SCREEN_HEIGHT - 225  # Near top
        self.textbox_width = 200
        self.textbox_height = 30
        self.textbox_active = False

        # ✳️ Avatar Area (Moved down)
        self.avatar_sprites = []
        self.avatar_width = 64
        self.avatar_height = 64
        self.avatar_y = self.button_y + 100  # Place avatars above the button
        self.selected_avatar_index = None

        for i, avatar_image in enumerate(AVATAR_IMAGES):
            sprite = arcade.Sprite(avatar_image, scale=0.5)
            sprite.center_x = (SCREEN_WIDTH // 2 - (len(AVATAR_IMAGES) * self.avatar_width // 2)
                               + i * self.avatar_width + 50)
            sprite.center_y = self.avatar_y
            self.avatar_sprites.append(sprite)

        # Pyglet cursors
        self.cursor_default = self.get_system_mouse_cursor(self.CURSOR_DEFAULT)
        self.cursor_text = self.get_system_mouse_cursor(self.CURSOR_TEXT)

    def on_draw(self):
        self.clear()

        # Username Label + Textbox
        arcade.draw_text("Username:", self.textbox_x - 210, self.textbox_y + 10, arcade.color.WHITE, 14)
        arcade.draw_rectangle_filled(self.textbox_x, self.textbox_y + 15,
                                     self.textbox_width, self.textbox_height, arcade.color.WHITE)
        arcade.draw_text(self.username,
                         self.textbox_x - self.textbox_width // 2 + 5,
                         self.textbox_y + 10,
                         arcade.color.BLACK, 14)

        # ✳️ Avatar Section Label
        label_y = self.avatar_y + 60
        arcade.draw_text("Select an Avatar", SCREEN_WIDTH // 2, label_y,
                         arcade.color.WHITE, 16, anchor_x="center")

        # Avatars
        for i, sprite in enumerate(self.avatar_sprites):
            if self.selected_avatar_index == i:
                arcade.draw_rectangle_outline(sprite.center_x, sprite.center_y,
                                              self.avatar_width + 10, self.avatar_height + 10,
                                              arcade.color.YELLOW, 3)
            sprite.draw()

        # Submit Button
        arcade.draw_rectangle_filled(self.button_x, self.button_y,
                                     self.button_width, self.button_height, arcade.color.BLUE)
        arcade.draw_text(self.button_text,
                         self.button_x, self.button_y,
                         arcade.color.WHITE, 18,
                         anchor_x="center", anchor_y="center")

    def on_mouse_motion(self, x, y, dx, dy):
        inside = (
            self.textbox_x - self.textbox_width // 2 <= x <= self.textbox_x + self.textbox_width // 2 and
            self.textbox_y - self.textbox_height // 2 <= y <= self.textbox_y + self.textbox_height // 2
        )
        if inside:
            self.set_mouse_cursor(self.cursor_text)
        else:
            self.set_mouse_cursor(self.cursor_default)

    def on_mouse_press(self, x, y, button, modifiers):
        if (self.button_x - self.button_width / 2 <= x <= self.button_x + self.button_width / 2 and
                self.button_y - self.button_height / 2 <= y <= self.button_y + self.button_height / 2):
            print("Submit button clicked!")
            if self.selected_avatar_index is not None and self.username:
                print(f"Player selected avatar: {AVATAR_IMAGES[self.selected_avatar_index]}")
                print(f"Username: {self.username}")
            else:
                print("Please select an avatar and enter a username.")

        for i, sprite in enumerate(self.avatar_sprites):
            if sprite.collides_with_point((x, y)):
                self.selected_avatar_index = i
                print(f"Avatar selected: {AVATAR_IMAGES[i]}")

        self.textbox_active = (
            self.textbox_x - self.textbox_width // 2 <= x <= self.textbox_x + self.textbox_width // 2 and
            self.textbox_y - self.textbox_height // 2 <= y <= self.textbox_y + self.textbox_height // 2
        )

    def on_key_press(self, symbol, modifiers):
        if self.textbox_active:
            if symbol == arcade.key.BACKSPACE:
                self.username = self.username[:-1]
            elif 32 <= symbol <= 126:
                self.username += chr(symbol)

    def on_resize(self, width, height):
        print(f"Window resized to: {width}x{height}")

def main():
    print("Starting the game window...")
    window = Username_Selection()
    arcade.run()

if __name__ == "__main__":
    main()
