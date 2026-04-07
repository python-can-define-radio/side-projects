/// Beginning to migrate JS code to Dart.
library;

import 'dart:js_interop';
import 'package:web/web.dart';
import 'dart:async';
import 'dart:math';
import 'package:async/async.dart';


const canvWidth = 600;
const canvHeight = 400;

num sq(num x) => x * x;

/// Returns a sublist including all items except the last item.
/// If `orig` is empty, return it.
List<T> withoutLast<T>(List<T> orig) =>
  orig.isEmpty ? orig : orig.getRange(0, orig.length - 1).toList();


extension FunctionPipe<T extends Object> on T {
  /// Source: https://github.com/dart-lang/language/issues/1246
  R then<R>(R Function (T) f) => f(this);
}


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

  /// Return number with 70000 added to look more like a grid coordinate
  String _padbig(double u) => (u + 70000).toInt().toString();
  String get pretty => "${_padbig(x)}, ${_padbig(y)}";
}


abstract class Drawable {
  void draw(CanvasRenderingContext2D ctx, Pos center);
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


extension Scanner<T> on Stream<T> {
  Stream<S> scan<S>(S initial, S Function(S, T) combine) async* {
    S prevIteration = initial;
    yield prevIteration;
    await for(final current in this) {
      prevIteration = combine(prevIteration, current);
      yield prevIteration;
    }
  }
}


/// A wrapped stream that keeps a record of the most recent stream value.
class Observable<T> {
  T _latestVal;
  T get latestVal => _latestVal;
  Observable(this._latestVal, Stream<T> stream) {
    stream.listen((val) => _latestVal = val);
  }
}


typedef KbStm = ElementStream<KeyboardEvent>;
typedef DuStm = Stream<Duration>;


class Player {
  final Stream<Pos> posStm;
  late final Observable<Pos> _posObs;
  Pos get pos => _posObs.latestVal;

  Player(Pos initPos, KbStm keydown, KbStm keyup, DuStm tdelta) :
    posStm = _makePosStm(initPos, keydown, keyup, tdelta) {
      _posObs = Observable(initPos, posStm);  
    }
    
  static Stream<Pos> _makePosStm(Pos initPos, KbStm keydown, KbStm keyup, DuStm tdelta) {
    
    final speed = _makeSpeed(0.2, keydown, keyup);
    final dirx = _makeDirx(keydown, keyup);
    final diry = _makeDiry(keydown, keyup);
    final x = _makeX(initPos.x, dirx, tdelta, speed);
    final y = _makeY(initPos.y, diry, tdelta, speed);
    return StreamZip<double>([x, y])
      .map((xypair) => Pos(xypair[0], xypair[1]))
      .asBroadcastStream();
  }

  static Stream<double> _makeX(double initX, Observable<double> dirx, DuStm tdelta, Observable<double> speed) async* {
    var curX = initX;
    await for(final tdeltaVal in tdelta) {
      curX += dirx.latestVal * speed.latestVal * tdeltaVal.inMilliseconds;
      yield curX;
    }
  }

  static Stream<double> _makeY(double initY, Observable<double> diry, DuStm tdelta, Observable<double> speed) async* {
    var curY = initY;
    await for(final tdeltaVal in tdelta) {
      curY += diry.latestVal * speed.latestVal * tdeltaVal.inMilliseconds;
      yield curY;
    }
  }
  
  static Observable<double> _makeDirx(KbStm keydown, KbStm keyup) {
    final sc = StreamController<double>();
    keydown.listen((ev) {
      if (ev.key == "ArrowLeft") {
        sc.add(-1);
      } else if (ev.key == "ArrowRight") {
        sc.add(1);
      }
    });
    keyup.listen((ev) {
      if (["ArrowLeft", "ArrowRight"].contains(ev.key)) {
        sc.add(0);
      }
    });
    return Observable(0, sc.stream);
  }
  
  static Observable<double> _makeDiry(KbStm keydown, KbStm keyup) {
    final sc = StreamController<double>();
    keydown.listen((ev) {
      if (ev.key == "ArrowDown") {
        sc.add(1);
      } else if (ev.key == "ArrowUp") {
        sc.add(-1);
      }
    });
    keyup.listen((ev) {
      if (["ArrowDown", "ArrowUp"].contains(ev.key)) {
        sc.add(0);
      }
    });
    return Observable(0, sc.stream);
  }

  static Observable<double> _makeSpeed(double initSpeed, KbStm keydown, KbStm keyup) {
    final speed = StreamController<double>();
    keydown.listen((ev) {
      if (ev.key == "Shift") {
        speed.add(2*initSpeed);
      }
    });
    keyup.listen((ev) {
      if (ev.key == "Shift") {
        speed.add(initSpeed);
      }
    });
    return Observable(initSpeed, speed.stream);
  }
}

class PlayerHUD {
  final Stream<Pos> _posStm;
  PlayerHUD(this._posStm);
  HTMLDivElement disp() {
    final posEl = HTML.span();
    _posStm.listen((pos) => posEl.innerText = "pos: ${pos.pretty}");
    return HTML.div()..appendChild(posEl);
  }
}

class Avatar implements Drawable {
  final String color; 
  Avatar(this.color); 

  @override
  void draw(CanvasRenderingContext2D ctx, Pos center) {
    const sz = 2;
    const cenx = canvWidth / 2;
    const ceny = canvHeight / 2;
    ctx.fillStyle = color.toJS;
    fillCircle(cenx + sz, ceny - sz * 3, sz * 3, ctx);
    ctx.fillRect(cenx - sz * 1, ceny - sz * 2, sz * 4, sz * 12);
    ctx.fillRect(cenx - sz * 4, ceny + sz * 2, sz * 10, sz);
    ctx.fillRect(cenx - sz * 1, ceny + sz * 10, sz * 1.5, sz * 5);
    ctx.fillRect(cenx + sz * 1, ceny + sz * 10, sz * 1.5, sz * 5);
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


class CanvM {
  final HTMLCanvasElement _canv = HTML.canvas();
  late final CanvasRenderingContext2D _ctx;
  late final ImmuList<Drawable> _drawItems;
  late final Stream<MouseEvent> click = _canv.onClick;

  CanvM(String cssid, int w, int h) {
    _canv
      ..width = w
      ..height = h
      ..id = cssid;
    _ctx = _canv.getContext('2d') as CanvasRenderingContext2D;
  }
  
  /// Basically 'constructor part two'. Had to separate to avoid
  /// a circular dependency.
  void config(Stream<Pos> posStm, List<Drawable> drawItems) {
    _drawItems = ImmuList(drawItems);
    posStm.listen(_frameUpdate);
  }
  
  HTMLCanvasElement disp() => _canv;

  void _frameUpdate(Pos pos) {
    _ctx.clearRect(0, 0, _canv.width, _canv.height);
    for (final item in _drawItems.values) {
      item.draw(_ctx, pos);
    }
  }
}

class Grid implements Drawable {
  @override
  void draw(CanvasRenderingContext2D ctx, Pos center) {
    const gridSpacing = 50;

    ctx.strokeStyle = "#ccc".toJS;
    ctx.lineWidth = 0.5;

    final px = center.x;
    final py = center.y;

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
  }
}


class TxRadio implements Drawable {
  final pos = Pos(400, 370);
  final txpower = Power(mW: 100);
  
  @override
  void draw(CanvasRenderingContext2D ctx, Pos center) {
    ctx.fillStyle = "#00f".toJS;
    fillRectRel(pos.x - 5, pos.y - 5, 10, 10, ctx, center);
  }
}


Stream<Duration> makeFrameStm() {
  final timeDiffSC = StreamController<Duration>();
  runEachFrame((Duration tdelta) => timeDiffSC.add(tdelta));
  return timeDiffSC.stream.asBroadcastStream();
}


class Bush implements Drawable {
  final Pos _pos;
  final String _color;
  final int _size;
  Bush(double x, double y, this._color, this._size)
  : _pos = Pos(x, y);
  

  @override
  void draw(CanvasRenderingContext2D ctx, Pos center) {
    final xd = _pos.x - center.x;
    final yd = _pos.y - center.y;
    
    if (yd.abs() > (0.7 * canvHeight) || xd.abs() > (0.7 * canvWidth)) {
      return;
    }
    ctx.fillStyle = "#440".toJS;
    fillRectRel(
      _pos.x - _size,
      _pos.y + _size * 0.7,
      _size * 0.9,
      6,
      ctx,
      center,
    );
    fillRectRel(_pos.x, _pos.y + _size * 0.7, _size * 0.9, 6, ctx, center);
    fillRectRel(
      _pos.x + _size * 0.7,
      _pos.y + _size * 0.7,
      _size * 0.9,
      6,
      ctx,
      center,
    );
    ctx.fillStyle = _color.toJS;
    fillCircleRel(_pos.x - _size, _pos.y, _size, ctx, center);
    fillCircleRel(_pos.x, _pos.y, _size, ctx, center);
    fillCircleRel(_pos.x, _pos.y - _size, _size, ctx, center);
    fillCircleRel(_pos.x + _size, _pos.y, _size, ctx, center);
    fillCircleRel(_pos.x, _pos.y - _size, _size, ctx, center);
    fillCircleRel(_pos.x + 2 * _size, _pos.y, _size, ctx, center);
    fillCircleRel(_pos.x + 1.5 * _size, _pos.y - _size, _size, ctx, center);
  }
}

typedef LOB = ({Pos source, Azimuth azimuth, Power rxpow});

class ImmuList<T> {
  /// wrapped list
  final List<T> _wrlist;
  /// I don't know how to make a shallow copy in Dart
  List<T> get values => _wrlist.map((x) => x).toList();
  ImmuList(List<T> vals) : _wrlist = vals.map((x) => x).toList();
}

class LOBCol implements Drawable {
  final HTMLInputElement _gatheringLobsCb = HTML.checkbox()..defaultChecked = true;
  final HTMLButtonElement _clearBtn = HTML.button()
    ..id = "clear-btn"
    ..innerText = "Clear LOBs [ c ]";
  late final Stream<ImmuList<LOB>> _lobsStm;
  late final Observable<ImmuList<LOB>> _lobs;
  /// Selected LOB
  late final Observable<LOB?> _sellob;

  LOBCol(KbStm keydown, Stream<LOB> univLobs, Stream<MouseEvent> canvclick, Player p1) {
    _configGKey(keydown, _gatheringLobsCb);
    final clear = _configClearing(keydown, _clearBtn);
    final filtlobs = univLobs.where((_) => _gatheringLobsCb.checked);
    _lobsStm = _makeLobStream(clear, filtlobs);
    _lobs = Observable(ImmuList([]), _lobsStm);
    _sellob = _configChosenLOB(_lobs, canvclick, p1);
  }

  static Observable<LOB?> _configChosenLOB(Observable<ImmuList<LOB>> lobs, Stream<MouseEvent> canvclick, Player p1) {
    final sc = StreamController<LOB?>();
    canvclick.listen((ev) { 
       sc.add(decideClosest(lobs.latestVal, p1.pos, ev));
    });
    return Observable(null, sc.stream);
  }
  
  static LOB? decideClosest(ImmuList<LOB> immulobs, Pos p1pos, MouseEvent ev) {
    final lobs = immulobs.values;
    final shiftx = p1pos.x + ev.offsetX - canvWidth / 2;
    final shifty = p1pos.y + ev.offsetY - canvHeight / 2;
    num dist(LOB lob) {
      final dx = (lob.source.x - shiftx).abs();
      final dy = (lob.source.y - shifty).abs();
      return dx + dy;
    }
    lobs.sort((a, b) => dist(a).compareTo(dist(b)));
    final near = lobs.where((lob) => dist(lob) < 40);
    return near.firstOrNull;
  }
  
  static void _configGKey(KbStm keydown, HTMLInputElement gatheringLobsCb) {
    keydown
      .where((ev) => ev.key.toLowerCase() == "g")
      .listen((_) => gatheringLobsCb.checked = !gatheringLobsCb.checked);
  }
  
  static Stream<Event> _configClearing(KbStm keydown, HTMLButtonElement clearBtn) {
    final cDown = keydown.where((ev) => ev.key.toLowerCase() == "c").asBroadcastStream();
    _buttonAesthetic(cDown, clearBtn);
    return StreamGroup.merge([cDown, clearBtn.onClick]);
  }

  static void _buttonAesthetic(Stream<Event> cDown, HTMLElement btn) {
    cDown.listen((_) {
      btn.classList.add("button-active");
      Future.delayed(Duration(milliseconds: 100), () => btn.classList.remove("button-active"));
    });
  }

  /// Makes a stream of the lobs saved on the simulated DFing equipment,
  /// not to be confused with the stream of lobs coming from the universe.
  static Stream<ImmuList<LOB>> _makeLobStream(Stream<Object> clear, Stream<LOB> filtlobs)  {
    final sc = StreamController<ImmuList<LOB>>();
    final curLobList = <LOB>[];
    filtlobs.listen((lob) {
      curLobList.add(lob); 
      sc.add(ImmuList(curLobList));
    });
    clear.listen((_) {
      curLobList.clear();
      sc.add(ImmuList(curLobList));
    });
    return sc.stream.asBroadcastStream();
  }

  static String _fmtpow(LOB? lob) {
    final fm = lob?.rxpow.dBm.toStringAsFixed(1);
    return "LOB power: ${fm ?? "__"} dBm\n";
  }

  HTMLDivElement dispInfo() {
    final lobPowEl = HTML.div();
    _lobsStm.listen((lobs) => lobPowEl.innerText = _fmtpow(lobs.values.lastOrNull));
    return lobPowEl;
  }

  HTMLDivElement dispCtl() {
  return HTML.div()
    ..style.display = "flex"
    ..style.flexDirection = "column"
    ..style.alignItems = "right"
    ..appendChild(_clearBtn)
    ..appendChild(HTML.div()
      ..appendChild(HTML.span()..innerText = "Gathering LOBs [ g ]: ")
      ..appendChild(_gatheringLobsCb)
    );
}

  @override
  void draw(CanvasRenderingContext2D ctx, Pos center) {
    final lobs = _lobs.latestVal.values;

    void drawOne(LOB lob, {String color = "orange"}) {
      const loblength = 10000;
      final endx = lob.source.x + loblength * lob.azimuth.cosresult;
      final endy = lob.source.y + loblength * lob.azimuth.sinresult;
      ctx.beginPath();
      ctx.lineWidth = 2;
      ctx.strokeStyle = color.toJS;
      moveToRel(lob.source.x, lob.source.y, ctx, center);
      lineToRel(endx, endy, ctx, center);
      ctx.stroke();
    }

    for (final lob in withoutLast(lobs)) {
      drawOne(lob);
    }
    lobs.lastOrNull?.then((lob) => drawOne(lob, color: "red"));
    _sellob.latestVal?.then((lob) => drawOne(lob, color: "blue"));
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
class Sim {
  final _random = Random();
  /// LOBs coming from the universe (as opposed to those which we have gathered)
  late final Stream<LOB> univLobs;
  Sim(Player p1, TxRadio t1) {
    univLobs = 
      Stream<Null>.periodic(Duration(milliseconds: 50))
        .where((_) => _random.nextInt(5) == 0)
        .map((_) => _makelob(p1, t1))
        .asBroadcastStream();
  }

  LOB _makelob(Player p1, TxRadio t1) => (
    source: p1.pos,
    azimuth: _noi(Azimuth.fromPositions(p1, t1)),
    rxpow: _distLoss(t1, p1),
  );

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
    return t.txpower * 0.1 * (1 / sq(dist)) * (_random.nextDouble() * 0.1 + 0.9);
  }
}

void attachElems(HTMLElement root, PlayerHUD ph, LOBCol lobc, CanvM cmLife, CanvM cmLob){
  root
    ..style.display = "flex"
    ..style.flexDirection = "column"
    ..style.alignItems = "center"
    ..appendChild(HTML.div()
      ..style.display = "flex"
      ..style.flexDirection = "row"
      ..style.gap = "16px"
      ..appendChild(cmLife.disp())
      ..appendChild(HTML.div()
        ..style.position = "relative"
        ..appendChild(cmLob.disp())
        ..appendChild(ph.disp()
          ..style.position = "absolute"
          ..style.top = "20px"
          ..style.left = "25px"
          ..style.color = "lightgreen"
          ..style.fontFamily = "monospace"
        )
        ..appendChild(lobc.dispInfo()
          ..style.position = "absolute"
          ..style.top = "35px"
          ..style.left = "25px"
          ..style.color = "lightgreen"
          ..style.fontFamily = "monospace"
        )
        ..appendChild(lobc.dispCtl()
          ..style.position = "absolute"
          ..style.top = "20px"
          ..style.right = "20px"
          ..style.color = "lightgreen"
          ..style.fontFamily = "monospace"
        )
      )
    );
}

class ObjCol implements Drawable {
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

    _objs = List.unmodifiable([for (var i = 0; i < 10000; i++) makebush()]);
  }

  @override
  void draw(CanvasRenderingContext2D ctx, Pos center) {
    for (final obj in _objs) {
      obj.draw(ctx, center);
    }
  }
}

void main() {
  final keydown = document.body!.onKeyDown;
  final keyup = document.body!.onKeyUp;
  final frameStm = makeFrameStm();
  final p1 = Player(Pos(380.0, 400.0), keydown, keyup, frameStm);
  final ph = PlayerHUD(p1.posStm);
  final t1 = TxRadio();
  final sim = Sim(p1, t1);
  final bushes = ObjCol();
  final grid = Grid();
  final avatarlife = Avatar("#000");
  final avatarhud = Avatar("#fff");
  final cmLife = CanvM("life", canvWidth, canvHeight);
  final cmLob = CanvM("hud", canvWidth, canvHeight);
  final lobc = LOBCol(keydown, sim.univLobs, cmLob.click, p1);
  cmLife.config(p1.posStm, [avatarlife, bushes, t1]);
  cmLob.config(p1.posStm, [avatarhud, lobc, grid]);
  attachElems(document.body!, ph, lobc, cmLife, cmLob); 
}


/*

Next steps as of 2026 march 25
- incorporate hud boxes into the lob view possibly add some kind of reticule?
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
