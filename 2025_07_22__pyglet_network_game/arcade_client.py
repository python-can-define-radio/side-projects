import arcade
import zmq
from shared_constants import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SCALING, PLAYER_SCALING, AVATAR_IMAGES



context = zmq.Context()

#  Socket to talk to server
print("Connecting to server")
to_srv_sock = context.socket(zmq.PUB)
to_srv_sock.connect("tcp://localhost:5555")
from_srv_sock = context.socket(zmq.SUB)
from_srv_sock.connect("tcp://localhost:5556")
from_srv_sock.setsockopt_string(zmq.SUBSCRIBE, "")


class MyGameView(arcade.View):
    def __init__(self, username: str, avatar_index: int):
        super().__init__()
        self.username = username
        self.avatar_index = avatar_index

        self.camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

        self.setup()

    def setup(self):
        map_name = ":resources:tiled_maps/level_1.json"
        self.tile_map = arcade.load_tilemap(map_name, TILE_SCALING)
        self.scene = arcade.Scene.from_tilemap(self.tile_map)

        # Set up the player with selected avatar
        avatar_image = AVATAR_IMAGES[self.avatar_index]
        self.player_sprite = arcade.Sprite(avatar_image, PLAYER_SCALING)
        self.player_sprite.center_x = 196
        self.player_sprite.center_y = 128
        self.scene.add_sprite("Player", self.player_sprite)

        # Background color
        arcade.set_background_color((200, 200, 255))

    def on_show_view(self):
        # Reset camera when view is shown
        self.camera.resize(self.window.width, self.window.height)

    def on_draw(self):
        self.clear()
        self.camera.use()
        self.scene.draw()

        # Draw username on screen (optional)
        arcade.draw_text(f"Username: {self.username}", 10, self.window.height - 30,
                         arcade.color.BLACK, 14)

    def on_resize(self, width, height):
        self.camera.resize(width, height)

    def on_key_press(self, key, modifiers):
        to_srv_sock.send_json({"keypress": key})

    def on_key_release(self, key, modifiers):
        to_srv_sock.send_json({"keyrelease": key})

    def pan_camera_to_user(self, panning_fraction: float = 1.0):
        screen_center_x = self.player_sprite.center_x - (self.camera.viewport_width / 2)
        screen_center_y = self.player_sprite.center_y - (self.camera.viewport_height / 2)
        user_centered = screen_center_x, screen_center_y
        self.camera.move_to(user_centered, panning_fraction)

    def on_update(self, delta_time):
        latest_message = None
        while True:
            try:
                message = from_srv_sock.recv_json(flags=zmq.NOBLOCK)
                latest_message = message  # Always keep the latest one
            except zmq.Again:
                break  # No more messages

        if latest_message:
            self.player_sprite.center_x = latest_message["playerx"]
            self.player_sprite.center_y = latest_message["playery"]
        self.pan_camera_to_user(panning_fraction=0.12)


class UsernameSelectionView(arcade.View):
    def __init__(self):
        super().__init__()

        self.button_text = "Submit"

        self.button_x = SCREEN_WIDTH // 2
        self.button_y = SCREEN_HEIGHT // 4  # Submit button lower on screen
        self.button_width = 200
        self.button_height = 50

        self.username = ""
        self.textbox_x = SCREEN_WIDTH // 2 + 40
        self.textbox_y = SCREEN_HEIGHT - 225  # Textbox near top
        self.textbox_width = 200
        self.textbox_height = 30
        self.textbox_active = False

        self.avatar_sprites = []
        self.avatar_width = 64
        self.avatar_height = 64
        self.avatar_y = self.button_y + 100  # Avatars above button
        self.selected_avatar_index = None
        self.cursor_default = self.window.get_system_mouse_cursor(self.window.CURSOR_DEFAULT)
        self.cursor_text = self.window.get_system_mouse_cursor(self.window.CURSOR_TEXT)

        for i, avatar_image in enumerate(AVATAR_IMAGES):
            sprite = arcade.Sprite(avatar_image, scale=0.5)
            sprite.center_x = (SCREEN_WIDTH // 2 - (len(AVATAR_IMAGES) * self.avatar_width // 2)
                               + i * self.avatar_width + 50)
            sprite.center_y = self.avatar_y
            self.avatar_sprites.append(sprite)

    def on_show_view(self):
        arcade.set_background_color(arcade.color.DARK_MIDNIGHT_BLUE)

    def on_draw(self):
        self.clear()

        # Username label + textbox
        arcade.draw_text("Username:", self.textbox_x - 210, self.textbox_y + 10, arcade.color.WHITE, 14)
        arcade.draw_rectangle_filled(self.textbox_x, self.textbox_y + 15,
                                     self.textbox_width, self.textbox_height, arcade.color.WHITE)
        arcade.draw_text(self.username,
                         self.textbox_x - self.textbox_width // 2 + 5,
                         self.textbox_y + 10,
                         arcade.color.BLACK, 14)

        # Label: Select an Avatar
        label_y = self.avatar_y + 60
        arcade.draw_text("Select an Avatar", SCREEN_WIDTH // 2, label_y,
                         arcade.color.WHITE, 16, anchor_x="center")

        # Avatars with highlight
        for i, sprite in enumerate(self.avatar_sprites):
            if self.selected_avatar_index == i:
                arcade.draw_rectangle_outline(sprite.center_x, sprite.center_y,
                                              self.avatar_width + 10, self.avatar_height + 10,
                                              arcade.color.YELLOW, 3)
            sprite.draw()

        # Submit button
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
            self.window.set_mouse_cursor(self.cursor_text)
        else:
            self.window.set_mouse_cursor(self.cursor_default)


    def on_mouse_press(self, x, y, button, modifiers):
        # Submit button click
        if (self.button_x - self.button_width / 2 <= x <= self.button_x + self.button_width / 2 and
                self.button_y - self.button_height / 2 <= y <= self.button_y + self.button_height / 2):
            if self.selected_avatar_index is not None and self.username.strip():
                # Pass username and avatar index to game view
                game_view = MyGameView(
                    username=self.username.strip(),
                    avatar_index=self.selected_avatar_index
                )
                self.window.show_view(game_view)
            else:
                print("Please select an avatar and enter a username.")

        # Check avatar clicks
        for i, sprite in enumerate(self.avatar_sprites):
            if sprite.collides_with_point((x, y)):
                self.selected_avatar_index = i
                print(f"Avatar selected: {AVATAR_IMAGES[i]}")

        # Check textbox click
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


def main():
    """Start the arcade window and show UsernameSelectionView"""
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, "Game Client", resizable=True)

    selection_view = UsernameSelectionView()
    window.show_view(selection_view)
    arcade.run()


if __name__ == "__main__":
    main()
