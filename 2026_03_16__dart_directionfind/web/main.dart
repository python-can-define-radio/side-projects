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
  final double x;
  final double y;
  Pos(this.x, this.y);
  /// Return a new Pos shifted based on distance=rate*time
  Pos move(Vel v, Duration t) {
    return Pos(x + v.vx*t.inMilliseconds, y + v.vy*t.inMilliseconds);
  }
  /// Return number with 70000 added to look more like a grid coordinate
  String _padbig(double u) => (u + 70000).toInt().toString();
  String get pretty => "${_padbig(x)}, ${_padbig(y)}";
}

typedef Player = ({Pos pos, double vx, double vy});

class PlayerMutable {
  /// initial position is arbitrary
  Pos _pos;
  double _vx;
  double _vy;
  final _speed = 0.2;
  PlayerMutable(this._pos, this._vx, this._vy);
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
    _pos = _pos.move((vx: _vx, vy: _vy), tdelta);
  }
  void draw(CanvasRenderingContext2D ctx) {
    const s = 15;
    const s2 = s * 2;
    ctx.fillStyle = "#000".toJS; 
    ctx.fillRect(canvWidth / 2 - s, canvHeight / 2 - s, s2, s2);
  }
  /// A read-only copy (to avoid passing a mutable object)
  Player get ro => (pos: _pos, vx: _vx, vy: _vy);
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

class SimpleObject {
  late final Pos _pos;
  SimpleObject(double x, double y) {
    _pos = Pos(x, y);
  }
  void draw(CanvasRenderingContext2D ctx, Pos playerPos) {
    ctx.fillStyle = "#000".toJS; 
    fillRectRel(_pos.x + 6, _pos.y + 10, 3, 30, ctx, playerPos);
    ctx.fillStyle = "#0f0".toJS; 
    fillRectRel(_pos.x, _pos.y, 16, 10, ctx, playerPos);
  }
}

typedef LOB = ({Pos source, Azimuth azimuth, Power rxpow});

/// Collection of LOBs
class LOBCol {
  final List<LOB> _lobs = [];
  LOB? get lastlob => _lobs.lastOrNull;
  void addlob(LOB? newlob) {
    if (newlob != null) {
      _lobs.add(newlob);
    }
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
  
  /// add random noise
  Azimuth _noi(Azimuth a) {
    return Azimuth.fromSinCos(
      a.sinresult + 0.2*(_random.nextDouble() - 0.5),
      a.cosresult + 0.2*(_random.nextDouble() - 0.5)
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
    if (_random.nextInt(40) != 0) {
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
  final _objs = [SimpleObject(400, 1000), SimpleObject(450, 1200)];
  void draw(CanvasRenderingContext2D ctx, Player p) {
    for (final obj in _objs) {
      obj.draw(ctx, p.pos);
    }
  }
}

void main() async {
  final cm = CanvM();
  final hud = HUD();
  final t1 = TxRadio();
  final sim = Sim();
  final oc = ObjCol();
  final lobc = LOBCol();
  final p1 = PlayerMutable(Pos(500, 1050), 0, 0);

  hud.bodyAppend();
  cm.bodyAppend();
  
  p1.addEventListeners();

  runEachFrame((Duration tdelta) {
    p1.update(tdelta);
    lobc.addlob(sim.simulateLOB(p1.ro, t1));
    hud.update(p1.ro, t1, lobc);
    cm.drawBackground();
    p1.draw(cm.ctx);
    t1.draw(cm.ctx, p1.ro);
    oc.draw(cm.ctx, p1.ro);
    lobc.draw(cm.ctx, p1.ro);
  });
}
