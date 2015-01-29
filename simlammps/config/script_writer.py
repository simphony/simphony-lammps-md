

class ScriptWriter(object):
    """ Writer of a LAMMPS-commands script

    The ScriptWriter generates a series of LAMMPS commands
    (that make up a LAMMPS-input script).

    The command script generated by this class can be passed to
    a LAMMPS executable as a file or string. Alternately, this
    script can be passed to the library interface of LAMMPS or
    individual commands generated by this script can be passed
    "one by one" to the library interface of LAMMPS

    """

    @staticmethod
    def get_configuration(data_file, number_steps, time_step,
                          pair_style, pair_coeff):
        """ Return configuration command-script

        Parameters
        ----------
        data_file: string
            name of data file to be read before run (input)
            and written to after run (output)
        number_steps: int
            number of time steps for run
        time_step: float
            length of time step
        pair_style: string
            pair style information
        pair_coeff: string
            pair coefficient information between pairs of atoms

        Returns
        -------
        command script - string
            lines of a LAMMPS command script

        """

        # TODO improve the script writer so becomes a list of config
        # objects that it can then organizes into lines of a LAMMPS
        # script (and ensure that the order of commands
        # is in agreement with LAMMPS).

        return CONFIGURATION.format(DATAFILE=data_file,
                                    NUMBER_STEPS=number_steps,
                                    TIME_STEP=time_step,
                                    PAIR_STYLE=pair_style,
                                    PAIR_COEFF=pair_coeff)


CONFIGURATION = """
# Control file generated by SimPhoNy
# 2-d LJ flow simulation

dimension   2
boundary    p s p

atom_style  atomic
neighbor    0.3 bin
neigh_modify    delay 5

{PAIR_STYLE}

# read from simphony-generated file
read_data {DATAFILE}

{PAIR_COEFF}

# define groups based on type

group flow type 1
group lower type 2
group upper type 3

compute      mobile flow temp
fix      1 all nve
fix      2 flow temp/rescale 200 1.0 1.0 0.02 1.0
fix_modify   2 temp mobile

# Poiseuille flow

fix      3 lower setforce 0.0 0.0 0.0
fix      4 upper setforce 0.0 NULL 0.0
fix      5 upper aveforce 0.0 -1.0 0.0
fix      6 flow addforce 0.5 0.0 0.0
fix      7 all enforce2d

# Run

timestep    {TIME_STEP}
thermo      500
thermo_modify   temp mobile

run {NUMBER_STEPS}

# write reults to simphony-generated file
write_data {DATAFILE}
"""
