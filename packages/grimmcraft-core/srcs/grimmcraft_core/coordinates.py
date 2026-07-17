"""
a coordinate class
"""

class Coordinate:
    def __init__(self, x: int, y: int, z: int) -> None:
        self.x = x
        self.y = y
        self.z = z

    @property
    def xyz(self):
        return (self.x, self.y, self.z)

    @property.setter
    def set_xyz(self, x : int, y : int, z :int):
        self.x = x
        self.y = y
        self.z = z
