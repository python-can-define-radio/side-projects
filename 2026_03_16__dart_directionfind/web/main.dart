/// Beginning to migrate JS code to Dart.
library;

import 'dart:js_interop';
import 'package:web/web.dart';
import 'dart:math';


const canvWidth = 600;
const canvHeight = 400;

/// Distance per second.
typedef Vel = ({double vx, double vy});

num sq(num x) => x*x;

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
  final double x;
  final double y;
  Pos(this.x, this.y);
  /// Return a new Pos shifted based on distance=rate*time
  Pos? move(Vel v, Duration t) {
    if (v == (vx: 0.0, vy: 0.0)) {
      return null;
    }
    return Pos(x + v.vx*t.inMilliseconds, y + v.vy*t.inMilliseconds);
  }
  /// Return number with 70000 added to look more like a grid coordinate
  String _padbig(double u) => (u + 70000).toInt().toString();
  String get pretty => "${_padbig(x)}, ${_padbig(y)}";
}

// A read-only view of the current player state.
class Player {
  final Pos pos;
  Player(this.pos);
} 

class PlayerMutable {
  Pos _pos;
  double _vx = 0;
  double _vy = 0;
  final _speed = 0.2;
  PlayerMutable(this._pos);
  Player get ro => Player(_pos);
  void addEventListeners(HTMLElement eventElem) {
    eventElem
      ..onKeyDown.listen(_handleOnKeyDown)
      ..onKeyUp.listen(_handleOnKeyUp);
  }
  void _handleOnKeyDown(KeyboardEvent event) {
    if (event.key == 'ArrowUp') { _vy = -_speed; }
    else if (event.key == 'ArrowDown') { _vy = _speed; }
    else if (event.key == 'ArrowLeft') { _vx = -_speed; }
    else if (event.key == 'ArrowRight') { _vx = _speed; }
  }
  void _handleOnKeyUp(KeyboardEvent event) {
    if (event.key == 'ArrowUp') { _vy = 0; }
    else if (event.key == 'ArrowDown') { _vy = 0; }
    else if (event.key == 'ArrowLeft') { _vx = 0; }
    else if (event.key == 'ArrowRight') { _vx = 0; }
  }
  void update(Duration tdelta) {
    final newPos = _pos.move((vx: _vx, vy: _vy), tdelta);
    if (newPos != null) {
      _pos = newPos;
    }
  }
  void draw(CanvasRenderingContext2D ctx) {
    const sz = 2; // size
    const cenx = canvWidth / 2;
    const ceny = canvHeight / 2;
    ctx.fillStyle = "#000".toJS; 
    fillCircle(cenx + sz, ceny-sz*3, sz*3, ctx); // head
    ctx.fillRect(cenx-sz*1, ceny-sz*2, sz*4, sz*12); // torso
    ctx.fillRect(cenx-sz*4, ceny+sz*2, sz*10, sz);  // arms
    ctx.fillRect(cenx-sz*1, ceny+sz*10, sz*1.5, sz*5); // leg
    ctx.fillRect(cenx+sz*1, ceny+sz*10, sz*1.5, sz*5); // leg
  }
}

void fillRectRel(num x, num y, num w, num h, CanvasRenderingContext2D ctx, Pos relpos) {
  ctx.fillRect(x - relpos.x + canvWidth/2, y - relpos.y + canvHeight/2, w, h);
}
void moveToRel(num x, num y, CanvasRenderingContext2D ctx, Pos relpos){
  ctx.moveTo(x - relpos.x + canvWidth/2, y - relpos.y + canvHeight/2);
}
void lineToRel(num x, num y, CanvasRenderingContext2D ctx, Pos relpos){
  ctx.lineTo(x - relpos.x + canvWidth/2, y - relpos.y + canvHeight/2);
}
void fillCircle(num x, num y, num radius, CanvasRenderingContext2D ctx) {
  ctx.beginPath();
  ctx.arc(x, y, radius, 0, 2 * pi);
  ctx.fill();  
}
void fillCircleRel(num x, num y, num radius, CanvasRenderingContext2D ctx, Pos relpos) {
  fillCircle(x - relpos.x + canvWidth/2, y - relpos.y + canvHeight/2, radius, ctx);
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
  void elemAppend(HTMLElement elem) {
    elem.appendChild(_canv);
  }
}

class HUD {
  /// Currently this `div` just contains the status.
  final _div = HTML.div();
  late final HTMLSpanElement _status = HTML.span();
  late final HTMLInputElement _gatheringLobs = HTML.checkbox()..defaultChecked = true;
  bool get gatheringLobs => _gatheringLobs.checked;
  HUD() {
    _div.appendChild(HTML.div()..innerText = "Direction Finding Simulator");
    _div.appendChild(HTML.div()..innerText = "Arrow keys to move.");
    _div.appendChild(_status);
    _div.appendChild(HTML.span()..innerText = "Gathering Lobs (Toggle: 'L'):");
    _div.appendChild(_gatheringLobs);
  }
  void addEventListeners(HTMLElement eventElem) {
    eventElem.onKeyDown.listen(_handleOnKeyDown);
  }
  void _handleOnKeyDown(KeyboardEvent event) {
    if (event.key.toLowerCase() == "l") {
      _gatheringLobs.checked = !_gatheringLobs.checked;
    }
  }
  /// Mutate the parent to append this class's HTML elem
  void elemAppend(HTMLElement parent) {
    parent.appendChild(_div);
  }
  void update(Player p, TxRadio t, LOBCol lobc) {
    final dBm = lobc.lastlob?.rxpow.dBm.toStringAsFixed(1);
    _status.innerText = 
      "Player pos: ${p.pos.pretty}\n"
      "Transmitting radio pos: ${t.pos.pretty}\n"
      "Most recent LOB power: ${dBm ?? "__"} dBm\n";
  }
}

class TxRadio {
  final pos = Pos(400, 370);
  final txpower = Power(1000);

  void draw(CanvasRenderingContext2D ctx, Player p) {
    ctx.fillStyle = "#00f".toJS; 
    fillRectRel(pos.x, pos.y, 10, 10, ctx, p.pos);
  }
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



class Bush {
  late final Pos _pos;
  final String _color;
  final int _size;
  Bush(double x, double y, this._color, this._size) {
    _pos = Pos(x, y);
  }
  void draw(CanvasRenderingContext2D ctx, Player p1) {
    final xd = _pos.x - p1.pos.x;
    final yd = _pos.y - p1.pos.y;
    /// Distance threshold. Basically pythagorean theorem but without sqrt and with some scaling to make it so bushes near the edge still render
    final dthr = 2 * (sq(xd) + sq(yd));
    if (dthr > sq(canvHeight) && dthr > sq(canvWidth)) {
      return;
    }
    ctx.fillStyle = "#440".toJS;
    fillRectRel(_pos.x - _size, _pos.y + _size*0.7, _size*0.9, 6, ctx, p1.pos);
    fillRectRel(_pos.x, _pos.y + _size*0.7, _size*0.9, 6, ctx, p1.pos);
    fillRectRel(_pos.x + _size*0.7, _pos.y + _size*0.7, _size*0.9, 6, ctx, p1.pos);
    ctx.fillStyle = _color.toJS; 
    fillCircleRel(_pos.x - _size, _pos.y, _size, ctx, p1.pos);
    fillCircleRel(_pos.x, _pos.y, _size, ctx, p1.pos);
    fillCircleRel(_pos.x, _pos.y - _size, _size, ctx, p1.pos);
    fillCircleRel(_pos.x + _size, _pos.y, _size, ctx, p1.pos);
    fillCircleRel(_pos.x, _pos.y - _size, _size, ctx, p1.pos);
    fillCircleRel(_pos.x + 2*_size, _pos.y, _size, ctx, p1.pos);
    fillCircleRel(_pos.x + 1.5*_size, _pos.y - _size, _size, ctx, p1.pos);
  }
}

typedef LOB = ({Pos source, Azimuth azimuth, Power rxpow});

/// Collection of LOBs
class LOBCol {
  final List<LOB> _lobs = [];
  LOB? get lastlob => _lobs.lastOrNull;
  void addlob(LOB? newlob, HUD hud) {
    if (hud.gatheringLobs == false) {
      return;
    } else if (newlob == null) {
      return;
    }
    _lobs.add(newlob);
  }
  void draw(CanvasRenderingContext2D ctx, Player p) {
    const loblength = 10000; // arbitrarily long so that the lob appears to be an unending ray
    for (var lob in _lobs) {
      final endx = lob.source.x + loblength*lob.azimuth.cosresult;
      final endy = lob.source.y + loblength*lob.azimuth.sinresult;
      ctx.beginPath();
      ctx.lineWidth = 2;
      ctx.strokeStyle = "orange".toJS;
      moveToRel(lob.source.x, lob.source.y, ctx, p.pos);
      lineToRel(endx, endy, ctx, p.pos);
      ctx.stroke();
    }
  }
}


class Azimuth {
  late final double sinresult;
  late final double cosresult;
  Azimuth.fromPositions(Player p, TxRadio t) {
    final xd = t.pos.x - p.pos.x;
    final yd = t.pos.y - p.pos.y;
    final dist = sqrt(xd*xd + yd*yd);
    sinresult = yd / dist;
    cosresult = xd / dist;
  }
  Azimuth.fromSinCos(this.sinresult, this.cosresult);
}

double logbase10(double x) => log(x) / log(10);

class Power {
  final double mW;
  double get dBm => 10 * logbase10(mW);
  Power(this.mW);
  Power operator *(double other) {
    return Power(mW * other);
  }
}

/// Simulator. A class that simulates LOBs.
/// Has no local state except a random number generator.
class Sim {
  final _random = Random();
  
  /// add random noise. Need to figure out whether this is typical distribution
  Azimuth _noi(Azimuth a) {
    p3(double x) => x*x*x;
    return Azimuth.fromSinCos(
      a.sinresult + 0.003*p3(6*(_random.nextDouble() - 0.5)),
      a.cosresult + 0.003*p3(6*(_random.nextDouble() - 0.5))
    );
  }
  /// A very rudimentary path loss computation
  Power _distLoss(TxRadio t, Player p1) {
    final xd = t.pos.x - p1.pos.x;
    final yd = t.pos.y - p1.pos.y;
    final dist = sqrt(xd*xd + yd*yd);
    return t.txpower * (1 / dist);
  }
  
  LOB? simulateLOB(Player p1, TxRadio t) {
    if (_random.nextInt(10) != 0) {
      return null;
    }
    return (
      source: p1.pos,
      azimuth: _noi(Azimuth.fromPositions(p1, t)),
      rxpow: _distLoss(t, p1),
    );
  }
}

class ObjCol {
  late final List<Bush> _objs;
  ObjCol() {
    final random = Random();
    Bush makebush() {
      final redandblue = "${random.nextInt(5)}";
      final green = "${random.nextInt(5)+5}";
      final size = random.nextInt(6) + 2;
      return Bush(
        (random.nextDouble() - 0.5) * 10000,
        (random.nextDouble() - 0.5) * 10000,
        "#$redandblue$green$redandblue",
        size
      );
    }
    _objs = [for (var i = 0; i < 10000; i++) makebush()];
  }
  void draw(CanvasRenderingContext2D ctx, Player p1) {
    for (final obj in _objs) {
      obj.draw(ctx, p1);
    }
  }
}

void main() async {
  final cm = CanvM();
  final t1 = TxRadio();
  final sim = Sim();
  final oc = ObjCol();
  final lobc = LOBCol();
  final playermut = PlayerMutable(Pos(500, 1050));
  final hud = HUD();

  hud.elemAppend(document.body!);
  cm.elemAppend(document.body!);
  
  playermut.addEventListeners(document.body!);
  hud.addEventListeners(document.body!);

  runEachFrame((Duration tdelta) {
    playermut.update(tdelta);
    final p1 = playermut.ro;
    lobc.addlob(sim.simulateLOB(p1, t1), hud);
    hud.update(p1, t1, lobc);
    cm.drawBackground();
    t1.draw(cm.ctx, p1);
    playermut.draw(cm.ctx);
    oc.draw(cm.ctx, p1);
    lobc.draw(cm.ctx, p1);
  });
}
