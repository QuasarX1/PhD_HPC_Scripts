"""
File: velociraptor_particle_retrieval_extension.py

Author: Christopher Rowe
Vesion: 1.0.0
Date:   23/01/2023

Provides modification of velociraptor.particles.particles.VelociraptorGroups
and velociraptor.particles.particles.VelociraptorParticles designed for
efficient loading of multiple halos at once.

VelociraptorParticles_Multiselect's constructor takes file objects instead
of file paths.

VelociraptorGroups_Multiselect declares a new method extract_multiple_halos
that takes a list of indexes.

Public API:

    VelociraptorParticles_Multiselect (class)
    VelociraptorGroups_Multiselect (class)

Dependancies:

    h5py
    typing
    velociraptor
"""

import h5py
from typing import Union, Dict, List, Tuple
from velociraptor.particles.particles import VelociraptorGroups, VelociraptorParticles

class VelociraptorParticles_Multiselect(VelociraptorParticles):
    """
    Modification of velociraptor.particles.particles.VelociraptorParticles designed for efficient loading of multiple halos at once.

    Velociraptor particles object, holds information on a single
    halo's particles, including which IDs and particle types are
    in that halo. This provides extra post-processing options, such
    as splitting the IDs by particle type.
    """

    def __init__(self, particles_file, parttypes_file, offset: int, group_size: int, groups_instance: VelociraptorGroups):
        """
        Modification of velociraptor.particles.particles.VelociraptorParticles.__init__ designed fo efficient loading of multiple halos at once.

        Takes:

        + particles file, the file object representing the .catalog_particles file
        + parttype file, the file object representing the .catalog_parttypes file
        + offset, the offset from the .catalog_groups file
        + group_size, the size of the group in number of particles.
        + groups_instance, the associated groups instance
        """

        self.__particles_file = particles_file
        self.__parttypes_file = parttypes_file
        self.offset = offset
        self.group_size = group_size
        self.groups_instance = groups_instance

        self.__load_particles()
        self.__load_parttypes()

        return

    def __load_particles(self):
        """
        Modification of velociraptor.particles.particles.VelociraptorParticles.__load_particles designed for efficient loading of multiple halos at once.

        Load the information from the .catalog_particles file.
        """

        read_to_attribute = [
            "File_id",
            "Num_of_files",
            "Num_of_particles_in_groups",
            "Total_num_of_particles_in_all_groups",
        ]

        #with h5py.File(self.particles_filename, "r") as handle:
        handle = self.__particles_file
        for attribute in read_to_attribute:
            setattr(self, f"particle_{attribute.lower()}", handle[attribute][0])

        # Load only the particle ids that we actually need
        self.particle_ids = handle["Particle_IDs"][self.offset : self.offset + self.group_size]

    def __load_parttypes(self):
        """
        Modification of velociraptor.particles.particles.VelociraptorParticles.__load_parttypes designed for efficient loading of multiple halos at once.

        Load the information from the .catalog_parttypes file.
        """

        read_to_attribute = [
            "File_id",
            "Num_of_files",
            "Num_of_particles_in_groups",
            "Total_num_of_particles_in_all_groups",
        ]

        #with h5py.File(self.parttypes_filename, "r") as handle:
        handle = self.__parttypes_file
        for attribute in read_to_attribute:
            setattr(self, f"parttypes_{attribute.lower()}", handle[attribute][0])

        # Load only the particle ids that we actually need
        self.particle_types = handle["Particle_types"][self.offset : self.offset + self.group_size]

        __arr_particle_types = np.array(self.particle_types)
        #TODO: check the parttype numbers used for stars and BH
        self.parttype_filters = { "gas" : __arr_particle_types == 0, "dark_matter" : __arr_particle_types == 1, "star" : __arr_particle_types == 4, "black_hole" : __arr_particle_types == 5 }

        self.parttype_numbers = { key : self.parttype_filters[key].sum() for key in self.parttype_filters }

    def get_particle_ids(self, parttype: str = None):
        if parttype is None:
            return self.particle_ids
        else:
            return self.particle_ids[self.parttype_filters[parttype]]

class VelociraptorGroups_Multiselect(VelociraptorGroups):
    """
    Modification of velociraptor.particles.particles.VelociraptorGroups designed for efficient loading of multiple halos at once.

    Velociraptor particles object, holds information on a single
    halo's particles, including which IDs and particle types are
    in that halo. This provides extra post-processing options, such
    as splitting the IDs by particle type.
    """

    def extract_multiple_halos(self, halo_indexes: List[int], filenames: Union[Dict[str, str], None] = None) -> List[Tuple[VelociraptorParticles_Multiselect, VelociraptorParticles_Multiselect]]:
        """
        Modification of velociraptor.particles.particles.VelociraptorGroups.extract_halo designed for efficient loading of multiple halos at once.

        Get multiple halo particles objects for given indexes into the catalogue (NOT the halo unique id).
        Filenames is either a dictionary with the following structure:

        {
            "particles_filename": "...",
            "parttypes_filename": "...",
            "unbound_particles_filename": "...",
            "unbound_parttypes_filename": "...",
        }

        or None, in which case we guess what the filename should be from the filename of the groups that has already been passed.
        """

        if filenames is None:
            particles_filename = str(self.filename).replace(
                "catalog_groups", "catalog_particles"
            )
            parttypes_filename = str(self.filename).replace(
                "catalog_groups", "catalog_parttypes"
            )
            unbound_particles_filename = str(self.filename).replace(
                "catalog_groups", "catalog_particles.unbound"
            )
            unbound_parttypes_filename = str(self.filename).replace(
                "catalog_groups", "catalog_parttypes.unbound"
            )
        else:
            particles_filename = filenames["particles_filename"]
            parttypes_filename = filenames["parttypes_filename"]
            unbound_particles_filename = filenames["unbound_particles_filename"]
            unbound_parttypes_filename = filenames["unbound_parttypes_filename"]

        particles_file = h5py.File(particles_filename)
        parttypes_file = h5py.File(parttypes_filename)
        unbound_particles_file = h5py.File(unbound_particles_filename)
        unbound_parttypes_file = h5py.File(unbound_parttypes_filename)

        result = []

        try:
            for halo_index in halo_indexes:

                if halo_index == self.offset.size - 1:  # last halo in catalog
                    #with h5py.File(particles_filename) as particles_file:
                    total_particles = particles_file["Total_num_of_particles_in_all_groups"][0]
                    number_of_particles = total_particles - self.offset[halo_index]
                    #with h5py.File(unbound_particles_filename) as unbound_particles_file:
                    total_unbound_particles = unbound_particles_file["Total_num_of_particles_in_all_groups"][0]
                    number_of_unbound_particles = total_unbound_particles - self.offset_unbound[halo_index]
                else:
                    number_of_particles = self.offset[halo_index + 1] - self.offset[halo_index]
                    number_of_unbound_particles = self.offset_unbound[halo_index + 1] - self.offset_unbound[halo_index]
                    
                assert (number_of_particles + number_of_unbound_particles == self.group_size[halo_index],
                        "Something is incorrect in the calculation of group sizes for halo {}. Group_Size: {}, Bound: {}, Unbound: {}".format(
                            halo_index,
                            self.group_size[halo_index],
                            number_of_particles,
                            number_of_unbound_particles,
                        )
                       )

                particles = VelociraptorParticles_Multiselect(particles_file =  particles_file,
                                                              parttypes_file =  parttypes_file,
                                                              offset =          self.offset[halo_index],
                                                              group_size =      number_of_particles,
                                                              groups_instance = self)

                unbound_particles = VelociraptorParticles_Multiselect(particles_file =  unbound_particles_file,
                                                                      parttypes_file =  unbound_parttypes_file,
                                                                      offset =          self.offset_unbound[halo_index],
                                                                      group_size =      number_of_unbound_particles,
                                                                      groups_instance = self)

                if self.catalogue is not None:
                    particles.register_halo_attributes(self.catalogue, halo_index)
                    unbound_particles.register_halo_attributes(self.catalogue, halo_index)

                result.append((particles, unbound_particles))

        finally:
            particles_file.close()
            unbound_particles_file.close()

        return result
            



import swiftsimio
import numpy as np

from velociraptor.particles.particles import VelociraptorParticles

from typing import Union, Tuple

from collections import namedtuple






def generate_spatial_mask(particles_list: Union[List[VelociraptorParticles], VelociraptorParticles], snapshot_filename) -> swiftsimio.mask:
    """
    Determines the mask defining the spatial region containing
    the particles of interest.

    This uses `r_max` to define the extent of the region, so you
    will need to instantiate the VelociraptorParticles instance
    with an associated catalogue to use this feature, as it requires
    the knowledge of `r_max`.

    Takes two arguments:

    + particles, the VelociraptorParticles instance,
    + snapshot_filename, the path to the associated SWIFT snapshot.

    It returns:

    + mask, an object containing masks for all available datasets in the
            swift dataset.
    """

    if isinstance(particles_list, VelociraptorParticles):
        particles_list = [particles_list]

    # First use the swiftsimio spatial masking to constrain our dataset
    # to only contain particles within the cube that contains the halo
    # (this is only approximate down to the swift cell size)
    swift_mask = swiftsimio.mask(snapshot_filename, spatial_only=True)

    # SWIFT data is stored in comoving units, so we need to un-correct
    # the velociraptor data if it is stored in physical.
    try:
        if not particles_list[0].groups_instance.catalogue.units.comoving:
            length_factor = particles_list[0].groups_instance.catalogue.units.a
        else:
            length_factor = 1.0
    except AttributeError:
        raise RuntimeError(
            "Please use a particles instance with an associated halo " "catalogue."
        )

    max_size = max([particles.r_size for particles in particles_list])

    spatial_mask = [
        [
            min([particles.x for particles in particles_list]) / length_factor - max_size / length_factor,
            max([particles.x for particles in particles_list]) / length_factor + max_size / length_factor,
        ],
        [
            min([particles.y for particles in particles_list]) / length_factor - max_size / length_factor,
            max([particles.y for particles in particles_list]) / length_factor + max_size / length_factor,
        ],
        [
            min([particles.z for particles in particles_list]) / length_factor - max_size / length_factor,
            max([particles.z for particles in particles_list]) / length_factor + max_size / length_factor,
        ],
    ]

    swift_mask.constrain_spatial(spatial_mask)

    return swift_mask


def generate_bound_mask(data: swiftsimio.reader.SWIFTDataset, particles: VelociraptorParticles, particle_types: Union[List[str], None] = None) -> namedtuple:
    """
    Determines the mask defining the particles bound to the object
    of interest.

    Takes two arguments:

    + data, a SWIFTDataset, which may be spatially masked,
    + particles, the VelociraptorParticles instance.

    It returns:

    + mask, an object containing masks for all available datasets in the
            swift dataset.
    """
    # Now we must generate the secondary mask, for all available
    # particle types.

    particle_name_masks = {}

    selection_particle_types = particle_types if particle_types is not None else data.metadata.present_particle_names

    for particle_name in selection_particle_types:
        # This will change if we ever take advantage of the
        # parttypes available through velociraptor.
        particle_name_masks[particle_name] = np.in1d(
            getattr(data, particle_name).particle_ids, particles.particle_ids
        )

    # Finally we generate a named tuple with the correct fields and
    # fill it with the contents of our dictionary
    MaskTuple = namedtuple("MaskCollection", selection_particle_types)
    mask = MaskTuple(**particle_name_masks)

    return mask

def from_swiftsimio_dataset(data: swiftsimio.reader.SWIFTDataset,
                            particles_list: Union[List[VelociraptorParticles], VelociraptorParticles],
                            particle_types: Union[List[str], None] = None
                           ) -> List[namedtuple]:
    if isinstance(particles_list, VelociraptorParticles):
        return generate_bound_mask(data, particles_list, particle_types)
    else:
        return [generate_bound_mask(data, particles_object, particle_types) for particles_object in particles_list]

def to_swiftsimio_dataset(particles_list: List[VelociraptorParticles], snapshot_filename, generate_extra_mask: bool = False, particle_types: Union[List[str], None] = None, use_spatial_mask = True) -> Union[
    swiftsimio.reader.SWIFTDataset, Tuple[swiftsimio.reader.SWIFTDataset, namedtuple]
]:
    """
    Loads multiple VelociraptorParticles instances for each halo into a
    `swiftsimio` masked dataset.

    Initially, this uses `r_max` to perform a spatial mask, and
    then returns the `swiftsimio` dataset and a secondary mask
    that may be used to extract only the particles that are
    part of the FoF group.

    You will need to instantiate the VelociraptorParticles instance
    with an associated catalogue to use this feature, as it requires
    the knowledge of `r_max`.

    Takes three arguments:

    + particles_list, list of the VelociraptorParticles instances,
    + snapshot_filename, the path to the associated SWIFT snapshot.
    + generate_extra_mask, whether or not to generate the secondary
                           mask object that allows for the extraction
                           of particles that are present only in the
                           FoF group.

    It returns:

    + data,  the swiftsimio dataset
    + masks, a list of objects containing masks for all available datasets in the
             swift dataset. The initial masking is performed on a
             spatial only basis, and this is required to only extract
             the particles in the FoF group as identified by
             velociraptor. This is only provided if generate_extra_mask
             has a truthy value.
    """

    swift_mask = None
    if use_spatial_mask:
        swift_mask = generate_spatial_mask(particles_list, snapshot_filename)

    data = swiftsimio.load(snapshot_filename, mask = swift_mask)

    if not generate_extra_mask:
        return data

    masks = from_swiftsimio_dataset(data, particles_list, particle_types)

    return data, masks
