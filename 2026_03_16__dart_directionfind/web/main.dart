/// Beginning to migrate JS code to Dart.
library;

import 'dart:js_interop';
import 'package:web/web.dart';
import 'dart:math';
import 'dart:collection';

const canvWidth = 600;
const canvHeight = 400;

/// Distance per second.
typedef Vel = ({double vx, double vy});

num sq(num x) => x * x;

/// Methods for creating HTML elems
class HTML {
  static HTMLButtonElement button() =>
      document.createElement('button') as HTMLButtonElement;
  static HTMLInputElement checkbox() {
    final el = document.createElement('input') as HTMLInputElement;
    el.setAttribute("type", "checkbox");
    return el;
  }

  static HTMLCanvasElement canvas() =>
      document.createElement('canvas') as HTMLCanvasElement;
  static HTMLDivElement div() =>
      document.createElement('div') as HTMLDivElement;
  static HTMLSpanElement span() =>
      document.createElement('span') as HTMLSpanElement;
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
    return Pos(x + v.vx * t.inMilliseconds, y + v.vy * t.inMilliseconds);
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
  final _events = Queue<KeyboardEvent>();
  PlayerMutable(this._pos);
  Player get ro => Player(_pos);
  
  void addev(KeyboardEvent ev) => _events.add(ev);

  void _handleOnKeyDown(KeyboardEvent event) {
    if (event.type != "keydown") {
      return;
    }
    
    if (event.key == 'ArrowUp') {
      _vy = -_speed;
    } else if (event.key == 'ArrowDown') {
      _vy = _speed;
    } else if (event.key == 'ArrowLeft') {
      _vx = -_speed;
    } else if (event.key == 'ArrowRight') {
      _vx = _speed;
    }
  }

  void _handleOnKeyUp(KeyboardEvent event) {
    if (event.type != "keyup") {
      return;
    }

    if (event.key == 'ArrowUp') {
      _vy = 0;
    } else if (event.key == 'ArrowDown') {
      _vy = 0;
    } else if (event.key == 'ArrowLeft') {
      _vx = 0;
    } else if (event.key == 'ArrowRight') {
      _vx = 0;
    }
  }

  void update(Duration tdelta) {
    while (_events.isNotEmpty) {
      final ev = _events.removeFirst();
      _handleOnKeyUp(ev);
      _handleOnKeyDown(ev);
    }
     
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
    fillCircle(cenx + sz, ceny - sz * 3, sz * 3, ctx); // head
    ctx.fillRect(cenx - sz * 1, ceny - sz * 2, sz * 4, sz * 12); // torso
    ctx.fillRect(cenx - sz * 4, ceny + sz * 2, sz * 10, sz); // arms
    ctx.fillRect(cenx - sz * 1, ceny + sz * 10, sz * 1.5, sz * 5); // leg
    ctx.fillRect(cenx + sz * 1, ceny + sz * 10, sz * 1.5, sz * 5); // leg
  }
}

void fillRectRel(
  num x,
  num y,
  num w,
  num h,
  CanvasRenderingContext2D ctx,
  Pos relpos,
) {
  ctx.fillRect(
    x - relpos.x + canvWidth / 2,
    y - relpos.y + canvHeight / 2,
    w,
    h,
  );
}

void moveToRel(num x, num y, CanvasRenderingContext2D ctx, Pos relpos) {
  ctx.moveTo(x - relpos.x + canvWidth / 2, y - relpos.y + canvHeight / 2);
}

void lineToRel(num x, num y, CanvasRenderingContext2D ctx, Pos relpos) {
  ctx.lineTo(x - relpos.x + canvWidth / 2, y - relpos.y + canvHeight / 2);
}

void fillCircle(num x, num y, num radius, CanvasRenderingContext2D ctx) {
  ctx.beginPath();
  ctx.arc(x, y, radius, 0, 2 * pi);
  ctx.fill();
}

void fillCircleRel(
  num x,
  num y,
  num radius,
  CanvasRenderingContext2D ctx,
  Pos relpos,
) {
  fillCircle(
    x - relpos.x + canvWidth / 2,
    y - relpos.y + canvHeight / 2,
    radius,
    ctx,
  );
}

/// Canvas Manager.
class CanvM {
  final String _bgcolor;
  final canv = HTML.canvas();
  late final CanvasRenderingContext2D ctx;

  CanvM(this._bgcolor, int w, int h) {
    canv
      ..width = w
      ..height = h;
    ctx = canv.getContext('2d') as CanvasRenderingContext2D;
  }

  void drawBackground() {
    ctx.fillStyle = _bgcolor.toJS;
    ctx.fillRect(0, 0, canv.width, canv.height);
  }
  
  void drawGrid(Player p) {
    const gridSpacing = 50;

    ctx.save();
    ctx.strokeStyle = "#ccc".toJS;
    ctx.lineWidth = 0.5;

    final px = p.pos.x;
    final py = p.pos.y;

    for (var x = -canvWidth ~/ 2; x <= canvWidth * 1.5; x += gridSpacing) {
      final screenX = x - px % gridSpacing + canvWidth / 2;
      ctx.beginPath();
      ctx.moveTo(screenX, 0);
      ctx.lineTo(screenX, canvHeight);
      ctx.stroke();
    }

    for (var y = -canvHeight ~/ 2; y <= canvHeight * 1.5; y += gridSpacing) {
      final screenY = y - py % gridSpacing + canvHeight / 2;
      ctx.beginPath();
      ctx.moveTo(0, screenY);
      ctx.lineTo(canvWidth, screenY);
      ctx.stroke();
    }

    ctx.restore();
  }
}


class HUDEvent {
  final KeyboardEvent? kb;
  final bool clear;
  HUDEvent({this.kb, this.clear = false});
}


class HUD {
  final rootdiv = HTML.div()..id = "hud";
  final HTMLSpanElement _playerpos = HTML.span();
  final HTMLSpanElement _lobpower = HTML.span();
  final HTMLInputElement _gatheringLobs = HTML.checkbox()
    ..defaultChecked = true;
  final HTMLButtonElement _clearBtn = HTML.button()
    ..innerText = "Clear LOBs [ c ]";
  final _events = Queue<HUDEvent>();
  bool _clearRequested = false;
  /// Read-only views
  bool get gatheringLobs => _gatheringLobs.checked;
  bool get clearRequested => _clearRequested;

  HUD() {
    rootdiv
      ..appendChild(HTML.div()
        ..appendChild(_playerpos))
      ..appendChild(HTML.div()
        ..appendChild(_lobpower)
        ..appendChild(HTML.span()..innerText = "Gathering Lobs [ g ]:")
        ..appendChild(_gatheringLobs)
        ..appendChild(_clearBtn)
      );
  }

  void addEventListeners(HTMLElement eventElem) {
    eventElem.onKeyDown.listen((ev) => _events.add(HUDEvent(kb: ev)));
    _clearBtn.onClick.listen((_)  => _events.add(HUDEvent(clear: true)));
  }

  void _handleEvent(HUDEvent hev) {
    if (hev.clear) {
      _clearRequested = true;
    }
    final kb = hev.kb;
    if (kb == null) {
      return;
    }

    final key = kb.key.toLowerCase();
    final iskeydown = kb.type == "keydown";

    if (iskeydown && key == "g") {
      _gatheringLobs.checked = !_gatheringLobs.checked;
    } else if (iskeydown && key == "c") {
      _clearRequested = true;
    }
  }

  (bool, bool) _stateFromEvents(List<HUDEvent> recentevents) {
    // TODO: make this static
    _clearRequested = false; // reset this from whatever it was in the last frame
    while (_events.isNotEmpty) {
      _handleEvent(_events.removeFirst());
    }
    return (_clearRequested, _gatheringLobs.checked);
  }

  void update(Player p, TxRadio t, LOBCol lobc) {
    final (cr, gl) = _stateFromEvents(_events.toList());
    _clearRequested = cr;
    _gatheringLobs.checked = gl;
    _events.clear(); // TODO: drain the queue atomically

    final dBm = lobc.lastlob?.rxpow.dBm.toStringAsFixed(1);
    _playerpos.innerText = "Use the arrow keys to move.\nPlayer pos: ${p.pos.pretty}\n";
    _lobpower.innerText = "Selected LOB power: ${dBm ?? "__"} dBm\n";
  }
}

class TxRadio {
  final pos = Pos(400, 370);
  final txpower = Power(mW: 100);

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

Next steps as of 2026 march 25
- Move the junk out of `main`
- Option in HUD to switch between separate map or overlay
  - implementation: have a variable that gets set to the proper canvas
- Zoom in/out on LOB view


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
    fillRectRel(
      _pos.x - _size,
      _pos.y + _size * 0.7,
      _size * 0.9,
      6,
      ctx,
      p1.pos,
    );
    fillRectRel(_pos.x, _pos.y + _size * 0.7, _size * 0.9, 6, ctx, p1.pos);
    fillRectRel(
      _pos.x + _size * 0.7,
      _pos.y + _size * 0.7,
      _size * 0.9,
      6,
      ctx,
      p1.pos,
    );
    ctx.fillStyle = _color.toJS;
    fillCircleRel(_pos.x - _size, _pos.y, _size, ctx, p1.pos);
    fillCircleRel(_pos.x, _pos.y, _size, ctx, p1.pos);
    fillCircleRel(_pos.x, _pos.y - _size, _size, ctx, p1.pos);
    fillCircleRel(_pos.x + _size, _pos.y, _size, ctx, p1.pos);
    fillCircleRel(_pos.x, _pos.y - _size, _size, ctx, p1.pos);
    fillCircleRel(_pos.x + 2 * _size, _pos.y, _size, ctx, p1.pos);
    fillCircleRel(_pos.x + 1.5 * _size, _pos.y - _size, _size, ctx, p1.pos);
  }
}

typedef LOB = ({Pos source, Azimuth azimuth, Power rxpow});
typedef LobClickEv = ({double x, double y});

/// Collection of LOBs
class LOBCol {
  final List<LOB> _lobs = [];
  final _events = Queue<LobClickEv>();

  bool _selected = false;

  LOB? get lastlob => _lobs.lastOrNull;

  void addEventListeners(HTMLCanvasElement canv) {
    canv.onClick.listen((ev) {
      final rect = canv.getBoundingClientRect();
      final x = ev.clientX - rect.left;
      final y = ev.clientY - rect.top;
      _events.add((x: x, y: y));
    });
  }

  void update(HUD hud, Player p) {
    if (hud.clearRequested) {
      _lobs.clear();
    }

    while (_events.isNotEmpty) {
      final click = _events.removeFirst();
      _handleClick(click, p);
    }
  }

  void _handleClick(LobClickEv click, Player p) {
    _selected = true;
    if (_lobs.isNotEmpty) {
      _lobs.add(_lobs.removeAt(0));
    }
  }

  void addlob(LOB? newlob, HUD hud) {
    if (hud.gatheringLobs && newlob != null) {
      _lobs.add(newlob);
    }
  }

  void draw(CanvasRenderingContext2D ctx, Player p) {
    const loblength = 10000;  /// arbitrarily long so that the lob appears to be an unending ray

    void drawOne(LOB? lob, String color) {
      if (lob == null) return;

      final endx = lob.source.x + loblength * lob.azimuth.cosresult;
      final endy = lob.source.y + loblength * lob.azimuth.sinresult;

      ctx.beginPath();
      ctx.lineWidth = 2;
      ctx.strokeStyle = color.toJS;

      moveToRel(lob.source.x, lob.source.y, ctx, p.pos);
      lineToRel(endx, endy, ctx, p.pos);
      ctx.stroke();
    }

    if (_lobs.isNotEmpty) {
      for (final lob in _lobs.getRange(0, _lobs.length - 1)) {
        drawOne(lob, "orange");
      }
      if (_selected) {
        drawOne(_lobs.lastOrNull, "red");
      }
    }
  }
}

class Azimuth {
  late final double sinresult;
  late final double cosresult;
  Azimuth.fromPositions(Player p, TxRadio t) {
    final xd = t.pos.x - p.pos.x;
    final yd = t.pos.y - p.pos.y;
    final dist = sqrt(xd * xd + yd * yd);
    sinresult = yd / dist;
    cosresult = xd / dist;
  }
  Azimuth.fromSinCos(this.sinresult, this.cosresult);
}

double logbase10(double x) => log(x) / log(10);

class Power {
  final double mW;
  double get dBm => 10 * logbase10(mW);
  Power({required this.mW});
  Power operator *(double other) {
    return Power(mW: mW * other);
  }
}

/// Simulator. A class that simulates LOBs.
/// Has no local state except a random number generator.
class Sim {
  final _random = Random();

  /// add random noise. Need to figure out whether this is typical distribution
  Azimuth _noi(Azimuth a) {
    p3(double x) => x * x * x;
    return Azimuth.fromSinCos(
      a.sinresult + 0.003 * p3(6 * (_random.nextDouble() - 0.5)),
      a.cosresult + 0.003 * p3(6 * (_random.nextDouble() - 0.5)),
    );
  }

  /// A very rudimentary path loss computation
  Power _distLoss(TxRadio t, Player p1) {
    final xd = t.pos.x - p1.pos.x;
    final yd = t.pos.y - p1.pos.y;
    final dist = sqrt(xd * xd + yd * yd);
    return t.txpower * 0.1 * (1 / sq(dist));
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
      final green = "${random.nextInt(5) + 5}";
      final size = random.nextInt(6) + 2;
      return Bush(
        (random.nextDouble() - 0.5) * 10000,
        (random.nextDouble() - 0.5) * 10000,
        "#$redandblue$green$redandblue",
        size,
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


/// Attaches HTML elements to `root`
void createPageHTML(HTMLElement root, HUD hud, CanvM cmLife, CanvM cmLob) {
  root
    ..appendChild(hud.rootdiv)
    ..appendChild(HTML.div()
      ..style.display = "flex"
      ..style.flexDirection = "row"
      ..appendChild(cmLife.canv)
      ..appendChild(cmLob.canv)
    );
}


void main() async {
  final cmLife = CanvM("#cfc", canvWidth, canvHeight);
  final cmLob = CanvM("#eef", canvWidth, canvHeight);
  final t1 = TxRadio();
  final sim = Sim();
  final oc = ObjCol();
  final lobc = LOBCol();
  final playermut = PlayerMutable(Pos(500, 1050));
  final hud = HUD();

  createPageHTML(document.body!, hud, cmLife, cmLob);

  document.body!.onKeyDown.listen(playermut.addev);
  document.body!.onKeyUp.listen(playermut.addev);
  hud.addEventListeners(document.body!);
  lobc.addEventListeners(cmLob.canv);

  runEachFrame((Duration tdelta) {
    playermut.update(tdelta);
    final p1 = playermut.ro;

    lobc.addlob(sim.simulateLOB(p1, t1), hud);
    hud.update(p1, t1, lobc);
    lobc.update(hud, p1);

    /// LEFT canvas: life
    cmLife.drawBackground();
    t1.draw(cmLife.ctx, p1);
    playermut.draw(cmLife.ctx);
    oc.draw(cmLife.ctx, p1);

    /// RIGHT canvas: lobs
    cmLob.drawBackground();
    cmLob.drawGrid(p1);
    lobc.draw(cmLob.ctx, p1);
    playermut.draw(cmLob.ctx);
  });
}
