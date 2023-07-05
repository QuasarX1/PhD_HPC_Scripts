import swiftsimio
from unyt import unyt_quantity

def get_redshift(data: swiftsimio.SWIFTDataset):
    return data.metadata.z

def get_critical_gas_density(data: swiftsimio.SWIFTDataset, unit: str = None):
    v = unyt_quantity.from_astropy(data.metadata.cosmology.Ob(data.metadata.z) * data.metadata.cosmology.critical_density(data.metadata.z))
    if unit is not None:
        v = v.to(unit)
    return v
