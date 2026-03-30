/// Beginning to migrate JS code to Dart.
library;

import 'dart:js_interop';
import 'package:web/web.dart';
import 'dart:async';


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


class Pos {
  final double x;
  final double y;
  Pos(this.x, this.y);
}

typedef KbStm = ElementStream<KeyboardEvent>;
typedef DuStm = Stream<Duration>;

class Player {
  late final Stream<double> vxStm;
  late final Stream<double> vyStm;
  late final Stream<double> xStm;
  static const speed = 0.2;
  Player(KbStm keydown, KbStm keyup, DuStm tdeltaStm) {
    vxStm = _makeVxStream(0, keydown, keyup);
    vyStm = _makeVyStream(0, keydown, keyup);
    xStm = _makeXStream(0, vxStm, tdeltaStm);
  }
  
  static Stream<double> _makeXStream(double initX, Stream<double> vxStm, DuStm tdeltaStm) async* {
    yield initX;
    var curX = initX;
    double curVx = 0;
    vxStm.listen((vx) => curVx = vx);
    await for(final tdelta in tdeltaStm) {
      curX += curVx * tdelta.inMilliseconds;
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
    vyStm.listen((vy) => vyEl.innerText = "vy: $vy ");
    xStm.listen((x) => xEl.innerText = "x: $x");
    return HTML.div()
      ..appendChild(vyEl)
      ..appendChild(xEl);
  }
}

void attachElems(HTMLElement root, Player p1, LOBCol lobc){
  root
    ..appendChild(p1.disp())
    ..appendChild(lobc.disp());
}

Stream<Duration> makeFrameStm() {
  final timeDiffSC = StreamController<Duration>();
  runEachFrame((Duration tdelta) => timeDiffSC.add(tdelta));
  return timeDiffSC.stream;
}

class LOBCol {
  late final List<double> _lobs = [];

  HTMLDivElement disp() {
    final clearBtn = HTML.button()
      ..innerText = "Clear Lobs"
      ..onClick.listen((_) => _lobs.clear());
    return HTML.div()
      ..appendChild(clearBtn);
  }
}

void main() {
  final keydown = document.body!.onKeyDown;
  final keyup = document.body!.onKeyUp;
  final frameStm = makeFrameStm();
  final p1 = Player(keydown, keyup, frameStm);
  final lobc = LOBCol();
  attachElems(document.body!, p1, lobc);
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
