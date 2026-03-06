///
/// Beginning to migrate JS code to Dart.
///

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
  int x = 0;
  int y = 0;
  int vx = 0;
  int vy = 0;
  void updatePos() {
    this.x += this.vx;
    this.y += this.vy;
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
    if (event.key == 'ArrowUp') { p.vy = -1; }
    else if (event.key == 'ArrowDown') { p.vy = 1; }
    else if (event.key == 'ArrowLeft') { p.vx = -1; }
    else if (event.key == 'ArrowRight') { p.vx = 1; }
    else { print("${event.key} down"); }
  });
  
  docbody.onKeyUp.listen((event) {
    if (event.key == 'ArrowUp') { p.vy = 0; }
    else if (event.key == 'ArrowDown') { p.vy = 0; }
    else if (event.key == 'ArrowLeft') { p.vx = 0; }
    else if (event.key == 'ArrowRight') { p.vx = 0; }
    else { print("${event.key} up"); }
  });

  void animate(num ms) {
    status.innerText = "x: ${p.x}, y: ${p.y}";
    p.updatePos();
    ctx.clearRect(0, 0, canv.width, canv.height);
    ctx.fillRect(p.x, p.y, 10, 10);
    dartRAF(animate);
  }
  dartRAF(animate);
}

