# Overall: Make an Electromagnetic (EM) propagation/modulation learning game.

## 1: Gameplay aspects
- What will the objectives be? (maybe map locations?)
- Levels?
- Teams vs free-for-all?
- Three or four different maps?
- Moveable terrain (sandbox-style game)?
    - Maybe this and/or others are power-ups
      from accomplishing EM missions?
- Possible power-ups:
  - Transmit power
  - Larger antenna
  - Amplifier
  - Ability to move terrain

## 2: Make Arcade work with multiplayer.

### 1: Determine what part of the arcade_starting_point.py should do socket transmitting.
 Answer: `on_update`

### 2: What should be tracked?
  Server:
  - All current players and their stats
  - The map: walls and anything else that exists
  - ...
  Client:
  - We need at least sprites for everything, but those sprites just need positions, I think.
  - We're ignoring the EM aspects for the moment.

### 3: What should be sent?
  - keypresses

### 4: We're going to try this and see whether it's fast enough -- 
    client says "keypress"
    server handles physics
    client draws

### 5: Attempt: Have server do physics

#### 1: Cli/Serv: Which creates objects? (Players, walls, etc)
    Possible? -> 
      Server creates full-featured objects
      Client creates very simple sprites that
          just draw in certain positions

### Init:
  Login screen: choose name, player sprite image
  Server records info
  Map and all objects would only need to be on server side, except enough for the client to draw it
  So, pass the object back to the client which can then be drawn

  So, client will just have window creation and drawing



## EM aspects:

### 



----
Reference info:
Source for arcade example: "Camera Example": https://api.arcade.academy/en/2.6.17/examples/camera_platform.html