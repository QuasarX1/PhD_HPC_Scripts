"""
File: img_data.py

Author: Christopher Rowe
Vesion: alpha_0.3.3
Date:   01/11/2022

Creates an image file from 2D or 3D data.
Supports both rendered image projections or graphed outputs.



Commandline arguments & flags (r = required paramiter, f = optional flag,
                               f+ = optional flag with a required argument):

    (f ) --help               || -h --> Display this docstring.

    (f ) --verbose            || -v --> Display progression infomation.

    (f ) --debug              || -d --> Display debug infomation.

    (f ) --3D                 || -3 --> Data format is 3D (default assumes 2D).

    (f+) --data_mask          || -m --> Sequence of 0's and 1's to identify which
                                            columns should be used (1's are True).
                                            A single use of the character c may be
                                            used to indicate a column is to
                                            indicate the colour of the data points.

    (f ) --all_axes_spatial   || -s --> All axes are spatial data
                                            and have the same scale/magnitude.

    ( r) --output_file        || -o --> Name (or relitive file path) to store
                                            the resulting image.

    (f+) --3D_projection_axis || -p --> Axis along which to project 3D images for
                                            a single projection (no --graph flag).
                                            Use either 'x', 'y' or 'z'.

    (f+) --brightness         || -b --> Scale the brightness of pixels in images
                                            (no --graph flag) using various functions.
                                            Values between 0 and 4 (see below)
                                            (default assumes 0).

    (f+) --image_size         || -r --> Size of each image dimension in pixels
                                            (no --graph flag) (default is 1000).

    (f ) --graph              || -g --> Make image a graph
                                            (uses matplotlib.pyplot).

    (f+) --2D_line_graph      || -l --> Data (2D only) should be plotted as a
                                            line graph (use with --graph flag).

    (f+) --graph_title        || -t --> Graph title (use with --graph flag).

    (f+) --graph_x_axis       || -x --> Axis label for x axis
                                            (use with --graph flag).

    (f+) --graph_y_axis       || -y --> Axis label for y axis
                                            (use with --graph flag).

    (f+) --graph_point_colour || -c --> Colour value for graph points.
                                            Format is either "#RGB", "#RGBA",
                                            "#RRGGBB", "#RRGGBBAA" or the column index
                                            within the data.

    (f+) --graph_args               --> Arguments to be passed to matplotlib
                                            (use with --graph flag).
                                            Must be the final flag. All following
                                            flags will be parsed as kwargs and
                                            should not procede any args.



Brightness Setting:

    The brightness of rendered images may be configured using the -b flag.

          Value | Description
    (default) 0 | Pixels overlapping the projection of any datapoint's area will have
                |     a value of 255.
              1 | As with 4, but applies sqrt(n) to the pixel values before scaling
                |     between 0 and 255.
              2 | As with 1, but uses the average of sqrt(n) and ln(n+1).
              3 | As with 1, but uses the ln(n+1).
              4 | Pixel brightness will be set linearly with the number of encountered
                |     projected data points.



Dependancies:

    argparse
    csv
    cuda-python (optional *)
    json
    matplotlib
    math
    mpi4py (optional **)
    numpy as np
    os
    pickle
    PIL (pillow) (optional * or **)
    sys
    traceback

    *  For use on a NVIDIA GPU with an avalible CUDA driver installed.

    ** For use in an HPC facility with MPI avalible.
       Start script using "mpiexec -np <x> python img_data.py <params>"
                       OR "mpirun -np <x> python img_data.py <params>".
       <x> MUST be a factor of the length of the dataset.



Example Usage:

    python img_data.py data.csv -o test.png -g -l
    python img_data.py data.csv -o output_file.png -g --graph_args -s 0.1 -c red
"""



from argparse import ArgumentError
import csv
import json
from math import ceil
from matplotlib import pyplot as plt
import numpy as np
import os
import pickle
import sys
import traceback

__CUDA_AVALIBLE = False
try:
    from cuda_factory import CUDA_Kernel
    __CUDA_AVALIBLE = True
except: pass

__PIL_AVALIBLE = False
try:
    import PIL
    __PIL_AVALIBLE = True
except: pass

__MPI_AVALIBLE = False
try:
    from mpi4py import MPI
    __MPI_AVALIBLE = True
except: pass

class __Settings(object):
    VERBOSE_ENABLED = False
    DEBUG_ENABLED = False
    CUDA_THREADS_PER_BLOCK = 512
    MPI_COMM = None
    MPI_RANK = None



__print_custom_newline_spaces = "                "
def __print_custom_newline_format(s):
    return s.replace("\n", f"\n{__print_custom_newline_spaces}")

def print_info(firstValue = "", *args, **kwargs):
    mpi_rank_insert = f" ({__Settings.MPI_RANK})" if __MPI_AVALIBLE else ""
    print(f"--|| INFO ||--{mpi_rank_insert}  {__print_custom_newline_format(firstValue)}", *[__print_custom_newline_format(arg) for arg in args], **kwargs)

def print_verbose_info(firstValue = "", *args, **kwargs):
    if __Settings.VERBOSE_ENABLED:
        print_info(firstValue, *args, **kwargs)

def print_warning(firstValue = "", *args, **kwargs):
    mpi_rank_insert = f" ({__Settings.MPI_RANK})" if __MPI_AVALIBLE else ""
    print(f"--¿¿ WARN ??--{mpi_rank_insert}  {__print_custom_newline_format(firstValue)}", *[__print_custom_newline_format(arg) for arg in args], **kwargs)

def print_verbose_warning(firstValue = "", *args, **kwargs):
    if __Settings.VERBOSE_ENABLED:
        print_warning(firstValue, *args, **kwargs)

def print_error(firstValue = "", *args, **kwargs):
    mpi_rank_insert = f" ({__Settings.MPI_RANK})" if __MPI_AVALIBLE else ""
    print(f"--!! ERRO !!--{mpi_rank_insert}  {__print_custom_newline_format(firstValue)}", *[__print_custom_newline_format(arg) for arg in args], **kwargs)

def print_verbose_error(firstValue = "", *args, **kwargs):
    if __Settings.VERBOSE_ENABLED:
        print_error(firstValue, *args, **kwargs)

def print_debug(firstValue = "", *args, **kwargs):
    if __Settings.DEBUG_ENABLED:
        mpi_rank_insert = f" ({__Settings.MPI_RANK})" if __MPI_AVALIBLE else ""
        print(f"--<< DEBG >>--{mpi_rank_insert}  {__print_custom_newline_format(firstValue)}", *[__print_custom_newline_format(arg) for arg in args], **kwargs)




def __MPI_make_2D_image_data_chunk_pixels(x_values, y_values, rgba_colours, min_x, max_x, min_y, max_y, data_length, pixel_side_length) -> np.ndarray:
    chunk_index = int(__Settings.MPI_RANK)
    n_chunks = int(__Settings.MPI_COMM.Get_size())
    pixel_index = int(pixel_index)
    x_values = np.array(x_values)
    y_values = np.array(y_values)
    min_x = float(min_x)
    max_x = float(max_x)
    min_y = float(min_y)
    max_y = float(max_y)
    data_length = int(data_length)
    pixel_side_length = int(pixel_side_length)

    W = max_x - min_x
    space_pixel_width_ratio = W / pixel_side_length

    k = np.sqrt(0.8 / float(data_length) / 3.1415926535)
    point_radius: float = W * k
    pixel_radius: int = ceil(pixel_side_length * k)

    image_pixels = np.zeros((pixel_side_length**2 * 4,))

    chunk_size = int(data_length / n_chunks)
    data_index_offset = chunk_index * chunk_size
    for i in range(data_index_offset, data_index_offset + chunk_size):
        point_x_offset = min_x - x_values[i]
        point_y_offset = min_y - y_values[i]

        for px_x in range(((x_values[i] - min_x) / space_pixel_width_ratio) - pixel_radius, ((x_values[i] - min_x) / space_pixel_width_ratio) + pixel_radius):
            for px_y in range(((y_values[i] - min_y) / space_pixel_width_ratio) - pixel_radius, ((y_values[i] - min_y) / space_pixel_width_ratio) + pixel_radius):
                if (point_x_offset + (W * px_x))**2 + (point_y_offset + (W * px_y))**2 <= point_radius:
                    alpha = rgba_colours[i * 4 + 3] / 255.0
                    image_pixels[(px_x + (pixel_side_length * px_y)) * 4] = alpha
                    image_pixels[(px_x + (pixel_side_length * px_y)) * 4 + 0] = rgba_colours[i * 4 + 1] * alpha
                    image_pixels[(px_x + (pixel_side_length * px_y)) * 4 + 1] = rgba_colours[i * 4 + 2] * alpha
                    image_pixels[(px_x + (pixel_side_length * px_y)) * 4 + 2] = rgba_colours[i * 4 + 3] * alpha

    return image_pixels

def __MPI_not_root_process_handeler():
    data_info_dict = None
    data_info_dict = __Settings.MPI_COMM.bcast(data_info_dict, root = 0)
    min_x = data_info_dict["min_x"]
    max_x = data_info_dict["max_x"]
    min_y = data_info_dict["min_y"]
    max_y = data_info_dict["max_y"]
    data_length = data_info_dict["data_length"]
    pixel_side_length = data_info_dict["pixel_side_length"]

    if float(data_length) / float(__Settings.MPI_COMM.Get_size()) != float(data_length // __Settings.MPI_COMM.Get_size()):
        raise AssertionError("The data avalible was not evenly divisable by the number of processes.")

    x_values = np.empty((data_length,), dtype = float)
    __Settings.MPI_COMM.Bcast(x_values, root = 0)
    y_values = np.empty((data_length,), dtype = float)
    __Settings.MPI_COMM.Bcast(y_values, root = 0)
    rgba_colours = np.empty((data_length * 4,), dtype = int)
    __Settings.MPI_COMM.Bcast(rgba_colours, root = 0)

    pixels = __MPI_make_2D_image_data_chunk_pixels(x_values, y_values, min_x, max_x, min_y, max_y, data_length, pixel_side_length)

    __Settings.MPI_COMM.Reduce(pixels, None, op = MPI.SUM, root = 0)

    print_verbose_info("MPI process exiting.")

def __NO_CUDA_make_2D_image_pixels(x_values, y_values, rgba_colours, min_x, max_x, min_y, max_y, data_length, pixel_side_length) -> np.ndarray:
    x_values = np.array(x_values, dtype = float)
    y_values = np.array(y_values, dtype = float)
    min_x = float(min_x)
    max_x = float(max_x)
    min_y = float(min_y)
    max_y = float(max_y)
    data_length = int(data_length)
    pixel_side_length = int(pixel_side_length)

    def calculate_pixel_value(pixel_index, x_values, y_values, rgba_colours, min_x, max_x, min_y, max_y, data_length, pixel_side_length) -> list:
        pixel_index = int(pixel_index)
        x_values = np.array(x_values)
        y_values = np.array(y_values)
        min_x = float(min_x)
        max_x = float(max_x)
        min_y = float(min_y)
        max_y = float(max_y)
        data_length = int(data_length)
        pixel_side_length = int(pixel_side_length)
        
        if pixel_index >= pixel_side_length**2: return None

        point_radius: float = (max_x - min_x) * np.sqrt(0.8 / float(data_length) / 3.1415926535)

        pixel_x: int = int(pixel_index / pixel_side_length)
        pixel_y: int = pixel_index % pixel_side_length

        value_x: float = min_x + (pixel_x * (max_x - min_x) / float(pixel_side_length))
        value_y: float = min_y + (pixel_y * (max_y - min_y) / float(pixel_side_length))

        pixel_hit_count: float = 0.0
        pixel_R: float = 0.0
        pixel_G: float = 0.0
        pixel_B: float = 0.0

        for i in range(data_length):
            if (np.sqrt(((value_x - x_values[i]) * (value_x - x_values[i])) + ((value_y - y_values[i]) * (value_y - y_values[i]))) <= point_radius):
                alpha = rgba_colours[i * 4 + 3] / 255.0
                pixel_hit_count += alpha
                pixel_R += rgba_colours[i * 4] * alpha
                pixel_G += rgba_colours[i * 4 + 1] * alpha
                pixel_B += rgba_colours[i * 4 + 2] * alpha

        return [pixel_hit_count, pixel_R, pixel_G, pixel_B]

    if not __MPI_AVALIBLE:
        image_pixels = np.empty((pixel_side_length**2 * 4,), dtype = float)

        for i in range(pixel_side_length**2):
            image_pixels[i * 4: i * 4 + 4] = calculate_pixel_value(i,
                                                                   x_values,
                                                                   y_values,
                                                                   rgba_colours,
                                                                   min_x,
                                                                   max_x,
                                                                   min_y,
                                                                   max_y,
                                                                   len(x_values),
                                                                   pixel_side_length)
        
    else:
        # MPI on the root process
        # chunk_index = __Settings.MPI_RANK
        # n_chunks = __Settings.MPI_COMM.Get_size()

        # Distribute the data
        data_info_dict = __Settings.MPI_COMM.bcast({ "min_x": min_x,
                                                     "max_x": max_x,
                                                     "min_y": min_y,
                                                     "max_y": max_y,
                                                     "data_length": data_length,
                                                     "pixel_side_length": pixel_side_length },
                                                    root = 0)

        # Now the length of the data has been passed to all processes, check if the number of processes is appropriate and error if not (all processes should check this!)
        if float(data_length) / float(__Settings.MPI_COMM.Get_size()) != float(data_length // __Settings.MPI_COMM.Get_size()):
            raise AssertionError("The data avalible was not evenly divisable by the number of processes.")

        __Settings.MPI_COMM.Bcast(x_values, root = 0)
        __Settings.MPI_COMM.Bcast(y_values, root = 0)
        __Settings.MPI_COMM.Bcast(rgba_colours, root = 0)
        
        # Run own chunk
        pixels = __MPI_make_2D_image_data_chunk_pixels(x_values, y_values, rgba_colours, min_x, max_x, min_y, max_y, data_length, pixel_side_length)

        # Gather and combine pixel data
        image_pixels = np.zeros((pixel_side_length**2,))
        __Settings.MPI_COMM.Reduce(pixels, image_pixels, op = MPI.SUM, root = 0)

    return image_pixels

def __CUDA_make_2D_image_pixels(x_values, y_values, rgba_colours, min_x, max_x, min_y, max_y, data_length, pixel_side_length):
    render_function = """
    extern "C" __global__
    void render_function(float *x, float *y, int *colour, float x_min, float x_max, float y_min, float y_max, int data_length, int pixel_side_length, float *out)
    {
        size_t tid = blockIdx.x * blockDim.x + threadIdx.x;

        if (tid < pow(pixel_side_length, 2.0))// if the thread is for a pixel that exists within the image
        {
            //float point_radius = (x_max - x_min) * 0.0005f;
            float point_radius = (x_max - x_min) * sqrt(0.8f / (float)data_length / 3.1415926535f);

            //if (tid == 0) { printf("%d    (%f, %f) -> %f [%d]\\n", tid, cx, cy, r, side_length); }

            float pixel_x = (int)(tid / pixel_side_length);
            float pixel_y = tid % pixel_side_length;

            float value_x = x_min + (pixel_x * (x_max - x_min) / (float)pixel_side_length);
            float value_y = y_min + (pixel_y * (y_max - y_min) / (float)pixel_side_length);

            float pixel_hits = 0;
            float pixel_r = 0;
            float pixel_g = 0;
            float pixel_b = 0;

            int i;
            for (i = 0; i < data_length; ++i)
            {
                if (sqrt(((value_x - x[i]) * (value_x - x[i])) + ((value_y - y[i]) * (value_y - y[i]))) <= point_radius)
                {
                    int *pixel_colour = colour + (i * 4);
                    int alpha = (float)pixel_colour[3] / 255.0f;
                    pixel_hits += alpha;//                       ALPHA channel
                    pixel_r += (float)pixel_colour[0] * alpha;// RED
                    pixel_g += (float)pixel_colour[1] * alpha;// GREEN
                    pixel_b += (float)pixel_colour[2] * alpha;// BLUE
                }
            }

            out[tid * 4] = pixel_hits;
            out[tid * 4 + 1] = pixel_r;
            out[tid * 4 + 2] = pixel_g;
            out[tid * 4 + 3] = pixel_b;
        }
    }
    """
    render = CUDA_Kernel(render_function, 
                         "render_function",
                         [np.float32, np.float32, np.int32, np.float32, np.float32, np.float32, np.float32, np.int32, np.int32, np.float32],
                         [data_length, data_length, data_length * 4, 1, 1, 1, 1, 1, 1, pixel_side_length**2 * 4],
                         [9])

    render.threads_per_block = __Settings.CUDA_THREADS_PER_BLOCK
    render.blocks = int(pixel_side_length**2 / render.threads_per_block) + 1# Blocks per grid

    return render(x_values,
                  y_values,
                  rgba_colours,
                  min_x,
                  max_x,
                  min_y,
                  max_y,
                  data_length,
                  pixel_side_length)

def make_2D_image(data, output_file_name, image_size = 1000 if __CUDA_AVALIBLE else 10, detail_level = 0, point_colours = None):
    print_verbose_info("Ensuring PIL is avalible.")
    if not __PIL_AVALIBLE:
        raise ModuleNotFoundError("This method requires use of the PIL (pillow) module which was not found.")

    print_verbose_info("Resizing data bounds.")
    min_x = min(data[:, 0])
    min_y = min(data[:, 1])

    max_x = max(data[:, 0])
    max_y = max(data[:, 1])
    
    x_range = max_x - min_x
    y_range = max_y - min_y
    if x_range < y_range:
        diff = y_range - x_range
        d_2 = diff / 2
        min_x -= d_2
        max_x += d_2
    elif x_range > y_range:
        diff = x_range - y_range
        d_2 = diff / 2
        min_y -= d_2
        max_y += d_2

    print_verbose_info("Parsing colour(s).")
    _hex_letter_values = { "0": 0, "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "A": 10, "B": 11, "C": 12, "D": 13, "E": 14, "F": 15 }
    def parse_hex_value(value: str) -> int:
        decimal_value = 0
        places = len(value)
        for i in range(places):
            v = places - i - 1
            decimal_value += _hex_letter_values[value[i]] * 16**i
        return decimal_value

    def parse_colour_string(colour: str) -> list:
        if len(colour) == 4:
            return [parse_hex_value(colour[1]) * 17, parse_hex_value(colour[2]) * 17, parse_hex_value(colour[3]) * 17, 255]
        elif len(colour) == 5:
            return [parse_hex_value(colour[1]) * 17, parse_hex_value(colour[2]) * 17, parse_hex_value(colour[3]) * 17, parse_hex_value(colour[4]) * 17]
        elif len(colour) == 7:
            return [parse_hex_value(colour[1:3]), parse_hex_value(colour[3:5]), parse_hex_value(colour[5:7]), 255]
        elif len(colour) == 9:
            return [parse_hex_value(colour[1:3]), parse_hex_value(colour[3:5]), parse_hex_value(colour[5:7]), parse_hex_value(colour[7:9])]
        else:
            raise ValueError(f"Colour string {colour} is not valid hex colour.")

    rgba_colours = None
    if point_colours is not None:
        print_verbose_info("Found colour specification.")
        rgba_colours = np.empty(len(data) * 4, dtype = int)

        if isinstance(point_colours, (list, np.ndarray)):
            if isinstance(point_colours[0], str) and point_colours[0][0] == "#":
                print_verbose_info("Colour is list of hex string values.")
                point_colours = [parse_colour_string(colour) for colour in point_colours]
            else:
                print_verbose_info("Colour is list of data.")
                point_colours = np.array(point_colours, dtype = float)
                point_colours = [[int(255 * size / max(point_colours)), 0, 255 - int(255 * size / max(point_colours)), 255] for size in point_colours]

            for i in range(len(point_colours)):
                rgba_colours[i * 4] = point_colours[i][0]
                rgba_colours[i * 4 + 1] = point_colours[i][1]
                rgba_colours[i * 4 + 2] = point_colours[i][2]
                rgba_colours[i * 4 + 3] = point_colours[i][3]

        else:
            # Should be a string
            print_verbose_info("Colour is a single value.")
            point_colours = parse_colour_string(point_colours)
            for i in range(len(data)):
                rgba_colours[i * 4] = point_colours[0]
                rgba_colours[i * 4 + 1] = point_colours[1]
                rgba_colours[i * 4 + 2] = point_colours[2]
                rgba_colours[i * 4 + 3] = point_colours[3]
    else:
        print_verbose_info("No colour specified.")
        print_verbose_info("Setting all points to white.")
        rgba_colours = np.full(len(data) * 4, 255, dtype = int)

    if __CUDA_AVALIBLE:
        print_verbose_info("Using CUDA.")
        image_pixels_function = __CUDA_make_2D_image_pixels
    else:
        print_verbose_info("CUDA unavalible.")
        print_verbose_info("CUDA using Python renderer.")
        image_pixels_function = __NO_CUDA_make_2D_image_pixels

    print_verbose_info("Rendering pixels.")
    image_pixels = image_pixels_function(data[:, 0].reshape(len(data)),
                                         data[:, 1].reshape(len(data)),
                                         rgba_colours,
                                         min_x,
                                         max_x,
                                         min_y,
                                         max_y,
                                         len(data),
                                         image_size)

    print_verbose_info("Unpacking colour channels.")
    # Convert to float data type to allow division without truncation
    #image_pixels = np.array(image_pixels, dtype = np.float32)
    image_pixels = np.array([[image_pixels[i * 4], image_pixels[i * 4 + 1], image_pixels[i * 4 + 2], image_pixels[i * 4 + 3]] for i in range(int(len(image_pixels) / 4))], dtype = np.float32)

    print_verbose_info("Applying detail level function.")
    if detail_level == 0:
        image_pixels[:, 0][image_pixels[:, 0] > 0] = 1
    elif detail_level == 1:
        # Use square root to prevent 'over exposed' regions from resulting in extreme contrast (makes detail too faint)
        image_pixels[:, 0] = np.sqrt(image_pixels[:, 0])
    elif detail_level == 2:
        # Use average of sqrt ant log to prevent 'over exposed' regions from resulting in extreme contrast (makes detail too faint)
        image_pixels[:, 0] = (np.sqrt(image_pixels[:, 0]) + np.log(image_pixels[:, 0] + 1)) / 2
    elif detail_level == 3:
        # Use log to prevent 'over exposed' regions from resulting in extreme contrast (makes detail too faint)
        image_pixels[:, 0] = np.log(image_pixels[:, 0] + 1)

    # Scale to be 0 to 255
    print_verbose_info("Value scaling pixels.")
    image_pixels[:, 1:] /= np.max(image_pixels[:, 0])
    image_pixels[:, 0] /= np.max(image_pixels[:, 0])
    image_pixels = np.array(image_pixels, dtype = int)

    ## Remove 0 ofset caused by above function(s)
    #image_pixels -= np.min(image_pixels)

    # Make into a 2D pixel array (transpose due to np.reshape)
    print_verbose_info("Re-aranging pixels (stage 1).")
    #image_pixels = image_pixels.reshape((image_size, image_size, 4)).T
    image_pixels = np.transpose(image_pixels.reshape((image_size, image_size, 4)), (1, 0, 2))

    # Convert from monitor coordinates (y=0 at top) to image orientation (y=0 at bottom)
    print_verbose_info("Re-aranging pixels (stage 2).")
    image_pixels = np.flip(image_pixels, 0)

    # Remove hit count values
    print_verbose_info("Removing extra data.")
    image_pixels = image_pixels[:, :, 1:]
    
    # Save as an image file
    print_verbose_info(f"Saving image as {output_file_name}.")
    image = PIL.Image.fromarray(image_pixels.astype("uint8"), "RGB")
    image.save(output_file_name)

def make_2D_graph_image(data: np.ndarray, output_file_name, graph_title, graph_xlabel, graph_ylabel, graph_args, graph_kwargs, force_equal_aspect, isLineGraph, point_colours):
    plot_kwargs = {}
    if force_equal_aspect:
        plot_kwargs["aspect"] = "equal"
    if point_colours is not None:
        graph_kwargs["c"] = point_colours

    fig = plt.figure(figsize = (8, 8))
    ax = fig.add_subplot(1, 1, 1, **plot_kwargs)
    
    if isLineGraph:
        ax.plot(data[:, 0].reshape(len(data)), data[:, 1].reshape(len(data)), *graph_args, **graph_kwargs)
    else:
        ax.scatter(data[:, 0].reshape(len(data)), data[:, 1].reshape(len(data)), *graph_args, **graph_kwargs)
    if graph_title != "":
        ax.set_title(graph_title)
    if graph_xlabel != "":
        ax.set_xlabel(graph_xlabel)
    if graph_ylabel != "":
        ax.set_ylabel(graph_ylabel)
    plt.savefig(output_file_name)

def make_3D_image_projection(data, output_file_name, projection_axis, image_size = 1000, detail_level = 0, point_colours = None):
    if projection_axis == "z":
        make_2D_image(data[:, 0:2], output_file_name, image_size, detail_level, point_colours)
    elif projection_axis == "y":
        make_2D_image(data[:, 0:3:2], output_file_name, image_size, detail_level, point_colours)
    else:
        make_2D_image(data[:, 1:3], output_file_name, image_size, detail_level, point_colours)

def make_3D_graph_images(data, output_file_name, graph_title, graph_xlabel, graph_ylabel, graph_args, graph_kwargs, force_equal_aspect, point_colours):
    plot_kwargs = {}
    if force_equal_aspect:
        plot_kwargs["aspect"] = "equal"
    if point_colours is not None:
        graph_kwargs["c"] = point_colours

    fig = plt.figure(figsize = (8, 8))
    axes = [[fig.add_subplot(2, 2, 1, **plot_kwargs), fig.add_subplot(2, 2, 2, **plot_kwargs)], [fig.add_subplot(2, 2, 3, **plot_kwargs)]]
    axes[0][0].scatter(data[:, 0].reshape(len(data)), data[:, 1].reshape(len(data)), *graph_args, **graph_kwargs)
    axes[0][1].scatter(data[:, 0].reshape(len(data)), data[:, 2].reshape(len(data)), *graph_args, **graph_kwargs)
    axes[1][0].scatter(data[:, 1].reshape(len(data)), data[:, 2].reshape(len(data)), *graph_args, **graph_kwargs)
    if graph_title != "":
        fig.suptitle(graph_title)
    if graph_xlabel != "":
        fig.supxlabel(graph_xlabel)
    if graph_ylabel != "":
        fig.supylabel(graph_ylabel)
    fig.savefig(output_file_name)



def __main():
    print_verbose_info("Loading arguments.")
    args = sys.argv[1:]
    print_debug(f"Arguments are: {args}")
    if len(args) == 0 or args[0][0] == "-" and args[0].lower() not in ("-h", "--help"):
        raise ArgumentError(None, "No data is provided. Data must be the first argument (other than the '-h' flag).")

    is3D = False
    output_file_name = None
    data_column_mask = None
    use_graph = False
    spatial_axes = False
    single_projection_axis = None
    isLineGraph = False
    graph_title = ""
    graph_xlabel = ""
    graph_ylabel = ""
    graph_point_colour = None
    graph_point_colour_column = None
    graph_args = []
    graph_kwargs = {}
    image_brightness_param = 0
    image_pixel_size = 1000
    
    print_verbose_info("Parsing arguments.")
    arg_index = 0
    while arg_index < len(args):
        if args[arg_index].lower() in ("-h", "--help"):
            print_verbose_info("Handling help flag.")
            print(__doc__)
            sys.exit()
        elif args[arg_index].lower() in ("-d", "--debug", "-v", "--verbose"):
            print_verbose_info(f"Skipping pre-parsed {args[arg_index]} flag.")
        elif args[arg_index].lower() in ("-3", "--3d"):
            print_verbose_info("Handling 3D flag.")
            is3D = True
            print_debug(f"3D flag value is {is3D}.")
        elif args[arg_index].lower() in ("-o", "--output_file"):
            print_verbose_info("Handling output file flag.")
            output_file_name = args[arg_index + 1]
            print_debug(f"output file flag value is {output_file_name}.")
            arg_index += 1
        elif args[arg_index].lower() in ("-m", "--data_mask"):
            print_verbose_info("Handling data mask flag.")
            mask_list = []
            for i, mask_digit in enumerate(args[arg_index + 1]):
                if mask_digit == "1":
                    mask_list.append(True)
                elif mask_digit == "0":
                    mask_list.append(False)
                elif mask_digit == "c":
                    graph_point_colour_column = i
                    mask_list.append(False)
                else:
                    raise ArgumentError(None, "Data mask argument contained a character that wasn't either '0', '1' or 'c'.")
            data_column_mask = np.array(mask_list)
            print_debug(f"data column mask value is {mask_list}.")
            arg_index += 1
        elif args[arg_index].lower() in ("-g", "--graph"):
            print_verbose_info("Handling graph flag.")
            use_graph = True
            print_debug(f"graph flag value is {use_graph}.")
        elif args[arg_index].lower() in ("-s", "--all_axes_spatial"):
            print_verbose_info("Handling spatial axes flag.")
            spatial_axes = True
            print_debug(f"spatial axes flag value is {spatial_axes}.")
        elif args[arg_index].lower() in ("-b", "--brightness"):
            print_verbose_info("Handling brightness flag.")
            image_brightness_param = args[arg_index + 1]
            print_debug(f"image brightness flag value is {image_brightness_param}.")
        elif args[arg_index].lower() in ("-r", "--image_size"):
            print_verbose_info("Handling image size flag.")
            image_pixel_size = args[arg_index + 1]
            print_debug(f"image pixel size flag value is {image_pixel_size}.")
            try:
                image_pixel_size = int(image_pixel_size)
            except:
                raise ArgumentError(None, f"-r flag value must be an integer, not {image_pixel_size}.")
        elif args[arg_index].lower() in ("-p", "--3D_projection_axis"):
            print_verbose_info("Handling 3D projection axis flag.")
            single_projection_axis = args[arg_index + 1]
            print_debug(f"3D projection axis flag value is {single_projection_axis}.")
            arg_index += 1
        elif args[arg_index].lower() in ("-l", "--2D_line_graph"):
            print_verbose_info("Handling 2D line graph flag.")
            isLineGraph = True
            print_debug(f"2D line graph flag value is {isLineGraph}.")
        elif args[arg_index].lower() in ("-t", "--graph_title"):
            print_verbose_info("Handling graph title flag.")
            graph_title = args[arg_index + 1]
            print_debug(f"graph title flag value is {graph_title}.")
            arg_index += 1
        elif args[arg_index].lower() in ("-x", "--graph_x_axis"):
            print_verbose_info("Handling graph x axis flag.")
            graph_xlabel = args[arg_index + 1]
            print_debug(f"graph x axis flag value is {graph_xlabel}.")
            arg_index += 1
        elif args[arg_index].lower() in ("-y", "--graph_y_axis"):
            print_verbose_info("Handling graph y axis flag.")
            graph_ylabel = args[arg_index + 1]
            print_debug(f"graph y axis flag value is {graph_ylabel}.")
            arg_index += 1
        elif args[arg_index].lower() in ("-c", "--graph_point_colour"):
            print_verbose_info("Handling graph point colour flag.")
            graph_point_colour = args[arg_index + 1]
            print_debug(f"graph point colour flag value is {graph_point_colour}.")
            arg_index += 1
        elif args[arg_index].lower() == "--graph_args":
            print_verbose_info("Handling graph args flag.")
            raw_graph_args = args[arg_index + 1:]
            graph_arg_index = 0
            kwargs_started = False
            while graph_arg_index < len(raw_graph_args):
                if raw_graph_args[graph_arg_index][0] == "-":
                    kwargs_started = True

                if not kwargs_started:
                    graph_args.append(float(raw_graph_args[graph_arg_index][0]))

                else:
                    kwarg_name = raw_graph_args[graph_arg_index].lstrip("-")
                    next_kwarg_index = graph_arg_index + 1
                    while next_kwarg_index < len(raw_graph_args) and not (raw_graph_args[next_kwarg_index][0] == "-" and not raw_graph_args[next_kwarg_index].strip("-").strip(".") == ""):
                        next_kwarg_index += 1
                    if next_kwarg_index - (graph_arg_index + 1) == 0:
                        print_warning(f"Named graph argument {kwarg_name} has no value.")
                    elif next_kwarg_index - (graph_arg_index + 1) == 1:
                        value = raw_graph_args[graph_arg_index + 1]
                        try:
                            value = float(raw_graph_args[graph_arg_index + 1])
                        except:
                            pass
                        graph_kwargs[kwarg_name] = value
                    else:
                        kwarg_component_strings = []
                        for i in range(graph_arg_index + 1, next_kwarg_index):
                            kwarg_component_strings.append(raw_graph_args[i])
                        graph_kwargs[kwarg_name] = " ".join(kwarg_component_strings)
                    graph_arg_index = next_kwarg_index - 1

                graph_arg_index += 1
            print_verbose_info(f"Graph args:   {graph_args}.")
            print_verbose_info(f"Graph kwargs: {graph_kwargs}.")
            print_verbose_info("Terminating argument parsing.")
            break
        else:
            print_verbose_warning(f"Argument or flag {args[arg_index]} is not recognised and is being ignored.")

        arg_index += 1

    print_verbose_info("Validating arguments.")

    if output_file_name is None:
        raise ArgumentError(None, "No output file name is specified (use the '-f' flag).")

    if data_column_mask is not None:
        expected_columns = 2 if not is3D else 3
        masked_columns = sum([1 if mask else 0 for mask in data_column_mask])
        if masked_columns != expected_columns:
            raise ArgumentError(None, f"Data mask indicated {masked_columns} columns but {expected_columns} are expected.")

    if is3D and not use_graph:
        if single_projection_axis is None:
            raise ArgumentError(None, "No projection axis is specified (use the '-p' flag).")
        if single_projection_axis not in ("x", "y", "z"):
            raise ArgumentError(None, f"Projection axis is specified but the value {single_projection_axis} is invalid.")

    if graph_point_colour is not None:
        if graph_point_colour[0] != "#":
            try:
                graph_point_colour_column = int(graph_point_colour)
                graph_point_colour = None
            except:
                raise ArgumentError(None, f"Colour specified ({graph_point_colour}) was not in a valid format (see -h) or was not a valid column index.")
        else:
            if len(graph_point_colour) - 1 not in (3, 4, 6, 8):
                raise ArgumentError(None, f"Colour specified ({graph_point_colour}) had wrong number of values (see -h).")
            for value in graph_point_colour[1:]:
                if value.upper() not in ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C", "D", "E", "F"):
                    raise ArgumentError(None, f"Colour specified ({graph_point_colour}) had an R, G, B or A specifier that wasn't a valid hexidecimal unit value.")

    if image_brightness_param not in (0, "0", "1", "2", "3", "4"):
        raise ArgumentError(None, f"Data mask indicated {masked_columns} columns but {expected_columns} are expected.")
    elif image_brightness_param != 0:
        image_brightness_param = int(image_brightness_param)

    if image_pixel_size < 2:
        raise ArgumentError(None, f"Image pixel size must be 2 or greater. Value was {image_pixel_size}.")

    print_verbose_info("Loading/parsing data.")

    data_file_sections = args[0].rsplit(".", 1)
    if len(data_file_sections) < 2:
        # Data is assumed to be a string (validate!!! - maybe json or xml!!!)
        data  = json.loads(args[0])
    else:
        target_directory = args[0].rsplit(os.pathsep, 1)[0]
        if not os.path.exists(target_directory):
            raise ArgumentError(None, f"The directory {target_directory} does not exist.")

        file_extension = data_file_sections[-1]
        if file_extension.lower() == "txt":
            data = np.loadtxt(args[0])
        elif file_extension.lower() == "csv":
            with open(args[0], "r") as file:
                reader = csv.reader(file)
                data = [[item for item in line] for line in reader]
        elif file_extension.lower() == "json":
            with open(args[0], "r") as file:
                data = json.load(file)
        elif file_extension.lower() == "xml":
            raise NotImplementedError("XML is not yet supported!")#TODO: load data
        elif file_extension.lower() == "pickle":
            with open(args[0], "rb") as file:
                data = pickle.load(file)

    print_verbose_info("Forcing data type to np.ndarray.")
    data = np.array(data)

    print_verbose_info("Validating data format.")
    if (len(data[0]) < 2 and not is3D) or (len(data[0]) < 3 and is3D):
        raise ArgumentError(None, "Data format has too few columns per row.")
    elif (len(data[0]) > 2 and not is3D and data_column_mask is None) or (len(data[0]) > 3 and is3D and data_column_mask is None):
        raise ArgumentError(None, "Data format has too many columns per row and no mask is provided (use the '-m' flag).")

    if graph_point_colour is not None or graph_point_colour_column is not None:
        if graph_point_colour is None:
            if graph_point_colour_column >= len(data[0]) or graph_point_colour_column < -len(data[0]):
                raise ArgumentError(None, f"Column specified as colour ({graph_point_colour_column}) was not in a valid column index.")
            graph_point_colour = data[:, graph_point_colour_column]

    if data_column_mask is not None:
        print_verbose_info("Applying data mask.")
        data = np.array([data[i, :][data_column_mask] for i in range(len(data))], dtype = float)
    else:
        data = np.array(data, dtype = float)
        
    if not is3D:
        if use_graph:
            print_verbose_info("Using function make_2D_graph_image.")
            make_2D_graph_image(data, output_file_name, graph_title, graph_xlabel, graph_ylabel, graph_args, graph_kwargs, spatial_axes, isLineGraph, graph_point_colour)
        else:
            print_verbose_info("Using function make_2D_image.")
            make_2D_image(data, output_file_name, image_pixel_size, image_brightness_param, graph_point_colour)
    else:
        if use_graph:
            print_verbose_info("Using function make_3D_graph_images.")
            make_3D_graph_images(data, output_file_name, graph_title, graph_xlabel, graph_ylabel, graph_args, graph_kwargs, spatial_axes, graph_point_colour)
        else:
            print_verbose_info("Using function make_3D_image_projection.")
            make_3D_image_projection(data, output_file_name, single_projection_axis, image_pixel_size, image_brightness_param, graph_point_colour)

if __name__ == "__main__":
    if __MPI_AVALIBLE:
        try:
            __Settings.MPI_COMM = MPI.COMM_WORLD
            __Settings.MPI_RANK = __Settings.MPI_COMM.Get_rank()
            if __Settings.MPI_RANK == 0:
                print_verbose_info(f"MPI avalible and enabled with {__Settings.MPI_COMM.Get_size()} processes.")
        except:
            __MPI_AVALIBLE = False
            print_verbose_warning("MPI is avalible but the program was not started for use with MPI.")
            print_verbose_warning("Disabling MPI functionality for this run.")

    lowercase_args = [arg.lower() for arg in sys.argv]
    if "-d" in lowercase_args or "--debug" in lowercase_args:
        __Settings.DEBUG_ENABLED = True
    if "-v" in lowercase_args or "--verbose" in lowercase_args:
        __Settings.VERBOSE_ENABLED = True

    try:
        if not __MPI_AVALIBLE or __MPI_AVALIBLE and  __Settings.MPI_RANK == 0:
            # Either the first MPI process or MPI isn't active
            #print("ROOT")
            #print(__MPI_AVALIBLE)
            #print(__Settings.MPI_RANK)
            #exit()
            __main()
            print_info("Done")
        else:
            # MPI active and not the first process
            print("WORKER")
            print(__MPI_AVALIBLE)
            print(__Settings.MPI_RANK)
            exit()
            __MPI_not_root_process_handeler()
    except Exception as e:
        has_message = e.__str__() != ""
        print_error(f"Execution encountered an error{(':' if has_message else ' (no details avalible).') if __Settings.DEBUG_ENABLED or __Settings.VERBOSE_ENABLED else '.'}")
        print_debug("Traceback (most recent call last):\n" + "".join(traceback.format_tb(e.__traceback__)) + type(e).__name__ + (f": {e.__str__()}" if has_message else ""))
        if has_message and not __Settings.DEBUG_ENABLED:
            print_error(e.__str__())
        print_info("Terminating.")