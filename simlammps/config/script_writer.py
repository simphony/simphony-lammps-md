from simphony.api import CUBA


from .pair_style import PairStyle
from .atom_type_fixes import get_per_atom_type_fixes
from ..common.atom_style import (get_lammps_string, AtomStyle)


class ConfigurationError(RuntimeError):
    pass


class ScriptWriter(object):
    """ Writer of a LAMMPS-commands script

    The ScriptWriter generates a series of LAMMPS commands
    (that make up a LAMMPS-input script).

    The command script generated by this class can be passed to
    a LAMMPS executable as a file or string.

    TODO: script can be passed to the library interface of LAMMPS or
    individual commands generated by this script can be passed
    "one by one" to the library interface of LAMMPS

    Parameters
    ----------
    atom_style: str
        atom_style

    """

    def __init__(self, atom_style):
        self._atom_style = atom_style

    def get_configuration(self, materials, BC, CM, SP,
                          input_data_file, output_data_file):
        """ Return configuration command-script

        Parameters
        ----------
        materials : list of Material
            materials
        BC : DataContainer
            container of attributes related to the boundary conditions
        CM : DataContainer
            container of attributes related to the computational method
        SP : DataContainer
            container of attributes related to the system parameters/conditions
        input_data_file: string
            name of data file to be read at beginning of run (input)
        output_data_file: string
            name of data file to be written after run (output)

        Returns
        -------
        command script - string
            lines of a LAMMPS command script

        """

        result = "# Control file generated by SimPhoNy\n"

        result += "dimension 3\n"

        result += ScriptWriter.get_boundary(BC)

        result += self.get_initial_setup()

        if self._atom_style == AtomStyle.GRANULAR:
            # TODO hard-coding certain values for DEM example
            result += DEM_DUMMY

        result += ScriptWriter.get_pair_style(SP)

        if input_data_file:
            result += READ_DATA.format(INPUT_DATAFILE=input_data_file)

        result += get_per_atom_type_fixes(self._atom_style, materials)

        if self._atom_style == AtomStyle.GRANULAR:
            # TODO hard-coding certain values for DEM example
            result += DEM_DUMMY_FIXES

        result += ScriptWriter.get_fix(CM)

        result += ScriptWriter.get_pair_coeff(SP)

        result += ScriptWriter.get_run(CM)

        if output_data_file:
            result += WRITE_DATA.format(OUTPUT_DATAFILE=output_data_file)

        return result

    @staticmethod
    def get_run(CM):
        """ Return run command-script

        """
        _check_configuration(CM)
        number_steps = CM[CUBA.NUMBER_OF_TIME_STEPS]
        time_step = CM[CUBA.TIME_STEP]
        return CONFIGURATION_RUN.format(NUMBER_STEPS=number_steps,
                                        TIME_STEP=time_step)

    @staticmethod
    def get_pair_style(SP):
        """ Return pair_coeff command-script

        """
        # TODO this should be change once this class
        # keeps track of states
        pair_style = PairStyle(SP)
        return pair_style.get_global_config()

    @staticmethod
    def get_pair_coeff(SP):
        """ Return pair_coeff command-script

        """
        # TODO this should be change once this class
        # keeps track of states
        pair_style = PairStyle(SP)
        return pair_style.get_pair_coeffs()

    @staticmethod
    def get_fix(CM):
        _check_configuration(CM)
        return _get_thermodynamic_ensemble(CM)

    @staticmethod
    def get_boundary(BC, change_existing_boundary=False):
        """ get lammps commands related to boundary conditions (BC)

        Parameters:
        ----------
        BC : DataContainer
            container of attributes related to the boundary conditions
        change_existing_boundary : boolean
            if true then return lammps commands that change existing boundary
            conditions. if false, then return lammps commands that set the
            boundary conditions
        """
        return _get_boundary(BC, change_existing_boundary)

    def get_initial_setup(self):
        return INITIAL.format(get_lammps_string(self._atom_style))


INITIAL = """atom_style  {}
atom_modify     map array
neighbor    0.3 bin
neigh_modify    delay 5
"""


def _check_configuration(CM):
    """ Check if everything is configured correctly

    Raises
    ------
    ConfigurationError
        if anything is wrong with the configuration
    """
    cm_requirements = [CUBA.NUMBER_OF_TIME_STEPS,
                       CUBA.TIME_STEP,
                       CUBA.THERMODYNAMIC_ENSEMBLE]

    missing = [str(req) for req in cm_requirements
               if req not in CM.keys()]

    msg = ""
    if missing:
        msg = "Problem with CM component. "
        msg += "Missing: " + ', '.join(missing)

    # TODO check SP, BC

    if msg:
        # TODO throw unique exception that
        # users can catch and then try to fix
        # their configuration
        raise ConfigurationError(msg)


def _get_thermodynamic_ensemble(CM):
    esemble = CM[CUBA.THERMODYNAMIC_ENSEMBLE]
    if esemble == "NVE":
        return "fix 1 all nve\n"
    else:
        message = ("Unsupported ensemble was provided "
                   "CM[CUBA.THERMODYNAMIC_ENSEMBLE] = {}")
        ConfigurationError(message.format(esemble))


def _get_boundary(BC, change_existing_boundary):
    """ get lammps boundary command from BC

    The boundary command can be either fixed or periodic.

    >> BC[CUBA.FACE] = ("periodic", "fixed", "periodic"]

    """

    error_message = ""
    boundary_command = ""
    if change_existing_boundary:
        boundary_command = "change_box all boundary"
    else:
        boundary_command = "boundary"

    # mapping of cuds-value to lammps string
    mappings = {'periodic': 'p', 'fixed': 'f'}

    if len(BC[CUBA.FACE]) != 3:
        error_message += "3 dimensions need to be given.\n"
    for b in BC[CUBA.FACE]:
        if b in mappings:
            boundary_command += " {}".format(mappings[b])
        else:
            error_message += "'{}' is not supported\n"
    if error_message:
        message = ("Unsupported boundary was provided "
                   "BC[CUBA.FACE] = {}\n"
                   "{}")
        ConfigurationError(message.format(
            BC[CUBA.FACE], error_message))
    boundary_command += "\n"
    return boundary_command


READ_DATA = """
# read from SimPhoNy-generated file
read_data {INPUT_DATAFILE}

"""


CONFIGURATION_RUN = """
# Run

timestep {TIME_STEP}

run {NUMBER_STEPS}
"""

WRITE_DATA = """

# write results to simphony-generated file
write_data {OUTPUT_DATAFILE}
"""

DEM_DUMMY = """
# It is heavily recommended to use 'neigh_modify delay 0' with granular
neigh_modify    delay 0

#  Pair granular with shear history requires newton pair off
newton          off

# Pair granular requires ghost atoms store velocity
communicate     single vel yes
"""

DEM_DUMMY_FIXES = """ 
#Material properties required for new pair styles

fix m3 all property/global coefficientRestitution peratomtypepair 1 0.95
fix m4 all property/global coefficientFriction peratomtypepair 1 0.0

#New pair style
pair_style gran model hertz tangential history
pair_coeff      * *

fix xwall_low all wall/gran model hertz tangential history primitive type 1 xplane -10.0
fix xwall_up all wall/gran model hertz tangential history primitive type 1 xplane 15.0
fix ywall_low all wall/gran model hertz tangential history primitive type 1 yplane -7.5
fix ywall_up all wall/gran model hertz tangential history primitive type 1 yplane 7.5
fix zwall_low all wall/gran model hertz tangential history primitive type 1 zplane -0.5
fix zwall_up all wall/gran model hertz tangential history primitive type 1 zplane 0.5
"""  # NOQA
