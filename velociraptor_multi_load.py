import velociraptor as vr
import os
import glob
from typing import Union, List, Callable
from unyt import unyt_array
import numpy as np
import h5py

class Multifile_VR_Catalogue_Query(object):
    def __init__(self, parent):
        self.__parent = parent
        self.__path_items = []

    def copy(self):
        new_object =  Multifile_VR_Catalogue_Query(self.__parent)
        new_object.__path_items = self.__path_items.copy()
        return new_object

    def __getattr__(self, name):
        new_object = self.copy()
        new_object.__path_items.append(name)
        return new_object

    @property
    def parent(self):
        return self.__parent

    @property
    def value(self) -> Union[str, unyt_array]:
        if len(self.__path_items) == 0:
            #raise RuntimeError("Unable to retrive values from an empty query.")
            return str(self.__parent._catalogues[0])
        
        states = self.__parent._catalogues.copy()
        for state_index in range(len(states)):
            for name in self.__path_items:
                states[state_index] = getattr(states[state_index], name)

        try:
            unit = states[0].units
        except:
            return np.concatenate(states, axis = 0)
        return unyt_array(np.concatenate(states, axis = 0), unit)

class Multifile_VR_Catalogue(object):
    def __init__(self, catalogue_folder: str, filename_without_extension: str, specific_file_indexes: Union[List[int], None] = None, disregard_units: bool = False, registration_file_path: Union[List[str], str, None] = None, mask: Union[slice, None] = None):
        if not os.path.isdir(catalogue_folder):
            raise ValueError(f"catalogue_folder specified is not an existing folder ({catalogue_folder}).")
        
        self.__file_pattern_base = os.path.join(catalogue_folder, filename_without_extension)
        
        file_patern = f"{self.__file_pattern_base}.properties.*"
        self.__properties_files = glob.glob(file_patern)
        if specific_file_indexes is not None:
            self.__properties_files = [file for i, file in enumerate(self.__properties_files) if i in specific_file_indexes]
            self.__file_indexes = specific_file_indexes
        else:
            self.__file_indexes = [int(file.split(".")[-1]) for file in self.__properties_files]
        self.__n_files = len(self.__properties_files)

        if self.__n_files == 0:
            raise FileNotFoundError(f"No catalogue files were found that match the specified pattern ({file_patern}).")
        
        if mask == None:
            mask = [Ellipsis for _ in range(self.__n_files)]

        self.__vr_catalogues = [vr.load(self.__properties_files[i], disregard_units, registration_file_path, mask[i]) for i in range(self.__n_files)]

        self.__large_data_cache = None

    def __getattr__(self, name):
        query = Multifile_VR_Catalogue_Query(self)
        query = getattr(query, name)
        return query
    
    def __len__(self):
        return self.__n_files
    
    def __create_multi_file_paths(self, template_file):
        return [f"{template_file}.{i}" for i in self.__file_indexes]
    
    @property
    def _catalogues(self):
        return self.__vr_catalogues
    
    @property
    def catalog_SOlist_filepaths(self) -> List[str]:
        return self.__create_multi_file_paths(f"{self.__file_pattern_base}.catalog_SOlist")
    
    @property
    def catalog_groups_filepaths(self) -> List[str]:
        return self.__create_multi_file_paths(f"{self.__file_pattern_base}.catalog_groups")
    
    @property
    def bound_catalog_particles_filepaths(self) -> List[str]:
        return self.__create_multi_file_paths(f"{self.__file_pattern_base}.catalog_particles")
    
    @property
    def unbound_catalog_particles_filepaths(self) -> List[str]:
        return self.__create_multi_file_paths(f"{self.__file_pattern_base}.catalog_particles.unbound")
    
    @property
    def bound_catalog_parttypes_filepaths(self) -> List[str]:
        return self.__create_multi_file_paths(f"{self.__file_pattern_base}.catalog_parttypes")
    
    @property
    def unbound_catalog_parttypes_filepaths(self) -> List[str]:
        return self.__create_multi_file_paths(f"{self.__file_pattern_base}.catalog_parttypes.unbound")
    
    @property
    def configuration_filepath(self) -> str:
        return f"{self.__file_pattern_base}.configuration"
    
    @property
    def hierarchy_filepaths(self) -> List[str]:
        return self.__create_multi_file_paths(f"{self.__file_pattern_base}.hierarchy")
    
    @property
    def profiles_filepaths(self) -> List[str]:
        return self.__create_multi_file_paths(f"{self.__file_pattern_base}.profiles")
    
    @property
    def properties_filepaths(self) -> List[str]:
        return self.__properties_files
    
    @property
    def siminfo_filepath(self) -> str:
        return f"{self.__file_pattern_base}.siminfo"
    
    @property
    def units_filepath(self) -> str:
        return f"{self.__file_pattern_base}.units"
    
    def _get_paths_from_filetype(self, type_extension):
        if type_extension == "catalog_SOlist":
            return self.catalog_SOlist_filepaths
        elif type_extension == "catalog_groups":
            return self.catalog_groups_filepaths
        elif type_extension == "catalog_particles":
            return self.bound_catalog_particles_filepaths
        elif type_extension == "catalog_particles.unbound":
            return self.unbound_catalog_particles_filepaths
        elif type_extension == "catalog_parttypes":
            return self.bound_catalog_parttypes_filepaths
        elif type_extension == "catalog_parttypes.unbound":
            return self.unbound_catalog_parttypes_filepaths
        elif type_extension == "configuration":
            return [self.configuration_filepath]
        elif type_extension == "hierarchy":
            return self.hierarchy_filepaths
        elif type_extension == "profiles":
            return self.profiles_filepaths
        elif type_extension == "properties":
            return self.properties_filepaths
        elif type_extension == "siminfo":
            return self.siminfo_filepath
        elif type_extension == "units":
            return self.units_filepath
        else:
            raise ValueError()#TODO:

    def read_raw_file_data(self, filepaths: Union[List[str], str], operations: Union[List[Callable], Callable]):
        """
        Paramiter "filepaths" provided as a single string value will lookup the appropriate file paths for the common extension provided.

        func(h5py.File) -> numpy.ndarray | unyt.unyt_array
        """
        if not isinstance(operations, list):
            operations = [operations]

        results = [[] for _ in range(len(operations))]

        for filepath in self._get_paths_from_filetype(filepaths) if isinstance(filepaths, str) else filepaths:
            with h5py.File(filepath, "r") as file:
                for i, func in enumerate(operations):
                    results[i].append(func(file))
            
        return_list = []
        for i in range(len(operations)):
            return_array = results[i][0]
            for result in results[i][1:]:
                return_array = np.append(return_array, result, axis = 0)
            return_list.append(return_array)

        return return_list if len(return_list) != 1 else return_list[0]
    
    def halo_properties_by_particle(self, fields: Union[List[str], str], parttype: int = None, use_cache = True, write_cache = True, overwrite_cache = False):
        if isinstance(fields, str):
            fields = [fields]

        if self.__large_data_cache is not None and not overwrite_cache:
            all_fields_present = True
            new_fields = []
            for field in fields:
                if field in self.__large_data_cache:
                    all_fields_present = False
                    if field not in ("particle_ids", "parttypes", "ids.id"):
                        new_fields.append(field)
        else:
            all_fields_present = False
            new_fields = [field for field in fields if field not in ("particle_ids", "parttypes", "ids.id")]
        
        result_data = None
        
        if use_cache and self.__large_data_cache is not None and all_fields_present:
            result_data = self.__large_data_cache

        else:
#            halo_ids = np.array(self.ids.id.value, dtype = np.int64)
            halo_ids = self.ids.id.value.value
#            halo_masses = np.array(self.masses.mass_200crit.value.to("Msun"), dtype = np.float64)
            field_halo_data = []
            for field in new_fields:
                data = self
                for section in field.split("."):
                    data = getattr(data, section)
                #field_halo_data.append(dict(zip(halo_ids, data.value)))
                field_halo_data.append(data.value)
            

            
            # Open the catalogue particles files and read data
            bound_particle_ids, bound_particle_number_by_file = self.read_raw_file_data("catalog_particles",
                [lambda file: np.array(file["Particle_IDs"], dtype = np.int64),
                lambda file: np.array([file["Num_of_particles_in_groups"][0]], dtype = np.int64)])
            unbound_particle_ids, unbound_particle_number_by_file = self.read_raw_file_data("catalog_particles.unbound",
                [lambda file: np.array(file["Particle_IDs"], dtype = np.int64),
                lambda file: np.array([file["Num_of_particles_in_groups"][0]], dtype = np.int64)])

            # Open the catalogue particle types files and read data
            bound_parttypes = self.read_raw_file_data("catalog_parttypes",
                                                    lambda file: np.array(file["Particle_types"], dtype = np.int16))
            unbound_parttypes = self.read_raw_file_data("catalog_parttypes.unbound",
                                                        lambda file: np.array(file["Particle_types"], dtype = np.int16))
            
            # Open the catalogue groups file and read data
            n_halos_by_file, parent_halo_ids, offsets__bound, offsets__unbound, group_size = self.read_raw_file_data("catalog_groups",
                [lambda file: np.array([file["Num_of_groups"][0]], dtype = np.int64),
                lambda file: np.array(file["Parent_halo_ID"], dtype = np.int64),
                lambda file: np.array(file["Offset"], dtype = np.int64),
                lambda file: np.array(file["Offset_unbound"], dtype = np.int64),
                lambda file: np.array(file["Group_Size"], dtype = np.int64)])
            
            # Process data from the groups files to act like its data from one big file
            n_halos = n_halos_by_file.sum()

            modified_offset_haloes = 0
            next_offset_boost_bound = 0
            next_offset_boost_unbound = 0
            for file_index, n_halos_in_file in enumerate(n_halos_by_file):
                data_slice = slice(modified_offset_haloes, modified_offset_haloes + n_halos_in_file)

                offsets__bound[data_slice] = offsets__bound[data_slice] + next_offset_boost_bound
                offsets__unbound[data_slice] = offsets__unbound[data_slice] + next_offset_boost_unbound

                modified_offset_haloes += n_halos_in_file
                
                next_offset_boost_bound += bound_particle_number_by_file[file_index]
                next_offset_boost_unbound += unbound_particle_number_by_file[file_index]



            # The final storage array contains both bound and unbound particles - calculate the offsets for each halo from the group_size data
            storage_offsets = np.zeros(n_halos, dtype = np.int64)
            storage_offsets[1:] = np.cumsum(group_size[:-1])

            # Only the offsets are stored for the bound/unbound files - compute the number of particles for each halo in each file
            halo_read_lengths__bound = np.zeros(offsets__bound.shape, dtype = np.int64)
            halo_read_lengths__bound[:-1] = offsets__bound[1:] - offsets__bound[:-1]
            halo_read_lengths__bound[-1] = bound_particle_ids.shape[0] - offsets__bound[-1]
            
            halo_read_lengths__unbound = np.zeros(offsets__unbound.shape, dtype = np.int64)
            halo_read_lengths__unbound[:-1] = offsets__unbound[1:] - offsets__unbound[:-1]
            halo_read_lengths__unbound[-1] = unbound_particle_ids.shape[0] - offsets__unbound[-1]
            


            # Create arrays to store the (unfiltered) data
            all_halo_particles__particle_ids = np.empty(group_size.sum(), dtype = np.int64)
            all_halo_particles__particle_types = np.empty(all_halo_particles__particle_ids.shape, dtype = np.int64)
            all_halo_particles__halo_ids = np.empty(all_halo_particles__particle_ids.shape, dtype = np.int64)
            all_halo_particles__field_halo_data = []
            for raw_dataset in field_halo_data:
                #all_halo_particles__field_halo_data.append(unyt_array(np.empty(all_halo_particles__particle_ids.shape, dtype = np.float64), list(raw_dataset.values())[0].units))
                all_halo_particles__field_halo_data.append(unyt_array(np.empty(all_halo_particles__particle_ids.shape, dtype = np.float64), raw_dataset.units))
#            halo_masses = np.empty(all_halo_particles__particle_ids.shape, dtype = np.float64)

            

            # Read in the data for each halo
            for halo_index in range(n_halos):            
                all_halo_particles__particle_ids[
                    storage_offsets[halo_index] : storage_offsets[halo_index] + halo_read_lengths__bound[halo_index]
                ] = bound_particle_ids[
                    offsets__bound[halo_index] : offsets__bound[halo_index] + halo_read_lengths__bound[halo_index]
                ]

                all_halo_particles__particle_ids[
                    storage_offsets[halo_index] + halo_read_lengths__bound[halo_index] : storage_offsets[halo_index] + halo_read_lengths__bound[halo_index] + halo_read_lengths__unbound[halo_index]
                ] = unbound_particle_ids[
                    offsets__unbound[halo_index] : offsets__unbound[halo_index] + halo_read_lengths__unbound[halo_index]
                ]

                all_halo_particles__particle_types[
                    storage_offsets[halo_index] : storage_offsets[halo_index] + halo_read_lengths__bound[halo_index]
                ] = bound_parttypes[
                    offsets__bound[halo_index] : offsets__bound[halo_index] + halo_read_lengths__bound[halo_index]
                ]

                all_halo_particles__particle_types[
                    storage_offsets[halo_index] + halo_read_lengths__bound[halo_index] : storage_offsets[halo_index] + halo_read_lengths__bound[halo_index] + halo_read_lengths__unbound[halo_index]
                ] = unbound_parttypes[
                    offsets__unbound[halo_index] : offsets__unbound[halo_index] + halo_read_lengths__unbound[halo_index]
                ]

                all_halo_particles__halo_ids[storage_offsets[halo_index] : storage_offsets[halo_index] + group_size[halo_index]] = halo_ids[halo_index]

                for i, field_data in enumerate(field_halo_data):
                    all_halo_particles__field_halo_data[i][storage_offsets[halo_index] : storage_offsets[halo_index] + group_size[halo_index]] = field_data[halo_index]

#                halo_masses[storage_offsets[halo_index] : storage_offsets[halo_index] + group_size[halo_index]] = actual_halo_id_to_mass[mass_tracking_ids[halo_index]]

            result_data = { "particle_ids": all_halo_particles__particle_ids,
                            "parttypes": all_halo_particles__particle_types,
                            "ids.id": all_halo_particles__halo_ids }

            for i in range(len(new_fields)):
                result_data[new_fields[i]] = all_halo_particles__field_halo_data[i]

            if self.__large_data_cache is not None and write_cache and not overwrite_cache:
                for field in result_data:
                    if field not in self.__large_data_cache:
                        self.__large_data_cache[field] = result_data[field]
                result_data = self.__large_data_cache
            elif (self.__large_data_cache is None and write_cache) or overwrite_cache:
                self.__large_data_cache = result_data

        return_data = {}
        for key in result_data:
            return_data[key] = result_data[key].copy()

        if parttype is not None:
            # Filter all read data to get only particles of a specific type
            halo_parttype_particles__filter = np.array(return_data["parttypes"], dtype = np.int64) == parttype

            for key in return_data:
                return_data[key] = return_data[key][halo_parttype_particles__filter]

        return { key: return_data[key] for key in return_data if key in (*fields, "particle_ids", "parttypes") }

















        
