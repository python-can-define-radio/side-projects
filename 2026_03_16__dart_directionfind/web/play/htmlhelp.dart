import 'package:web/web.dart';
import './ag1.dart' show Mut;


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