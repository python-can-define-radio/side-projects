/// Beginning to migrate JS code to Dart.
library;

import 'dart:js_interop';
import 'package:web/web.dart';
import 'dart:math';


const canvWidth = 600;
const canvHeight = 400;



/// Distance per second.
typedef Vel = ({double vx, double vy});


/// Methods for creating HTML elems
class HTML {
  static HTMLButtonElement button() => document.createElement('button') as HTMLButtonElement;
  static HTMLInputElement checkbox()  {
    final el = document.createElement('input') as HTMLInputElement;
    el.setAttribute("type", "checkbox");
    return el;
  }
  static HTMLCanvasElement canvas() => document.createElement('canvas') as HTMLCanvasElement;
  static HTMLDivElement div() => document.createElement('div') as HTMLDivElement;
  static HTMLSpanElement span() => document.createElement('span') as HTMLSpanElement;
}

class Pos {
  double _x;
  double _y;
  Pos(this._x, this._y);
  void move(Vel v, Duration t) {
    _x += v.vx * t.inMilliseconds;
    _y += v.vy * t.inMilliseconds;
  }
  /// A read-only copy of this position
  PosReadOnly get ro => PosReadOnly(_x, _y);
}

class PosReadOnly {
  final double x;
  final double y;
  PosReadOnly(this.x, this.y);
  /// Return number with 70000 added to look more like a grid coordinate
  String _padbig(double u) => (u + 70000).toInt().toString();
  String get pretty => "${_padbig(x)}, ${_padbig(y)}";
}

class Player {
  /// initial position is arbitrary
  final _pos = Pos(500, 1050);
  double _vx = 0;
  double _vy = 0;
  final _speed = 0.2;
  void addEventListeners() {
    document.body!
      ..onKeyDown.listen(_handleOnKeyDown)
      ..onKeyUp.listen(_handleOnKeyUp);
  }
  void _handleOnKeyDown(KeyboardEvent event) {
    if (event.key == 'ArrowUp') { _vy = -_speed; }
    else if (event.key == 'ArrowDown') { _vy = _speed; }
    else if (event.key == 'ArrowLeft') { _vx = -_speed; }
    else if (event.key == 'ArrowRight') { _vx = _speed; }
    else { print("${event.key} down"); }
  }
  void _handleOnKeyUp(KeyboardEvent event) {
    if (event.key == 'ArrowUp') { _vy = 0; }
    else if (event.key == 'ArrowDown') { _vy = 0; }
    else if (event.key == 'ArrowLeft') { _vx = 0; }
    else if (event.key == 'ArrowRight') { _vx = 0; }
    else { print("${event.key} up"); }
  }
  void update(Duration tdelta) {
    _pos.move((vx: _vx, vy: _vy), tdelta);
  }
  void draw(CanvasRenderingContext2D ctx) {
    ctx.fillStyle = "#000".toJS; 
    ctx.fillRect(canvWidth / 2, canvHeight / 2, 30, 30);
  }
  PosReadOnly get posro => _pos.ro;
}

void fillRectRel(num x, num y, num w, num h, CanvasRenderingContext2D ctx, PosReadOnly relpos) {
  ctx.fillRect(x - relpos.x + canvWidth/2, y - relpos.y + canvHeight/2, w, h);
}
void moveToRel(num x, num y, CanvasRenderingContext2D ctx, PosReadOnly relpos){
  ctx.moveTo(x - relpos.x + canvWidth/2, y - relpos.y + canvHeight/2);
}
void lineToRel(num x, num y, CanvasRenderingContext2D ctx, PosReadOnly relpos){
  ctx.lineTo(x - relpos.x + canvWidth/2, y - relpos.y + canvHeight/2);
}

/// Canvas Manager.
class CanvM {
  final _bgcolor = "#fcc";
  final _canv = HTML.canvas();
  late final CanvasRenderingContext2D ctx;
  CanvM() {
    _canv
      ..width = canvWidth
      ..height = canvHeight;
    ctx = _canv.getContext('2d') as CanvasRenderingContext2D;
  }
  void drawBackground() {
    ctx.fillStyle = _bgcolor.toJS; 
    ctx.fillRect(0, 0, _canv.width, _canv.height);
  }
  /// Mutate the document body to append this class's HTML elem
  void bodyAppend() {
    document.body!.appendChild(_canv);
  }
}

class HUD {
  /// Currently this `div` just contains the status.
  final _div = HTML.div()..style.color = "#f00";
  late final HTMLSpanElement _status;
  HUD() {
    _status = HTML.span();
    _div.appendChild(_status);
  }
  /// Mutate the document body to append this class's HTML elem
  void bodyAppend() {
    document.body!.appendChild(_div);
  }
  void update(PosReadOnly p1p, PosReadOnly t1p) {
    _status.innerText = "player pos: ${p1p.pretty}\n Transmitting radio pos: ${t1p.pretty}\n";
  }
}

class TxRadio {
  final _pos = Pos(400, 370);

  void update(Duration tdelta) {
    // Eventually might turn on/off or move
  }
  void draw(CanvasRenderingContext2D ctx, PosReadOnly playerPos) {
    ctx.fillStyle = "#00f".toJS; 
    fillRectRel(_pos.ro.x, _pos.ro.y, 10, 10, ctx, playerPos);
  }
  PosReadOnly get posro => _pos.ro;
}

/// Repeatedly call requestAnimationFrame; pass the time delta as an argument to `frameUpdate`
void runEachFrame(void Function(Duration) frameUpdate) {
  void dartRAF(void Function(double) callback) {
    window.requestAnimationFrame(callback.toJS);
  }
  double tlast = 0;
  void animate(double timems) {
    final deltams = timems - tlast;
    tlast = timems;
    frameUpdate(Duration(milliseconds: deltams.toInt()));
    dartRAF(animate);
  }
  dartRAF(animate);
}

/*


1. player stays in center of map -- movement moves the world, not the player

Player is direction finding a transmitter.
Initially, dfing is based on line-of-sight only. (Later: add reflections, path loss, etc)

- Draw a ray from the player to the transmitter.

- if line of sight exists.
  - How to determine line of sight?

- elevation
*/

class Tree {
  final _pos = Pos(350, 270);

  void draw(CanvasRenderingContext2D ctx, PosReadOnly playerPos) {
    ctx.fillStyle = "#000".toJS; 
    fillRectRel(_pos.ro.x + 6, _pos.ro.y + 10, 3, 30, ctx, playerPos);
    ctx.fillStyle = "#0f0".toJS; 
    fillRectRel(_pos.ro.x, _pos.ro.y, 16, 10, ctx, playerPos);
  }
}

class LOB {
  final PosReadOnly source;
  final PosReadOnly target;
  LOB(this.source, this.target);
}

class LOBDisplayer {
  final List<LOB> lobs = [];
  void update(PosReadOnly playerPos, EMPhys em) {
    var t = em.available.elementAtOrNull(0);
    if (t != null) {
      lobs.add(LOB(playerPos, t));
    }
  }
  void draw(CanvasRenderingContext2D ctx, PosReadOnly playerPos) {
    for (var lob in lobs) {
      ctx.beginPath();
      ctx.lineWidth = 3;
      ctx.strokeStyle = "orange".toJS;
      moveToRel(lob.source.x, lob.source.y, ctx, playerPos);
      lineToRel(lob.target.x, lob.target.y, ctx, playerPos);
      ctx.stroke();
    }
  }
}


class EMPhys {
  final _random = Random();
  final List<PosReadOnly> available = [];
  void update(PosReadOnly playerPos, PosReadOnly targetPos) {
    available.clear();
    if (_random.nextInt(20) == 0) {
      available.add(targetPos);
    }
  }
}

void main() async {
  final cm = CanvM();
  final hud = HUD();
  final p1 = Player();
  final t1 = TxRadio();
  final tr1 = Tree();
  final lobd = LOBDisplayer();
  final em = EMPhys();

  hud.bodyAppend();
  cm.bodyAppend();
  
  p1.addEventListeners();

  runEachFrame((Duration tdelta) {
    p1.update(tdelta);
    t1.update(tdelta);
    hud.update(p1.posro, t1.posro);
    em.update(p1.posro, t1.posro);
    lobd.update(p1.posro, em);
    cm.drawBackground();
    p1.draw(cm.ctx);
    t1.draw(cm.ctx, p1.posro);
    tr1.draw(cm.ctx, p1.posro);
    lobd.draw(cm.ctx, p1.posro);
  });
}
