import 'dart:async';
import 'dart:js_interop';
import 'package:web/web.dart';
import 'custom.dart' show Mut;


extension Flickerable on HTMLElement {
    /// Adds "button-active" to the classList, and then removes it 100 ms later.
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


Stream<Duration> makeFrameStm() {
    final timeDiffSC = StreamController<Duration>();
    runEachFrame((Duration tdelta) => timeDiffSC.add(tdelta));
    return timeDiffSC.stream.asBroadcastStream();
}