import arcade

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Avatar images
AVATAR_IMAGES = [
    ":resources:images/animated_characters/female_person/femalePerson_idle.png",
    ":resources:images/animated_characters/male_person/malePerson_idle.png",
    ":resources:images/animated_characters/zombie/zombie_idle.png"
]

class Username_Selection(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Username Selection")
        self.button_text = "Submit"
        
        # Button position and size (moved up by 100 pixels)
        self.button_x = SCREEN_WIDTH // 2
        self.button_y = SCREEN_HEIGHT // 4 + 100  # Move button up by 100 pixels
        self.button_width = 200
        self.button_height = 50

        # Avatar positions and sprite setup (moved up by 100 pixels)
        self.avatar_sprites = []
        self.avatar_width = 64
        self.avatar_height = 64
        self.avatar_y = self.button_y + 100  # Place avatars above the button, moved up by 100 pixels
        self.selected_avatar_index = None  # Track the selected avatar

        # Username text input (moved up by 100 pixels)
        self.username = ""
        self.textbox_x = SCREEN_WIDTH // 2 + 40  # Position textbox slightly to the right
        self.textbox_y = self.avatar_y + 50  # Move textbox up by 100 pixels (above avatars)
        self.textbox_width = 200
        self.textbox_height = 30
        self.textbox_active = False

        # Create avatar sprites (moved to the right a little)
        for i, avatar_image in enumerate(AVATAR_IMAGES):
            avatar_sprite = arcade.Sprite(avatar_image, scale=0.5)
            avatar_sprite.center_x = SCREEN_WIDTH // 2 - (len(AVATAR_IMAGES) * self.avatar_width // 2) + i * self.avatar_width + 50  # Move avatars right
            avatar_sprite.center_y = self.avatar_y
            self.avatar_sprites.append(avatar_sprite)

    def on_draw(self):
        """Draw the screen."""
        self.clear()  # Clear the screen

        # Draw the "Username" label and text box
        arcade.draw_text("Username:", self.textbox_x - 205, self.textbox_y - 5, arcade.color.WHITE, 14)  # Move label further left
        arcade.draw_rectangle_filled(self.textbox_x, self.textbox_y, self.textbox_width, self.textbox_height, arcade.color.WHITE)
        arcade.draw_text(self.username, self.textbox_x - self.textbox_width // 2, self.textbox_y - 5, arcade.color.BLACK, 14)

        # Draw the avatars above the button
        for i, avatar_sprite in enumerate(self.avatar_sprites):
            # Highlight the selected avatar
            if self.selected_avatar_index == i:
                arcade.draw_rectangle_outline(avatar_sprite.center_x, avatar_sprite.center_y, self.avatar_width + 10, self.avatar_height + 10, arcade.color.YELLOW, 3)
            avatar_sprite.draw()

        # Draw the "Submit" button (as a rectangle with text)
        arcade.draw_rectangle_filled(self.button_x, self.button_y, self.button_width, self.button_height, arcade.color.BLUE)
        arcade.draw_text(self.button_text, self.button_x, self.button_y, arcade.color.WHITE, 18, anchor_x="center", anchor_y="center")

    def on_mouse_press(self, x, y, button, modifiers):
        """Check if the mouse clicked on the button or an avatar."""
        # Check if the button is clicked
        if (self.button_x - self.button_width / 2 <= x <= self.button_x + self.button_width / 2 and
            self.button_y - self.button_height / 2 <= y <= self.button_y + self.button_height / 2):
            print("Submit button clicked!")
            if self.selected_avatar_index is not None and self.username:
                print(f"Player selected avatar: {AVATAR_IMAGES[self.selected_avatar_index]}")
                print(f"Username: {self.username}")
            else:
                print("Please select an avatar and enter a username.")

        # Check if an avatar is clicked
        for i, avatar_sprite in enumerate(self.avatar_sprites):
            if avatar_sprite.collides_with_point((x, y)):
                self.selected_avatar_index = i
                print(f"Avatar selected: {AVATAR_IMAGES[i]}")

        # Check if clicked inside the textbox
        if self.textbox_x - self.textbox_width // 2 <= x <= self.textbox_x + self.textbox_width // 2 and \
                self.textbox_y - self.textbox_height // 2 <= y <= self.textbox_y + self.textbox_height // 2:
            self.textbox_active = True
        else:
            self.textbox_active = False

    def on_key_press(self, symbol, modifiers):
        """Handle text input for the username."""
        if self.textbox_active:
            if symbol == arcade.key.BACKSPACE:
                self.username = self.username[:-1]  # Remove last character
            elif 32 <= symbol <= 126:  # Allowable characters (from space to ~)
                self.username += chr(symbol)

    def on_resize(self, width, height):
        """Handle window resizing."""
        print(f"Window resized to: {width}x{height}")

def main():
    """Start a basic arcade window to test drawing and UI."""
    print("Starting the game window...")
    window = Username_Selection()
    arcade.run()

if __name__ == "__main__":
    main()
