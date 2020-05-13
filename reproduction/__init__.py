''' Module to create offsprings of a creature '''
from random import randint, choice, shuffle
from copy import copy

from creature import Creature
from creature import get_all_possible_edges

from settings import MAX_EDGE_CHANGE_COUNT, MAX_VERTICES_PIXEL_CHANGE


def change_structure(offspring: Creature):
    ''' Changes the structure of a offspring and returns it '''
    all_edges = get_all_possible_edges(offspring.n)
    add_list = all_edges - set(offspring.edges)
    remove_list = set(filter(lambda edge: edge[0] + 1 != edge[1], offspring.edges))
    add = choice([True, False]) if add_list != set() else False
    if remove_list == set():
        add = True

    if add:
        # Adding edges logic
        edges = set(offspring.edges)
        for _ in range(randint(1, MAX_EDGE_CHANGE_COUNT)):
            if add_list == set():
                break
            random_edge = choice(list(add_list))
            add_list -= {(random_edge)}
            edges = edges.union({(random_edge)})
        offspring.edges = list(edges)
    else:
        # Removing edges logic
        edges = set(offspring.edges)
        for _ in range(randint(1, MAX_EDGE_CHANGE_COUNT)):
            if remove_list == set():
                break
            random_edge = choice(list(remove_list))
            remove_list -= {(random_edge)}
            edges = edges - {random_edge}
        offspring.edges = list(edges)

    vertex = offspring.vertices[0]
    x_del = randint(1, MAX_VERTICES_PIXEL_CHANGE)
    y_del = randint(1, MAX_VERTICES_PIXEL_CHANGE)
    x = vertex[0] + x_del * choice([-1, 1])
    x = max(0, x)
    x = min(offspring.size-1, x)
    y = vertex[1] + y_del * choice([-1, 1])
    y = max(0, y)
    y = min(offspring.size-1, y)
    offspring.vertices[0] = (x, y)
    return offspring


def reproduce(creature: Creature, serializable_creatures: dict):
    ''' Creates a offsprings of a creature by adding or removing some edges '''
    offspring = Creature(n=creature.n, view_port=creature.view_port, size=creature.size)
    offspring.vertices = copy(creature.vertices)
    offspring.edges = copy(creature.edges)
    offspring.parent = creature.identity

    offspring = change_structure(offspring)
    parent_id = offspring.parent
    parent = serializable_creatures[parent_id]

    while True:
        if parent is None:
            break
        if parent['vertices'] == offspring.vertices and parent['edges'] == offspring.edges:
            offspring = change_structure(offspring)
        else:
            if 'parent' not in parent:
                break
            if parent['parent'] is None:
                break
            parent_id = parent['parent']
            parent = serializable_creatures[parent_id]

    return offspring
