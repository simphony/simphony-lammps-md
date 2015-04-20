from simlammps.cuba_extension import CUBAExtension


def get_box(particle_data_containers, command_format=False):
    """ Get simulation box commands

    Using CUBA.BOX_VECTORS and CUBA.BOX_ORIGIN, return the
    string used by LAMMPS to define the simulation box in
    the LAMMPS data file or as a command.

    Currently the box vectors (and origin) have to be
    the same for each particle container.

    Parameters:
    -----------
    particle_data_containers: collection of DataContainer
        list of containers of data containers from particles
    command_format: boolean
        if command format is true, then box command suitable
        for lammps-command is returned.  Otherwise, the
        string retured is suitable for LAMMPS data file.
    """
    origin = None
    vectors = None

    for dc in particle_data_containers:
        # find box vectors (and origin) and ensure
        # that they are the same for each particle container
        if CUBAExtension.BOX_VECTORS in dc:
            if (vectors and
                    vectors != dc[CUBAExtension.BOX_VECTORS]):
                # TODO provide more info in exception message
                raise RuntimeError("Box vectors need to match")
            vectors = dc[CUBAExtension.BOX_VECTORS]
        if CUBAExtension.BOX_ORIGIN in dc:
            if origin and origin != dc[CUBAExtension.BOX_ORIGIN]:
                # TODO provide more info in exception message
                raise RuntimeError("Box origin need to match")
            origin = dc[CUBAExtension.BOX_ORIGIN]

    # origin is optional
    if not origin:
        origin = (0.0, 0.0, 0.0)

    # Note: For LAMMPS we can define a orthogonal simulation
    # or non-orthogonal simulation box. For the non-orthogonal
    # simulation box, the lammps doc states the following:
    # "a must lie on the positive x axis. b must lie in
    # the xy plane, with strictly positive y component. c may
    # have any orientation with strictly positive z component.
    # The requirement that a, b, and c have strictly positive
    # x, y, and z components, respectively, ensures that a, b,
    # and c form a complete right-handed basis."

    if not vectors:
        raise RuntimeError("CUBAExtension.BOX_VECTORS was not set")
    else:
        _check_vectors(vectors)

    box_string = ""
    if command_format:
        box_string = _get_command_region_box_string(vectors, origin)
    else:
        box_string = _get_data_file_box_string(vectors, origin)

    return box_string.format(origin[0], vectors[0][0]-origin[0],
                             origin[1], vectors[1][1]-origin[1],
                             origin[2], vectors[2][2]-origin[2])


def _check_vectors(vectors):
    # TODO: currently only handling orthogonal simulation box
    # (where a must lie on positive x axis..) so only something
    # like the following is allowed: (x, 0, 0), (0, y, 0)
    # and (0, 0, z).
    for i, v in enumerate(vectors):
        for j, x in enumerate(v):
            if i != j and float(x) != 0.0:
                msg = ("Box vectors must have the form "
                       "(x, 0, 0), (0, y, 0) and (0, 0, z)")
                raise RuntimeError(msg)


def _get_data_file_box_string(vectors, origin):
    box = "{:.16e} {:.16e} xlo xhi\n"
    box += "{:.16e} {:.16e} ylo yhi\n"
    box += "{:.16e} {:.16e} zlo zhi\n"
    return box


def _get_command_region_box_string(vectors, origin):
    box = "region box block {:.16e} {:.16e} "
    box += "{:.16e} {:.16e} "
    box += "{:.16e} {:.16e}\n"
    return box
