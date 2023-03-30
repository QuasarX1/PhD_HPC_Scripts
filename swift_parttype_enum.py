from enum import Enum
import swiftsimio as sw

# Enum for particle type
class PartType(Enum):
    gas = 0
    dark_matter = 1
    star = 4

    def __str__(self):
        if self == PartType.gas:
            return "gas"
        elif self == PartType.dark_matter:
            return "dark_matter"
        elif self == PartType.gas:
            return "stars"
        else:
            raise RuntimeError()

    def get_dataset(self, particle_data: sw.SWIFTDataset):
        if self == PartType.gas:
            return particle_data.gas
        elif self == PartType.dark_matter:
            return particle_data.dark_matter
        elif self == PartType.gas:
            return particle_data.stars
        else:
            raise RuntimeError()