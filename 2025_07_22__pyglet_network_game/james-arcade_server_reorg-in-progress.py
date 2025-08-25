import arcade

from server_networking import to_players_sock, recv_player_msg
from shared_constants import TILE_SCALING, PLAYER_SCALING, SCREEN_HEIGHT, SCREEN_WIDTH


    


# Map Layers
LAYER_NAME_PLATFORMS = "Platforms"
LAYER_NAME_COINS = "Coins"
LAYER_NAME_BOMBS = "Bombs"



def make_walls():
    wl = arcade.SpriteList()
    for i in range(0, 100):
        wall = arcade.Sprite(":resources:images/tiles/boxCrate_double.png", TILE_SCALING)
        wall.center_x = i * wall.width
        wall.center_y = 0
        wl.append(wall)
    return wl


def player_stuff():
    gravity = 0.2
    # Set up the player
    player_sprite = arcade.Sprite(
        ":resources:images/animated_characters/female_person/femalePerson_idle.png",
        PLAYER_SCALING,
    )

    # Starting position of the player
    self.player_sprite.center_x = 196
    self.player_sprite.center_y = 128
    self.player_list.append(self.player_sprite)

    # Keep player from running through the wall_list layer
    self.physics_engine = arcade.PhysicsEnginePlatformer(
        self.player_sprite,
        self.scene.get_sprite_list(LAYER_NAME_PLATFORMS),
        gravity_constant=gravity,
    )


def handle_message(message):
    """Update state based on what the client said.
    Not an arcade func."""
    if message == None:
        return
    
    assert isinstance(message, dict)

    jump_speed = 10
    movement_speed = 5
    if "keypress" in message:
        key = message["keypress"]
        if key == arcade.key.UP:
            if self.physics_engine.can_jump():
                self.player_sprite.change_y = jump_speed
        elif key == arcade.key.LEFT:
            self.player_sprite.change_x = -movement_speed
        elif key == arcade.key.RIGHT:
            self.player_sprite.change_x = movement_speed
    elif "keyrelease" in message:
        key = message["keyrelease"]
        if key == arcade.key.LEFT or key == arcade.key.RIGHT:
            self.player_sprite.change_x = 0
    else:
        print("Invalid message keys", message.keys())


class MyGame(arcade.Window):
    """Main application class."""

    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT,  "Server view", resizable=True)
        self.setup()

    def setup(self):
        """Set up the game and initialize the variables."""
        self.wall_list = make_walls()
        self.player_list = arcade.SpriteList()

    def on_draw(self):
        """Render the screen."""
        self.clear()
        self.wall_list.draw()
        self.player_list.draw()

    def on_update(self, delta_time):
        """Movement and game logic"""
        print("u", end="", flush=True)
        return
        handle_message(recv_player_msg())

        to_players_sock.send_json({"playerx": self.player_sprite.center_x, "playery": self.player_sprite.center_y})
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
