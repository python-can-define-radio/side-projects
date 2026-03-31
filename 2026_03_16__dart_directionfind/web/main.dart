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


class LatestStreamVal<T> {
  T _val;
  T get val => _val;
  LatestStreamVal(Stream<T> stream, this._val) {
    stream.listen((x) => _val = x);
  }
}


typedef KbStm = ElementStream<KeyboardEvent>;
typedef DuStm = Stream<Duration>;

class Player implements Drawable {
  late final Stream<Pos> posStm;
  late final LatestStreamVal<Pos> _pos;
  Pos get pos => _pos.val;
  static const speed = 0.2;
  Player(KbStm keydown, KbStm keyup, DuStm tdeltaStm) {
    final initPos = Pos(380.0, 400.0);
    final vxStm = _makeVxStream(0, keydown, keyup);
    final vyStm = _makeVyStream(0, keydown, keyup);
    final xStm = _makeXStream(initPos.x, vxStm, tdeltaStm);
    final yStm = _makeYStream(initPos.y, vyStm, tdeltaStm);
    posStm = StreamZip<double>([xStm, yStm])
      .map((xy) => Pos(xy[0], xy[1]))
      .asBroadcastStream();
    _pos = LatestStreamVal(posStm, initPos);
  }

  static Stream<double> _makeXStream(double initX, Stream<double> vxStm, DuStm tdeltaStm) async* {
    var curX = initX;
    final curVx = LatestStreamVal(vxStm, 0);
    await for(final tdelta in tdeltaStm) {
      curX += curVx.val * tdelta.inMilliseconds;
      yield curX;
    }
  }

  static Stream<double> _makeYStream(double initY, Stream<double> vyStm, DuStm tdeltaStm) async* {
    var curY = initY;
    var curVy = LatestStreamVal(vyStm, 0);
    await for(final tdelta in tdeltaStm) {
      curY += curVy.val * tdelta.inMilliseconds;
      yield curY;
    }
  }
  
  static Stream<double> _makeVxStream(double initVx, KbStm keydown, KbStm keyup) {
    final scx = StreamController<double>()..add(initVx);
    keydown.listen((ev) {
      if (ev.key == "ArrowLeft") {
        scx.add(-speed);
      } else if (ev.key == "ArrowRight") {
        scx.add(speed);
      }
    });
    keyup.listen((ev) {
      if (["ArrowLeft", "ArrowRight"].contains(ev.key)) {
        scx.add(0);
      }
    });
    return scx.stream;
  }
  
  static Stream<double> _makeVyStream(double initVy, KbStm keydown, KbStm keyup) {
    final scy = StreamController<double>()..add(initVy);
    keydown.listen((ev) {
      if (ev.key == "ArrowDown") {
        scy.add(speed);
      } else if (ev.key == "ArrowUp") {
        scy.add(-speed);
      }
    });
    keyup.listen((ev) {
      if (["ArrowDown", "ArrowUp"].contains(ev.key)) {
        scy.add(0);
      }
    });
    return scy.stream;
  }
  
  HTMLDivElement disp() {
    final posEl = HTML.span()..style.color = "lightgreen";
    posStm.listen((pos) => posEl.innerText = "pos: ${pos.x.toStringAsFixed(2)} ${pos.y.toStringAsFixed(2)}");
    return HTML.div()..appendChild(posEl);
  }
  
  @override
  void draw(CanvasRenderingContext2D ctx, Pos _) {
    const sz = 2;
    const cenx = canvWidth / 2;
    const ceny = canvHeight / 2;
    ctx.fillStyle = "#000".toJS;
    fillCircle(cenx + sz, ceny - sz * 3, sz * 3, ctx); /// head
    ctx.fillRect(cenx - sz * 1, ceny - sz * 2, sz * 4, sz * 12); /// torso
    ctx.fillRect(cenx - sz * 4, ceny + sz * 2, sz * 10, sz); /// arms
    ctx.fillRect(cenx - sz * 1, ceny + sz * 10, sz * 1.5, sz * 5); /// leg
    ctx.fillRect(cenx + sz * 1, ceny + sz * 10, sz * 1.5, sz * 5); /// leg
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
  final String _bgcolor;
  final _canv = HTML.canvas();
  late final CanvasRenderingContext2D _ctx;

  CanvM(this._bgcolor, int w, int h, Stream<Pos> posStm, List<Drawable> drawItems) {
    _canv
      ..width = w
      ..height = h;
    _ctx = _canv.getContext('2d') as CanvasRenderingContext2D;
    posStm.listen((pos) => _frameUpdate(pos, drawItems));
  }

  void _frameUpdate(Pos pos, List<Drawable> drawItems) {
    _drawBackground();
    for (final item in drawItems) {
      item.draw(_ctx, pos);
    }
  }

  void _drawBackground() {
    _ctx.fillStyle = _bgcolor.toJS;
    _ctx.fillRect(0, 0, _canv.width, _canv.height);
  }
  HTMLCanvasElement disp() => _canv;
}

class TxRadio implements Drawable {
  final pos = Pos(400, 370);
  final txpower = Power(mW: 100);
  
  @override
  void draw(CanvasRenderingContext2D ctx, Pos center) {
    ctx.fillStyle = "#00f".toJS;
    fillRectRel(pos.x, pos.y, 10, 10, ctx, center);
  }
}


Stream<Duration> makeFrameStm() {
  final timeDiffSC = StreamController<Duration>();
  runEachFrame((Duration tdelta) => timeDiffSC.add(tdelta));
  return timeDiffSC.stream.asBroadcastStream();
}


typedef LOB = ({Pos source, Azimuth azimuth, Power rxpow});


class LOBCol implements Drawable {
  List<LOB> _lobs = _lunmo([]);
  final _gatheringLobsCb = HTML.checkbox()..defaultChecked = true;
  late final Stream<LOB> _gathLobStm;
  /// Make an unmodifiable list
  static List<T> _lunmo<T>(List<T> ls) => List.unmodifiable(ls);

  LOBCol(KbStm keydown, Stream<LOB> lobStm) {
    keydown
      .where((ev) => ev.key.toLowerCase() == "g")
      .listen((_) => 
        _gatheringLobsCb.checked = !_gatheringLobsCb.checked);
    keydown
      .where((ev) => ev.key.toLowerCase() == "c")
      .listen((_) => _lobs = _lunmo([]));
    _gathLobStm = lobStm.where((_) => _gatheringLobsCb.checked).asBroadcastStream();
    _gathLobStm.listen((lob) => _lobs = _lunmo(_lobs + [lob]));
  }
    
  static String _fmtpow(LOB lob) =>
    "Most recent LOB power: ${lob.rxpow.dBm.toStringAsFixed(1)} dBm\n";

  HTMLDivElement disp() {
    final lobPowEl = HTML.div();
    _gathLobStm.listen((lob) => lobPowEl.innerText = _fmtpow(lob));
    return HTML.div()
      ..appendChild(HTML.div()
        ..appendChild(HTML.span()..innerText = "Gathering Lobs [ g ]:")
        ..appendChild(_gatheringLobsCb))
      ..appendChild(HTML.button()
        ..innerText = "Clear LOBs [ c ]"
        ..onClick.listen((_) => _lobs = _lunmo([])))
      ..appendChild(lobPowEl);
  }

  @override
  void draw(CanvasRenderingContext2D ctx, Pos center) {
    void drawOne(LOB lob, String color) {
      const loblength = 10000;  /// arbitrarily long so that the lob appears to be an unending ray
      final endx = lob.source.x + loblength * lob.azimuth.cosresult;
      final endy = lob.source.y + loblength * lob.azimuth.sinresult;
      ctx.beginPath();
      ctx.lineWidth = 2;
      ctx.strokeStyle = color.toJS;
      moveToRel(lob.source.x, lob.source.y, ctx, center);
      lineToRel(endx, endy, ctx, center);
      ctx.stroke();
    }
    if (_lobs.isNotEmpty) {
      final [...beginning, lastlob] = _lobs;
      beginning.forEach((lob) => drawOne(lob, "orange"));
      drawOne(lastlob, "red"); // eventually this will be the selected lob; currently it's just the last.
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
  late final Stream<LOB> lobStm;
  Sim(Player p1, TxRadio t1) {
    lobStm = 
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


void attachElems(HTMLElement root, Player p1, LOBCol lobc, CanvM cmLife){
  root
    ..appendChild(p1.disp())
    ..appendChild(lobc.disp())
    ..appendChild(cmLife.disp());
}


void main() {
  final keydown = document.body!.onKeyDown;
  final keyup = document.body!.onKeyUp;
  final frameStm = makeFrameStm();
  final p1 = Player(keydown, keyup, frameStm);
  final t1 = TxRadio();
  final sim = Sim(p1, t1);
  final lobc = LOBCol(keydown, sim.lobStm);
  final cmLife = CanvM("#cfc", canvWidth, canvHeight, p1.posStm, [p1, t1, lobc]);
  attachElems(document.body!, p1, lobc, cmLife); 
}



/*
Stream<int> timedCounter(Duration interval) async* {
  int i = 0;
  while (true) {
    yield i;
    i += 1;
    await Future.delayed(interval);
  }
}
//   timedCounter(Duration(seconds: 1))
//     .doubleEach()
//     .listen((val) => p.innerText = "count is $val");
*/


/*
extension Doubler on Stream<int> {
  Stream<int> doubleEach() async* {
    await for(final val in this) {
      yield val * 2;
    }
  }
}
*/

/*
extension Counter<T> on Stream<T> {
  Stream<int> count({int init = 0}) async* {
    int i = init;
    await for(final _ in this) {
      yield i;
      i += 1;
    }
  }
}
*/
