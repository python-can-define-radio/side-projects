/// LOBSTER Game.
library;


import 'dart:async';
import 'dart:js_interop';
import 'dart:math';
import 'package:async/async.dart' hide Result;
import 'package:meta/meta.dart';
import 'package:web/web.dart';
import 'custom.dart';
import './htmlhelp.dart';


const canvWidth = 600;
const canvHeight = 400;


typedef Cctx = CanvasRenderingContext2D;
typedef KbStm = ElementStream<KeyboardEvent>;
typedef DuStm = Stream<Duration>;



/// Methods for creating HTML elems
class HTML {
    static HTMLButtonElement button() =>
            document.createElement('button') as HTMLButtonElement;
    static HTMLCanvasElement canvas() =>
            document.createElement('canvas') as HTMLCanvasElement;
    static HTMLDialogElement dialog() =>
            document.createElement('dialog') as HTMLDialogElement;
    static HTMLFormElement form() =>
            document.createElement('form') as HTMLFormElement;
    static HTMLHeadingElement h2() =>
            document.createElement("h2") as HTMLHeadingElement;    
    static HTMLParagraphElement p() =>
            document.createElement('p') as HTMLParagraphElement;    
    static HTMLSpanElement span() =>
            document.createElement('span') as HTMLSpanElement;
    static HTMLInputElement checkbox() {
        final el = document.createElement('input') as HTMLInputElement;
        el.setAttribute("type", "checkbox");
        return el;
    }
    // static HTMLDivElement div() {
    //     return document.createElement('div') as HTMLDivElement;
    // }
    static HTMLDivElement div({String? id, String? className, List<HTMLElement>? children}) {
        final e = document.createElement('div') as HTMLDivElement;
        if (id != null) {
            e.id = id;
        }
        if (className != null) {
            e.className = className;
        }
        if (children != null) {
            for (final c in children) {
                e.appendChild(c);
            }
        }
        return e;
    }
    static HTMLInputElement inputsubmit() {
        final el = document.createElement('input') as HTMLInputElement;
        el.setAttribute("type", "submit");
        return el;
    }
}


/// Load an image. Wait for it to decode before returning.
@Eff("http-req")
Future<HTMLImageElement> imageload(String path) async {
    final el = HTMLImageElement()..src = path;
    await el.decode().toDart;
    return el;
}


class OkCancelDialog {
    final _dialogWrap = HTML.div();

    /// Return value:
    ///  `true` => user clicked `OK`
    ///  `false` => user clicked `Cancel`
    @Mut(["this._dialogWrap"])
    Future<bool> showWith(String msg) {
        final dialog = HTML.dialog()..className = "game-dialog";
        dialog.innerText = msg;
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
        dialog.appendChild(buttonRow);
        _dialogWrap.replaceChildren(dialog);
        dialog.show();
        return completer.future;
    }
    HTMLElement disp() => _dialogWrap;
}


/// Grid to Canvas Converter
@immutable
class GridCC {
    /// "grid Meter Base".
    /// An arbitrarily chosen number of pixels
    /// that corresponds to one meter when scale is `1.0`.
    static const gridMB = 22;
    /// Zoom scale. Example: scale = 0.5 would be zoomed out by a factor of 2.
    final double scale;
    final Pos center;
    GridCC(this.scale, this.center);
    
    /// Returns (x, y) in canvas units
    (double, double) cu(Pos p) => (
        p.x.val * gridMB * scale,
        p.y.val * gridMB * scale,
    );

    Pos gc(num x, num y) => Pos(
        GC(x / gridMB / scale),
        GC(y / gridMB / scale),
    );

    /// Given a position (which uses Grid Coordinates),
    /// - converts to canvas units
    /// - shifts based on `center` and the size of the canvas
    /// Returns a pair that is suitable for canvas draw functions.
    ({double xcu, double ycu}) cush(Pos p) {
        final (xcuUnshifted, ycuUnshifted) = cu(p);
        final (xcentcu, ycentcu) = cu(center);
        /// Notice that the vertical formula is inverted 
        /// because canvases use down as positive y direction
        return (
            xcu: xcuUnshifted - xcentcu + canvWidth / 2,
            ycu: ycentcu - ycuUnshifted + canvHeight / 2,
        );
    }

    /// Fill rectangle, but `p` specifies the center, not the top-left corner.
    @Mut(["ctx"])
    void fillRectCent(Pos p, num wcu, num hcu, Cctx ctx) {
        final (:xcu, :ycu) = cush(p);
        ctx.fillRect(xcu - wcu/2, ycu - hcu/2, wcu, hcu);
    }

    /// `p` specifies the center, not the top-left corner.
    @Mut(["ctx"])
    void drawImage(Pos p, HTMLImageElement img, num wcu, num hcu, Cctx ctx) {
        final (:xcu, :ycu) = cush(p);
        ctx.drawImage(img, xcu - wcu/2, ycu - hcu/2, wcu, hcu);
    }

    /// Line from `pos1` to `pos2`
    @Mut(["ctx"])
    void drawLine(Pos pos1, Pos pos2, Cctx ctx) {
        final one = cush(pos1);
        final two = cush(pos2);
        ctx.beginPath();
        ctx.moveTo(one.xcu, one.ycu);
        ctx.lineTo(two.xcu, two.ycu);
        ctx.stroke();
    }

    /// Line from `pos1` to `pos2`
    @Mut(["ctx"])
    void fillText(String text, Pos p, Cctx ctx) {
        final (:xcu, :ycu) = cush(p);
        ctx.fillText(text, xcu, ycu);
    }

    /// Line from `rp1` to `rp2`.
    /// Both are relative to `center`.
    /// Example: given
    ///   - center x is 70030
    ///   - rp1 x is -5
    ///   - rp2 x is 10
    ///   it would draw the line from x=70025 to x=70040.
    /// (The same logic applies for y.)
    @Mut(["ctx"])
    void drawLineRel(Pos rp1, Pos rp2, Cctx ctx) {
        drawLine(center + rp1, center + rp2, ctx);
    }
}

/// Grid Coordinates
@immutable
class GC {
    final num val;
    GC(this.val);
    GC operator +(GC other) => GC(val + other.val);
    GC operator -(GC other) => GC(val - other.val);
    GC operator *(GC other) => GC(val * other.val);
    GC operator /(GC other) => GC(val / other.val);
    String get asfivedig => val.round().toString().padLeft(5, '0');
}

@immutable
class Pos {
    final GC x;
    final GC y;
    Pos(this.x, this.y);

    Pos operator +(Pos other) =>
        Pos(x + other.x, y + other.y);
}


abstract class Drawable {
    void draw(Cctx ctx, GridCC gridcc);
}


class PlayerPos {
    final Stream<Pos> posStm;
    late final Observable<Pos> posObs;

    PlayerPos(Pos initPos, KbStm keydown, KbStm keyup, DuStm tdelta)
        : posStm = _makePosStm(initPos, keydown, keyup, tdelta) {
        posObs = Observable(initPos, posStm);
    }

    static Stream<Pos> _makePosStm(Pos initPos, KbStm keydown, KbStm keyup, DuStm tdelta) {
        const baseSpeed = 2.0 * 0.001;
        final pressed = <String>{};
        final sc = StreamController<Pos>();
        keydown.listen((e) {
            if (!e.repeat) {
                pressed.add(e.code);
            }
        });
        keyup.listen((e) {
            pressed.remove(e.code);
        });
        var cur = initPos;
        tdelta.listen((dt) {
            var dx = 0.0;
            var dy = 0.0;
            if (pressed.contains("KeyA")) dx -= 1;
            if (pressed.contains("KeyD")) dx += 1;
            if (pressed.contains("KeyW")) dy += 1;
            if (pressed.contains("KeyS")) dy -= 1;
            /// Normalize diagonal movement so that movement speed is always 1.
            /// Without this, diagonal would be faster
            final mag = sqrt(dx * dx + dy * dy);
            if (mag > 0) {
                dx /= mag;
                dy /= mag;
            }
            final running = pressed.contains("ShiftLeft") ||
                            pressed.contains("ShiftRight");
            final speed = running ? baseSpeed * 2 : baseSpeed;
            final dist = speed * dt.inMilliseconds;
            cur = Pos(
                GC(cur.x.val + dx * dist),
                GC(cur.y.val + dy * dist),
            );
            sc.add(cur);
        });
        return sc.stream.asBroadcastStream();
    }
}

class PlayerHUD {
    final Stream<Pos> _posStm;
    PlayerHUD(this._posStm);
    HTMLDivElement disp() {
        final posEl = HTML.div()..id = "player-pos";
        _posStm.listen((pos) =>
            posEl.innerText =
                "grid: 55P DE "
                "${pos.x.asfivedig} "
                "${pos.y.asfivedig}"
        );
        return posEl;
    }
}

class Avatar implements Drawable {
    final HTMLImageElement _avatarSheet;
    final int _horizFrames = 4;
    final int _vertFrames = 4;
    late final Observable<int> _curFrame;

    Pos? _lastPos;
    int _directionRow = 0;

    Avatar(this._avatarSheet) {
        final stm = Stream.periodic(
            const Duration(milliseconds: 200),
            (c) => c % _horizFrames
        );
        _curFrame = Observable(0, stm);
    }

    @Eff("http-req")
    @factory
    static Future<Avatar> create() async {
        return Avatar(await imageload("../assets/avatar_sheet2.png"));
    }

    @Mut(["ctx"])
    void _drawSlice(Cctx ctx, int xidx, int yidx, num xpos, num ypos, num size) {
        final fw = _avatarSheet.width / _horizFrames;
        final fh = _avatarSheet.height / _vertFrames;

        ctx.drawImage(_avatarSheet, xidx * fw, yidx * fh,  fw, fh, xpos, ypos, size, size);
    }

    @override
    @Mut(["ctx"])
    void draw(Cctx ctx, GridCC gridcc) {
        const cenx = canvWidth / 2;
        const ceny = canvHeight / 2;
        const avsize = 50;
        final curPos = gridcc.center;

        // Default: idle frame
        int frame = 0;

        if (_lastPos != null) {
            final dx = curPos.x.val - _lastPos!.x.val;
            final dy = curPos.y.val - _lastPos!.y.val;

            final moving = dx != 0 || dy != 0;

            if (moving) {
                // Horizontal dominates
                if (dx.abs() > dy.abs()) {
                    if (dx > 0) {
                        _directionRow = 3; 
                    } else {
                        _directionRow = 2; 
                    }
                }
                // Vertical dominates
                else {
                    if (dy > 0) {
                        _directionRow = 1; 
                    } else {
                        _directionRow = 0; 
                    }
                }

                frame = _curFrame.latestVal;
            } else {
                // idle → freeze on first frame of direction
                frame = 0;
            }
        }

        _lastPos = curPos;

        _drawSlice(ctx, frame, _directionRow, cenx - avsize / 2, ceny - avsize / 2, avsize);
    }
}

class Reticle implements Drawable {
    final Observable<Pos> _p1pob;
    Reticle(this._p1pob);

    @override
    void draw(Cctx ctx, GridCC gridCC) {
        final color = "#fff".toJS;
        ctx.globalAlpha = 0.5; // semi-transparent
        ctx.strokeStyle = color;
        ctx.fillStyle = color;
        ctx.lineWidth = 1.5;
        final (:xcu, :ycu) = gridCC.cush(_p1pob.latestVal);
        /// outer circle
        ctx.beginPath();
        ctx.arc(xcu, ycu, 6, 0, 2 * pi);
        ctx.stroke();
        /// center dot
        ctx.beginPath();
        ctx.arc(xcu, ycu, 1.5, 0, 2 * pi);
        ctx.fill();
        ctx.globalAlpha = 1.0; // reset
    }
}


void fillCircle(num x, num y, num radius, Cctx ctx) {
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, 2 * pi);
    ctx.fill();
}


class CanvM {
    final HTMLCanvasElement _canv = HTML.canvas();
    late final Cctx _ctx;
    late final ImmuList<Drawable> _drawItems;
    late final Stream<MouseEvent> click = _canv.onClick;
    final Observable<double> _scale;
    late final Observable<Pos>? _panCenter;
    late final Stream<MEv> mevStm;

    CanvM(String cssid, int w, int h, this._scale, Stream<MouseEvent> docMouseUp) {
        _canv
            ..width = w
            ..height = h
            ..id = cssid;
        _ctx = _canv.getContext('2d') as Cctx;
        /// as per AI recommendation, the mouseUp should be from the document in case the cursor leaves the canvas
        mevStm = makeMouseMoveStm(_canv.onMouseDown, _canv.onMouseMove, docMouseUp);
    }
    
    /// Basically 'constructor part two'. Had to separate to avoid
    /// a circular dependency.
    void config(Stream<Pos> posStm, List<Drawable> drawItems, [Observable<Pos>? panCenter]) {
        _drawItems = ImmuList(drawItems);
        _panCenter = panCenter;
        posStm.listen(_frameUpdate);
    }
    
    HTMLCanvasElement disp() => _canv;

    void _frameUpdate(Pos center) {
        final panCent = _panCenter == null ? center : _panCenter.latestVal;
        final gridcc = GridCC(_scale.latestVal, panCent);
        _ctx.clearRect(0, 0, _canv.width, _canv.height);
        for (final item in _drawItems.values) {
            item.draw(_ctx, gridcc);
        }
    }
}

class Grid implements Drawable {
    final Observable<double> _scale;
    Grid(this._scale);
    @override
    void draw(Cctx ctx, GridCC gridcc) {

        /// Space between gridlines in meters
        final gridUnitSpcExponent = switch(_scale.latestVal) {
            <0.0099  => 3,
            <0.099  => 2,
            <0.99  => 1,
            _  => 0,
        };

        final gridUnitSpc = pow(10, gridUnitSpcExponent);

        GC toGrid(GC gc) =>
            GC((gc.val / gridUnitSpc).floorToDouble() * gridUnitSpc);

        ctx.strokeStyle = "#ccc".toJS;
        ctx.fillStyle = "#ccc".toJS;
        ctx.lineWidth = 0.5;

        final far = GC(gridUnitSpc * 20);
        final doublefar = far * GC(2);
        final xstart = toGrid(gridcc.center.x - far);
        final xstop = xstart + doublefar;
        final ystart = toGrid(gridcc.center.y - far);
        final ystop = ystart + doublefar;
        final xtext = gridcc.center.x - GC(13.6 / gridcc.scale);
        final ytext = gridcc.center.y + GC(8.7 / gridcc.scale);

        /// this is an empirical guess. Eventually we should use a monospace
        /// font and fetch the width of it if possible.
        final charWidth = 0.3 / gridcc.scale;
        /// see note on charWidth
        final charHeight = 0.2 / gridcc.scale;

        String lastDigits(GC gc) {
            final numdig = (gridUnitSpcExponent + 2).clamp(2, 5);
            return gc.asfivedig.substring(5 - numdig, 5);
        }
        
        for (var x = xstart.val; x <= xstop.val; x += gridUnitSpc) {
            gridcc.drawLine(Pos(GC(x), ystart), Pos(GC(x), ystop), ctx);
            gridcc.fillText(
                lastDigits(GC(x)),
                Pos(GC(x - charWidth), ytext),
                ctx
            );
        }
        for (var y = ystart.val; y <= ystop.val; y += gridUnitSpc) {
            gridcc.drawLine(Pos(xstart, GC(y)), Pos(xstop, GC(y)), ctx);
            gridcc.fillText(
                lastDigits(GC(y)),
                Pos(xtext, GC(y - charHeight)),
                ctx
            );
        }
    }
}


class TxRadio implements Drawable {
    final Pos pos = Pos(GC(70008), GC(40012));
    final Power txpower = Power(mW: 100);
    final HTMLImageElement _img;
    late final num _w;
    late final num _h;

    TxRadio(this._img) {
        const size = 30;
        _h = size;
        _w = size * _img.width / _img.height;
    }

    @Eff("http-req")
    @factory
    static Future<TxRadio> create() async { return TxRadio(await imageload("../assets/tx.png")); }

    @override
    @Mut(["ctx"])
    void draw(Cctx ctx, GridCC gridcc) { gridcc.drawImage(pos, _img, _w, _h, ctx); }
}


class SimpleOb implements Drawable {
    final Pos _pos;
    final HTMLImageElement _img;
    late final num _width;
    late final num _height;

    SimpleOb(GC x, GC y, this._img, num size)
        : _pos = Pos(x, y) {
        _height = size;
        _width = size * _img.width / _img.height;
    }

    @override
    void draw(Cctx ctx, GridCC gridcc) {
        gridcc.drawImage(_pos, _img, _width, _height, ctx);
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

    LOBCol(KbStm keydown, Stream<LOB> univLobs, Stream<MouseEvent> canvclick, Observable<Pos> p1pob, Observable<double> scale) {
        _gatheringLobsCb = _configGath(keydown);
        final (clear, cbtn) = _configClearing(keydown);
        _clearBtn = cbtn;
        final filtlobs = univLobs.where((_) => _gatheringLobsCb.checked);
        _lobsStm = _makeLobStream(clear, filtlobs);
        _lobs = Observable(ImmuList([]), _lobsStm);
        _sellob = _configChosenLOB(_lobs, canvclick, p1pob, scale);
    }

    static Observable<LOB?> _configChosenLOB(Observable<ImmuList<LOB>> lobs, Stream<MouseEvent> canvclick, Observable<Pos> p1pob, Observable<double> scale) {
        final sc = StreamController<LOB?>();
        canvclick.listen((ev) {
            final gridcc = GridCC(scale.latestVal, p1pob.latestVal);
            final chosen = decideClosest(lobs.latestVal, gridcc, ev);
            print("Selected lob: $chosen");
            sc.add(chosen);
        });
        return Observable(null, sc.stream);
    }
    
    static LOB? decideClosest(ImmuList<LOB> immulobs, GridCC gridcc, MouseEvent ev) {
        /// TODO
        // window.alert("${gridcc.cush(gridcc.center)}");
        // final lobs = immulobs.values;
        // final shiftx = p1pos.xcu + ev.offsetX - canvWidth / 2;
        // final shifty = p1pos.ycu + ev.offsetY - canvHeight / 2;
        // num dist(LOB lob) {
        //     final dx = (lob.source.xcu - shiftx).abs();
        //     final dy = (lob.source.ycu - shifty).abs();
        //     return dx + dy;
        // }
        // lobs.sort((a, b) => dist(a).compareTo(dist(b)));
        // final near = lobs.where((lob) => dist(lob) < 40);
        // return near.firstOrNull;
        
        /// this is temporary
        return immulobs.values.firstOrNull;
    }
    
    /// Creates and returns a checkbox.
    /// The checkbox's `checked` attribute is mutated by the keydown stream.
    static HTMLInputElement _configGath(KbStm keydown) {
        final gcb = HTML.checkbox()
            ..id = "lob-cb"
            ..defaultChecked = true;
        keydown
            .where((ev) => ev.code == "KeyG")
            .listen((_) => gcb.checked = !gcb.checked);
        return gcb;
    }
    
    /// Returns a stream and the clear button.
    /// Events in the stream (both clicks and keypresses) should cause a clear.
    static (Stream<Object>, HTMLButtonElement) _configClearing(KbStm keydown) {
        final cDown = keydown.where((ev) => ev.code == "KeyC").asBroadcastStream();
        final cbtn = HTML.button()
            ..addFlicker(cDown)
            ..id = "clear-btn"
            ..innerText = "Clear LOBs [ C ]";
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
        ..appendChild(HTML.div(id: "lobs-cb-with-text", children: [
            HTML.span()..innerText = "Gathering LOBs [ G ]: ",
            _gatheringLobsCb
        ]));
    }

    @override
    @Mut(["ctx"])
    void draw(Cctx ctx, GridCC gridcc) {
        final lobs = _lobs.latestVal.values;

        void drawOne(LOB lob, {String color = "orange"}) {
            const arbitrarilyLargeLobLength = 1000;
            final dest = lob.source + Pos(
                GC(arbitrarilyLargeLobLength * lob.azimuth.cosresult),
                GC(arbitrarilyLargeLobLength * lob.azimuth.sinresult)
            );
            ctx.lineWidth = 2;
            ctx.strokeStyle = color.toJS;
            gridcc.drawLine(lob.source, dest, ctx);
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
    Azimuth.fromPositions(Pos p1pos, Pos txpos) {
        final xd = txpos.x.val - p1pos.x.val;
        final yd = txpos.y.val - p1pos.y.val;
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
    /// p1pob: Player 1 Position Observable
    Sim(Observable<Pos> p1pob, Pos txpos, Power txpower) {
        univLobs = 
            Stream<Null>.periodic(Duration(milliseconds: 50))
                .where((_) => _random.nextInt(5) == 0)
                .map((_) => _makelob(p1pob.latestVal, txpos, txpower))
                .asBroadcastStream();
    }

    LOB _makelob(Pos p1pos, Pos txpos, Power txpower) => (
        source: p1pos,
        azimuth: _noi(Azimuth.fromPositions(p1pos, txpos)),
        rxpow: _distLoss(p1pos, txpos, txpower),
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
    Power _distLoss(Pos p1pos, Pos txpos, Power txpower) {
        final xd = txpos.x.val - p1pos.x.val;
        final yd = txpos.y.val - p1pos.y.val;
        final dist = sqrt(xd * xd + yd * yd);
        return txpower * 0.1 * (1 / sq(dist)) * (_random.nextDouble() * 0.1 + 0.9);
    }
}

enum Mission { explore, tutorial, m1 }

Mission strToMission(String? missionName) { 
    for (final m in Mission.values) {
        if (m.name == missionName) {
            return m;
        }
    }
    print("Invalid mission name '$missionName'. Choices: ${Mission.values}. Defaulting to 'explore' mode.");
    return Mission.explore;
}


class MissionUI {
    final Mission mission;
    final Pos txpos;
    final _dialog = OkCancelDialog();

    MissionUI(String href, this.txpos) :
      mission = _parseMission(href);

    static Mission _parseMission(String href) {
        final uri = Uri.parse(href);
        return strToMission(uri.queryParameters["mission"]);
    }

    @Eff("window.open")
    HTMLElement disp() => 
        switch (mission) {
            Mission.explore =>  HTML.div(),
            Mission.tutorial => _form(),
            Mission.m1 => _form(),
        };
        
    static Result<(int, int), String> parseSubmission(String submission) {
        const errmsg = "You must enter two numbers separated by one space.\nExample: 12345 45678";
        
        /// If `val` is a list of exactly two integers, return them wrapped in `Success`.
        /// Else, return a Failure.
        Result<(int, int), String> twoInts(List<int?> val) => 
            switch (val) {
                [int easting, int northing] => Success((easting, northing)),
                _ => Failure(errmsg),
            };

        return submission
            .trim()
            .then((x) => succIf(x, x.length == 11, errmsg))
            .map((x) => x.split(" "))
            .map((x) => x.map(int.tryParse).toList())
            .map((x) => twoInts(x))
            .then((x) => flatten(x));
    }
    
    @Eff("window.open")
    void _handleSubmit(String submission) {
        final p = parseSubmission(submission);
        final msg = switch (p) { Success(val: final coords) => "you submitted $coords. Not sure if correct.", Failure(val: final errmsg) => "Error: $errmsg" };
        _dialog
            .showWith(msg)
            .then((response) {
                if (response) {
                    window.open("..", "_self");
                }
            });   
    }

    @Eff("window.open")
    HTMLFormElement _form() {
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
    /// The result of submitting the form
    HTMLElement dispResult() => _dialog.disp();
}

/// Previous name: attachElems()
HTMLElement assembleElems(CanvM cmLife, CanvM cmLob, PlayerHUD phud, LOBCol lobc, MissionUI mui, Zoom zoom, Messages msgs) {
    final cmLobHudWrapped = HTML.div(id: "hudwrap", children: [cmLob.disp()]);
    final cmLobAndAssociated = HTML.div(id: "cmlobparent", children: [
        cmLobHudWrapped,
        phud.disp(),
        lobc.dispInfo(),
        lobc.dispCtl(),
        mui.disp(),
        mui.dispResult(),
        zoom.disp(),
        msgs.dispenv(),
        msgs.dispoverlay(),
    ]);
    
    return HTML.div(children: [
        HTML.div(id: "two-canvasses", children: [cmLife.disp(), cmLobAndAssociated])
    ]);
}


class Zoom {
    late final Observable<double> scale;
    late final HTMLElement _dispElem;

    Zoom() {
        const initzoom = 1.0;
        final (elem, stm) = makePlusMinus();
        _dispElem = elem;
        scale = Observable(initzoom, makeScale(initzoom, stm));
    }

    /// Return a stream of the current zoom level.
    /// The stream `stm` controls the output stream:
    ///   `true` => zoom in by a factor of 2
    ///   `false` => zoom out by a factor of 2
    /// Example:
    ///  If initzoom = 1 and stm produces [true, false, false, true],
    /// then the output stream would be 1, 2, 1, 0.5, 1.
    static Stream<double> makeScale(double initzoom, Stream<bool> stm) {
        return stm.scan<double>(
            initzoom,
            (prev, zoomIn) => zoomIn ?
              prev * 2 :
              max(prev / 2, 0.005),
        );
    }

    HTMLElement disp() => _dispElem;
    
    static (HTMLElement, Stream<bool>) makePlusMinus() {
        final zoomintext = HTML.p()
            ..className = "fa-solid fa-magnifying-glass-plus fa-2x msgs-text";

        final zoomouttext = HTML.p()
            ..className = "fa-solid fa-magnifying-glass-minus fa-2x msgs-text";

        final zoomin = HTML.button()
            ..className = "game-btn"
            ..id = "zoomin"
            ..appendChild(zoomintext);

        final zoomout = HTML.button()
            ..className = "game-btn"
            ..id = "zoomout"
            ..appendChild(zoomouttext);

        final wrapperdiv = HTML.div()
            ..appendChild(zoomin)
            ..appendChild(zoomout);

        final inoutstm = combineInOut(zoomin.onClick, zoomout.onClick);
        return (wrapperdiv, inoutstm);
    }

    static Stream<bool> combineInOut(Stream<Object> instm, Stream<Object> outstm) {
        final t = instm.map((_) => true);
        final f = outstm.map((_) => false);
        return StreamGroup.merge([t, f]);
    }
}


/// A custom Mouse Event record for use with makeMouseMoveStm because I don't like how JS handles mouse events.
typedef MEv = ({bool isDown, num dx, num dy});

/// Given the mouseDown, mouseMove, and mouseUp streams from the browser,
/// return a stream of `MEv`. Example:
/// Mouse is not clicked. Mouse moves from 30, 90 to 35, 92.
/// This stream will contain (isdown: false, dx: 5, dy: 2).
/// Mouse is clicked. Mouse moves to 37, 100.
/// This stream will contain (isdown: true, dx: 2, dy: 8).
Stream<MEv> makeMouseMoveStm(Stream<MouseEvent> mouseDown, Stream<MouseEvent> mouseMove, Stream<MouseEvent> mouseUp) {
    final sc = StreamController<MEv>();
    ({num x, num y})? prev;
    var isDown = false;
    mouseDown.listen((e) {
        isDown = true;
        prev = (x: e.clientX, y: e.clientY);
    });
    mouseUp.listen((_) {
        isDown = false;
        prev = null;
    });
    mouseMove.listen((e) {
        final p = prev;
        // First move after down OR first ever move → no delta
        if (p == null) {
            prev = (x: e.clientX, y: e.clientY);
            return;
        }
        final dx = e.clientX - p.x;
        final dy = e.clientY - p.y;
        prev = (x: e.clientX, y: e.clientY);
        sc.add((isDown: isDown, dx: dx, dy: dy));
    });
    return sc.stream.asBroadcastStream();
}


class Pan {
    late final Observable<Pos> center;
    final resetBtn = HTML.button()..innerText = "ZR";

    Pan(Stream<MEv> mevStm, Observable<Pos> p1pob, Observable<double> scale) {
        final sc = StreamController<Pos>();
        final initCenter = p1pob.latestVal;
        var current = initCenter;
        mevStm.where((mev) => mev.isDown).listen((mev) {
            current += GridCC(scale.latestVal, current).gc(-mev.dx, mev.dy);
            sc.add(current);
        });

        center = Observable(initCenter, sc.stream);
    }

    // /// Recenter camera back to origin (player center handled by CanvM)
    // void recenter() {
    //     final zero = Pos(GC(0), GC(0));
    //     _offsetController.add(zero);
    // }
}

class Messages {
    var _incmsg = true;
    final _shown = StreamController<bool>(); 
    
    HTMLElement dispenv() {
        final messagetext = HTML.p()
            ..className = "fa-regular fa-2x msgs-text";

        final msgbutton = HTML.button()
            ..className = "game-btn msgs-position"
            ..appendChild(messagetext);

        if (_incmsg) {
            messagetext.classList.add("fa-envelope");
            msgbutton.classList.add("msgs-unread");
        } else {
            messagetext.classList.add("fa-envelope-open");
            msgbutton.classList.remove("msgs-unread");
        }
        msgbutton.onClick.listen((_) => _shown.add(true));
        return msgbutton;
        }
    
    HTMLElement dispoverlay() {
        final buttontext = HTML.p()
            ..className = "fa-solid fa-chevron-left fa-2x msgs-text";
        final overlay = HTML.div()
            ..id = "overlay"
            ..className = "hidden"
            ..appendChild(HTML.h2()
                ..innerText = "Messages")
            ..appendChild(HTML.button()
                ..className = "game-btn"
                ..id = "backbtn"
                ..appendChild(buttontext)
                ..onClick.listen((_) => _shown.add(false))
            );
        _shown.stream.listen((visible) {
            if (visible) {
                overlay.classList.remove("hidden");
            }
            else {
                overlay.classList.add("hidden");
            }
        });
        return overlay;
    }
}


@immutable
class Objs implements Drawable {
    final ImmuList<SimpleOb> _objs;

    Objs(this._objs);

    /// Create randomly-distributed bushes
    @Eff("http-req")
    @factory
    static Future<Objs> create() async {
        /// the top-left end of the random distribution 
        final (x, y) = (GC(69900), GC(39900));
        
        final random = Random();
        final bush1 = await imageload("../assets/bush_1.png");
        final bush2 = await imageload("../assets/bush_2.png");

        SimpleOb makebush() {
            final size = random.nextInt(6) * 5 + 20;
            final img = random.nextBool() ? bush1 : bush2;
            return SimpleOb(
                x + GC(random.nextDouble() * 200),
                y + GC(random.nextDouble() * 200),
                img,
                size,
            );
        }

        return Objs(ImmuList(
            [for (var i = 0; i < 2000; i++) makebush()]
            + [SimpleOb(GC(70000), GC(40000), bush1, 10),
               SimpleOb(GC(70005), GC(40000), bush1, 10),
               SimpleOb(GC(70010), GC(40000), bush1, 10)]
        ));
    }

    @override
    @Mut(["ctx"])
    void draw(Cctx ctx, GridCC gridcc) {
        for (final obj in _objs.values) {
            obj.draw(ctx, gridcc);
        }
    }
}


void main() async {
    final keydown = document.body!.onKeyDown;
    final keyup = document.body!.onKeyUp;
    final frameStm = makeFrameStm();
    final p1 = PlayerPos(Pos(GC(70012), GC(40008)), keydown, keyup, frameStm);
    final ph = PlayerHUD(p1.posStm);
    final t1 = await TxRadio.create();
    final sim = Sim(p1.posObs, t1.pos, t1.txpower);
    final bushes = await Objs.create();
    final avatarlife = await Avatar.create();
    final reticle = Reticle(p1.posObs);
    final zoom = Zoom();
    final grid = Grid(zoom.scale);
    final cmLife = CanvM("life", canvWidth, canvHeight, Observable(1, Stream.empty()), document.body!.onMouseUp);
    final cmLob = CanvM("hud", canvWidth, canvHeight, zoom.scale, document.body!.onMouseUp);
    final lobc = LOBCol(keydown, sim.univLobs, cmLob.click, p1.posObs, zoom.scale);
    final mui = MissionUI(window.location.href, t1.pos);
    final msg = Messages();
    final pan = Pan(cmLob.mevStm, p1.posObs, zoom.scale);
    cmLife.config(p1.posStm, [avatarlife, bushes, t1]);
    cmLob.config(p1.posStm, [lobc, grid, reticle], pan.center);
    document.getElementById("gameroot")!.replaceChildren(
        assembleElems(cmLife, cmLob, ph, lobc, mui, zoom, msg)
    ); 
}
