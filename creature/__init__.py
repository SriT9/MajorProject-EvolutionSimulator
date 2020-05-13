"Module to generate random connected graphs"
import tkinter as tk
from random import choice, randint, sample

import cv2
import numpy as np


def get_all_possible_edges(n):
    ''' Returns all the possible edges for a given number of vertices '''
    all_edges = set()
    for vertex_a in range(n):
        for vertex_b in range(vertex_a+1, n):
            all_edges.add((vertex_a, vertex_b))
    return all_edges


def create_edges(n):
    "Generation of random graph"
    all_edges = get_all_possible_edges(n)

    edges = set(
        filter(lambda edge: edge[0] + 1 == edge[1], all_edges))

    remaining_edges = all_edges - edges
    for _ in range(randint(0, len(remaining_edges))):
        random_edge = choice(list(remaining_edges))
        remaining_edges -= {(random_edge)}
        edges = edges.union({(random_edge)})
    return list(edges)


def create_vertices(n, size):
    "Generation of random vertices"
    vertices = set()
    for y in range(size):
        for x in range(size):
            vertices.add((y, x))
    return sample(vertices, n)


def resize_vertices(vertices, scale):
    "Resizes the vertices"
    output = []
    for vertex in vertices:
        output.append((vertex[0] * scale, vertex[1] * scale))
    return output


def find_adjacent_edges(my_edge, edges):
    "Finds the adjacent edges of an edge"
    adjacent = []
    for edge in edges:
        if tuple(edge) == tuple(my_edge):
            continue
        if my_edge[0] in edge:
            adjacent.append(edge)
    return adjacent


class Creature:
    ''' Saves the data of a creature '''
    count = 0

    def __init__(self, **kwargs):
        self.n = kwargs.get('n')

        identity = kwargs.get('identity', None)
        if identity is None:
            self.identity = Creature.count + 1
            Creature.count += 1
        else:
            self.identity = identity
        self.size = kwargs.get('size', 10)
        self.vertices = kwargs.get('vertices', create_vertices(self.n, self.size))
        self.edges = kwargs.get('edges', create_edges(self.n))
        self.fitness = kwargs.get('fitness', 0.0)
        self.parent = kwargs.get('parent', None)

        # Tkinter GUI
        view_port = kwargs.get('view_port', None)
        if view_port is not None:
            self.view_port = view_port
            self.frame = tk.Frame(self.view_port)
            self.right_click = None
            self.description = tk.Label(
                self.frame, font=(None, 7,), width=10, anchor='w', justify='left')
        else:
            self.view_port = None
            self.frame = None
            self.description = None

    def get_data(self):
        ''' Returns a picklable data '''
        return {
            'n': self.n,
            'identity': self.identity,
            'size': self.size,
            'vertices': self.vertices,
            'edges': self.edges,
            'fitness': self.fitness,
            'parent': self.parent,
        }

    def get_image(self, scale=50):
        ''' Returns a cv2 image representation of the creature '''
        vertices, edges = self.vertices, self.edges
        padding = scale
        paper = np.ones((scale*self.size, scale*self.size, 3)).astype(np.uint8) * 255
        paper = cv2.copyMakeBorder(
            paper,
            top=padding,
            bottom=padding,
            left=padding,
            right=padding, borderType=cv2.BORDER_CONSTANT, value=[255, 255, 255])
        vertices = resize_vertices(vertices, scale)

        padded_vertices = []
        for vertex in vertices:
            vertex = tuple([x + padding for x in vertex])
            padded_vertices.append(vertex)

        for edge in edges:
            start, end = padded_vertices[edge[0]], padded_vertices[edge[1]]
            cv2.line(paper, start, end, (0, 0, 255), scale//10+1, lineType=cv2.LINE_AA)
        for vertex in padded_vertices:
            cv2.circle(paper, vertex, scale//2, (255, 0, 0), -1, lineType=cv2.LINE_AA)
        return paper

    def draw_creature(self, scale=50):
        "Draws connected graph using vertices and edges"
        cv2.imshow("", self.get_image(scale))
        cv2.waitKey()

    def get_species(self):
        ''' Returns the species code of the creature '''
        return f'V{len(self.vertices)}'

    def set_description(self):
        ''' Sets the description label component '''
        self.description['text'] = (
            f'Creature {self.identity} \n'
            f'Fit.: {"{:.2f}".format(self.fitness)}\n'
            f'Spe.: {self.get_species()}'
        )
