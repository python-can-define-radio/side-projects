import 'dart:async';
import 'package:web/web.dart';

HTMLParagraphElement htmlp() => document.createElement('p') as HTMLParagraphElement;
HTMLDivElement htmldiv() => document.createElement('div') as HTMLDivElement;
HTMLButtonElement htmlbutton() => document.createElement('button') as HTMLButtonElement;


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




extension Doubler on Stream<int> {
  Stream<int> doubleEach() async* {
    await for(final val in this) {
      yield val * 2;
    }
  }
}

extension Counter<T> on Stream<T> {
  Stream<int> count({int init = 0}) async* {
    int i = init;
    await for(final _ in this) {
      yield i;
      i += 1;
    }
  }
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

class Player {
  late final Stream<int> vxStm;
  late final Stream<int> vyStm;
  static const speed = 2;
  Player(KbStm keydown, KbStm keyup) {
    vxStm = _makeVxStream(0, keydown, keyup);
    vyStm = _makeVyStream(0, keydown, keyup);
  }
  
  static Stream<int> _makeVxStream(int initVx, KbStm keydown, KbStm keyup) {
    final scx = StreamController<int>()..add(initVx);
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
  
  static Stream<int> _makeVyStream(int initVy, KbStm keydown, KbStm keyup) {
    final scy = StreamController<int>()..add(initVy);
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
  
  static HTMLDivElement disp(Player p1) {
    final vxp = htmlp()..style.color = "white";
    final vyp = htmlp()..style.color = "yellow";
    p1.vxStm.listen((vx) => vxp.innerText = "vx: $vx");
    p1.vyStm.listen((vy) => vyp.innerText = "vy: $vy");
    final hud = htmldiv()
      ..appendChild(vxp)
      ..appendChild(vyp);
    return hud;
  }
}

void makeGui(Player p1){
  document.body!
    .appendChild(Player.disp(p1));
}

void main() {
  final p1 = Player(document.body!.onKeyDown, document.body!.onKeyUp);
  makeGui(p1);
}

