import arcade
import zmq

TILE_SCALING = 0.5
PLAYER_SCALING = 0.5

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

SCREEN_TITLE = "Camera Example"
SPRITE_PIXEL_SIZE = 128
GRID_PIXEL_SIZE = SPRITE_PIXEL_SIZE * TILE_SCALING

# Physics
MOVEMENT_SPEED = 5
JUMP_SPEED = 23
GRAVITY = 1.1

# Map Layers
LAYER_NAME_PLATFORMS = "Platforms"
LAYER_NAME_COINS = "Coins"
LAYER_NAME_BOMBS = "Bombs"


context = zmq.Context()
from_players_sock = context.socket(zmq.SUB)
from_players_sock.bind("tcp://*:5555")
from_players_sock.setsockopt_string(zmq.SUBSCRIBE, "")
to_players_sock = context.socket(zmq.PUB)
to_players_sock.bind("tcp://*:5556")



class MyGame(arcade.Window):
    """Main application class."""

    def __init__(self):
        """
        Initializer
        """
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, resizable=True)
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

        # Keep player from running through the wall_list layer
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite,
            self.scene.get_sprite_list(LAYER_NAME_PLATFORMS),
            gravity_constant=GRAVITY,
        )

    def on_resize(self, width, height):
        """Resize window"""
        self.camera.resize(width, height)

    def on_draw(self):
        """Render the screen."""
        self.clear()
        self.camera.use()
        self.scene.draw()

    def handle_message(self, message):
        """Update state based on what the client said.
        Not an arcade func."""

        if "keypress" in message:
            key = message["keypress"]
            if key == arcade.key.UP:
                if self.physics_engine.can_jump():
                    self.player_sprite.change_y = JUMP_SPEED
            elif key == arcade.key.LEFT:
                self.player_sprite.change_x = -MOVEMENT_SPEED
            elif key == arcade.key.RIGHT:
                self.player_sprite.change_x = MOVEMENT_SPEED
        elif "keyrelease" in message:
            key = message["keyrelease"]
            if key == arcade.key.LEFT or key == arcade.key.RIGHT:
                self.player_sprite.change_x = 0
        else:
            print("Invalid message keys", message.keys())

    def on_update(self, delta_time):
        """Movement and game logic"""
        try:
            message: dict = from_players_sock.recv_json(flags=zmq.NOBLOCK)
            print("Received message:", message)
            self.handle_message(message)
            # to_players_sock.send_json(message)
        except zmq.Again:
            pass

        # Call update on all sprites
        self.physics_engine.update()

        coins_hit = arcade.check_for_collision_with_list(
            self.player_sprite, self.scene.get_sprite_list("Coins")
        )
        for coin in coins_hit:
            coin.remove_from_sprite_lists()


def main():
    """Get this game started."""
    window = MyGame()
    arcade.run()


if __name__ == "__main__":
    main()
