/// Beginning to migrate JS code to Dart.
library;

import 'dart:js_interop';
import 'package:web/web.dart';
import 'dart:async';
import 'dart:math';
import 'package:async/async.dart';


const canvWidth = 600;
const canvHeight = 400;

/// "grid Meter Base".
/// Currently, this number of pixels corresponds to one meter,
/// and is also the number of pixels per grid square (that is,
/// the grid square size is one meter).
/// We are working on being able to zoom out in the tablet view,
/// which will cause a different ratio (to scale, of course).
const gridMB = 22;

num sq(num x) => x * x;

/// Returns a sublist including all items except the last item.
/// If `orig` is empty, return it.
List<T> withoutLast<T>(List<T> orig) =>
    orig.isEmpty ? orig : orig.getRange(0, orig.length - 1).toList();


extension FunctionPipe<T extends Object> on T {
    /// Source: https://github.com/dart-lang/language/issues/1246
    R then<R>(R Function (T) f) => f(this);
}


sealed class Result<S, F> {
    Result<U, F> map<U>(U Function(S) f);
}
class Success<S, F> extends Result<S, F> {
    final S val;
    Success(this.val);
    @override
    Result<U, F> map<U>(U Function(S) f) {
        return Success(f(val));
    }
}
class Failure<S, F> extends Result<S, F> {
    final F val;
    Failure(this.val);
    @override
    Result<U, F> map<U>(_) {
        return Failure(val);
    }
}

extension Flickerable on HTMLElement {
    void addFlicker(Stream<Object> stm) {
        stm.listen((_) {
            classList.add("button-active");
            Future.delayed(Duration(milliseconds: 100), () => classList.remove("button-active"));
        });
    }
}


/// Methods for creating HTML elems
class HTML {
    static HTMLButtonElement button() =>
            document.createElement('button') as HTMLButtonElement;
    static HTMLCanvasElement canvas() =>
            document.createElement('canvas') as HTMLCanvasElement;
    static HTMLInputElement checkbox() {
        final el = document.createElement('input') as HTMLInputElement;
        el.setAttribute("type", "checkbox");
        return el;
    }

    static HTMLDivElement div() =>
            document.createElement('div') as HTMLDivElement;
    static HTMLFormElement form() =>
            document.createElement('form') as HTMLFormElement;
    static HTMLDialogElement dialog() =>
            document.createElement('dialog') as HTMLDialogElement;
    static HTMLParagraphElement p() =>
            document.createElement('p') as HTMLParagraphElement;        
    static HTMLInputElement inputsubmit() {
        final el = document.createElement('input') as HTMLInputElement;
        el.setAttribute("type", "submit");
        return el;
    }
    static HTMLSpanElement span() =>
            document.createElement('span') as HTMLSpanElement;
}

Future<bool> showGameDialog(String message) {
  final dialog = HTML.dialog()..id = 'game-dialog';
  final text = HTML.p()..textContent = message;
  final okButton = HTML.button()
      ..textContent = 'OK'
      ..classList.add('game-btn');
  final cancelButton = HTML.button()
      ..textContent = 'Cancel'
      ..classList.add('game-btn');
  final buttonRow = HTML.div()
      ..id = 'game-dialog-buttons'
      ..appendChild(okButton)
      ..appendChild(cancelButton);
  final completer = Completer<bool>();
  okButton.onClick.listen((_) {
    dialog.close();
    completer.complete(true);
  });
  cancelButton.onClick.listen((_) {
    dialog.close();
    completer.complete(false);
  });
  dialog.append(text);
  dialog.append(buttonRow);
  document.body!.append(dialog);
  dialog.show();
  return completer.future;
}

class Pos {
    static final _gridorigin = (x: 70000, y: 40000);
    
    /// x expressed in canvas units
    final double xcu;
    /// y expressed in canvas units
    final double ycu;
    /// x expressed in grid units
    double get xgrid => xCUToGrid(xcu);
    /// y expressed in grid units
    double get ygrid => yCUToGrid(ycu);

    Pos.fromCanvUnits(this.xcu, this.ycu);
    Pos.fromGridCoords(double xgrid, double ygrid) :
      xcu = xgridToCU(xgrid),
      ycu = ygridToCU(ygrid);

    static double xgridToCU(double xgrid) => (xgrid - _gridorigin.x) * gridMB;
    static double ygridToCU(double ygrid) => -(ygrid - _gridorigin.y) * gridMB;
    static double xCUToGrid(double xcu) => ((xcu / gridMB) + _gridorigin.x);
    static double yCUToGrid(double ycu) => ((-ycu / gridMB) + _gridorigin.y);
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
        const speedMetersPerSecond = 2.0;
        final speed = _makeSpeed(speedMetersPerSecond * 0.001, keydown, keyup);
        final dirx = _makeDirx(keydown, keyup);
        final diry = _makeDiry(keydown, keyup);
        final x = _makeX(initPos.xgrid, dirx, tdelta, speed);
        final y = _makeY(initPos.ygrid, diry, tdelta, speed);
        return StreamZip<double>([x, y])
            .map((xypair) => Pos.fromGridCoords(xypair[0], xypair[1]))
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
                sc.add(-1);
            } else if (ev.key == "ArrowUp") {
                sc.add(1);
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
        final posEl = HTML.div()..id = "player-pos";
        _posStm.listen((pos) => posEl.innerText = "grid: 55P DE ${pos.xgrid.toStringAsFixed(0)} ${pos.ygrid.toStringAsFixed(0)}");
        return posEl;
    }
}

class Avatar implements Drawable {
    final String color; 
    Avatar(this.color); 

    @override
    void draw(CanvasRenderingContext2D ctx, Pos _) {
        const sz = 2;
        const cenx = canvWidth / 2;
        const ceny = canvHeight / 2;
        ctx.fillStyle = color.toJS;
        void head() => fillCircle(cenx + sz, ceny - sz * 4, sz * 3, ctx);
        void torso() => ctx.fillRect(cenx - sz * 1, ceny - sz * 2, sz * 4, sz * 8);
        void arms() => ctx.fillRect(cenx - sz * 4, ceny + sz * 0, sz * 10, sz);
        void leg1() => ctx.fillRect(cenx - sz * 1, ceny + sz * 6, sz * 1.5, sz * 5);
        void leg2() => ctx.fillRect(cenx + sz * 1.5, ceny + sz * 6, sz * 1.5, sz * 5);
        head(); torso(); arms(); leg1(); leg2();
    }
}

class Reticle implements Drawable {
    final String color;
    Reticle(this.color);

    @override
    void draw(CanvasRenderingContext2D ctx, Pos _) {
        const cenx = canvWidth / 2;
        const ceny = canvHeight / 2;
        final rbig = 6;
        final rsmall = 1.5;

        ctx.globalAlpha = 0.5; // semi-transparent
        ctx.strokeStyle = color.toJS;
        ctx.fillStyle = color.toJS;
        ctx.lineWidth = 1.5;

        // outer circle
        ctx.beginPath();
        ctx.arc(cenx, ceny, rbig, 0, 2 * pi);
        ctx.stroke();

        // center dot
        ctx.beginPath();
        ctx.arc(cenx, ceny, rsmall, 0, 2 * pi);
        ctx.fill();

        ctx.globalAlpha = 1.0; // reset
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
        x - relpos.xcu + canvWidth / 2,
        y - relpos.ycu + canvHeight / 2,
        w,
        h,
    );
}

void moveToRel(num x, num y, CanvasRenderingContext2D ctx, Pos relpos) {
    ctx.moveTo(x - relpos.xcu + canvWidth / 2, y - relpos.ycu + canvHeight / 2);
}

void lineToRel(num x, num y, CanvasRenderingContext2D ctx, Pos relpos) {
    ctx.lineTo(x - relpos.xcu + canvWidth / 2, y - relpos.ycu + canvHeight / 2);
}

void fillTextRel(String text, num x, num y, CanvasRenderingContext2D ctx, Pos relpos) {
    ctx.fillText(text, x - relpos.xcu + canvWidth / 2, y - relpos.ycu + canvHeight / 2);
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
        x - relpos.xcu + canvWidth / 2,
        y - relpos.ycu + canvHeight / 2,
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
        /// Space between gridlines in meters
        const gridUnitSpc = 1;
        /// Space between gridlines in canvas units
        const gridSpacing = gridMB * gridUnitSpc;
        /// this is an empirical guess. Eventually we should use a monospace
        /// font and fetch the width of it if possible.
        const charWidth = 6;
        /// see note on charWidth
        const charHeight = 3;
        /// center to x edge, in grid units
        const ctoxeg = 0.7 * canvWidth / gridMB;
        /// center to y edge, in grid units
        const ctoyeg = 0.7 * canvHeight / gridMB;

        double toGrid(double v) => (v / gridUnitSpc).floorToDouble() * gridUnitSpc;

        ctx.strokeStyle = "#ccc".toJS;
        ctx.fillStyle = "#ccc".toJS;
        ctx.lineWidth = 0.5;
        
        final startx = Pos.xgridToCU(toGrid(center.xgrid - ctoxeg));
        final starty = Pos.ygridToCU(toGrid(center.ygrid + ctoyeg));

        for (var x = startx; x <= startx + 1.5*canvWidth; x += gridSpacing) {
            ctx.beginPath();
            moveToRel(x, center.ycu + canvHeight, ctx, center);
            lineToRel(x, center.ycu - canvHeight, ctx, center);
            ctx.stroke();
            final gridVal = Pos.xCUToGrid(x).toString().substring(3);
            fillTextRel(
                gridVal,
                x - charWidth,
                center.ycu - (canvHeight/2) + 10,
                ctx,
                center
            );
        }

        for (var y = starty; y <= starty + 1.5*canvHeight; y += gridSpacing) {
            ctx.beginPath();
            moveToRel(center.xcu + canvWidth, y, ctx, center);
            lineToRel(center.xcu - canvWidth, y, ctx, center);
            ctx.stroke();
            final gridVal = Pos.yCUToGrid(y).toString().substring(3);
            fillTextRel(
                gridVal,
                center.xcu - (canvWidth/2),
                y + charHeight,
                ctx,
                center
            );
        }
    }
}


class TxRadio implements Drawable {
    final pos = Pos.fromGridCoords(70008, 40012);
    final txpower = Power(mW: 100);
    
    @override
    void draw(CanvasRenderingContext2D ctx, Pos center) {
        ctx.fillStyle = "#00f".toJS;
        fillRectRel(pos.xcu - 5, pos.ycu - 5, 10, 10, ctx, center);
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
    : _pos = Pos.fromGridCoords(x, y);
    

    @override
    void draw(CanvasRenderingContext2D ctx, Pos center) {
        final xd = _pos.xcu - center.xcu;
        final yd = _pos.ycu - center.ycu;
        
        if (yd.abs() > (0.7 * canvHeight) || xd.abs() > (0.7 * canvWidth)) {
            return;
        }
        ctx.fillStyle = "#440".toJS;
        fillRectRel(
            _pos.xcu - _size,
            _pos.ycu + _size * 0.7,
            _size * 0.9,
            6,
            ctx,
            center,
        );
        fillRectRel(_pos.xcu, _pos.ycu + _size * 0.7, _size * 0.9, 6, ctx, center);
        fillRectRel(
            _pos.xcu + _size * 0.7,
            _pos.ycu + _size * 0.7,
            _size * 0.9,
            6,
            ctx,
            center,
        );
        ctx.fillStyle = _color.toJS;
        fillCircleRel(_pos.xcu - _size, _pos.ycu, _size, ctx, center);
        fillCircleRel(_pos.xcu, _pos.ycu, _size, ctx, center);
        fillCircleRel(_pos.xcu, _pos.ycu - _size, _size, ctx, center);
        fillCircleRel(_pos.xcu + _size, _pos.ycu, _size, ctx, center);
        fillCircleRel(_pos.xcu, _pos.ycu - _size, _size, ctx, center);
        fillCircleRel(_pos.xcu + 2 * _size, _pos.ycu, _size, ctx, center);
        fillCircleRel(_pos.xcu + 1.5 * _size, _pos.ycu - _size, _size, ctx, center);
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
    late final HTMLInputElement _gatheringLobsCb;
    late final HTMLButtonElement _clearBtn;
    late final Stream<ImmuList<LOB>> _lobsStm;
    late final Observable<ImmuList<LOB>> _lobs;
    /// Selected LOB
    late final Observable<LOB?> _sellob;

    LOBCol(KbStm keydown, Stream<LOB> univLobs, Stream<MouseEvent> canvclick, Player p1) {
        _gatheringLobsCb = _configGath(keydown);
        final (clear, cbtn) = _configClearing(keydown);
        _clearBtn = cbtn;
        final filtlobs = univLobs.where((_) => _gatheringLobsCb.checked);
        _lobsStm = _makeLobStream(clear, filtlobs);
        _lobs = Observable(ImmuList([]), _lobsStm);
        _sellob = _configChosenLOB(_lobs, canvclick, p1);
    }

    static Observable<LOB?> _configChosenLOB(Observable<ImmuList<LOB>> lobs, Stream<MouseEvent> canvclick, Player p1,) {
        final sc = StreamController<LOB?>();
        canvclick.listen((ev) {
            final chosen = decideClosest(lobs.latestVal, p1.pos, ev);
            if (chosen != null) {
                print("I am the selected lob");
            }
            sc.add(chosen);
        });
        return Observable(null, sc.stream);
    }
    
    static LOB? decideClosest(ImmuList<LOB> immulobs, Pos p1pos, MouseEvent ev) {
        final lobs = immulobs.values;
        final shiftx = p1pos.xcu + ev.offsetX - canvWidth / 2;
        final shifty = p1pos.ycu + ev.offsetY - canvHeight / 2;
        num dist(LOB lob) {
            final dx = (lob.source.xcu - shiftx).abs();
            final dy = (lob.source.ycu - shifty).abs();
            return dx + dy;
        }
        lobs.sort((a, b) => dist(a).compareTo(dist(b)));
        final near = lobs.where((lob) => dist(lob) < 40);
        return near.firstOrNull;
    }
    
    static HTMLInputElement _configGath(KbStm keydown) {
        final gcb = HTML.checkbox()
            ..id = "lob-cb"
            ..defaultChecked = true;
        keydown
            .where((ev) => ev.key.toLowerCase() == "g")
            .listen((_) => gcb.checked = !gcb.checked);
        return gcb;
    }
    
    static (Stream<Event>, HTMLButtonElement) _configClearing(KbStm keydown) {
        final cDown = keydown.where((ev) => ev.key.toLowerCase() == "c").asBroadcastStream();
        final cbtn = HTML.button()
            ..addFlicker(cDown)
            ..id = "clear-btn"
            ..innerText = "Clear LOBs [ c ]";
        return (StreamGroup.merge([cDown, cbtn.onClick]), cbtn);
    }
    /// Makes a stream of the lobs saved on the simulated DFing equipment,
    /// not to be confused with the stream of lobs coming from the universe.
    static Stream<ImmuList<LOB>> _makeLobStream(Stream<Object> clear, Stream<LOB> filtlobs)    {
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
        final lobPowEl = HTML.div()..id = "lob-power";
        _lobsStm.listen((lobs) => lobPowEl.innerText = _fmtpow(lobs.values.lastOrNull));
        return lobPowEl;
    }

    HTMLDivElement dispCtl() {
    return HTML.div()
        ..appendChild(_clearBtn..className = "game-btn")
        ..appendChild(HTML.div()..id = "lobs-cb-with-text"
            ..appendChild(HTML.span()..innerText = "Gathering LOBs [ g ]: ")
            ..appendChild(_gatheringLobsCb)
        );
    }

    @override
    void draw(CanvasRenderingContext2D ctx, Pos center) {
        final lobs = _lobs.latestVal.values;

        void drawOne(LOB lob, {String color = "orange"}) {
            const loblength = 10000;
            final endx = lob.source.xcu + loblength * lob.azimuth.cosresult;
            final endy = lob.source.ycu + loblength * lob.azimuth.sinresult;
            ctx.beginPath();
            ctx.lineWidth = 2;
            ctx.strokeStyle = color.toJS;
            moveToRel(lob.source.xcu, lob.source.ycu, ctx, center);
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
    /// Given the player (receiver) position and the transmitter position
    /// compute the azimuth from the player's perspective.
    Azimuth.fromPositions(Player p, TxRadio t) {
        final xd = t.pos.xcu - p.pos.xcu;
        final yd = t.pos.ycu - p.pos.ycu;
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
        final xd = t.pos.xgrid - p1.pos.xgrid;
        final yd = t.pos.ygrid - p1.pos.ygrid;
        final dist = sqrt(xd * xd + yd * yd);
        return t.txpower * 0.1 * (1 / sq(dist)) * (_random.nextDouble() * 0.1 + 0.9);
    }
}

class MissionUI {
    late final String? missionName;
    final Pos txpos;

    MissionUI(String href, this.txpos) {
        final uri = Uri.parse(href);
        missionName = uri.queryParameters["mission"];
    }

    HTMLElement disp() {
        if (missionName == "m1") {
            return _form();
        }
        return HTML.div();
    }

    static void _handleSubmit(String submission) {
        Result<({double? easting, double? northing}), String> validateOneSpace(String val) {
            final preproc = val
                .trim()
                .split(" ")
                .map(double.tryParse)
                .toList();
            switch (preproc) {
                case [double easting, double northing]:
                    return Success((easting: easting, northing: northing));
                case _:
                    return Failure("You must enter two numbers separated by a space.\nExample: 12345 45678");
                    // TODO // return Failure("That's too many spaces. Submission must be in this format: 12345 45678");
            }
        }
        final r = validateOneSpace(submission);
        showGameDialog(r.toString()).then((goToHomeScreen) {
            if (goToHomeScreen) {
                window.open("..", "_self");
            }
        });
    }

    static HTMLFormElement _form() {
        final form = HTML.form();
        final inpEl = HTMLInputElement()
            ..id = "grid-input"
            ..placeholder = "Enter grid coordinates";
        final subbtn = HTML.inputsubmit()
            ..addFlicker(form.onSubmit)
            ..id = "submit-btn"
            ..className = "game-btn";
        form
            ..appendChild(inpEl)
            ..appendChild(subbtn);
        form.onSubmit.listen((e) {
            e.preventDefault();
            Future.delayed(Duration(milliseconds: 1), () => _handleSubmit(inpEl.value));
        });
        return form;
    }
}

void attachElems(HTMLElement root, PlayerHUD phud, LOBCol lobc, CanvM cmLife, CanvM cmLob, MissionUI mui){
    root..id = "root"
        ..appendChild(HTML.div()..id = "two-canvasses"
            ..appendChild(cmLife.disp())
            ..appendChild(HTML.div()
                ..style.position = "relative"
                ..appendChild(HTML.div()..id = "hudwrap"
                    ..appendChild(cmLob.disp())) 
                ..appendChild(phud.disp())
                ..appendChild(lobc.dispInfo())
                ..appendChild(lobc.dispCtl())
                ..appendChild(mui.disp())
            )
        )
        ..appendChild(HTML.div()..id = "directions"
            ..innerText =
                "\nDirections: Find the transmitter using Lines of Bearing.\n"
                "- Arrow keys to move\n"
                "- 'Shift' to run\n"
                "- 'g' to toggle LOB gathering\n"
                "- 'c' to clear LOBs\n"
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
                69900 + (random.nextDouble() * 200),
                39900 + (random.nextDouble() * 200),
                "#$redandblue$green$redandblue",
                size,
            );
        }

        _objs = List.unmodifiable([for (var i = 0; i < 2000; i++) makebush()]);
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
    final p1 = Player(Pos.fromGridCoords(70005, 40008), keydown, keyup, frameStm);
    final ph = PlayerHUD(p1.posStm);
    final t1 = TxRadio();
    final sim = Sim(p1, t1);
    final bushes = ObjCol();
    final grid = Grid();
    final avatarlife = Avatar("#000");
    final reticle = Reticle("#fff");
    final cmLife = CanvM("life", canvWidth, canvHeight);
    final cmLob = CanvM("hud", canvWidth, canvHeight);
    final lobc = LOBCol(keydown, sim.univLobs, cmLob.click, p1);
    final mui = MissionUI(window.location.href, t1.pos);
    cmLife.config(p1.posStm, [avatarlife, bushes, t1]);
    cmLob.config(p1.posStm, [lobc, grid, reticle]);
    attachElems(document.body!, ph, lobc, cmLife, cmLob, mui); 
}


/*

### Brainstorming 2026 April 13

#### Possible simple mission

- Tablet should show mission: "Current Mission: Find location of enemy transmitter. If you go beyond the FLOT, you fail the mission."
  - (Once we add the mission code, the mission stuff will be hidden in 'Explore' mode.)
- Put a collection of stuff in a line-ish shape.
  - You are freely able to move past the stuff, but if you go beyond it, you immediately fail the mission. { Functional reason for adding this: you can't walk right next to transmitter to see its exact location }
- There's a text entry field (probably on the 'tablet') for reporting up the grid coordinates of the transmitter. Minimum 6 digit grid accuracy (100 meters). If you report the correct grid coordinates, then you suceeded the mission.
- How to see it?
  - Probably need zooming in and out on the tablet interface because right now the cut/fix would be too far away to see if you can't walk up to it
  - Probably need map labels along edges of tablet grid view so there's a correlation between the location and the grid
    Like this:
       3    4    5
       |    |    |
       |    |    |
- Right canvas would have the dotted line for the FLOT
- Left canvas would have stick figures or whatever troops and equipment maybe
  
#############################################################################

#### Brief history review

- What led to J wanting rewrites in the past?
  - 2d game version 1 (tiles, Python server, small Javascript client)
    Status: we had started adding missions
    RFL: We decided multiplayer was not worth the extra effort that we were having to put into synchronizing locations and such
  - 2d game version 2 (tiles, all client side, pyodide)
    RFL: Switched to 3D 
  - 3d game (Three JS, Pyodide, etc):
    RFL: 
      1. J thought code was not manageable -- too much was organized by AI
      2. Changed our focus from accurate physics to ray-based DFing simulation

#############################################################################

Next steps 

- Add a compass.
  We need to discuss different execution possibilities.
  - G N with a vertical line?
  - magnetic north too? 
  
- Option in HUD to switch between separate map or overlay
    - implementation: have a variable that gets set to the proper canvas
- Zoom in/out on LOB view

Player is direction finding a transmitter.
Initially, dfing is based on line-of-sight only. (Later: add reflections, path loss, etc)

- Draw a ray from the player to the transmitter.

- if line of sight exists.
    - How to determine line of sight?

- elevation

- selected lob not showing
- alerts should be shown on the tablet (cmlob canvas) and should be tailored as a response from you unit
*/
