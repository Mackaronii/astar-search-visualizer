from astar_node import Node
from operator import attrgetter
import time
import math


class AStarModel:
    def __init__(self, view=None, nRow: int = 10, nCol: int = 10):
        self.__view = view

        # Validate arguments
        if nRow < 1:
            raise ValueError(
                "There must be at least 1 row. Received {} rows instead.".format(nRow))

        if nCol < 1:
            raise ValueError(
                "There must be at least 1 column. Received {} columns instead.".format(nCol))

        self.__nRow = nRow
        self.__nCol = nCol

        # Default top-left start node and bottom-right end node
        self.__start = (0, 0)
        self.__end = (self.__nRow - 1, self.__nCol - 1)

        # Takes part in determining whether or not to update the GUI
        self.__is_currently_solving = False

        # Stores symbols representing walls, unsolved, solved, or path nodes
        self.__curr_maze = []
        self.__prev_maze = []

        # Containers for solving
        self.unsolved = set()
        self.solved = set()
        self.path = []

        self.__settings = {
            "allowDiagonals": True,
            "enablePrintToConsole": True
        }

        self.__stats = {
            "numUnsolved": 0,
            "numSolved": 0,
            "numPath": 0,
            "elapsedTime": 0
        }

        # Initialize a 2D array representing the walls in the maze
        self.__walls = set()

        # Initialize a 2D containing symbols representing the maze
        self.__initialize_maze()

    def __initialize_maze(self):
        """ Initializes a 2D array representing the maze.

        Initially, the maze only contains [space] characters
        in addition to the start and end characters.

        Args:
            None

        Returns:
            None
        """
        self.__curr_maze = [[" "] * self.__nCol for _ in range(self.__nRow)]
        self.__prev_maze = self.__curr_maze
        self.__curr_maze[self.__start[0]][self.__start[1]] = "S"
        self.__curr_maze[self.__end[0]][self.__end[1]] = "E"

    def __update_maze(self, is_rapid_config):
        """ Updates the maze array to reflect the current search state.

        By maintaining the maze array, the GUI can be easily updated
        after each iteration of the search.

        Symbols:
            [space] - Empty
            W - Wall
            S - Start
            E - End
            ? - Unsolved
            X - Solved
            P - Path

        Args:
            None

        Returns:
            None
        """
        # Update stats
        self.__update_stats()

        # Store current maze into previous maze
        self.__prev_maze = self.__curr_maze

        # Clear potentially removed symbols ("S", "E", or "W")
        self.__curr_maze = [[" "] * self.__nCol for _ in range(self.__nRow)]

        # Update the current maze
        for x in range(self.__nRow):
            for y in range(self.__nCol):
                symbol = " "
                if self.__is_wall((x, y)):
                    symbol = "W"
                elif Node(position=(x, y)) in self.solved:
                    symbol = "X"
                elif Node(position=(x, y)) in self.unsolved:
                    symbol = "?"

                self.__curr_maze[x][y] = symbol

        # Path symbols overwrite wall, solved, and unsolved symbols
        for (x, y) in self.path:
            self.__curr_maze[x][y] = "P"

        # Start and end symbols overwrite everything
        self.__curr_maze[self.__start[0]][self.__start[1]] = "S"
        self.__curr_maze[self.__end[0]][self.__end[1]] = "E"

        if self.__settings["enablePrintToConsole"]:
            self.print_maze()

        # Update the GUI
        self.__notify_maze_changed(is_rapid_config)

    def __update_stats(self):
        """ Updates some metrics.

        Args:
            None

        Returns:
            None
        """
        self.__stats["numUnsolved"] = len(self.unsolved)
        self.__stats["numSolved"] = len(self.solved)
        self.__stats["numPath"] = len(self.path)

        if self.is_solving():
            self.__stats["elapsedTime"] = "{:.3f}".format(
                time.time() - self.__start_time)

    def __notify_maze_changed(self, is_rapid_config):
        """ Notifies the attached view to update its interface based on the new data.
        Only update nodes that have changed to improve performance.

        Args:
            is_rapid_config::[bool]
                Calls update_idletasks() on the GUI if true, and update() if false

        Returns:
            None
        """
        if self.__view is not None:
            diff_positions = self.__get_diff_positions()
            self.__view.update_gui(
                maze=self.__curr_maze,
                diff_positions=diff_positions,
                is_rapid_config=is_rapid_config)

    def __get_diff_positions(self):
        """ Returns a list of positions representing the positions that differ between
        the current maze and the previous maze.

        Args:
            None

        Returns:
            diff_positions::[list]
                The positions that differ between the current and previous mazes
        """
        diff_positions = []

        # Only update nodes that have changed
        for x in range(self.__nRow):
            for y in range(self.__nCol):
                if self.__curr_maze[x][y] != self.__prev_maze[x][y]:
                    diff_positions.append((x, y))

        return diff_positions

    """
    GETTERS.
    """

    def get_nrow(self):
        return self.__nRow

    def get_ncol(self):
        return self.__nCol

    def get_curr_maze(self):
        return self.__curr_maze

    def get_walls(self):
        return self.__walls

    def get_start(self):
        return self.__start

    def get_end(self):
        return self.__end

    def is_solving(self):
        return self.__is_currently_solving

    def get_setting(self, setting):
        if setting not in self.__settings:
            raise ValueError(
                "The setting [{}] does not exist.".format(setting))
        return self.__settings[setting]

    def get_stat(self, stat):
        if stat not in self.__stats:
            raise ValueError("The stat [{}] does not exist.".format(stat))
        return self.__stats[stat]

    """
    SETTERS.
    """

    def stop_solving(self):
        self.__is_currently_solving = False

    def set_setting(self, setting, val):
        if setting not in self.__settings:
            raise ValueError(
                "The setting [{}] does not exist.".format(setting))
        self.__settings[setting] = val

    """
    SETTERS FOR SPECIAL NODES.
    """

    def set_start(self, start):
        if self.__is_position_valid(start):
            if not self.__is_wall(start) and start != self.__end:
                self.__clear_solve_containers()
                if self.__settings["enablePrintToConsole"]:
                    print("Setting new start point: {}".format(start))
                self.__start = start
                self.__update_maze(is_rapid_config=True)
            elif self.__settings["enablePrintToConsole"]:
                raise ValueError(
                    "The starting position cannot be the same as the end position or a wall: {}".format(start))
        else:
            raise ValueError(
                "The provided start position is out of bounds for an {} x {} maze: {}".format(self.__nRow, self.__nCol, start))

    def set_end(self, end):
        if self.__is_position_valid(end):
            if not self.__is_wall(end) and end != self.__start:
                self.__clear_solve_containers()
                if self.__settings["enablePrintToConsole"]:
                    print("Setting new end point: {}".format(end))
                self.__end = end
                self.__update_maze(is_rapid_config=True)
            elif self.__settings["enablePrintToConsole"]:
                raise ValueError(
                    "The end position cannot be the same as the starting position or a wall: {}".format(end))
        else:
            raise ValueError(
                "The provided end position is out of bounds for an {} x {} maze: {}".format(self.__nRow, self.__nCol, end))

    def set_wall(self, pos, val: bool):
        if self.__is_position_valid(pos):
            # You cannot place a wall ontop of the start and end nodes
            if pos != self.__start and pos != self.__end:
                self.__clear_solve_containers()

                if self.__settings["enablePrintToConsole"]:
                    print("{} wall: {}".format(
                        "Setting" if val else "Removing", str(pos)))

                x, y = pos

                # Set / remove wall
                if val:
                    self.__walls.add(pos)
                elif pos in self.__walls:
                    self.__walls.remove(pos)

                self.__update_maze(is_rapid_config=True)

            elif self.__settings["enablePrintToConsole"]:
                raise ValueError(
                    "You cannot place a wall ontop of a start or end node: {}".format(pos))
        else:
            raise ValueError(
                "The provided wall position is out of bounds for an {} x {} maze: {}".format(self.__nRow, self.__nCol, pos))

    def import_maze_data(self, maze_data):
        self.__start = tuple(maze_data['start'])
        self.__end = tuple(maze_data['end'])
        self.__walls = set([tuple(wall) for wall in maze_data['walls']])
        self.__update_maze(is_rapid_config=True)

    def __clear_solve_containers(self):
        self.unsolved = set()
        self.solved = set()
        self.path = []
        self.__stats["elapsedTime"] = 0

    """
    VALIDATION METHODS.
    """

    def __is_position_valid(self, pos):
        return 0 <= pos[0] < self.__nRow and 0 <= pos[1] < self.__nCol

    def __is_wall(self, pos):
        return pos in self.__walls

    def __can_move_to_node(self, node):
        # You can move to a node if it is at a valid position and if it is not a wall
        pos = node.position
        return self.__is_position_valid(pos) and not self.__is_wall(pos)

    """
    PRINT METHODS.
    """

    def print_maze(self):
        [print(row) for row in self.__curr_maze]
        print()

    def print_path(self):
        print("Path: {}".format(" -> ".join(map(str, self.path))))

    """
    SEARCH METHODS.
    """

    def __calculate_path(self, curNode):
        self.path = []

        # Iterate through the parent nodes of the end node until the start node is reached
        while (curNode is not None):
            self.path.append(curNode.position)
            curNode = curNode.parent

        self.path.reverse()

    def solve(self):
        self.__is_currently_solving = True
        self.__start_time = time.time()
        self.__clear_solve_containers()

        # Constant offsets
        DIAGONAL_OFFSETS = [(-1, 1), (1, 1), (-1, -1), (1, -1)]
        OFFSETS = [(0, 1), (-1, 0), (1, 0), (0, -1)]

        # Add DIAGONAL_OFFSETS to OFFSETS if diagonal movement is allowed
        if self.__settings["allowDiagonals"]:
            OFFSETS.extend(DIAGONAL_OFFSETS)

        print("Solving the maze starting at {} and ending at {}.".format(
            self.__start, self.__end))

        # Start and end nodes
        startNode = Node(None, self.__start)
        endNode = Node(None, self.__end)

        # Queue the starting node
        self.unsolved.add(startNode)

        while self.is_solving() and len(self.unsolved) != 0:
            self.__update_maze(is_rapid_config=False)

            # Get the node with the minimum 'f' value from the unsolved list
            curNode = min(self.unsolved, key=attrgetter("f"))

            # Remove the current node from the unsolved list and append it to the solved list
            self.unsolved.remove(curNode)
            self.solved.add(curNode)

            # Done if the current node is the end node
            if curNode == endNode:
                self.stop_solving()
                self.__calculate_path(curNode)
                self.print_path()
                self.__update_maze(is_rapid_config=False)
                print(
                    "A* search completed in {} seconds!\n".format(self.__stats["elapsedTime"]))
                return True

            # Check adjacent nodes
            for offset in OFFSETS:
                offsetPos = (curNode.position[0] + offset[0],
                             curNode.position[1] + offset[1])

                adjNode = Node(None, offsetPos)

                # Don't do anything if the adjacent node is a wall or already solved
                if not self.__can_move_to_node(adjNode) or adjNode in self.solved:
                    continue

                # Calculate adjacent node properties
                adjNode.parent = curNode
                adjNode.g = curNode.g + 1
                adjNode.h = math.sqrt(abs(endNode.position[0] - adjNode.position[0]) ** 2 + abs(
                    endNode.position[1] - adjNode.position[1]) ** 2)
                adjNode.f = adjNode.g + adjNode.h

                # Add adjacent nodes to the unsolved list
                if adjNode not in self.unsolved:
                    self.unsolved.add(adjNode)

                # Update the adjacent node in the unsolved list if the new g value is less than the old g value
                else:
                    # Get the existing adjacent node from the unsolved list
                    for existingNode in self.unsolved:
                        if existingNode.__eq__(adjNode):
                            # Update the existing node's values
                            if adjNode.g < existingNode.g:
                                existingNode.g = adjNode.g
                                existingNode.f = adjNode.f
                                existingNode.parent = adjNode.parent

        # Failed to find a path
        self.stop_solving()
        self.__update_maze(is_rapid_config=False)
        print("Failed to complete the search in {} seconds.\n".format(
            self.__stats["elapsedTime"]))
        return False


def main():
    print("Starting A* search application.\n")
    model = AStarModel(nRow=10, nCol=10)
    model.set_start((1, 2))
    model.set_end((4, 4))
    model.set_wall((2, 3), True)
    model.solve()


if __name__ == '__main__':
    main()
