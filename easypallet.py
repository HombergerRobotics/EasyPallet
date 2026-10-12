import DRCF
import json
import os


class Pallet:
    """Represents a pallet with length and width dimensions."""

    def __init__(self):
        self.length = None
        self.width = None

    def get_length(self) -> float:
        """
        Get Pallet length.

        Returns: Pallet length.

        """
        return self.length

    def get_width(self) -> float:
        """
        Get Pallet width.

        Returns: Pallet width.

        """
        return self.width


class Box:
    """Represents a box with length, width, height, and weight."""

    def __init__(self):
        self.length = None
        self.width = None
        self.height = None
        self.weight = None

    def get_length(self) -> float:
        """
        Get Box length.

        Returns: Box length.

        """
        return self.length

    def get_width(self) -> float:
        """
        Get Box width.

        Returns: Box width.

        """
        return self.width

    def get_height(self) -> float:
        """
        Get Box height.

        Returns: Box height.

        """
        return self.height

    def get_weight(self) -> float:
        """
        Get Box weight.

        Returns: Box weight.

        """
        return self.weight


class BoxPlacement:
    """Represents the position and orientation of a box."""

    def __init__(self):
        self.x = None
        self.y = None
        self.th = None

    def get_x(self) -> float:
        """Get the X coordinate of the box placement in mm.

        Returns:
            The X coordinate of the box placement in mm.
        """
        return self.x

    def get_y(self) -> float:
        """Get the Y coordinate of the box placement in mm.

        Returns:
            The Y coordinate of the box placement in mm.
        """
        return self.y

    def get_th(self) -> float:
        """Get the box orientation.

        The orientation can be TH0, TH90, TH180, or TH270.

        Returns:
            The box orientation.
        """
        return self.th


class Layer:
    """Represents a layer containing boxes and an optional interlayer."""

    def __init__(self):
        self.boxes = []
        self.interlayer = None

    def get_boxes(self) -> list:
        """Get the boxes in the layer.

        Returns:
            A list of BoxPlacement objects representing the boxes
            in the layer.
        """
        return self.boxes

    def get_interlayer(self) -> bool:
        """Check whether the layer has an interlayer.

        Returns:
            True if the layer has an interlayer, False otherwise.
        """
        return self.interlayer


class EasyPalletProject:
    """Represents a palletization project containing pallet and box specifications
    and the arrangement of boxes across multiple layers.

    The project provides access to the pallet, box, and layer data, as well as
    utilities for counting and navigating the palletized boxes.
    """

    def __init__(self):
        self.pallet = None
        self.box = None
        self.layers = []

    def get_pallet(self) -> Pallet:
        """
        Get Pallet data.

        Returns: Pallet data.

        """
        return self.pallet

    def get_box(self) -> Box:
        """
        Get Box data.

        Returns: Box data.

        """
        return self.box

    def get_layers(self) -> list:
        """Get the layers in the project.

        Returns:
        A list of Layer objects representing the project layers.
        """
        return self.layers

    def get_total_count(self):
        """Get the total number of palletized boxes.

        Returns:
            The total number of boxes across all layers.
        """
        counter = 0
        for index in range(len(self.layers)):
            counter = counter + len(self.layers[index].boxes)

        return counter

    def get_count(self, layer, box):
        """Get the sequential box count for a layer and box position.

        Args:
            layer: The index of the layer.
            box: The index of the box within the layer.

        Returns:
            The sequential index of the box across all layers.
        """
        if box >= len(self.layers[layer].boxes):
            box = 0
            layer = layer + 1

        if layer >= len(self.layers):
            layer = 0

        counter = 0
        for index in range(layer):
            counter += len(self.layers[index].boxes)
        counter += box
        return counter

    def get_next_count(self, layer, box):
        """Get the layer and box index of the next box.

        Args:
            layer: The index of the current layer.
            box: The index of the current box within the layer.

        Returns:
            A tuple containing the layer index and box index of the next box.
        """
        box = box + 1
        if box >= len(self.layers[layer].boxes):
            box = 0
            layer = layer + 1

        if layer >= len(self.layers):
            layer = 0

        return layer, box


class EasyPalletBuilder:
    """Builds and manages palletizing operations based on an EasyPallet project.

        The EasyPalletBuilder loads a palletization layout created with the
        graphical EasyPallet editor and provides access to the configured pallet,
        box, and layer data. It can be used to iterate through the boxes in
        palletizing or depalletizing order and to calculate the robot pose
        required to pick or place each box.

        The builder also supports starting the palletizing sequence from a
        specific layer and box and applying calibration data to the calculated
        box poses.

        Args:
            name: Name of the EasyPallet editor project to load.
    """

    def __init__(self, name):
        """Initialize the EasyPalletBuilder and load the specified project.

        Args:
            name: Name of the EasyPallet editor project to load.
        """
        self.name = None
        self.project = None

        self.current_layer = 0
        self.current_box = 0

        self.offset = [0, 0, 0, 0]

        self.box_frame = None
        self.pick_delta = None
        self.box_l = None
        self.box_w = None
        self.box_h = None
        self.calibrated = False

        self.depalletizing = False

        self.load_project(name)

    def load_project(self, name):
        """Load an EasyPallet project.

            The specified project must be available in the configured EasyPallet
            projects. Loading a new project replaces the currently loaded project.

            Args:
                name: Name of the EasyPallet project to load.

            Raises:
                DR_Error: If the specified project does not exist.
            """
        if name not in get_pallet_projects():
            raise DRCF.DR_Error(DRCF.DR_ERROR_RUNTIME, "EasyPallet project " + name + " does NOT exists.")

        self.project = get_project(name)
        self.name = name

    def __iter__(self):
        """Initialize and return the palletizing iterator.

        Returns:
            The current EasyPalletBuilder instance.
        """
        self._first_iteration = True
        return self

    def __next__(self):
        """Get the next box in the palletizing or depalletizing sequence.

            In palletizing mode, boxes are returned from the first layer to the last
            layer. In depalletizing mode, boxes are returned in reverse order.

            Returns:
                The next BoxPlacement in the iteration sequence.

            Raises:
                StopIteration: When all boxes have been processed.
        """
        if not self.depalletizing:
            # FORWARD MODE
            if self.current_layer >= len(self.project.layers):
                raise StopIteration

            if self._first_iteration:
                self._first_iteration = False

                if self.current_box >= len(self.project.layers[self.current_layer].boxes):
                    self.current_box = 0
                    self.current_layer = self.current_layer + 1

                if self.current_layer >= len(self.project.layers):
                    self.current_layer = 0

            else:
                self.current_box += 1
                if self.current_box >= len(self.project.layers[self.current_layer].boxes):
                    self.current_layer += 1
                    if self.current_layer >= len(self.project.layers):
                        raise StopIteration
                    self.current_box = 0

        else:
            # REVERSE MODE
            if self.current_layer < 0:
                raise StopIteration

            if self._first_iteration:
                self._first_iteration = False
            else:
                self.current_box -= 1
                if self.current_box < 0:
                    self.current_layer -= 1
                    if self.current_layer < 0:
                        raise StopIteration
                    self.current_box = len(self.project.layers[self.current_layer].boxes) - 1

        return self.project.layers[self.current_layer].boxes[self.current_box]

    def start_from(self, layer, box):
        """Set the starting position for palletizing or depalletizing iteration.

            Args:
                layer: Zero-based index of the layer to start from.
                box: Zero-based index of the box within the layer to start from.
        """
        self.current_layer = layer
        self.current_box = box

    def get_project(self) -> EasyPalletProject:
        """Get the currently loaded EasyPallet project.

            Returns:
                The currently loaded EasyPalletProject instance.
        """
        return self.project

    def _get_th(self, value):
        if value == "TH0":
            return 0
        elif value == "TH90":
            return 90
        elif value == "TH180":
            return 180
        elif value == "TH270":
            return -90
        else:
            return 0

    def get_current_pose(self, palletizing_mode=True):
        """Calculate the robot pose for the currently selected box.

            The pose is calculated from the current layer and box position defined
            by the iterator. The pose coordinates are expressed in the pallet reference frame.

            If the builder has been calibrated, the calibration
            transformation is applied to the calculated pose. Otherwise, the
            configured position offsets are applied.

            Args:
                palletizing_mode: If True, the B-axis angle is forced to 180 degrees.
                    If False, the calculated orientation is preserved.

            Returns:
                The robot pose corresponding to the current box.
        """
        x = self.project.layers[self.current_layer].boxes[self.current_box].x
        y = self.project.layers[self.current_layer].boxes[self.current_box].y
        z = (1 + self.current_layer) * self.project.box.height
        th = self.project.layers[self.current_layer].boxes[self.current_box].th

        if self.calibrated:
            result = DRCF.htrans(DRCF.posx(x, y, z, self._get_th(th), 0, 0), self.pick_delta)
            if palletizing_mode:
                result[4] = 180
            return result
        else:
            return DRCF.posx(x + self.offset[0], y + self.offset[1], z + self.offset[2], self._get_th(th), 180,
                             self.offset[3])

    def get_box_pose(self, layer, box, palletizing_mode=True):
        """Calculate the robot pose for a specific box in the project.

            The pose is calculated from the box position, layer height, and box
            orientation. If the builder has been calibrated, the calibration
            transformation is applied to the calculated pose. Otherwise, the
            configured position offsets are applied.

            Args:
                layer: Zero-based index of the layer containing the box.
                box: Zero-based index of the box within the layer.
                palletizing_mode: If True, the B-axis angle is forced to 180 degrees.
                    If False, the calculated orientation is preserved.

            Returns:
                The robot pose corresponding to the specified box.
        """
        x = self.project.layers[layer].boxes[box].x
        y = self.project.layers[layer].boxes[box].y
        z = (1 + layer) * self.project.box.height
        th = self.project.layers[layer].boxes[box].th

        if self.calibrated:
            result = DRCF.htrans(DRCF.posx(x, y, z, self._get_th(th), 0, 0), self.pick_delta)
            if palletizing_mode:
                result[4] = 180
            return result
        else:
            return DRCF.posx(x + self.offset[0], y + self.offset[1], z + self.offset[2], self._get_th(th), 180,
                             self.offset[3])

    def get_pick_pose(self):
        """Calculate the robot pick pose for the current box.

            The pick pose is calculated from the current box position and orientation
            and adjusted using the configured pick transformation. When calibration
            data is available, the calibrated transformation is applied to the pose.

            This function can be used only if palletizing project has been calibrated.

            Args:
                palletizing_mode: If True, the B-axis angle is forced to 180 degrees.
                    If False, the calculated orientation is preserved.

            Returns:
                The calibrated robot pose to use for picking the current box.
            """
        box_origin_frame = DRCF.htrans(self.box_frame,
                                       DRCF.posx(-self.box_l / 2, -self.box_w / 2, -self.box_h, 0, 0, 0))
        new_box_frame = DRCF.htrans(box_origin_frame, DRCF.posx(self.project.box.length / 2, self.project.box.width / 2,
                                                                self.project.box.height, 0, 0, 0))
        return DRCF.htrans(new_box_frame, self.pick_delta)

    def is_layer_completed(self) -> bool:
        """Check whether the current layer has reached its last box.

        This method can be used to determine when the current layer is complete
        and when an interlayer or cardboard sheet may need to be placed.

        Returns:
            True if the current box is the last box in the current layer,
            False otherwise.
        """
        return self.current_box >= len(self.project.layers[self.current_layer].boxes) - 1

    def has_interlayer(self):
        """Check whether the current layer requires an interlayer. This method checks the interlayer configuration of
        the current layer and can be used to determine whether a cardboard or interlayer sheet should be placed
        before continuing with the palletizing operation.

        Returns:
            True if the current layer requires an interlayer, False otherwise.
        """
        return self.project.layers[self.current_layer].interlayer is not None and self.project.layers[
            self.current_layer].interlayer

    def get_current_box(self):
        """Get the index of the current box in the execution sequence.

        Returns:
            The zero-based index of the current box within the current layer.
        """
        return self.current_box

    def get_current_layer(self) -> int:
        """Get the index of the current layer in the execution sequence.

        Returns:
            The zero-based index of the current layer.
        """
        return self.current_layer

    def get_current_count(self):
        """Get the current number of palletized boxes. In palletizing mode, the count represents the number of boxes
        that have been reached in the forward execution sequence.

        In depalletizing mode, the count is calculated according to the reverse execution sequence.

        Returns:
            The current box count in the execution sequence.
        """

        if not self.depalletizing:
            counter = 0
            for index in range(self.current_layer):
                counter += len(self.project.layers[index].boxes)
            counter += self.current_box
            return counter
        else:
            counter = 0
            for index in range(self.current_layer + 1, len(self.project.layers)):
                counter += len(self.project.layers[index].boxes)

            counter += (
                    len(self.project.layers[self.current_layer].boxes)
                    - self.current_box - 1
            )
            return counter

    def get_box_count(self, layer, box):
        """Get the sequential box count for a specified layer and box.

        The count is calculated according to the current execution mode.
        In palletizing mode, boxes are counted from the beginning of the palletization
        sequence. In depalletizing mode, the count follows the reverse execution sequence.
        Args:
            layer: Zero-based index of the layer.
            box: Zero-based index of the box within the specified layer.

        Returns:
            The sequential box count for the specified position.
        """
        if not self.depalletizing:
            counter = 0
            for index in range(layer):
                counter += len(self.project.layers[index].boxes)
            counter += box
            return counter
        else:
            counter = 0
            for index in range(self.current_layer + 1, len(self.project.layers)):
                counter += len(self.project.layers[index].boxes)

            counter += (
                    len(self.project.layers[self.current_layer].boxes)
                    - self.current_box - 1
            )
            return counter

    def set_offset(self, x=0, y=0, z=0, th=0):
        """Set positional and orientation offsets for palletizing positions.

        The offsets are applied to the calculated palletizing poses when the builder is not using calibration data.
        The offsets can be provided either as four individual values or as a list containing the values in X, Y, Z, and
        orientation order.

        Args:
            x: Offset along the X axis.
            y: Offset along the Y axis.
            z: Offset along the Z axis.
            th: Orientation offset. """
        if isinstance(x, list):
            self.offset = x
        else:
            self.offset = [x, y, z, th]

    def calibrate(self, p1, p2, p3, box_l, box_w, box_h, pick_pose):
        """Calibrate the box picking position for the palletizing process. This procedure establishes the relationship
        between a box coordinate frame and the robot picking position.
        A reference box is used to teach three points defining its position and orientation, together with its
        dimensions and the desired picking pose.
        The resulting calibration is then used to calculate the appropriate pick position for other boxes based on
        their dimensions and palletizing positions.

        Calibration procedure:
        1. Place a reference box at the picking position.
        2. Determine whether the setup is Left or Right.
        3. Teach the three reference points P1, P2, and P3 on the box.
        4. Teach the picking position for the reference box.
        5. Specify the dimensions of the reference box.

        Args:
            p1: Position defining the box origin.
            p2: Position defining the box X-axis direction.
            p3: Position defining the box Y-axis direction.
            box_l: Length of the reference box.
            box_w: Width of the reference box.
            box_h: Height of the reference box.
            pick_pose: Robot pose used to pick the reference box. """
        self.box_frame = DRCF.htrans(DRCF.calc_coord(p1, p2, p3, p1, ref=DRCF.DR_BASE, mod=0),
                                     DRCF.posx(box_l / 2, box_w / 2, 0, 0, 0, 0))
        self.pick_delta = DRCF.htrans(DRCF.inverse_pose(self.box_frame), pick_pose)
        self.calibrated = True
        self.box_l = box_l
        self.box_w = box_w
        self.box_h = box_h

    def set_depalletizing(self, value):
        self.depalletizing = value


def get_pallet_projects():
    """
    Get list of EasyPallet projects saved on the robot system.

    Returns:
        list of EasyPallet project names.

    """
    projects = []
    if os.path.isdir("/opt/easypallet"):
        for file in os.listdir("/opt/easypallet"):
            if file.endswith(".pallet"):
                projects.append(file.replace(".pallet", ""))
    return projects


def delete_pallet_project(project):
    """
    Delete specified EasyPallet project from robot system.

    Args:
        project: (str) project name
    """
    os.remove("/opt/easypallet/" + project + ".pallet")


def get_project(name):
    """
    Get a EasyPallet project saved on the robot system.

    Args:
        name: (str) project name
    """
    if name not in get_pallet_projects():
        raise DRCF.DR_Error(DRCF.DR_ERROR_RUNTIME, "EasyPallet project " + name + " does NOT exists.")

    project_path = "/opt/easypallet/" + name + ".pallet"
    file = open(project_path)
    project_map = json.load(file)

    project = EasyPalletProject()

    pallet = Pallet()
    pallet.width = project_map["pallet"]["width"]
    pallet.length = project_map["pallet"]["length"]
    project.pallet = pallet

    box = Box()
    box.width = project_map["box"]["width"]
    box.length = project_map["box"]["length"]
    box.height = project_map["box"]["height"]
    box.weight = project_map["box"]["weight"]
    project.box = box

    for layer_map in project_map["layers"]:
        layer = Layer()
        layer.interlayer = layer_map["interlayer"]
        for box_map in layer_map["boxes"]:
            box_placement = BoxPlacement()
            box_placement.x = box_map["x"]
            box_placement.y = box_map["y"]
            box_placement.th = box_map["th"]
            layer.boxes.append(box_placement)
        project.layers.append(layer)

    return project
