#!/usr/bin/env python

class Transformation(object):
    def __init__(self, Name, Parent):
        self.Name = Name
        self.Parent = Parent

    def __str__(self):
        return "{} ({})".format(self.Name, "Transformation")

class Translation(Transformation):
    def __init__(self, Name, Parent):
        super().__init__(Name, Parent)
        self.X = 0.0  # m
        self.Y = 0.0  # m
        self.Z = 0.0  # m
    def __str__(self):
        return "{} ({})".format(self.Name, "Translation")

class Rotation(Transformation):
    def __init__(self, Name, Parent):
        super().__init__(Name, Parent)
        self.X = 0.0  # m
        self.Y = 0.0  # m
        self.Z = 0.0  # m
        self.Angle = 0.0  # degrees
    def __str__(self):
        return "{} ({})".format(self.Name, "Rotation")

class TransformationList(list):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
    def __str__(self):
        return "Transformations"

class Component(object):
    def __init__(self, Name):
        self.Name = Name
        self.Transformations = TransformationList(self)
        self.Description = ""
    def __str__(self):
        return "{} ({})".format(self.Name, "Component")

class Mesh(Component):
    def __init__(self, Name, GeometryFile):
        super().__init__(Name)
        self.GeometryFile = GeometryFile
    def __str__(self):
        return "{} ({})".format(self.Name, "Mesh")

class Cylinder(Component):
    def __init__(self, Name):
        super().__init__(Name)
        self.Height = 1.0  # m
        self.Radius = 1.0  # m
        self.X = 0.0  # m
        self.Y = 0.0  # m
        self.Z = 0.0  # m
    def __str__(self):
        return "{} ({})".format(self.Name, "Cylinder")


