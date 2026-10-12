from DRCF import *
import easypallet

# Get the names of all available EasyPallet projects
projects = easypallet.get_pallet_projects()

tp_log("Available projects:")
for name in projects:
    tp_log(str(name))

# Load a project
project = easypallet.get_project(projects[0])

# Get pallet information
pallet = project.get_pallet()

tp_log("Pallet:")
tp_log("  Length: " + str(pallet.length) + " mm")
tp_log("  Width: " + str(pallet.width) + " mm")

# Get box information
box = project.get_box()

tp_log("Box:")
tp_log("  Length: " + str(box.length) + " mm")
tp_log("  Width: " + str(box.width) + " mm")
tp_log("  Height: " + str(box.height) + " mm")
tp_log("  Weight: " + str(box.weight) + " kg")

# Get layer information
layers = project.get_layers()

tp_log("Number of layers: " + str(len(layers)))
tp_log("Total number of boxes: " + str(project.get_total_count()))