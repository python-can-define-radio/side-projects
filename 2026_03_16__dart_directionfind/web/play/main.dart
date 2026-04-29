/// LOBSTER Game.
library;


/// TODO  2026 April 29 12:43 :
/// TODO  I am going to bring back the 
/// TODO  player position Observable in the places where it is currently commented.
/// TODO  Initially, I was thinking it should be avoided so that all data is passed using streams,
/// TODO  but I think the use is valid and won't cause negative effects.

import 'dart:js_interop';
import 'package:web/web.dart';
import 'dart:async';
import 'dart:math';
import 'package:async/async.dart' hide Result;
import 'package:meta/meta.dart';
import './ag1.dart';



const canvWidth = 600;
const canvHeight = 400;


typedef Cctx = CanvasRenderingContext2D;
typedef KbStm = ElementStream<KeyboardEvent>;
typedef DuStm = Stream<Duration>;


num sq(num x) => x * x;




extension Flickerable on HTMLElement {
    /// Temporarily adds "button-active" to the classList.
    /// Debugging note: this assumes that...
    /// - the element still exists after `milliseconds`
    /// - nothing else is adding/removing the "button-active" class
    @Mut(["this.classList"])
    void addFlicker(Stream<Object> stm, [int milliseconds = 100]) {
        stm.listen((_) {
            classList.add("button-active");
            Future.delayed(Duration(milliseconds: milliseconds), () => classList.remove("button-active"));
        });
    }
}


/// Methods for creating HTML elems
class HTML {
    static HTMLButtonElement button() =>
            document.createElement('button') as HTMLButtonElement;
    static HTMLCanvasElement canvas() =>
            document.createElement('canvas') as HTMLCanvasElement;
    static HTMLDialogElement dialog() =>
            document.createElement('dialog') as HTMLDialogElement;
    static HTMLDivElement div() =>
            document.createElement('div') as HTMLDivElement;
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
    static const _gridMB = 22;
    /// Zoom scale. Example: scale = 0.5 would be zoomed out by a factor of 2.
    final double _scale;
    final Pos _center;
    GridCC(this._scale, this._center);
    
    /// Returns (x, y) in canvas units
    (double, double) cu(Pos p) => (
        p.x.val * _gridMB * _scale,
        p.y.val * _gridMB * _scale,
    );

    /// Given a position (which uses Grid Coordinates),
    /// - converts to canvas units
    /// - shifts based on `_center` and the size of the canvas
    /// Returns a pair that is suitable for canvas draw functions.
    ({double left, double top}) lefttop(Pos p) {
        final (xcu, ycu) = cu(p);
        final (xcentcu, ycentcu) = cu(_center);
        /// Notice that the vertical formula is inverted 
        /// because canvases use down as positive y direction
        return (
            left: xcu - xcentcu + canvWidth / 2,
            top: ycentcu - ycu + canvHeight / 2,
        );
    }

    /// Fill rectangle, but `p` specifies the center, not the top-left corner.
    @Mut(["ctx"])
    void fillRectCent(Pos p, num wcu, num hcu, Cctx ctx) {
        final (:left, :top) = lefttop(p);
        ctx.fillRect(left - wcu/2, top - hcu/2, wcu, hcu);
    }

    /// `p` specifies the center, not the top-left corner.
    @Mut(["ctx"])
    void drawImage(Pos p, HTMLImageElement img, num wcu, num hcu, Cctx ctx) {
        final (:left, :top) = lefttop(p);
        ctx.drawImage(img, left - wcu/2, top - hcu/2, wcu, hcu);
    }
}

/// Grid Coordinates
@immutable
class GC {
    final double val;
    GC(this.val);
    GC operator +(GC other) => GC(val + other.val);
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

    PlayerPos(Pos initPos, KbStm keydown, KbStm keyup, DuStm tdelta) :
        posStm = _makePosStm(initPos, keydown, keyup, tdelta) {
        posObs = Observable(initPos, posStm);
    }
        
    static Stream<Pos> _makePosStm(Pos initPos, KbStm keydown, KbStm keyup, DuStm tdelta) {
        const speedMetersPerSecond = 2.0;
        final speed = _makeSpeed(speedMetersPerSecond * 0.001, keydown, keyup);
        final dirx = _makeDirx(keydown, keyup);
        final diry = _makeDiry(keydown, keyup);
        final x = _makeX(initPos.x, dirx, tdelta, speed);
        final y = _makeY(initPos.y, diry, tdelta, speed);
        return StreamZip<GC>([x, y])
            .map((xypair) => Pos(xypair[0], xypair[1]))
            .asBroadcastStream();
    }

    static Stream<GC> _makeX(GC initX, Observable<double> dirx, DuStm tdelta, Observable<double> speed) async* {
        var curX = initX;
        await for(final tdeltaVal in tdelta) {
            final change = dirx.latestVal * speed.latestVal * tdeltaVal.inMilliseconds;
            curX = GC(curX.val + change);
            yield curX;
        }
    }

    static Stream<GC> _makeY(GC initY, Observable<double> diry, DuStm tdelta, Observable<double> speed) async* {
        var curY = initY;
        await for(final tdeltaVal in tdelta) {
            final change = diry.latestVal * speed.latestVal * tdeltaVal.inMilliseconds;
            curY = GC(curY.val + change);
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
        _posStm.listen((pos) =>
            posEl.innerText =
                "grid: 55P DE ${pos.x.val.toStringAsFixed(0)} ${pos.y.val.toStringAsFixed(0)}"
        );
        return posEl;
    }
}

class Avatar implements Drawable {
    final HTMLImageElement _avatarSheet;
    final int _horizFrames = 4;
    final int _vertFrames = 4;
    double _curFrame = 0;

    Avatar(this._avatarSheet);

    @Eff("http-req")
    @factory
    static Future<Avatar> create() async { 
        return Avatar(await imageload("../assets/avatar_sheet.png"));
    }

    @Mut(["ctx"])
    void _drawSlice(Cctx ctx, int xidx, int yidx, num xpos, num ypos, num size) {
        final fw = _avatarSheet.width / _horizFrames;
        final fh = _avatarSheet.height / _vertFrames;
        ctx.drawImage(_avatarSheet,
            xidx * fw, yidx * fh, fw, fh,
            xpos, ypos, size, size);
    }

    @override
    @Mut(["this._curFrame", "ctx"])
    void draw(Cctx ctx, GridCC _) {
        const cenx = canvWidth / 2;
        const ceny = canvHeight / 2;
        final avsize = 50;
        _drawSlice(ctx, _curFrame.floor(), 0, cenx - avsize / 2, ceny - avsize / 2, avsize);
        _curFrame = (_curFrame + 0.1) % _horizFrames;
    }
}

class Reticle implements Drawable {
    final String color;
    Reticle(this.color);

    @override
    void draw(Cctx ctx, GridCC _) {
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

// void fillRectRel(
//     num x,
//     num y,
//     num w,
//     num h,
//     Cctx ctx,
//     Pos relpos,
// ) {
//     ctx.fillRect(
//         x - relpos.xcu + canvWidth / 2,
//         y - relpos.ycu + canvHeight / 2,
//         w,
//         h,
//     );
// }

// void moveToRel(num x, num y, Cctx ctx, Pos relpos) {
//     ctx.moveTo(x - relpos.xcu + canvWidth / 2, y - relpos.ycu + canvHeight / 2);
// }

// void lineToRel(num x, num y, Cctx ctx, Pos relpos) {
//     ctx.lineTo(x - relpos.xcu + canvWidth / 2, y - relpos.ycu + canvHeight / 2);
// }

// void fillTextRel(String text, num x, num y, Cctx ctx, Pos relpos) {
//     ctx.fillText(text, x - relpos.xcu + canvWidth / 2, y - relpos.ycu + canvHeight / 2);
// }

void fillCircle(num x, num y, num radius, Cctx ctx) {
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, 2 * pi);
    ctx.fill();
}

// void fillCircleRel(
//     num x,
//     num y,
//     num radius,
//     Cctx ctx,
//     Pos relpos,
// ) {
//     fillCircle(
//         x - relpos.xcu + canvWidth / 2,
//         y - relpos.ycu + canvHeight / 2,
//         radius,
//         ctx,
//     );
// }


class CanvM {
    final HTMLCanvasElement _canv = HTML.canvas();
    late final Cctx _ctx;
    late final ImmuList<Drawable> _drawItems;
    late final Stream<MouseEvent> click = _canv.onClick;
    double _scale;

    CanvM(String cssid, int w, int h, this._scale) {
        _canv
            ..width = w
            ..height = h
            ..id = cssid;
        _ctx = _canv.getContext('2d') as Cctx;
    }
    
    /// Basically 'constructor part two'. Had to separate to avoid
    /// a circular dependency.
    void config(Stream<Pos> posStm, List<Drawable> drawItems) {
        _drawItems = ImmuList(drawItems);
        posStm.listen(_frameUpdate);
    }
    
    HTMLCanvasElement disp() => _canv;

    void _frameUpdate(Pos center) {
        final gridcc = GridCC(_scale, center);
        _ctx.clearRect(0, 0, _canv.width, _canv.height);
        for (final item in _drawItems.values) {
            item.draw(_ctx, gridcc);
        }
    }
}

class Grid implements Drawable {
    @override
    void draw(Cctx ctx, GridCC gridcc) {

        /// TODO
        // /// Space between gridlines in meters
        // final gridUnitSpc = 5;
        // /// Space between gridlines in canvas units
        // final gridSpacing = 22 * gridUnitSpc;
        // /// this is an empirical guess. Eventually we should use a monospace
        // /// font and fetch the width of it if possible.
        // const charWidth = 6;
        // /// see note on charWidth
        // const charHeight = 3;
        // /// center to x edge, in grid units
        // const ctoxeg = 0.7 * canvWidth / 22;
        // /// center to y edge, in grid units
        // const ctoyeg = 0.7 * canvHeight / 22;

        // double toGrid(double v) => (v / gridUnitSpc).floorToDouble() * gridUnitSpc;

        // ctx.strokeStyle = "#ccc".toJS;
        // ctx.fillStyle = "#ccc".toJS;
        // ctx.lineWidth = 0.5;
        
        // final startx = Pos.xgridToCU(toGrid(center.xgrid - ctoxeg));
        // final starty = Pos.ygridToCU(toGrid(center.ygrid + ctoyeg));

        // for (var x = startx; x <= startx + 1.5*canvWidth; x += gridSpacing) {
        //     ctx.beginPath();
        //     moveToRel(x, center.ycu + canvHeight, ctx, center);
        //     lineToRel(x, center.ycu - canvHeight, ctx, center);
        //     ctx.stroke();
        //     final gridVal = Pos.xCUToGrid(x).toString().substring(3);
        //     fillTextRel(
        //         gridVal,
        //         x - charWidth,
        //         center.ycu - (canvHeight/2) + 10,
        //         ctx,
        //         center
        //     );
        // }

        // for (var y = starty; y <= starty + 1.5*canvHeight; y += gridSpacing) {
        //     ctx.beginPath();
        //     moveToRel(center.xcu + canvWidth, y, ctx, center);
        //     lineToRel(center.xcu - canvWidth, y, ctx, center);
        //     ctx.stroke();
        //     final gridVal = Pos.yCUToGrid(y).toString().substring(3);
        //     fillTextRel(
        //         gridVal,
        //         center.xcu - (canvWidth/2),
        //         y + charHeight,
        //         ctx,
        //         center
        //     );
        // }
    }
}


class TxRadio implements Drawable {
    final pos = Pos(GC(70008), GC(40012));
    final txpower = Power(mW: 100);
    
    @override
    void draw(Cctx ctx, GridCC gridcc) {
        ctx.fillStyle = "#00f".toJS;
        gridcc.fillRectCent(pos, 10, 10, ctx);
    }
}


Stream<Duration> makeFrameStm() {
    final timeDiffSC = StreamController<Duration>();
    runEachFrame((Duration tdelta) => timeDiffSC.add(tdelta));
    return timeDiffSC.stream.asBroadcastStream();
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

    LOBCol(KbStm keydown, Stream<LOB> univLobs, Stream<MouseEvent> canvclick, Stream<Pos> p1pos) {
        /// TODO
        // _gatheringLobsCb = _configGath(keydown);
        // final (clear, cbtn) = _configClearing(keydown);
        // _clearBtn = cbtn;
        // final filtlobs = univLobs.where((_) => _gatheringLobsCb.checked);
        // _lobsStm = _makeLobStream(clear, filtlobs);
        // _lobs = Observable(ImmuList([]), _lobsStm);
        // _sellob = _configChosenLOB(_lobs, canvclick, p1pos);
    }

    static Observable<LOB?> _configChosenLOB(Observable<ImmuList<LOB>> lobs, Stream<MouseEvent> canvclick, Stream<Pos> p1pos) {
        final sc = StreamController<LOB?>();
        /// TODO
        // canvclick.listen((ev) {
        //     final chosen = decideClosest(lobs.latestVal, p1.pos, ev);
        //     if (chosen != null) {
        //         print("I am the selected lob");
        //     }
        //     sc.add(chosen);
        // });
        return Observable(null, sc.stream);
    }
    
    static LOB? decideClosest(ImmuList<LOB> immulobs, Pos p1pos, MouseEvent ev) {
        final lobs = immulobs.values;
        /// TODO
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
        /// TODO
        // _lobsStm.listen((lobs) => lobPowEl.innerText = _fmtpow(lobs.values.lastOrNull));
        return lobPowEl;
    }

    HTMLDivElement dispCtl() {
    return HTML.div();
    /// TODO
        // ..appendChild(_clearBtn..className = "game-btn")
        // ..appendChild(HTML.div()..id = "lobs-cb-with-text"
        //     ..appendChild(HTML.span()..innerText = "Gathering LOBs [ g ]: ")
        //     ..appendChild(_gatheringLobsCb)
        // );
    }

    @override
    void draw(Cctx ctx, GridCC gridcc) {
        /// TODO
        // final lobs = _lobs.latestVal.values;

        // void drawOne(LOB lob, {String color = "orange"}) {
        //     const loblength = 10000;
        //     final endx = lob.source.xcu + loblength * lob.azimuth.cosresult;
        //     final endy = lob.source.ycu + loblength * lob.azimuth.sinresult;
        //     ctx.beginPath();
        //     ctx.lineWidth = 2;
        //     ctx.strokeStyle = color.toJS;
        //     moveToRel(lob.source.xcu, lob.source.ycu, ctx, center);
        //     lineToRel(endx, endy, ctx, center);
        //     ctx.stroke();
        // }

        // for (final lob in withoutLast(lobs)) {
        //     drawOne(lob);
        // }
        // lobs.lastOrNull?.then((lob) => drawOne(lob, color: "red"));
        // _sellob.latestVal?.then((lob) => drawOne(lob, color: "blue"));
    }
}


class Azimuth {
    late final double sinresult;
    late final double cosresult;
    /// Given the player (receiver) position and the transmitter position
    /// compute the azimuth from the player's perspective.
    Azimuth.fromPositions(Pos p1pos, TxRadio t) {
        final xd = t.pos.x.val - p1pos.x.val;
        final yd = t.pos.y.val - p1pos.y.val;
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
    Sim(Stream<Pos> p1pos, TxRadio t1) {
        /// TODO
        /// TEMP FIX:
        univLobs = Stream<LOB>.empty();
        // univLobs = 
        //     Stream<Null>.periodic(Duration(milliseconds: 50))
        //         .where((_) => _random.nextInt(5) == 0)
        //         .map((_) => _makelob(p1, t1))
        //         .asBroadcastStream();
    }

    /// TODO
    // LOB _makelob(Player p1, TxRadio t1) => (
    //     source: p1.pos,
    //     azimuth: _noi(Azimuth.fromPositions(p1, t1)),
    //     rxpow: _distLoss(t1, p1),
    // );

    /// add random noise. Need to figure out whether this is typical distribution
    Azimuth _noi(Azimuth a) {
        p3(double x) => x * x * x;
        return Azimuth.fromSinCos(
            a.sinresult + 0.003 * p3(6 * (_random.nextDouble() - 0.5)),
            a.cosresult + 0.003 * p3(6 * (_random.nextDouble() - 0.5)),
        );
    }

    /// TODO
    /// A very rudimentary path loss computation
    // Power _distLoss(TxRadio t, Player p1) {
    //     final xd = t.pos.x.val - p1.pos.x.val;
    //     final yd = t.pos.y.val - p1.pos.y.val;
    //     final dist = sqrt(xd * xd + yd * yd);
    //     return t.txpower * 0.1 * (1 / sq(dist)) * (_random.nextDouble() * 0.1 + 0.9);
    // }
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

Result<T, String> succIf<T>(T val, bool cond, String errmsg) {
    if (cond) {
        return Success(val);
    } else {
        return Failure(errmsg);
    }
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

void attachElems(HTMLElement root, PlayerHUD phud, LOBCol lobc, CanvM cmLife, CanvM cmLob, MissionUI mui, Zoom zoom, Messages msgs){
    root..id = "root"
        ..appendChild(HTML.div()..id = "two-canvasses"
            ..appendChild(cmLife.disp())
            ..appendChild(HTML.div()..id = "cmlobparent"
                ..style.position = "relative"
                ..appendChild(HTML.div()..id = "hudwrap"
                    ..appendChild(cmLob.disp())) 
                ..appendChild(phud.disp())
                ..appendChild(lobc.dispInfo())
                ..appendChild(lobc.dispCtl())
                ..appendChild(mui.disp())
                ..appendChild(mui.dispResult())
                ..appendChild(zoom.disp())
                ..appendChild(msgs.dispenv())
                ..appendChild(msgs.dispoverlay())
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
class Zoom {
    HTMLElement disp() {
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

        return HTML.div()
            ..appendChild(zoomin)
            ..appendChild(zoomout);
    }
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
    final p1 = PlayerPos(Pos(GC(70005), GC(40008)), keydown, keyup, frameStm);
    final ph = PlayerHUD(p1.posStm);
    final t1 = TxRadio();
    final sim = Sim(p1.posStm, t1);
    final bushes = await Objs.create();
    final grid = Grid();
    final avatarlife = await Avatar.create();
    final reticle = Reticle("#fff");
    final cmLife = CanvM("life", canvWidth, canvHeight, 1);
    final cmLob = CanvM("hud", canvWidth, canvHeight, .5);
    final lobc = LOBCol(keydown, sim.univLobs, cmLob.click, p1.posStm);
    final mui = MissionUI(window.location.href, t1.pos);
    final msg = Messages();
    final zoom = Zoom();
    cmLife.config(p1.posStm, [avatarlife, bushes, t1]);
    cmLob.config(p1.posStm, [lobc, grid, reticle]);
    attachElems(document.body!, ph, lobc, cmLife, cmLob, mui, zoom, msg); 
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

Next steps 

- Mission 1:
     In game, commander says something like this:
       "The adversary's scouts are watching in force.
       To avoid capture, stay behind the FLOT -- don't go any further North than grid 40100 northing.
       Once you have determined the transmitter's grid location to within 3 meters, send it to me using
       your tablet's grid coordinate submission form."
  
- Option in HUD to switch between separate map or overlay
    - implementation: have a variable that gets set to the proper canvas
- Add a full tutorial to introduce UI, controls, and have them submit a grid coordinate (no constraints in the tutorial; they can walk right up to the transmitter)
- finish Zoom in/out on LOB view (functionality)
- add reflections, refractions etc.
- elevation
- selected lob not showing
- Add a compass. We need to discuss different execution possibilities.
  - G N with a vertical line?
  - magnetic north too? 
- pushing shift + up + right does not move diagonally if i press up + right first it moves diagonally but will not run when shift is pressed




- Art:
  - Source: One of...
    - find licensed-for-our-use
    - create some pixel art
    - find a student who is interested
    - tell PapaB to stop shamming (ha)
  - Needed assets:
    - sooner:
      - Avatar we used a 1024 x 1024 spritesheet would be good if that didnt have to change
      - transmitter

    - slightly less soon:
      - Multiple avatar choices
      - Avatar frames for walking in four different directions
      - Avatar frames for running in four different directions
      - tree
      - building


      https://opengameart.org/content/bush
      https://opengameart.org/content/bush-0
      https://opengameart.org/content/hero-0
*/
