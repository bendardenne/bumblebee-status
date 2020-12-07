# pylint: disable=C0111,R0903

"""Displays the current color temperature of redshift

Requires the following executable:
    * redshift

Parameters:
    * redshift.location : location provider, either of "geoclue2" (default), \
"ipinfo" (requires the requests package), or "manual"
    * redshift.lat : latitude if location is set to "manual"
    * redshift.lon : longitude if location is set to "manual"
"""

import threading
try:
    import requests
except ImportError:
    pass

import bumblebee.input
import bumblebee.output
import bumblebee.engine


def is_terminated():
    for thread in threading.enumerate():
        if thread.name == "MainThread" and not thread.is_alive():
            return True
    return False


def get_redshift_value(widget):
    while True:
        if is_terminated():
            return
        widget.get("condition").acquire()
        while True:
            try:
                widget.get("condition").wait(1)
            except RuntimeError:
                continue
            break
        widget.get("condition").release()

        with open("/tmp/redshift") as res:
            for line in res:
                line = line.strip()
                if "Status" in line:
                    widget.set("status", line.split(" ")[1].lower())
                if "Color temperature" in line:
                    widget.set("temp", line.split(" ")[2])

class Module(bumblebee.engine.Module):
    def __init__(self, engine, config):
        widget = bumblebee.output.Widget(full_text=self.text)
        super(Module, self).__init__(engine, config, widget)

        self._text = ""
        self._condition = threading.Condition()
        widget.set("condition", self._condition)
        self._thread = threading.Thread(target=get_redshift_value,
                                        args=[widget])
        self._thread.start()
        self._condition.acquire()
        self._condition.notify()
        self._condition.release()

    def text(self, widget):
        return "{}".format(self._text)

    def update(self, widgets):
        widget = widgets[0]
        self._condition.acquire()
        self._condition.notify()
        self._condition.release()
        temp = widget.get("temp", "n/a")
        self._text = temp
        transition = widget.get("transition", None)
        #if transition:
            #self._text = "{} {}".format(temp, transition)
            #self._text = "{}".format(temp)


    def state(self, widget):
        return [widget.get("status", None), widget.get("period", None)]

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
