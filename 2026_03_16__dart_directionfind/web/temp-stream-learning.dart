/// Beginning to migrate JS code to Dart.
library;

import 'dart:js_interop';
import 'package:web/web.dart';
import 'dart:async';
import 'dart:math';


const canvWidth = 600;
const canvHeight = 400;

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


abstract class Drawable {
  void draw(CanvasRenderingContext2D ctx, Pos center);
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

class Pos {
  final double x;
  final double y;
  Pos(this.x, this.y);
}

typedef KbStm = ElementStream<KeyboardEvent>;
typedef DuStm = Stream<Duration>;

class Player implements Drawable {
  late final Stream<double> _vxStm;
  late final Stream<double> _vyStm;
  late final Stream<double> _xStm;
  late final LatestStreamVal<double> _xnow;
  Pos get pos => Pos(_xnow.val, 370);
  static const speed = 0.2;
  Player(KbStm keydown, KbStm keyup, DuStm tdeltaStm) {
    const initX = 380.0;
    _vxStm = _makeVxStream(0, keydown, keyup).asBroadcastStream();
    _vyStm = _makeVyStream(0, keydown, keyup).asBroadcastStream();
    _xStm = _makeXStream(initX, _vxStm, tdeltaStm).asBroadcastStream();
    _xnow = LatestStreamVal(_xStm, initX);
  }
  
  static Stream<double> _makeXStream(double initX, Stream<double> vxStm, DuStm tdeltaStm) async* {
    var curX = initX;
    var curVx = LatestStreamVal(vxStm, 0);
    await for(final tdelta in tdeltaStm) {
      curX += curVx.val * tdelta.inMilliseconds;
      yield curX;
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
        scy.add(-speed);
      } else if (ev.key == "ArrowUp") {
        scy.add(speed);
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
    final vyEl = HTML.span()..style.color = "yellow";
    final xEl = HTML.span()..style.color = "lightgreen";
    _vyStm.listen((vy) => vyEl.innerText = "vy: $vy ");
    _xStm.listen((x) => xEl.innerText = "x: $x");
    return HTML.div()
      ..appendChild(vyEl)
      ..appendChild(xEl);
  }
  
  @override
  void draw(CanvasRenderingContext2D ctx, Pos _) {
    ctx.fillStyle = "#f00".toJS;
    ctx.fillRect(300, 200, 30, 40);
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

  CanvM(this._bgcolor, int w, int h, Stream<Duration> frameStm, Player p1, List<Drawable> drawItems) {
    _canv
      ..width = w
      ..height = h;
    _ctx = _canv.getContext('2d') as CanvasRenderingContext2D;
    frameStm.listen((Duration tdelta) {
      _drawBackground();
      for (final item in drawItems) {
        item.draw(_ctx, p1.pos);
      }
    });
  }

  void _drawBackground() {
    _ctx.fillStyle = _bgcolor.toJS;
    _ctx.fillRect(0, 0, _canv.width, _canv.height);
  }
  
  HTMLCanvasElement disp() => _canv;
}




Stream<Duration> makeFrameStm() {
  final timeDiffSC = StreamController<Duration>();
  runEachFrame((Duration tdelta) => timeDiffSC.add(tdelta));
  return timeDiffSC.stream.asBroadcastStream();
}


typedef LOB = ({Pos source, Azimuth azimuth, Power rxpow});


class LOBCol {
  List<LOB> _lobs = _lunmo([]);
  final _gatheringLobsCb = HTML.checkbox()..defaultChecked = true;
  static List<T> _lunmo<T>(List<T> ls) => List.unmodifiable(ls);

  LOBCol(KbStm keydown) {
    _lobs = _lunmo([
      (source: Pos(3, 5), azimuth: Azimuth(), rxpow: Power(mW: 3))
    ]); /// TODO: remove this when ready
    print(_lobs);
    keydown
      .where((ev) => ev.key.toLowerCase() == "g")
      .listen((_) => 
        _gatheringLobsCb.checked = !_gatheringLobsCb.checked);
    keydown
      .where((ev) => ev.key.toLowerCase() == "c")
      .listen((_) => _lobs = _lunmo([]));
  }
  HTMLDivElement disp() {
    return HTML.div()
      ..appendChild(HTML.div()
        ..appendChild(HTML.span()..innerText = "Gathering Lobs [ g ]:")
        ..appendChild(_gatheringLobsCb))
      ..appendChild(HTML.button()
        ..innerText = "Clear LOBs [ c ]"
        ..onClick.listen((_) => _lobs = _lunmo([])));
  }
}

class Azimuth {}

double logbase10(double x) => log(x) / log(10);

class Power {
  final double mW;
  double get dBm => 10 * logbase10(mW);
  Power({required this.mW});
  Power operator *(double other) {
    return Power(mW: mW * other);
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
  final lobc = LOBCol(keydown);
  final t1 = TxRadio();
  final cmLife = CanvM("#cfc", canvWidth, canvHeight, frameStm, p1, [p1, t1]);
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
