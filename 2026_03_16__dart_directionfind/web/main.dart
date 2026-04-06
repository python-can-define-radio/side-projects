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
class StreamLV<T> {
  T _latestVal;
  T get latestVal => _latestVal;
  final Stream<T> stream;
  StreamLV(this._latestVal, this.stream) {
    stream.listen((val) => _latestVal = val);
  }
  StreamSubscription<T> listen(void Function(T) onData) => stream.listen(onData);
}


typedef KbStm = ElementStream<KeyboardEvent>;
typedef DuStm = Stream<Duration>;

enum DirUD { up, down, neutral }
enum DirLR { left, right, neutral }


class Player {
  late final StreamLV<Pos> posStmLV;
  Pos get pos => posStmLV.latestVal;

  Player(KbStm keydown, KbStm keyup, DuStm tdeltaStm) {
    final initPos = Pos(380.0, 400.0);
    final speedStm = _speedStream(0.2, keydown, keyup);
    final vxStmLV = _makeVxStream(keydown, keyup);
    final vyStmLV = _makeVyStream(keydown, keyup);
    final xStm = _makeXStream(initPos.x, vxStmLV, tdeltaStm, speedStm);
    final yStm = _makeYStream(initPos.y, vyStmLV, tdeltaStm, speedStm);
    final posStm = StreamZip<double>([xStm, yStm])
      .map((xy) => Pos(xy[0], xy[1]))
      .asBroadcastStream();
    posStmLV = StreamLV(initPos, posStm);
  }

  static double udconv(DirUD d) => switch(d) { .up => -1, .down => 1, .neutral => 0 };
  static double lrconv(DirLR d) => switch(d) { .left => -1, .right => 1, .neutral => 0 };

  static Stream<double> _makeXStream(double initX, StreamLV<DirLR> vxStm, DuStm tdeltaStm, StreamLV<double> speedStm) async* {
    var curX = initX;
    await for(final tdelta in tdeltaStm) {
      curX += lrconv(vxStm.latestVal) * speedStm.latestVal * tdelta.inMilliseconds;
      yield curX;
    }
  }

  static Stream<double> _makeYStream(double initY, StreamLV<DirUD> vyStm, DuStm tdeltaStm, StreamLV<double> speedStm) async* {
    var curY = initY;
    await for(final tdelta in tdeltaStm) {
      curY += udconv(vyStm.latestVal) * speedStm.latestVal * tdelta.inMilliseconds;
      yield curY;
    }
  }
  
  static StreamLV<DirLR> _makeVxStream(KbStm keydown, KbStm keyup) {
    final scx = StreamController<DirLR>()..add(DirLR.neutral);
    keydown.listen((ev) {
      if (ev.key == "ArrowLeft") {
        scx.add(DirLR.left);
      } else if (ev.key == "ArrowRight") {
        scx.add(DirLR.right);
      }
    });
    keyup.listen((ev) {
      if (["ArrowLeft", "ArrowRight"].contains(ev.key)) {
        scx.add(DirLR.neutral);
      }
    });
    return StreamLV(DirLR.neutral, scx.stream);
  }
  
  static StreamLV<DirUD> _makeVyStream(KbStm keydown, KbStm keyup) {
    final scy = StreamController<DirUD>()..add(DirUD.neutral);
    keydown.listen((ev) {
      if (ev.key == "ArrowDown") {
        scy.add(DirUD.down);
      } else if (ev.key == "ArrowUp") {
        scy.add(DirUD.up);
      }
    });
    keyup.listen((ev) {
      if (["ArrowDown", "ArrowUp"].contains(ev.key)) {
        scy.add(DirUD.neutral);
      }
    });
    return StreamLV(DirUD.neutral, scy.stream);
  }

  static StreamLV<double> _speedStream(double initSpeed, KbStm keydown, KbStm keyup) {
    final speed = StreamController<double>()..add(initSpeed);
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
    return StreamLV(initSpeed, speed.stream);
  }
}

class PlayerHUD {
  final StreamLV<Pos> _posStmLV;
  PlayerHUD(this._posStmLV);
  HTMLDivElement disp() {
    final posEl = HTML.span();
    _posStmLV.listen((pos) => posEl.innerText = "pos: ${pos.x.toStringAsFixed(2)} ${pos.y.toStringAsFixed(2)}");
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
  final ImmuList<Drawable> _drawItems;

  CanvM(String cssid, int w, int h, StreamLV<Pos> posStmLV, List<Drawable> drawItems)
      : _drawItems = ImmuList(drawItems) {
    _canv
      ..width = w
      ..height = h
      ..id = cssid;
    _ctx = _canv.getContext('2d') as CanvasRenderingContext2D;
    posStmLV.listen((pos) => _frameUpdate(pos));
  }

  HTMLCanvasElement disp() => _canv;

  void _frameUpdate(Pos pos) {
    _ctx.clearRect(0, 0, _canv.width, _canv.height);
    _ctx.save();
    for (final item in _drawItems.values) {
      item.draw(_ctx, pos);
    }
    _ctx.restore();
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
  late final StreamLV<ImmuList<LOB>> _gathLobStmLV;

  LOBCol(KbStm keydown, Stream<LOB> univLobStm) {
    keydown
      .where((ev) => ev.key.toLowerCase() == "g")
      .listen((_) => _gatheringLobsCb.checked = !_gatheringLobsCb.checked);

    final cStm = keydown.where((ev) => ev.key.toLowerCase() == "c").asBroadcastStream();
    buttonAesthetic(cStm, _clearBtn);

    final Stream<Object> clearStm = StreamGroup.merge([cStm, _clearBtn.onClick]);
    final gathLobStm = makeGathLobStream(
      clearStm,
      univLobStm.where((_) => _gatheringLobsCb.checked)
    );
    _gathLobStmLV = StreamLV(ImmuList([]), gathLobStm);
  }

  static void buttonAesthetic(Stream<Event> cStm, HTMLElement btn) {
    cStm.listen((_) {
      btn.classList.add("button-active");
      Future.delayed(Duration(milliseconds: 100), () => btn.classList.remove("button-active"));
    });
  }

  static Stream<ImmuList<LOB>> makeGathLobStream(Stream<Object> clearStm, Stream<LOB> filteredLobsStm)  {
    final sc = StreamController<ImmuList<LOB>>();
    final curLobList = <LOB>[];
    filteredLobsStm.listen((lob) {
      curLobList.add(lob); 
      sc.add(ImmuList(curLobList));
    });
    clearStm.listen((_) {
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
    _gathLobStmLV.listen((lobs) => lobPowEl.innerText = _fmtpow(lobs.values.lastOrNull));
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
    final lobs = _gathLobStmLV.latestVal.values;

    void drawOne(LOB lob, String color) {
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

    if (lobs.isNotEmpty) {
      final [...beginning, lastlob] = lobs;
      for (final lob in beginning) {drawOne(lob, "orange");}
      drawOne(lastlob, "red");
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
class Sim {
  final _random = Random();
  /// LOBs coming from the universe (as opposed to those which we have gathered)
  late final Stream<LOB> univLobStm;
  Sim(Player p1, TxRadio t1) {
    univLobStm = 
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
  final p1 = Player(keydown, keyup, frameStm);
  final ph = PlayerHUD(p1.posStmLV);
  final t1 = TxRadio();
  final sim = Sim(p1, t1);
  final lobc = LOBCol(keydown, sim.univLobStm);
  final bushes = ObjCol();
  final grid = Grid();
  final avatarlife = Avatar("#000");
  final avatarhud = Avatar("#fff");
  final cmLife = CanvM("life", canvWidth, canvHeight, p1.posStmLV, [avatarlife, bushes, t1],);
  final cmLob = CanvM("hud", canvWidth, canvHeight, p1.posStmLV, [avatarhud, lobc, grid],);
  attachElems(document.body!, ph, lobc, cmLife, cmLob); 
}
