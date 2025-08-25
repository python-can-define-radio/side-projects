import arcade
import zmq
from shared_constants import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SCALING, PLAYER_SCALING


context = zmq.Context()

#  Socket to talk to server
print("Connecting to server")
to_srv_sock = context.socket(zmq.PUB)
to_srv_sock.connect("tcp://localhost:5555")
from_srv_sock = context.socket(zmq.SUB)
from_srv_sock.connect("tcp://localhost:5556")
from_srv_sock.setsockopt_string(zmq.SUBSCRIBE, "")


class MyGame(arcade.Window):
    """Main application class."""

    def __init__(self):
        """
        Initializer
        """
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Game client", resizable=True)
        self.setup()

    def setup(self):
        """Set up the game and initialize the variables."""

        # Map name
        map_name = ":resources:tiled_maps/level_1.json"

        # Load in TileMap
        self.tile_map = arcade.load_tilemap(map_name, TILE_SCALING)

        # Initiate New Scene with our TileMap, this will automatically add all layers
        # from the map as SpriteLists in the scene in the proper order.
        self.scene = arcade.Scene.from_tilemap(self.tile_map)

        # Set up the player
        self.player_sprite = arcade.Sprite(
            ":resources:images/animated_characters/female_person/femalePerson_idle.png",
            PLAYER_SCALING,
        )

        # Starting position of the player
        self.player_sprite.center_x = 196
        self.player_sprite.center_y = 128
        self.scene.add_sprite("Player", self.player_sprite)

        self.camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

        # --- Other stuff
        # Set the background color
        self.background_color = (200, 200, 255)

    def on_resize(self, width, height):
        """Resize window"""
        self.camera.resize(width, height)

    def on_draw(self):
        """Render the screen."""
        self.clear()
        self.camera.use()
        self.scene.draw()

    def on_key_press(self, key, modifiers):
        to_srv_sock.send_json({"keypress": key})

    def on_key_release(self, key, modifiers):
        to_srv_sock.send_json({"keyrelease": key})
        
    def pan_camera_to_user(self, panning_fraction: float = 1.0):
        """
        Manage Scrolling

        :param panning_fraction: Number from 0 to 1. Higher the number, faster we
                                 pan the camera to the user.
        """

        # This spot would center on the user
        screen_center_x = self.player_sprite.center_x - (self.camera.viewport_width / 2)
        screen_center_y = self.player_sprite.center_y - (
            self.camera.viewport_height / 2
        )
        user_centered = screen_center_x, screen_center_y
        self.camera.move_to(user_centered, panning_fraction)

    def on_update(self, delta_time):
        """Movement and game logic"""
        try:
            message: dict = from_srv_sock.recv_json(flags=zmq.NOBLOCK)
            self.player_sprite.center_x = message["playerx"]
            self.player_sprite.center_y = message["playery"]
        except zmq.Again:
            pass
        # update_player_position_based_on_the_server_info()
        self.pan_camera_to_user(panning_fraction=0.12)


def main():
    """Get this game started."""
    window = MyGame()
    arcade.run()


if __name__ == "__main__":
    main()
