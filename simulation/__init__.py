''' Moudule for simulating physics without gui '''
from timeit import timeit

from Box2D import b2World, b2PolygonShape, b2FixtureDef, b2EdgeShape
from tqdm import tqdm

from creature import Creature, find_adjacent_edges
from file import load_generations
from maths.maths import line_to_rectangle
from settings import DENSITY, FRICTION, MOTOR_SPEED, MAX_MOTOR_TORQUE, STEP_LIMIT


TIME_STEP = 1.0/60
VEL_ITERS, POS_ITERS = 8, 3
THICKNESS = 0.5


def create_creature_bodies(world, creatures):
    ''' Creates a list of creature bodies and returns reference bodies '''
    reference_body = {}
    for creature in creatures:
        body = {}
        for edge in creature.edges:
            vertex = creature.vertices[edge[0]], creature.vertices[edge[1]]
            point = line_to_rectangle(*vertex, THICKNESS)

            fixture = b2FixtureDef(
                shape=b2PolygonShape(vertices=point),
                density=DENSITY,
                friction=FRICTION,
            )
            fixture.filter.groupIndex = -1
            body[tuple(edge)] = world.CreateDynamicBody(
                fixtures=fixture,
            )

        for edge in creature.edges:
            adjacent = find_adjacent_edges(edge, creature.edges)
            for a_edge in adjacent:
                anchor = int(creature.vertices[edge[0]][0]), int(creature.vertices[edge[0]][1])
                world.CreateRevoluteJoint(
                    bodyA=body[tuple(edge)],
                    bodyB=body[tuple(a_edge)],
                    anchor=anchor,
                    collideConnected=True,
                    motorSpeed=MOTOR_SPEED,
                    maxMotorTorque=MAX_MOTOR_TORQUE,
                    enableMotor=True,
                )
        reference_body[creature.identity] = body[tuple(edge)]
    return reference_body


class Simulation:
    ''' Class that handles simulation of the world '''

    def __init__(self):
        self.world = b2World()
        self.floor = self.world.CreateBody(shapes=b2EdgeShape(vertices=[(-1000, -1), (1000, -1)]))

    def simulate(self, creatures, builder=None):
        ''' Simulates a bunch of creatures and returns thier fitness without gui '''
        uncompleted = list(filter(lambda c: c.fitness == 0.0, creatures))
        if builder is None:
            pbar = tqdm(total=STEP_LIMIT, ncols=100)
        bodies = create_creature_bodies(self.world, uncompleted)
        for i in range(STEP_LIMIT):
            if builder is not None:
                progress = i * 100 // STEP_LIMIT
                builder.get_object('progress')['value'] = progress
            else:
                pbar.update(1)
            self.world.Step(TIME_STEP, VEL_ITERS, POS_ITERS)
        if builder is None:
            pbar.close()

        output = {}
        for creature in creatures:
            if creature in uncompleted:
                output[creature.identity] = bodies[creature.identity].position[0]
            else:
                output[creature.identity] = creature.fitness
        for body in self.world.bodies:
            if body != self.floor:
                self.world.DestroyBody(body)
        self.world.ClearForces()
        return output

    def simulate_individually(self, creatures):
        ''' Simulates a bunch of creatures individually and returns thier fitness without gui '''
        pbar = tqdm(total=len(creatures), ncols=100)
        output = {}
        for creature in creatures:
            body = create_creature_bodies(self.world, [creature])[creature.identity]
            for _ in range(STEP_LIMIT):
                self.world.Step(TIME_STEP, VEL_ITERS, POS_ITERS)
            output[creature.identity] = body.position[0]
            self.world.DestroyBody(body)
            pbar.update()
        pbar.close()
        return output
