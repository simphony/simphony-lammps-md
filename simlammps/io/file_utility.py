from simphony.api import CUDS
from simphony.core import CUBA
from simphony.cuds.meta.api import Material
from simphony.cuds.particles import Particle, Particles

from .lammps_data_file_parser import LammpsDataFileParser
from .lammps_data_file_writer import LammpsDataFileWriter
from .lammps_data_line_interpreter import LammpsDataLineInterpreter
from .lammps_simple_data_handler import LammpsSimpleDataHandler
from ..common.atom_style import (AtomStyle, get_atom_style)
from ..common.atom_style_description import ATOM_STYLE_DESCRIPTIONS
from ..common.utils import create_material_to_atom_type_map
from ..config.domain import get_box


def read_data_file(filename, atom_style=None, name=None):
    """ Reads LAMMPS data file and create CUDS objects

    Reads LAMMPS data file and create a Particles and CUDS. The CUDS
    will contain a material for each atom type (e.g. CUBA.MATERIAL_TYPE).

    The attributes for each particle are based upon what atom-style
    the file contains (i.e. "sphere" means that particles in addition to having
    CUBA.VELOCITY will also have a CUBA.RADIUS and CUBA.MASS). See
    'atom_style' for more details.

    Parameters
    ----------
    filename : str
        filename of lammps data file
    atom_style : AtomStyle, optional
        type of atoms in the file.  If None, then an attempt of
        interpreting the atom-style in the file is performed.
    name : str, optional
        name to be given to returned Particles.  If None, then filename is
        used.

    Returns
    -------
    particles : Particles
        particles
    SD : CUDS
        SD containing materials

    """
    handler = LammpsSimpleDataHandler()
    parser = LammpsDataFileParser(handler=handler)

    parser.parse(filename)

    if atom_style is None:
        atom_style = (
            get_atom_style(handler.get_atom_type())
            if handler.get_atom_type()
            else AtomStyle.ATOMIC)

    types = (atom_t for atom_t in
             range(1, handler.get_number_atom_types() + 1))
    atoms = handler.get_atoms()
    velocities = handler.get_velocities()
    masses = handler.get_masses()

    box_origin = handler.get_box_origin()
    box_vectors = handler.get_box_vectors()

    type_to_material_map = {}

    statedata = CUDS()

    # set up a Material for each different type
    for atom_type in types:
        material = Material()
        description = "Material for lammps atom type (originally '{}')".format(
            atom_type
        )
        material.description = description
        type_to_material_map[atom_type] = material.uid
        statedata.add([material])

    # add masses to materials
    for atom_type, mass in masses.iteritems():
        material = statedata.get(type_to_material_map[atom_type])
        material.data[CUBA.MASS] = mass
        statedata.update([material])

    def convert_atom_type_to_material(atom_type):
        return type_to_material_map[atom_type]

    interpreter = LammpsDataLineInterpreter(atom_style,
                                            convert_atom_type_to_material)

    # create particles
    particles = Particles(name=name if name else filename)
    data = particles.data
    data.update({CUBA.ORIGIN: box_origin,
                 CUBA.VECTOR: box_vectors})
    particles.data = data

    # add each particle
    for lammps_id, values in atoms.iteritems():
        coordinates, data = interpreter.convert_atom_values(values)
        data.update(interpreter.convert_velocity_values(velocities[lammps_id]))

        p = Particle(coordinates=coordinates, data=data)
        particles.add([p])

    return particles, statedata


def write_data_file(filename,
                    particles,
                    state_data,
                    atom_style=AtomStyle.ATOMIC):
    """ Writes LAMMPS data file from CUDS objects

    Writes LAMMPS data file from a list of Particles.

    The particles will be annotated with their Simphony-uid. For example::

        10 1 17 -1.0 10.0 5.0 6.0   # uid:'40fb302c-6e71-11e5-b35f-08606e7c2200'  # noqa


    Parameters
    ----------
    filename : str
        filename of lammps data file

    particles : Particles or iterable of Particles
        particles

    state_data : CUDS
        SD containing materials

    atom_style : AtomStyle, optional
        type of atoms to be written to file

    Raises

    """
    if type(particles) is not list:
        particles = [particles]

    num_particles = sum(
        pc.count_of(CUBA.PARTICLE) for pc in particles)

    # get a mapping from material_type to atom_type
    material_to_atom_type = create_material_to_atom_type_map(state_data)
    box = get_box([pc.data for pc in particles])

    material_type_to_mass = None if not _style_has_masses(
        atom_style) else _get_mass(state_data)

    writer = LammpsDataFileWriter(filename,
                                  atom_style=atom_style,
                                  number_atoms=num_particles,
                                  material_to_atom_type=material_to_atom_type,
                                  simulation_box=box,
                                  material_type_to_mass=material_type_to_mass)

    for pc in particles:
        for p in pc.iter(item_type=CUBA.PARTICLE):
            writer.write_atom(p)
    writer.close()


def _style_has_masses(atom_style):
    """ Returns if atom style has masses

    """
    return ATOM_STYLE_DESCRIPTIONS[atom_style].has_mass_per_type


def _get_mass(state_data):
    """ Get a dictionary from 'material type' to 'mass'.

    Parameters:
    -----------
    state_data : CUDS
        SD containing material with mass

    """
    material_type_to_mass = {}
    for material in state_data.iter(item_type=CUBA.PARTICLE):
        try:
            material_type_to_mass[material.uid] = material.data[CUBA.MASS]
        except KeyError:
            raise RuntimeError(
                "CUBA.MASS is missing from material '{}'".format(
                    material.uid))
    return material_type_to_mass
