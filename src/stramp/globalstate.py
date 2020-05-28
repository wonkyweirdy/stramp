from dataclasses import dataclass


@dataclass
class GlobalState:
    verbose: bool = False


_global_state = GlobalState()


def get_global_state():
    return _global_state
