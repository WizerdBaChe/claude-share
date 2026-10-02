"""Line probe for exercise.py -- loaded ONLY through PYTHONPATH when CC_PROBE_MAP is set.

Python imports `sitecustomize` at startup from the first sys.path entry that has
one, so putting this directory on PYTHONPATH loads it into the suite AND every
python child the suite spawns (the env is inherited). It records which of the
lines listed in CC_PROBE_MAP ({abs path: [line, ...]}) execute, and which of
those files ran any code at all (`file` records: the instruments the suite
touched), appending each first hit to CC_PROBE_OUT at once -- never at exit, so a child that leaves
through os._exit or a crash still reports what it ran.

Cost: sys.monitoring (PEP 669, Python 3.12+). PY_START fires once per code
object and is then DISABLEd; LINE events are switched on only in code objects
whose file holds a target line, and each line is DISABLEd after its first
event. Measured 2026-09-23 on the 51 live suites: no measurable overhead.

It must never change the traced program's behaviour: every failure is written
to CC_PROBE_OUT as an `error` record (so exercise.py can call that run
undetermined) and the program continues untraced. Without CC_PROBE_MAP it does
nothing at all.
"""
import os
import sys


def _install():
    out = os.environ.get("CC_PROBE_OUT")
    src = os.environ.get("CC_PROBE_MAP")
    if not (out and src):
        return

    def emit(line):
        try:
            with open(out, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except OSError:
            pass

    try:
        import json
        mon = sys.monitoring
        with open(src, encoding="utf-8") as fh:
            targets = {os.path.normcase(k): frozenset(v) for k, v in json.load(fh).items()}
        tool = next(i for i in (1, 3, 4, 5, 2, 0) if mon.get_tool(i) is None)
        mon.use_tool_id(tool, "class-closure-probe")
    except Exception as exc:  # no sys.monitoring, unreadable map, no free tool id
        emit(f"error\t{os.getpid()}\t{type(exc).__name__}: {exc}")
        return

    by_file = {}

    def lines_for(filename):
        got = by_file.get(filename)
        if got is None:
            got = targets.get(os.path.normcase(os.path.abspath(filename)), frozenset())
            by_file[filename] = got
        return got

    files_seen = set()

    def on_start(code, offset):
        if lines_for(code.co_filename):
            if code.co_filename not in files_seen:
                files_seen.add(code.co_filename)
                emit(f"file\t{os.path.normcase(os.path.abspath(code.co_filename))}")
            mon.set_local_events(tool, code, mon.events.LINE)
        return mon.DISABLE

    def on_line(code, line):
        if line in lines_for(code.co_filename):
            emit(f"hit\t{os.path.normcase(os.path.abspath(code.co_filename))}\t{line}")
        return mon.DISABLE

    mon.register_callback(tool, mon.events.PY_START, on_start)
    mon.register_callback(tool, mon.events.LINE, on_line)
    mon.set_events(tool, mon.events.PY_START)
    emit(f"start\t{os.getpid()}")


_install()
