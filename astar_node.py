class Node:
    '''
    @params
        parent: the parent node
        position: the position of this node
        f: the total cost of the node (g + h)
        g: the cost from the start to this node
        h: an approximate cost from this node to the end
    '''

    def __init__(self, parent=None, position=None):
        self.parent = parent
        self.position = position
        self.f = 0
        self.g = 0
        self.h = 0

    def __eq__(self, other):
        return self.position == other.position

    def __hash__(self):
        return hash(self.position)
