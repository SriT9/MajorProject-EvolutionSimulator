''' Main script of the program '''
import tkinter as tk
import threading
import os
import random
from copy import copy

from PIL import Image, ImageTk
import easygui

from gui import Gui, ContextMenu, ScrollFrame
from gui.utils import set_entry
from environment import Environment
from framework.framework import main as framework
from reproduction import reproduce
from analytics import show_analytics
from creature import Creature
from file import save_generations, load_generations
from simulation import Simulation
from util import get_default_name
from settings import (
    POPULATION_SIZE, SELECTION_SIZE, OFFSPRINGS_PER_SELECTION_SIZE, RANDOM_NEW_POPULATION_SIZE,
    MIN_VERTICES_COUNT, MAX_VERTICES_COUNT, MAX_SIZE, K_COUNT)

COL_COUNT = 8


def create_directories():
    "Creates necesesary directories"
    os.makedirs('data/generations', exist_ok=True)


class Application(Gui):
    ''' Main gui class '''

    def __init__(self, master):
        Gui.__init__(self, master, 'Evolution Simulator')
        self.builder.get_object('train')['state'] = 'disabled'
        self.builder.get_object('find_fitness')['state'] = 'disabled'
        self.builder.get_object('find_fitness_no_gui')['state'] = 'disabled'
        self.builder.get_object('sort')['state'] = 'disabled'
        self.builder.get_object('do_selection')['state'] = 'disabled'
        self.builder.get_object('reproduce')['state'] = 'disabled'
        set_entry(self.builder, 'save_as', get_default_name())

        self.scroll_frame = ScrollFrame(self.builder.get_object('creatures_frame'))
        self.scroll_frame.grid(sticky='nsew')
        for col in range(COL_COUNT):
            self.scroll_frame.view_port.columnconfigure(col, minsize=66)
        for row in range(POPULATION_SIZE//COL_COUNT + 1):
            self.scroll_frame.view_port.rowconfigure(row, minsize=106)

        self.simulation = Simulation()
        self.creatures = []
        self.serializable_creatures = {}
        self.generations = []

    def create_generation(self):
        ''' Creates a generation file '''
        creatures = []
        for creature in self.creatures:
            data = creature.get_data()
            self.serializable_creatures[creature.identity] = data
            creatures.append(creature.identity)
        self.generations.append(creatures)
        save_generations(
            self.generations,
            self.serializable_creatures,
            self.builder.get_object('save_as').get()
        )

    def create_creature(self, creature, i):
        ''' Creates a single creature '''
        self.creatures.append(creature)
        image = creature.get_image(7)
        pillow_image = Image.fromarray(image)
        imgtk = ImageTk.PhotoImage(image=pillow_image)
        creature.frame.grid(row=i//COL_COUNT, column=i % COL_COUNT)
        creature.set_description()
        creature.right_click = ContextMenu(self.master, [
            {'label': 'Test fitness', 'command': lambda c=creature: self.test_fitness(c)}, ])
        creature.description.grid(sticky='w')
        panel = tk.Label(creature.frame)
        panel.bind('<Button-3>', creature.right_click.popup)
        panel.grid()
        panel.imgtk = imgtk
        panel.config(image=imgtk)

    def create(self):
        ''' Create button callback '''
        threading.Thread(target=self.threaded_create, daemon=True).start()

    def find_fitness(self):
        ''' Find fitness button callback '''
        threading.Thread(target=self.threaded_find_fitness, daemon=True).start()

    def find_fitness_no_gui(self):
        ''' Find fitness no gui button callback '''
        threading.Thread(target=self.threaded_find_fitness_no_gui, daemon=True).start()

    def sort(self):
        ''' Sort button callback '''
        threading.Thread(target=self.threaded_sort, daemon=True).start()

    def do_selection(self):
        ''' Do selection button callback '''
        threading.Thread(target=self.threaded_selection, daemon=True).start()

    def reproduce(self):
        ''' Reproduce button callback '''
        threading.Thread(target=self.threaded_reproduce, daemon=True).start()

    def train(self):
        ''' Do generation button callback '''
        threading.Thread(target=self.threaded_train, daemon=True).start()

    def load(self):
        ''' Load button callback '''
        threading.Thread(target=self.threaded_load, daemon=True).start()

    def show_analytics(self):
        ''' Show analytics button callback '''
        if self.generations == []:
            easygui.msgbox('There is no data to show', 'Error')
            return
        show_analytics(self.get_generation()-1, self.generations, self.serializable_creatures)

    def threaded_create(self):
        ''' Creates an initial population of creatures '''
        self.builder.get_object('progress')['value'] = 0
        self.builder.get_object('create')['state'] = 'disabled'
        for i in range(POPULATION_SIZE):
            creature = Creature(
                n=random.randint(MIN_VERTICES_COUNT, MAX_VERTICES_COUNT),
                view_port=self.scroll_frame.view_port,
                size=MAX_SIZE)
            self.create_creature(creature, i)
            progress = i * 100 // POPULATION_SIZE
            self.builder.get_object('progress')['value'] = progress
        self.builder.get_object('progress')['value'] = 0
        self.builder.get_object('find_fitness')['state'] = 'active'
        self.builder.get_object('find_fitness_no_gui')['state'] = 'active'

    def threaded_find_fitness(self, render=True):
        ''' Finds the fitness of all the creatures'''
        self.builder.get_object('find_fitness')['state'] = 'disabled'
        self.builder.get_object('find_fitness_no_gui')['state'] = 'disabled'
        fitness = framework(
            Environment, render, f'Generation #{self.get_generation()}', self.creatures)
        for creature in self.creatures:
            creature.fitness = fitness[creature.identity]
            creature.set_description()
            creature.description.grid(sticky='w')
        self.builder.get_object('sort')['state'] = 'active'

    def threaded_find_fitness_no_gui(self):
        ''' Finds the fitness of all the creatures with render off '''
        self.builder.get_object('find_fitness')['state'] = 'disabled'
        self.builder.get_object('find_fitness_no_gui')['state'] = 'disabled'
        fitness = self.simulation.simulate(self.creatures, self.builder)
        for creature in self.creatures:
            creature.fitness = fitness[creature.identity]
            creature.set_description()
            creature.description.grid(sticky='w')
        self.builder.get_object('progress')['value'] = 0
        self.builder.get_object('sort')['state'] = 'active'

    def threaded_sort(self):
        ''' Sorts the creatures based on the fitness values '''
        self.builder.get_object('progress')['value'] = 0
        self.builder.get_object('sort')['state'] = 'disabled'

        # Empty the view port
        for widget in self.scroll_frame.view_port.winfo_children():
            widget.grid_forget()

        self.creatures.sort(key=lambda c: c.fitness, reverse=True)
        for i, creature in enumerate(self.creatures):
            creature.frame.grid(row=i//COL_COUNT, column=i % COL_COUNT)
            progress = i * 100 // POPULATION_SIZE
            self.builder.get_object('progress')['value'] = progress
        self.create_generation()
        self.builder.get_object('progress')['value'] = 0
        self.builder.get_object('train')['state'] = 'active'
        self.builder.get_object('do_selection')['state'] = 'active'

    def threaded_selection(self):
        ''' Selects the creatures based on the fitness values '''
        self.builder.get_object('progress')['value'] = 0
        self.builder.get_object('do_selection')['state'] = 'disabled'
        self.builder.get_object('train')['state'] = 'disabled'

        selected_population = []
        creatures = copy(self.creatures)
        for _ in range(SELECTION_SIZE):
            selected = max(random.choices(creatures, k=K_COUNT), key=lambda c: c.fitness)
            selected_population.append(selected)
            creatures.remove(selected)

        for i, creature in enumerate(copy(self.creatures)):
            if creature not in selected_population:
                creature.frame.grid_forget()
                creature.right_click.menu.destroy()
                creature.description.destroy()
                creature.frame.destroy()
                self.creatures.remove(creature)
            progress = i * 100 // POPULATION_SIZE
            self.builder.get_object('progress')['value'] = progress
        self.builder.get_object('progress')['value'] = 0
        self.builder.get_object('reproduce')['state'] = 'active'

    def threaded_reproduce(self):
        ''' Reproduces the creatures '''
        self.builder.get_object('progress')['value'] = 0
        self.builder.get_object('reproduce')['state'] = 'disabled'

        creatures = copy(self.creatures)
        total_creatures = len(creatures)
        self.creatures = []
        k = 0
        for i, creature in enumerate(creatures):
            for _ in range(OFFSPRINGS_PER_SELECTION_SIZE):
                self.creatures.append(creature)
                creature.frame.grid(row=k//COL_COUNT, column=k % COL_COUNT)
                k += 1
                offspring = reproduce(creature, self.serializable_creatures)
                self.create_creature(offspring, k)
                k += 1
            progress = i * 100 // total_creatures
            self.builder.get_object('progress')['value'] = progress

        for i in range(k, k+RANDOM_NEW_POPULATION_SIZE):
            creature = Creature(
                n=random.randint(MIN_VERTICES_COUNT, MAX_VERTICES_COUNT),
                view_port=self.scroll_frame.view_port,
                size=MAX_SIZE)
            self.create_creature(creature, i)

        self.builder.get_object('details')['text'] = f'Generation #{self.get_generation()}'
        self.builder.get_object('progress')['value'] = 0
        self.builder.get_object('train')['state'] = 'active'
        self.builder.get_object('find_fitness')['state'] = 'active'
        self.builder.get_object('find_fitness_no_gui')['state'] = 'active'

    def threaded_train(self):
        ''' Does training for x generations '''
        try:
            self.builder.get_object('train')['state'] = 'disabled'
            self.builder.get_object('find_fitness')['state'] = 'disabled'
            self.builder.get_object('find_fitness_no_gui')['state'] = 'disabled'
            repeat = int(self.builder.get_object('repeat').get())

            for _ in range(repeat):
                self.threaded_selection()
                self.threaded_reproduce()
                self.threaded_find_fitness_no_gui()
                self.threaded_sort()
            self.builder.get_object('do_selection')['state'] = 'active'
        except ValueError:
            easygui.msgbox('Make sure the value of X is an integer', 'Error')

    def threaded_load(self):
        ''' Loads the saved data from file '''
        file_path = easygui.fileopenbox('Load a generations file', default='./data/generations/')
        if file_path is None:
            return
        data = load_generations(file_path)
        self.serializable_creatures = data['creatures']
        self.generations = data['generations']
        self.builder.get_object('details')['text'] = f'Generation #{len(self.generations)+1}'
        self.creatures = []
        for i, creature_id in enumerate(self.generations[-1]):
            creature_data = self.serializable_creatures[creature_id]
            creature = Creature(**creature_data, view_port=self.scroll_frame.view_port)
            self.create_creature(creature, i)
        set_entry(self.builder, 'save_as', os.path.basename(os.path.splitext(file_path)[0]))
        self.builder.get_object('create')['state'] = 'disabled'
        self.builder.get_object('train')['state'] = 'active'
        self.builder.get_object('find_fitness')['state'] = 'disabled'
        self.builder.get_object('find_fitness_no_gui')['state'] = 'disabled'
        self.builder.get_object('sort')['state'] = 'disabled'
        self.builder.get_object('do_selection')['state'] = 'active'
        self.builder.get_object('reproduce')['state'] = 'disabled'

    def test_fitness(self, creature: Creature):
        ''' Tests the fitness of a single creature with render on '''
        fitness = framework(Environment, True, f'Generation #{self.get_generation()}', [creature])
        easygui.msgbox(
            f'Fitness of creature '
            f'#{creature.identity}: {"{:.2f}".format(fitness[creature.identity])}',
            'Fitness Test Result')

    def get_generation(self):
        ''' Returns the current generation '''
        return len(self.generations)+1


def main():
    ''' Main function of the script '''
    root = tk.Tk()
    Application(root)
    root.mainloop()


if __name__ == '__main__':
    create_directories()
    main()
