#!/usr/bin/env python

def generate_wrapper_component_list(input_model):
    return_list = []
    for component in input_model.components:
        return_list.append(Component(component))
    return return_list

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
    def __init__(self, original):
        self.original = original
        self.transformations = TransformationList(self)

    def __str__(self):
        return "{} ({})".format(self.original.name, self.original.nx_class)


