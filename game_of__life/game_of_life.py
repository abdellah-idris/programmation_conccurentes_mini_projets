"""
Abdellah IDRIS
Thiziri BOUCHAREB

Jeu de la vie avec barrière réutilisable
"""

import tkinter as tk
import threading
from queue import Queue
from multiprocessing import Value
import random
from tkinter import messagebox


class BarriereReutilisable:
    # Barriere Reutilisable en utilisant un compteur de threads et une barriere de synchronisation

    def __init__(self, nombre_threads, update_gui):
        self.nombre_threads = nombre_threads # nombre de threads
        self.compteur = Value('i', 0) # compteur de threads protégeait (un seul thread y accéde), partagée entre les threads
        self.barriere = threading.Condition() # barriere de synchronisation
        self.update_gui = update_gui # fonction à appeler à la fin de chaque étape

    def attendre(self):
        with self.barriere: # on utilise un context manager pour éviter d'avoir à faire un acquire et un release
            with self.compteur.get_lock(): # on utilise un lock pour éviter les accès concurrents au compteur
                self.compteur.value += 1

            if self.compteur.value < self.nombre_threads:
                self.barriere.wait() # on attend que tous les threads aient fini leur étape

            else:
                print(f"compteurs: {self.compteur.value} / nombre de thread: {self.nombre_threads}")

                with self.compteur.get_lock(): # on utilise un lock pour éviter les accès concurrents au compteur
                    self.compteur.value = 0 # on remet le compteur à 0
                    print("reset compteur")

                self.update_gui() # on appelle la fonction à la fin de chaque étape de calcul
                self.barriere.notify_all() # on notifie tous les threads qu'ils peuvent continuer et procéder à l'étape suivante

class JeuDeLaVie:
    def __init__(self, largeur, hauteur, taille_block):
        self.taille_block = taille_block # taille d'un bloc en pixels
        self.largeur = largeur # largeur de la grille
        self.hauteur = hauteur # hauteur de la grille
        self.canevas = None

        self.zero_cell_color = 'white' # couleur des cellules mortes
        self.one_cell_color = 'black' # couleur des cellules vivantes

        self.grille = [[random.choice([0, 1]) for _ in range(largeur)] for _ in range(hauteur)] # grille de départ

        self.rectangles = [[None for _ in range(largeur)] for _ in range(hauteur)] # liste des rectangles pour le dessin
        self.grille_de_calcule = [[0] * largeur for _ in range(hauteur)] # grille de calcul

        self.barriere = BarriereReutilisable(hauteur * largeur, self.mise_a_jour) # barriere de synchronisation
        self.update_queue = Queue() # queue pour mettre à jour l'interface graphique depuis le thread principal

        self.creer_interface()
        self.dessiner_grille()

        k = 0
        for i in range(hauteur):
            for j in range(largeur):
                th = threading.Thread(target=self.thread_mise_a_jour, args=(i, j, self.barriere),name=f'Thread-{i * hauteur + j}') # on crée un thread pour chaque cellule
                th.start() # on lance le thread

                k += 1
                if k % 1000 == 0:
                    print(f"Thread {k} lancé")


    def creer_interface(self):
        self.root = tk.Tk()
        self.root.title("Jeu de la Vie")

        self.canevas = tk.Canvas(self.root, width=self.largeur * self.taille_block,
                                 height=self.hauteur * self.taille_block, borderwidth=5, highlightthickness=0) # on crée le canevas
        self.canevas.pack()

        self.bouton_quitter = tk.Button(self.root, text="Quitter", command=self.root.destroy) # on crée le bouton quitter
        self.bouton_quitter.pack(side=tk.LEFT)

    def dessiner_grille(self):
        self.canevas.delete("cellule")  # on supprime les rectangles existants

        for i in range(self.hauteur):
            for j in range(self.largeur):
                couleur = self.zero_cell_color if self.grille[i][j] == 0 else self.one_cell_color
                self.rectangles[i][j] = self.canevas.create_rectangle(j * self.taille_block,
                                                                      i * self.taille_block,
                                                                      (j + 1) * self.taille_block,
                                                                      (i + 1) * self.taille_block,
                                                                      fill=couleur, outline="gray", tags="cellule") # on dessine les rectangles

    def thread_mise_a_jour(self, x, y, barriere):
        try:
            while True:
                voisins = 0

                # on compte le nombre de voisins vivants
                for i in range(-1, 2):
                    for j in range(-1, 2):
                        voisin_ligne = (x + i + self.hauteur) % self.hauteur
                        voisin_colonne = (y + j + self.largeur) % self.largeur
                        voisins += self.grille[voisin_ligne][voisin_colonne]

                voisins -= self.grille[x][y]

                if self.grille[x][y] == 1:
                    self.grille_de_calcule[x][y] = 0

                    if voisins == 2 or voisins == 3:
                        self.grille_de_calcule[x][y] = 1
                else:
                    if voisins == 3:
                        self.grille_de_calcule[x][y] = 1

                barriere.attendre() # on attend que tous les threads aient fini leur étape

                couleur = self.one_cell_color if self.grille[x][y] == 1 else self.zero_cell_color
                self.update_queue.put((x, y, couleur)) # permet de mettre à jour l'interface graphique

        except Exception as e:
            print(f"Vous avez quitté le jeu! ERREUR : {e}")
            messagebox.showinfo("Fin du jeu", "La partie est terminée! arrêtez le programme et relancez le pour rejouer")
            exit(0)
    def mise_a_jour(self):
        # mise a jour des threads une fois qu'ils ont tous fini
        self.root.after(0, self.update_gui)

    def update_gui(self):
        while not self.update_queue.empty():
            x, y, couleur = self.update_queue.get() # on récupère les informations de la queue (x, y, couleur)
            self.canevas.itemconfig(self.rectangles[x][y], fill=couleur) # mise à jour la couleur du rectangle

        self.grille = [row[:] for row in self.grille_de_calcule] # on met à jour la grille

    def executer(self):
        self.root.mainloop() # on lance la boucle principale

if __name__ == "__main__":
    """
    le nombre maximum de threads atteint sur ma machine est de 150_000
    """
    jeu = JeuDeLaVie(largeur=100, hauteur=100, taille_block=5)
    jeu.executer()
