import numpy as np
from netCDF4 import Dataset

_MISSING_VALUE = 1e20


def _check(subgrid):
    if not subgrid in ("t", "u", "v"):
        raise ValueError(f'Invalid ORCA subgrid: "{subgrid}"')


_orca_names = {
    (362, 292, 75): "ORCA1L75",
    (360, 331, 75): "eORCA1L75",
}


class OrcaGrid:
    def __init__(self, domain_cfg, masks=None):

        self.domain_cfg = domain_cfg
        self.masks = masks

        with Dataset(domain_cfg) as nc:
            try:
                ni = nc.dimensions["x"].size
                nj = nc.dimensions["y"].size
                nk = nc.dimensions["z"].size
            except KeyError:
                raise RuntimeError("Missing dimensions in NEMO domain config")

            self.shape = (ni, nj)
            self.size = ni * nj

            try:
                self.name = _orca_names[(ni, nj, nk)]
            except KeyError:
                raise RuntimeError("Unknown dimensions in NEMO domain config")

            if not {
                "glamt",
                "glamu",
                "glamv",
                "glamf",
                "gphit",
                "gphiu",
                "gphiv",
                "gphif",
                "e1t",
                "e1u",
                "e1v",
                "e1f",
                "e2t",
                "e2u",
                "e2v",
                "e2f",
                "top_level",
            }.issubset(nc.variables):
                raise RuntimeError("Missing variables in NEMO domain config")

        if self.masks is not None:
            with Dataset(self.masks) as nc:
                if not {"tmaskutil", "umaskutil", "vmaskutil"}.issubset(nc.variables):
                    raise RuntimeError("Missing variables in NEMO masks file")

    def read_center_latitudes(self, subgrid):
        _check(subgrid)
        with Dataset(self.domain_cfg) as nc:
            return nc.variables[f"gphi{subgrid}"][0, ...].data.T

    def read_center_longitudes(self, subgrid):
        _check(subgrid)
        with Dataset(self.domain_cfg) as nc:
            return nc.variables[f"glam{subgrid}"][0, ...].data.T

    #   For the ORCA grid and staggered subgrids, see NEMO book
    #   Section "4 Space Domain (DOM)"
    #   Corner numbering used below:
    #       j
    #       ^  1 ------- 0
    #       |  |         |
    #       |  |         |
    #       |  |         |
    #       |  2 --------3
    #       +------------> i

    def read_corner_latitudes(self, subgrid):
        _check(subgrid)
        lat_var = {
            "t": "gphif",
            "u": "gphiv",
            "v": "gphiu",
        }
        with Dataset(self.domain_cfg) as nc:
            lat_values = nc.variables[lat_var[subgrid]][0, ...].data.T
        corner_lats = np.full((*self.shape, 4), _MISSING_VALUE)

        if subgrid in ("t"):
            corner_lats[:, :, 0] = lat_values
            corner_lats[1:, :, 1] = lat_values[:-1, :]
            corner_lats[0, :, 1] = lat_values[-1, :]
            corner_lats[:, 1:, 3] = lat_values[:, :-1]
            corner_lats[:, 0, 3] = 2 * lat_values[:, 1] - lat_values[:, 2]
            corner_lats[1:, 1:, 2] = lat_values[:-1, :-1]
            corner_lats[0, 1:, 2] = lat_values[-1, :-1]
            corner_lats[1:, 0, 2] = 2 * lat_values[:-1, 1] - lat_values[:-1, 2]
            corner_lats[0, 0, 2] = 2 * lat_values[-1, 1] - lat_values[-1, 2]
        elif subgrid == "u":
            corner_lats[:, :, 1] = lat_values
            corner_lats[:-1, :, 0] = lat_values[1:, :]
            corner_lats[-1, :, 0] = lat_values[0, :]
            corner_lats[:, 1:, 2] = lat_values[:, :-1]
            corner_lats[:, 0, 2] = 2 * lat_values[:, 1] - lat_values[:, 2]
            corner_lats[:-1, 1:, 3] = lat_values[1:, :-1]
            corner_lats[-1, 1:, 3] = lat_values[0, :-1]
            corner_lats[:-1, 0, 3] = 2 * lat_values[1:, 1] - lat_values[1:, 2]
            corner_lats[-1, 0, 3] = 2 * lat_values[0, 1] - lat_values[0, 2]
        elif subgrid == "v":
            # F-pivot special treatment
            rever_lats = lat_values[::-1, -1]
            corner_lats[:, :-1, 0] = lat_values[:, 1:]
            corner_lats[:-1, -1, 0] = rever_lats[1:]
            corner_lats[-1, -1, 0] = rever_lats[0]
            #
            corner_lats[1:, :-1, 1] = lat_values[:-1, 1:]
            corner_lats[0, :-1, 1] = lat_values[-1, 1:]
            corner_lats[:, -1, 1] = rever_lats[:]
            #
            corner_lats[1:, :, 2] = lat_values[:-1, :]
            corner_lats[0, :, 2] = lat_values[-1, :]
            #
            corner_lats[:, :, 3] = lat_values
        return corner_lats

    def read_corner_longitudes(self, subgrid):
        _check(subgrid)
        lon_var = {
            "t": "glamf",
            "u": "glamv",
            "v": "glamu",
        }
        with Dataset(self.domain_cfg) as nc:
            lon_values = nc.variables[lon_var[subgrid]][0, ...].data.T
        corner_lons = np.full((*self.shape, 4), _MISSING_VALUE)

        if subgrid in ("t"):
            corner_lons[:, :, 0] = lon_values
            corner_lons[1:, :, 1] = lon_values[:-1, :]
            corner_lons[0, :, 1] = lon_values[-1, :]
            corner_lons[:, 1:, 3] = lon_values[:, :-1]
            corner_lons[:, 0, 3] = lon_values[:, 1]
            corner_lons[1:, 1:, 2] = lon_values[:-1, :-1]
            corner_lons[0, 1:, 2] = lon_values[-1, :-1]
            corner_lons[1:, 0, 2] = lon_values[:-1, 1]
            corner_lons[0, 0, 2] = lon_values[-1, 1]
        elif subgrid == "u":
            corner_lons[:, :, 1] = lon_values
            corner_lons[:-1, :, 0] = lon_values[1:, :]
            corner_lons[-1, :, 0] = lon_values[0, :]
            corner_lons[:, 1:, 2] = lon_values[:, :-1]
            corner_lons[:, 0, 2] = lon_values[:, 1]
            corner_lons[:-1, 1:, 3] = lon_values[1:, :-1]
            corner_lons[-1, 1:, 3] = lon_values[0, :-1]
            corner_lons[:, 0, 3] = corner_lons[:, 1, 3]
        elif subgrid == "v":
            # F-pivot special treatment
            rever_lons = lon_values[::-1, -1]
            corner_lons[:, :-1, 0] = lon_values[:, 1:]
            corner_lons[:-1, -1, 0] = rever_lons[1:]
            corner_lons[-1, -1, 0] = rever_lons[0]
            #
            corner_lons[1:, :-1, 1] = lon_values[:-1, 1:]
            corner_lons[0, :-1, 1] = lon_values[-1, 1:]
            corner_lons[:, -1, 1] = rever_lons[:]
            #
            corner_lons[1:, :, 2] = lon_values[:-1, :]
            corner_lons[0, :, 2] = lon_values[-1, :]
            #
            corner_lons[:, :, 3] = lon_values
        return corner_lons

    def read_areas(self, subgrid):
        _check(subgrid)
        with Dataset(self.domain_cfg) as nc:
            return (
                nc.variables[f"e1{subgrid}"][0, ...].data.T
                * nc.variables[f"e2{subgrid}"][0, ...].data.T
            )

    def read_mask(self, subgrid):
        _check(subgrid)

        # If a NEMO mask file is provided, just read T, U, V masks
        if self.masks:
            with Dataset(self.masks) as nc:
                mask = np.where(
                    nc.variables[f"{subgrid}maskutil"][0, ...].data.T > 0, 0, 1
                )
                return mask

        # Without a NEMO mask file, compute masks from top_level in domain_cfg
        # See Section "4.3.6 level bathymetry and mask" in the NEMO book
        with Dataset(self.domain_cfg) as nc:
            tmask = np.where(nc.variables["top_level"][0, ...].data.T == 0, 1, 0)
            if subgrid == "t":
                return tmask
            elif subgrid == "u":
                umask = tmask * tmask.take(
                    range(1, tmask.shape[0] + 1), axis=0, mode="wrap"
                )
                return umask
            elif subgrid == "v":
                vmask = tmask * tmask.take(
                    range(1, tmask.shape[1] + 1), axis=1, mode="clip"
                )
                return vmask


class OrcaTGrid:
    def __init__(self, domain_cfg, masks=None):
        ogrid = OrcaGrid(domain_cfg=domain_cfg, masks=masks)
        self.name = ogrid.name
        self.shape = ogrid.shape
        self.size = ogrid.size
        self.center_latitudes = ogrid.read_center_latitudes(subgrid="t")
        self.center_longitudes = ogrid.read_center_longitudes(subgrid="t")
        self.corner_latitudes = ogrid.read_corner_latitudes(subgrid="t")
        self.corner_longitudes = ogrid.read_corner_longitudes(subgrid="t")
        self.areas = ogrid.read_areas(subgrid="t")
        self.mask = ogrid.read_mask(subgrid="t")


class OrcaUGrid:
    def __init__(self, domain_cfg, masks=None):
        ogrid = OrcaGrid(domain_cfg=domain_cfg, masks=masks)
        self.name = ogrid.name
        self.shape = ogrid.shape
        self.size = ogrid.size
        self.center_latitudes = ogrid.read_center_latitudes(subgrid="u")
        self.center_longitudes = ogrid.read_center_longitudes(subgrid="u")
        self.corner_latitudes = ogrid.read_corner_latitudes(subgrid="u")
        self.corner_longitudes = ogrid.read_corner_longitudes(subgrid="u")
        self.areas = ogrid.read_areas(subgrid="u")
        self.mask = ogrid.read_mask(subgrid="u")


class OrcaVGrid:
    def __init__(self, domain_cfg, masks=None):
        ogrid = OrcaGrid(domain_cfg=domain_cfg, masks=masks)
        self.name = ogrid.name
        self.shape = ogrid.shape
        self.size = ogrid.size
        self.center_latitudes = ogrid.read_center_latitudes(subgrid="v")
        self.center_longitudes = ogrid.read_center_longitudes(subgrid="v")
        self.corner_latitudes = ogrid.read_corner_latitudes(subgrid="v")
        self.corner_longitudes = ogrid.read_corner_longitudes(subgrid="v")
        self.areas = ogrid.read_areas(subgrid="v")
        self.mask = ogrid.read_mask(subgrid="v")
