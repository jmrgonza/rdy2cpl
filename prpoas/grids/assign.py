import logging
from collections import namedtuple

from prpoas.grids.base.simple import GridA, GridB
from prpoas.grids.couple import CoupleGrid

_log = logging.getLogger(__name__)

_bgf = namedtuple(
    "BaseGridFactory",
    "type, args, kwargs, mask_mod",
    defaults=(
        {},
        [],
    ),
)

_map = {
    "IOCL": _bgf(GridB, (180, 90)),
    "ILCL": _bgf(GridB, (181, 91)),
    "RNFA": _bgf(GridB, (90, 45)),
    "NOUM": _bgf(GridA, (54, 18)),
    "NOVM": _bgf(GridA, (55, 19)),
    "NOTM": _bgf(GridA, (56, 18)),
}


def couple_grid(name):
    try:
        base_grid = _map[name].type(*_map[name].args, **_map[name].kwargs)
    except KeyError:
        _log.error(f'Grid id "{name}" not found in the assign map')
        raise
    for mm in _map[name].mask_mod or []:
        base_grid.mask = mm(base_grid.mask)
    return CoupleGrid(base_grid, name)