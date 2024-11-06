# from nullsourcenullsink import nullsourcenullsink
import multiprocessing as mp
import time
from gnuradio import gr
from basicsourcesinkwater import basicsourcesinkwater
from grc_main_prep import grc_main_prep


def event_loop(top_block_cls: gr.top_block, q: mp.Queue) -> None:
    """Used to run the Qt/GR process."""
    qapp = grc_main_prep(top_block_cls)
    while True:
        cmd = q.get(block=True)
        if cmd == "quit":
            print("Quitting!")
            break
        elif cmd == "exec":
            print("exec...")
            qapp.exec_()
            print("this will probably never run")
        else:
            print(cmd)

class ParallelGRC:
    def __init__(self, top_block_cls: gr.top_block) -> None:
        self.q = mp.Queue()
        self.proc = mp.Process(
            target=lambda: event_loop(top_block_cls, self.q)
        )

    def grc_run(self) -> None:
        self.proc.start()

    def putcmd(self, cmd):
        self.q.put(cmd)


pgrc = ParallelGRC(basicsourcesinkwater)
pgrc.grc_run()
pgrc.putcmd("hi")
time.sleep(0.5)
pgrc.putcmd("blah")
pgrc.putcmd("exec")
pgrc.putcmd("quit")
