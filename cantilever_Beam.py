import job
import visualization
import mesh
import step
import assembly
import section
import material
import part
import sketch
from abaqus import *
from abaqusConstants import *
import regionToolset


#session.viewports['Viewport : 1'].setValues(displayedObject=None)


# -----------------------------------------------------------------------------------------------------------
# CREATE MODEL
# the variable mdb provides access to a default model database.
# This variable is made available to the script thanks to the from abaqus import *

# change the name of the model from default of 'Model-1' to 'Cantilever Beam'
mdb.models.changeKey(fromName='Model-1', toName='Cantilever Beam')


# assings our model to the beamModel variable
beamModel = mdb.models['Cantilever Beam']

# -----------------------------------------------------------------------------------------------------------

# CREATE THE PART

beamProfileSketch = beamModel.ConstrainedSketch(
    name='Beam CS Profile', sheetSize=5)


# draw a rectangle on the sketch plane points from top left to bottom right
beamProfileSketch.rectangle(point1=(0.1, 0.1), point2=(0.3, -0.1))


# creating part
beamPart = beamModel.Part(
    name='Beam', dimensionality=THREE_D, type=DEFORMABLE_BODY)


beamPart.BaseSolidExtrude(sketch=beamProfileSketch, depth=5)


# -----------------------------------------------------------------------------------------------------------


# Create Materials

# Create material AISI 1005 Steel by assigning mass desinty, youngs modulus and poissons ratio

beamMaterial = beamModel.Material(name='AISI 1005 Steel')
beamMaterial.Density(table=((7872,),))  # table format
beamMaterial.Elastic(table=((200E9, 0.29), ))
# -----------------------------------------------------------------------------------------------------------
# Create solid section and assign the beam to it


# we cannot pass beamMaterial variable(because its material object), we should give string value which is 'AISI 1005 Steel'
beamSection = beamModel.HomogeneousSolidSection(
    name='Beam Section', material='AISI 1005 Steel')

# Assign the beam to this section

beam_region = (beamPart.cells, )  # used to find the cells of the beam
beamPart.SectionAssignment(region=beam_region, sectionName='Beam Section')


# -----------------------------------------------------------------------------------------------------------
# Create an Assembly


# Create the part instance

beamAssembly = beamModel.rootAssembly


beamInstance = beamAssembly.Instance(
    name='Beam Instance', part=beamPart, dependent=ON)


# -----------------------------------------------------------------------------------------------------------
# Create the step
# Create a static general step
beamModel.StaticStep(name='Apply Load', previous='Initial',
                     description='Load is applied during this step')

# -----------------------------------------------------------------------------------------------------------
# Create the field output request


beamModel.fieldOutputRequests.changeKey(
    fromName='F-Output-1', toName='Selected Field Outputs')
beamModel.fieldOutputRequests['Selected Field Outputs'].setValues(
    variables=('S', 'E', 'PEMAG', 'U', 'RF', 'CF'))


# -----------------------------------------------------------------------------------------------------------
# Create the history output requests

beamModel.HistoryOutputRequest(
    name='Default History Outputs', createStepName='Apply Load', variables=PRESELECT)

del beamModel.historyOutputRequests['H-Output-1']


# -----------------------------------------------------------------------------------------------------------
# Apply Loads

# Apply pressure load to top surface
# First we need to locate and select the top surface
# We place a point somewhere on the top surface based on our knowledge of the geometry
top_face_pt_x = 0.2
top_face_pt_y = 0.1
top_face_pt_z = 2.5
top_face_pt = (top_face_pt_x, top_face_pt_y, top_face_pt_z)
top_face = beamInstance.faces.findAt((top_face_pt,))
top_face_region = regionToolset.Region(side1Faces=top_face)
beamModel.Pressure(name='Uniform Applied Pressure', createStepName='Apply Load', region=top_face_region, distributionType=UNIFORM,
                   magnitude=10, amplitude=UNSET)
# -----------------------------------------------------------------------------------------------------------
# Apply Constraints and Boundary conditions
# Apply encastre boundary condition

fixed_end_face_pt_x = 0.2
fixed_end_face_pt_y = 0
fixed_end_face_pt_z = 0
fixed_end_face_pt = (fixed_end_face_pt_x,
                     fixed_end_face_pt_y, fixed_end_face_pt_z)

fixed_end_face = beamInstance.faces.findAt((fixed_end_face_pt,))
fixed_end_face_region = regionToolset.Region(faces=fixed_end_face)
beamModel.EncastreBC(name='Encaster one end',
                     createStepName='Initial', region=fixed_end_face_region)

# -----------------------------------------------------------------------------------------------------------
# Create the Mesh


# First we need to locate and select a point inside the solid
# We place a point somewhere inside it based on our knowledge of the geometry

beam_inside_xcoord = 0.2
beam_inside_ycoord = 0
beam_inside_zcoord = 2.5

elemType1 = mesh.ElemType(elemCode=C3D8R, elemLibrary=STANDARD, kinematicSplit=AVERAGE_STRAIN,
                          secondOrderAccuracy=OFF, hourglassControl=DEFAULT, distortionControl=DEFAULT)
beamCells = beamPart.cells
selectedBeamCells = beamCells.findAt(
    (beam_inside_xcoord, beam_inside_ycoord, beam_inside_zcoord),)
beamMeshRegion = (selectedBeamCells,)
beamPart.setElementType(regions=beamMeshRegion, elemTypes=(elemType1,))
beamPart.seedPart(size=0.1, deviationFactor=0.1)
beamPart.generateMesh()


# -----------------------------------------------------------------------------------------------------------
# Create and run the job


# Create the job
mdb.Job(name='CantileverBeamJob', model='Cantilever Beam', type=ANALYSIS,
        explicitPrecision=SINGLE, nodalOutputPrecision=SINGLE,
        description='Job simulates a loaded cantilever beam',
        parallelizationMethodExplicit=DOMAIN, multiprocessingMode=DEFAULT,
        numDomains=1, numCpus=1, memory=50,
        memoryUnits=PERCENTAGE, scratch='', echoPrint=OFF, modelPrint=OFF,
        contactPrint=OFF, historyPrint=OFF)

# Run the job
mdb.jobs['CantileverBeamJob'].submit(consistencyChecking=OFF)
# Do not return control till job is finished running
mdb.jobs['CantileverBeamJob'].waitForCompletion()
# End of run job

# -----------------------------------------------------------------------------------------------------------
# Post processing

beam_viewport = session.Viewport(name='Beam Results Viewport')
beam_Odb_Path = 'CantileverBeamJob.odb'
an_odb_object = session.openOdb(name=beam_Odb_Path)
beam_viewport.setValues(displayedObject=an_odb_object)
beam_viewport.odbDisplay.display.setValues(plotState=(DEFORMED, ))
