from CellModeller.Signalling.GridDiffusion import GridDiffusion
from CellModeller.Integration.CLCrankNicIntegrator import CLCrankNicIntegrator
from CellModeller.Integration.ScipyODEIntegrator import ScipyODEIntegrator
from CellModeller.Regulation.ModuleRegulator import ModuleRegulator
from CellModeller.Biophysics.BacterialModels.CLBacterium import CLBacterium
from CellModeller.GUI import Renderers
import numpy
import random

max_cells = 2**15

grid_dim = (64, 8, 12)
grid_size = (4, 4, 4)
grid_orig = (-128, -14, -8)


def setup(sim):
    sig = GridDiffusion(sim, 1, grid_dim, grid_size, grid_orig, [10.0])
    #integ = ScipyODEIntegrator(sim, 1, 4, max_cells, sig, True)
    integ = CLCrankNicIntegrator(sim, 1, 5, max_cells, sig, boundcond='reflect')
    biophys = CLBacterium(sim, max_cells=max_cells, max_contacts=32, max_sqs=64*16, jitter_z=False, reg_param=0.001, gamma=5.0)
    biophys.addPlane((0,-16,0), (0,1,0), 1)
    biophys.addPlane((0,16,0), (0,-1,0), 1)
    reg = ModuleRegulator(sim, __file__)

    sim.init(biophys, reg, sig, integ)

    sigrend = Renderers.GLGridRenderer(sig, integ)
    therend = Renderers.GL2DBacteriumRenderer(sim)
    sim.addRenderer(sigrend)
    sim.addRenderer(therend)

    #for i in range(4):
    #    for j in range(4):
    #        sim.addCell(cellType=0, pos=(i*16-32,j*16-32,0))
    #        sim.addCell(cellType=1, pos=(i*16-32-8,j*16-32-8,0))

    sim.addCell(cellType=1, pos=(-20.0,0,0), len=2.0)
    sim.addCell(cellType=0, pos=(20.0,0,0), len=2.0)

    sim.pickleSteps = 10


def init(cell):
    cell.targetVol = 2.5 + random.uniform(0.0,0.5)
    cell.length = 2.0
    cell.signals[:] = [0]
    cell.species[:] = [0, 0, 0, 0, 0]
    cell.growthRate = 0.5

def numSignals():
    return 1

def numSpecies():
    return 5

def specRateCL():
    return '''
    const float D1 = 0.1f;
    const float d1 = 1e-3;
    const float k1 = 1.f;
    const float k2 = 1.f;
    const float g1 = 1e-1;
    const float d2 = 1e-5;
    const float k3 = 1.f;
    const float k4 = 5e-5;
    const float k5 = 0.1f;
    const float k6 = 1e-2;
    const float d3 = 1e-3;
    const float g2 = 1e-1;
    const float dr = 0.1f;

    float AHL = signals[0];
    float LuxI = species[0];
    float AHLi = species[1];
    float AiiA = species[2];
    float CFP = species[3];
    float YFP = species[4];

    if (cellType==0) {
        rates[0] = 0.f;
        rates[1] = k1*LuxI/(k2+LuxI) - k5*AiiA*AHLi/(k6+AHLi) + D1*(AHL-AHLi)*area/volume;
        rates[2] = d3 - g2*AiiA;
        rates[3] = d2 + k3*AHLi*AHLi/(k4+AHLi*AHLi) - dr*CFP;
        rates[4] = 0.f;
    } else {
        rates[0] = d1 - g1*LuxI;
        rates[1] = k1*LuxI/(k2+LuxI) + D1*(AHL-AHLi)*area/volume;
        rates[2] = 0.f;
        rates[3] = 0.f;
        rates[4] = d2 + k3*AHLi*AHLi/(k4+AHLi*AHLi) - dr*YFP;
    }
    '''

def sigRateCL():
    return '''
    const float D1=0.1f;
    float AHL = signals[0];
    float AHLi = species[1];
    rates[0] = -D1*(AHL-AHLi)*area/gridVolume;
    '''

def update(cells):
    if len(cells) > max_cells-16:
        print 'reached cell limit'
        exit()
    for (i,cell) in cells.iteritems():
        cell.color = [0.1, 0.1+cell.species[3]/10.0, 0.1+cell.species[4]*20.0]
        if cell.volume > getattr(cell, 'target_volume', 3.0):
            cell.asymm = [1,1]
            cell.divideFlag = True

def divide(parent, d1, d2):
    d1.targetVol = 2.5 + random.uniform(0.0,0.5)
    d2.targetVol = 2.5 + random.uniform(0.0,0.5)
