""" LAMMPS SimPhoNy Wrapper

This module provides a wrapper to LAMMPS-md
"""
from simlammps.particle_container import ParticleContainer
from simlammps.lammps_fileio_data_manager import LammpsFileIoDataManager
from simlammps.lammps_process import LammpsProcess


class LammpsWrapper(object):
    """ Wrapper to LAMMPS-md

    """
    def __init__(self):
        self._data_filename = "data.lammps"
        self._data_manager = LammpsFileIoDataManager(
            data_filename=self._data_filename)

        self._particle_containers = {}

    def dummy_init_data(self):
        """ Dummy method to init data in _data_manager
        """
        # hack to force up-to-date data_manager
        self._data_manager.update_from_lammps()

        # hack to create some lammps-particle_containers
        for i in xrange(self._data_manager.number_types):
            pc = ParticleContainer(self._data_manager, i+1)
            self._particle_containers[str(i+1)] = pc

    def add_particle_container(self, name, particle_container=None):
        """Add particle container.

        Parameters
        ----------
        name : str
            name of particle container
        particle_container : ABCParticleContainer, optional
            particle container to be added. If none is give,
            then an empty particle container is added.

        Returns
        ----------
        ABCParticleContainer
            The particle container newly added to Lammps.  See
            get_particle_container for more information.

        """
        pass

    def get_particle_container(self, name):
        """Get particle container.

        The returned particle container can be used to query
        and change the related data inside LAMMPS.

        Parameters
        ----------
        name : str
            name of particle container to return
        """
        if name not in self._particle_containers:
            return self._particles_containers[name]
        else:
            raise ValueError(
                'Particle container \'{}\` does not exist'.format(name))

    def delete_particle_container(self, name):
        """Delete particle container.

        Parameters
        ----------
        name : str
            name of particle container to delete
        """
        pass

    def iter_particle_containers(self, names=None):
        """Returns an iterator over a subset or all
        of the particle containers. The iterator iterator yields
        (name, particlecontainer) tuples for each particle container.

        Parameters
        ----------
        names : list of str
            names of specific particle containers to be iterated over.
            If names is not given, then all particle containers will
            be iterated over.

        """
        if names is None:
            for name, pc in self._particle_containers.iteritems():
                yield name, pc
        else:
            for name, pc in names:
                yield name, self._particle_container.get(name)

    def run(self):
        """ Run for based on configuration

        """
        # before running, we flush any changes to lammps
        # and mark our data manager (cache of particles)
        # as being invalid
        self._data_manager.flush()
        self._data_manager.mark_as_invalid()

        number_steps = 10000
        commands = CONFIGURATION.format(
            DATAFILE=self._data_filename, NUMBER_STEPS=number_steps)

        # TODO remove
        with open('dummy.in', 'w') as f:
            f.write(commands)

        lammps = LammpsProcess()
        lammps.run(commands)


# dummy configuration
CONFIGURATION = """
# Control file generated by SimPhoNy
# 2-d LJ flow simulation

dimension	2
boundary	p s p

atom_style	atomic
neighbor	0.3 bin
neigh_modify	delay 5

# LJ potentials

pair_style lj/cut 1.12246

# read from simphony-generated file
read_data {DATAFILE}

# define groups based on type

group flow type 1
group lower type 2
group upper type 3
group boundary union lower upper

# initial velocities

compute	     mobile flow temp
velocity     flow create 1.0 482748 temp mobile
fix	     1 all nve
fix	     2 flow temp/rescale 200 1.0 1.0 0.02 1.0
fix_modify   2 temp mobile

# Poiseuille flow

velocity     boundary set 0.0 0.0 0.0
fix	     3 lower setforce 0.0 0.0 0.0
fix	     4 upper setforce 0.0 NULL 0.0
fix	     5 upper aveforce 0.0 -1.0 0.0
fix	     6 flow addforce 0.5 0.0 0.0
fix	     7 all enforce2d

# Run

timestep	0.003
thermo		500
thermo_modify	temp mobile

run {NUMBER_STEPS}

# write reults to simphony-generated file
write_data {DATAFILE}
"""
