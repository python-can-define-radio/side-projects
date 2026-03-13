/// Beginning to migrate JS code to Dart.
library;

import 'dart:js_interop';
import 'package:web/web.dart';
import 'dart:math';



/// Methods for creating HTML elems
class HTML {
  static HTMLDivElement div() => document.createElement('div') as HTMLDivElement;
  static HTMLCanvasElement canvas() => document.createElement('canvas') as HTMLCanvasElement;
}

class Transmitter {
  final _txmitx = 320.0;
  final _txmity = 200.0;
  bool active = false;
  /// In the case of a GPS spoofer, this is the currently transmitted (spoofed) x
  double? get txmitx {
    if (active) {
      return _txmitx;
    }
    return null;
  }
  /// In the case of a GPS spoofer, this is the currently transmitted (spoofed) y
  double? get txmity {
    if (active) {
      return _txmity;
    }
    return null;
  }
  void handleOnKeyDown(KeyboardEvent event) {
    if (event.key == 'ArrowUp') { active = true; }
  }
  void handleOnKeyUp(KeyboardEvent event) {
    if (event.key == 'ArrowUp') { active = false;}
  }
}

class Player {
  double x = 300;
  double y = 200;
  double vx = 0;
  double vy = 0;
  // final _speed = 0.2;
  void update(double tdelta) {
    x += vx * tdelta;
    y += vy * tdelta;
  }
  void handleOnKeyDown(KeyboardEvent event) {
    // if (event.key == 'ArrowUp') { vy = -_speed; }
    // else if (event.key == 'ArrowDown') { vy = _speed; }
    // else if (event.key == 'ArrowLeft') { vx = -_speed; }
    // else if (event.key == 'ArrowRight') { vx = _speed; }
    // else { print("${event.key} down"); }
  }
  void handleOnKeyUp(KeyboardEvent event) {
    // if (event.key == 'ArrowUp') { vy = 0; }
    // else if (event.key == 'ArrowDown') { vy = 0; }
    // else if (event.key == 'ArrowLeft') { vx = 0; }
    // else if (event.key == 'ArrowRight') { vx = 0; }
    // else { print("${event.key} up"); }
  }
  void draw(CanvasRenderingContext2D ctx) {
    ctx.fillStyle = "#000".toJS; 
    ctx.fillRect(x, y, 30, 30);
  }
}

/// World Draw-er (the class that handles drawing the world).
/// Just hiding some of the canvas details.
class WorldD {
  final _bgcolor = "#fcc";
  final canv = HTML.canvas();
  WorldD() {
    canv
      ..width = 600
      ..height = 400;
  }
  void draw(CanvasRenderingContext2D ctx) {
    ctx.fillStyle = _bgcolor.toJS; 
    ctx.fillRect(0, 0, canv.width, canv.height);
  }
}

class HUD {
  /// Currently this `div` just contains the status.
  final div = HTML.div()..style.color = "#f00";
  void update(Player p1, Drone d1) {
    div.innerText = "px: ${p1.x.toStringAsFixed(2)}, py: ${p1.y.toStringAsFixed(2)}, dx: ${d1.x.toStringAsFixed(2)}, dy: ${d1.y.toStringAsFixed(2)}";
  }
}


class Drone {
  double x = 0;
  double y = 0;
  double vx = 0;
  double vy = 0;
  double speed = 0;

  final _random = Random();

  /// Set the drone's x,y,vx,vy randomly near the edge of the screen.
  void _randomize(double width, double height) {
    /// 0=top,1=right,2=bottom,3=left
    int side = _random.nextInt(4);

    switch (side) {
      case 0: /// top
        x = _random.nextDouble() * width;
        y = -20;
        break;

      case 1: /// right
        x = width + 10;
        y = _random.nextDouble() * height;
        break;

      case 2: /// bottom
        x = _random.nextDouble() * width;
        y = height + 10;
        break;

      case 3: /// left
        x = -10;
        y = _random.nextDouble() * height;
        break;
    }
    speed = _random.nextDouble() * .25;
  }
  Drone(int width, int height) {
    _randomize(width.toDouble(), height.toDouble());
  }
  void update(double tdelta, double? fakedx, double? fakedy) {
    final perceivedx = fakedx ?? x;
    final perceivedy = fakedy ?? y;
    _setVelocityToward(perceivedx, perceivedy, 300, 200, speed);
    x += vx * tdelta;
    y += vy * tdelta;
  }
  void draw(CanvasRenderingContext2D ctx) {
    ctx.fillStyle = "#00f".toJS; 
    ctx.fillRect(x, y, 10, 10);
  }
  void _setVelocityToward(double perceivedx, double perceivedy, double targetX, double targetY, double speed) {
    double angle = atan2(targetY - perceivedy, targetX - perceivedx);
    vx = cos(angle) * speed;
    vy = sin(angle) * speed;
  }
}

/// Repeatedly call requestAnimationFrame; pass the time delta as an argument to `frameUpdate`
void runEachFrame(void Function(double) frameUpdate) {
  void dartRAF(void Function(double) callback) {
    window.requestAnimationFrame(callback.toJS);
  }
  double tlast = 0;
  void animate(double timems) {
    final deltams = timems - tlast;
    tlast = timems;
    frameUpdate(deltams);
    dartRAF(animate);
  }
  dartRAF(animate);
}

/*
Proposal:
- Add incoming enemy 'drone' which approaches from a random edge of the screen with a random velocity
- HUD shows detected drone with lat, lon, and height.
  - has a button for 'jam gps'
- height decreases
- different types of drones that are controlled in different ways
- realistic drone movement based on acceleration / momentum instead of being able to instantly change direction
*/

void main() async {
  final wd = WorldD();
  final p1 = Player();
  final txer = Transmitter();
  final hud = HUD();
  final ctx = wd.canv.getContext('2d') as CanvasRenderingContext2D;
  final d1 = Drone(wd.canv.width, wd.canv.height);

  document.body!
    ..appendChild(hud.div)
    ..appendChild(wd.canv)
    ..onKeyDown.listen(p1.handleOnKeyDown)
    ..onKeyUp.listen(p1.handleOnKeyUp)
    ..onKeyDown.listen(txer.handleOnKeyDown)
    ..onKeyUp.listen(txer.handleOnKeyUp)
    ;

  runEachFrame((double deltams) {
    p1.update(deltams);
    d1.update(deltams, txer.txmitx, txer.txmity);
    hud.update(p1, d1);
    wd.draw(ctx);
    p1.draw(ctx);
    d1.draw(ctx);
  });
}
