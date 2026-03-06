/// Beginning to migrate JS code to Dart.
library;

import 'dart:js_interop';
import 'package:web/web.dart';


/// A function which returns void and takes one num param
typedef FuncNum = void Function(num);

/// Call requestAnimationFrame with a normal Dart callback
void dartRAF(FuncNum callback) {
  window.requestAnimationFrame(callback.toJS);
}

/// Methods for creating HTML elems
class HTML {
  static HTMLDivElement div() => document.createElement('div') as HTMLDivElement;
  static HTMLCanvasElement canvas() => document.createElement('canvas') as HTMLCanvasElement;
}

class Player {
  double x = 0;
  double y = 0;
  double vx = 0;
  double vy = 0;
  void updatePos(num tdelta) {
    this.x += this.vx * tdelta;
    this.y += this.vy * tdelta;
  }
}


void main() async {
  final docbody = document.body!;
  final status = HTML.div()..style.color = "#f0f";
  final container = HTML.div()
    ..style.backgroundColor = "#fff"
    ..style.width = "300px";
  final canv = HTML.canvas();
  final ctx = canv.getContext('2d') as CanvasRenderingContext2D;
  docbody.appendChild(status);
  container.appendChild(canv);
  docbody.appendChild(container);
  
  final p = Player();
  docbody.onKeyDown.listen((event) {
    double speed = 0.2;
    if (event.key == 'ArrowUp') { p.vy = -speed; }
    else if (event.key == 'ArrowDown') { p.vy = speed; }
    else if (event.key == 'ArrowLeft') { p.vx = -speed; }
    else if (event.key == 'ArrowRight') { p.vx = speed; }
    else { print("${event.key} down"); }
  });
  
  docbody.onKeyUp.listen((event) {
    if (event.key == 'ArrowUp') { p.vy = 0; }
    else if (event.key == 'ArrowDown') { p.vy = 0; }
    else if (event.key == 'ArrowLeft') { p.vx = 0; }
    else if (event.key == 'ArrowRight') { p.vx = 0; }
    else { print("${event.key} up"); }
  });

  num tlast = 0;
  void animate(num timems) {
    final tdelta = timems - tlast;
    tlast = timems;
    status.innerText = "x: ${p.x}, y: ${p.y}";
    p.updatePos(tdelta);
    ctx.clearRect(0, 0, canv.width, canv.height);
    ctx.fillRect(p.x, p.y, 10, 10);
    dartRAF(animate);
  }
  dartRAF(animate);
}
