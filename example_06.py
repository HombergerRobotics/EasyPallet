from DRCF import *
import easypallet

# User coordinate frame IDs configured in the Doosan teach pendant.
# FRAME_A and FRAME_B define the reference frames for the two pallets.
# FRAME_BOX defines the reference frame used for picking boxes.
FRAME_A = 101
FRAME_B = 102
FRAME_BOX = 103

# Identifiers used to select the active pallet side.
A = "A"
B = "B"

# Configure these variables as System variables in the Doosan teach
# pendant if their values must be preserved between robot restarts.
System_selected_pallet = A
System_box_start = 1          # One-based index of the starting box.
System_layer_start = 1        # One-based index of the starting layer.
System_selected_project = None  # Name of the EasyPallet project to load.

# Retrieve the names of the projects available in EasyPallet Editor.
# This list can be used to populate a project-selection interface.
projects = easypallet.get_pallet_projects()

# Initialize the number of boxes processed and the total number of boxes.
current_count = 0
total_count = 0


# Implement these functions with the commands required to control
# the robot gripper or other end-of-arm tooling.
def grasp():
    pass


def release():
    pass


def load_project():
    """Load the selected project and initialize its box counters."""
    global total_count, current_count

    # Continue only if a project has been selected.
    if System_selected_project:
        project = easypallet.get_project(System_selected_project)

        # Get the total number of boxes and calculate the sequential
        # count corresponding to the configured starting position.
        # Convert the one-based operator indexes to zero-based indexes.
        total_count = project.get_total_count()
        current_count = project.get_count(
            System_layer_start - 1,
            System_box_start - 1
        )


def start_task():
    """Execute the palletizing sequence from the selected position."""
    global System_layer_start, System_box_start, total_count, current_count

    # Load the palletizing layout created with EasyPallet Editor.
    builder = easypallet.EasyPalletBuilder(System_selected_project)

    # Read the dimensions of the box defined in the project.
    # The X and Y coordinates locate the center of the box footprint.
    # The Z coordinate corresponds to the top surface of the box.
    box_x = builder.get_project().get_box().get_length() / 2
    box_y = builder.get_project().get_box().get_width() / 2
    box_z = builder.get_project().get_box().get_height()

    # Define the picking pose in the box reference frame, then transform
    # it into the robot base frame for the picking movements.
    pick_pose = coord_transform(
        posx(box_x, box_y, box_z, 0, 180, 0),
        ref_in=FRAME_BOX,
        ref_out=DR_BASE
    )

    # Select the reference frame corresponding to the active pallet.
    if System_selected_pallet == A:
        pallet_frame = FRAME_A
    else:
        pallet_frame = FRAME_B

    # Set the iterator to the requested starting layer and box.
    # EasyPallet uses zero-based indexes, so subtract one from each
    # one-based index configured by the operator.
    builder.start_from(
        System_layer_start - 1,
        System_box_start - 1
    )

    # Retrieve the total number of boxes in the selected project.
    total_count = builder.get_project().get_total_count()

    # Iterate through the boxes from the configured starting position.
    for box_placement in builder:

        # Save the current position using one-based indexes so it can
        # be displayed to the operator or restored after a restart.
        System_layer_start = builder.get_current_layer() + 1
        System_box_start = builder.get_current_box() + 1

        # Move to a point 100 mm above the picking pose.
        # This approach movement helps avoid approaching the box
        # horizontally at the picking height.
        movejx(
            trans(pick_pose, posx(z=100)),
            sol=get_current_solution_space()
        )

        # Move down to the picking pose.
        movel(pick_pose)

        # Grip the box using the configured end-of-arm tooling.
        grasp()

        # Retract 100 mm from the picking position after grasping.
        movel(trans(pick_pose, posx(z=100)))

        # Calculate the placement pose for the current box from
        # the EasyPallet layout.
        # The pose is interpreted relative to the selected pallet frame
        # in the following robot movements.
        place_pose = builder.get_current_pose()

        # Move to an approach position above and slightly offset from
        # the target placement position.
        # The X and Y offsets are 20 mm; the Z offset is 100 mm.
        # The pallet frame defines the coordinate system for this move.
        movejx(
            trans(place_pose, posx(x=20, y=20, z=100)),
            ref=pallet_frame,
            sol=get_current_solution_space()
        )

        # Move to the final placement pose on the pallet.
        movel(place_pose, ref=pallet_frame)

        # Release the box at the target position.
        release()

        # Retract 100 mm from the placement position before continuing.
        movel(
            trans(place_pose, posx(z=100)),
            ref=pallet_frame
        )

        # Update the number of boxes processed in the current sequence.
        current_count = builder.get_current_count()

    # Reset the starting position after the sequence completes.
    System_layer_start = 1
    System_box_start = 1