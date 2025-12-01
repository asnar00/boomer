# testbed/metering/spectrum

from . import spectrum

def register_all(register_fn):
    register_fn('spectrum', spectrum)
