import monocle
from monocle import _o
from monocle.experimental import Channel
from monocle.stack import eventloop


@_o
def main():
    s = 2
    ch = Channel(s)
    for i in range(s):
        print(i)
        yield ch.send(i)

    print(ch.bufsize, len(ch._msgs))
    for i in range(s):
        print((yield ch.recv()))
    print("done")


monocle.launch(main)
eventloop.run()
