import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import os
import shutil
import time
from PIL import Image, ImageTk, ImageDraw


class FileExplorer:
    def __init__(self, root):
        self.root = root
        self.root.title("Explorateur de Fichiers avec Icônes")
        self.root.geometry("900x600")

        self.current_path = os.path.expanduser("~")
        self.favorites = []

        # Création des icônes
        self.icons = self.create_icons()

        # Barre de chemin
        self.path_bar = tk.Frame(root)
        self.path_bar.pack(fill=tk.X, padx=5, pady=2)
        self.path_label = tk.Label(self.path_bar, text=self.current_path, anchor="w")
        self.path_label.pack(fill=tk.X)

        # Zone principale
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Colonne de gauche (favoris)
        self.sidebar = tk.Frame(self.main_frame, width=150, bg="lightgray")
        self.sidebar.pack(fill=tk.Y, side=tk.LEFT, padx=(0, 5))
        tk.Label(self.sidebar, text="Favoris", bg="lightgray", font=('Arial', 10, 'bold')).pack(pady=5)
        self.favorites_listbox = tk.Listbox(self.sidebar)
        self.favorites_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.favorites_listbox.bind("<Double-Button-1>", self.open_favorite)

        # Colonne centrale (contenu)
        self.content_frame = tk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        # Barre de recherche et boutons
        self.top_controls = tk.Frame(self.content_frame)
        self.top_controls.pack(fill=tk.X, pady=(0, 5))

        tk.Button(self.top_controls, text="↑ Parent", command=self.go_parent).pack(side=tk.LEFT, padx=2)
        tk.Button(self.top_controls, text="Nouveau Dossier", command=self.create_folder).pack(side=tk.LEFT, padx=2)
        tk.Button(self.top_controls, text="Actualiser", command=self.refresh).pack(side=tk.LEFT, padx=2)

        self.search_entry = tk.Entry(self.top_controls)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Button(self.top_controls, text="Rechercher", command=self.search_files).pack(side=tk.LEFT, padx=2)

        # Liste des fichiers/dossiers avec icônes
        self.tree = ttk.Treeview(self.content_frame, columns=("fullpath", "type", "size"), selectmode="browse")
        self.tree.heading("#0", text="Nom")
        self.tree.heading("type", text="Type")
        self.tree.heading("size", text="Taille")

        self.tree.column("#0", width=300, anchor="w")
        self.tree.column("type", width=100, anchor="center")
        self.tree.column("size", width=100, anchor="e")

        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-Button-1>", self.navigate)
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<<TreeviewSelect>>", self.show_info)

        # Barre de statut
        self.status_bar = tk.Label(root, text="Prêt", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, padx=5, pady=2)

        # Menu contextuel
        self.context_menu = tk.Menu(root, tearoff=0)
        self.context_menu.add_command(label="Ouvrir", command=self.open_selected)
        self.context_menu.add_command(label="Ouvrir l'emplacement", command=self.open_location)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Renommer", command=self.rename_selected)
        self.context_menu.add_command(label="Supprimer", command=self.delete_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Ajouter aux Favoris", command=self.add_to_favorites)
        self.context_menu.add_command(label="Propriétés", command=self.show_properties)

        self.load_directory()

    def create_icons(self):
        """Crée des icônes basiques pour différents types de fichiers"""
        icons = {}
        size = (16, 16)  # Taille des icônes

        # Icône de dossier
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([(1, 1), (14, 14)], fill="#FFD700", outline="#FFA500")
        draw.rectangle([(3, 3), (14, 8)], fill="#FFA500")
        icons['folder'] = ImageTk.PhotoImage(img)

        # Icône de fichier générique
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([(2, 2), (14, 14)], fill="#FFFFFF", outline="#AAAAAA")
        icons['file'] = ImageTk.PhotoImage(img)

        # Icône d'image
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([(2, 2), (14, 14)], fill="#FFC0CB", outline="#FF69B4")
        draw.rectangle([(5, 5), (11, 11)], fill="#FF69B4")
        icons['image'] = ImageTk.PhotoImage(img)

        # Icône de document
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.polygon([(2, 2), (12, 2), (14, 4), (14, 14), (2, 14)], fill="#ADD8E6", outline="#4682B4")
        icons['document'] = ImageTk.PhotoImage(img)

        return icons

    def get_file_icon(self, filename):
        """Retourne l'icône appropriée selon l'extension du fichier"""
        ext = os.path.splitext(filename)[1].lower()

        if not ext:  # Pas d'extension - probablement un dossier
            return self.icons['folder']

        # Dictionnaire des extensions communes
        image_exts = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff')
        doc_exts = ('.txt', '.doc', '.docx', '.pdf', '.rtf', '.odt')

        if ext in image_exts:
            return self.icons['image']
        elif ext in doc_exts:
            return self.icons['document']
        else:
            return self.icons['file']

    def load_directory(self):
        try:
            self.path_label.config(text=self.current_path)
            self.tree.delete(*self.tree.get_children())

            items = os.listdir(self.current_path)

            # Trier: dossiers d'abord, puis fichiers, tout en minuscules
            items.sort(key=lambda x: (not os.path.isdir(os.path.join(self.current_path, x)), x.lower()))

            for item in items:
                item_path = os.path.join(self.current_path, item)

                if os.path.isdir(item_path):
                    icon = self.icons['folder']
                    filetype = "Dossier"
                    size = ""
                else:
                    icon = self.get_file_icon(item)
                    filetype = "Fichier" + os.path.splitext(item)[1]
                    try:
                        size = self.get_file_size(os.path.getsize(item_path))
                    except:
                        size = "N/A"

                self.tree.insert('', 'end', text=item, values=(item_path, filetype, size), image=icon)

            self.status_bar.config(text=f"{len(items)} éléments")

        except PermissionError:
            messagebox.showerror("Erreur", "Accès refusé à ce dossier")
            self.status_bar.config(text="Erreur: Accès refusé")

    def get_file_size(self, size_bytes):
        """Convertit la taille des fichiers en unités lisible"""
        for unit in ['octets', 'Ko', 'Mo', 'Go']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} To"

    def navigate(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return
        item_path = self.tree.item(selected[0])['values'][0]
        if os.path.isdir(item_path):
            self.current_path = item_path
            self.load_directory()

    def go_parent(self):
        """Remonter au dossier parent"""
        parent = os.path.dirname(self.current_path)
        if os.path.exists(parent):
            self.current_path = parent
            self.load_directory()

    def show_context_menu(self, event):
        try:
            selected = self.tree.selection()
            if selected:
                self.context_menu.post(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def open_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        path = self.tree.item(selected[0])['values'][0]
        if os.path.isdir(path):
            self.current_path = path
            self.load_directory()
        else:
            try:
                os.startfile(path)
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible d'ouvrir le fichier: {e}")

    def open_location(self):
        """Ouvrir l'emplacement du fichier dans l'explorateur"""
        selected = self.tree.selection()
        if not selected:
            return
        path = self.tree.item(selected[0])['values'][0]
        folder = os.path.dirname(path) if os.path.isfile(path) else path
        try:
            os.startfile(folder)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir l'emplacement: {e}")

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        path = self.tree.item(selected[0])['values'][0]
        name = os.path.basename(path)

        confirm = messagebox.askyesno("Confirmer", f"Voulez-vous supprimer : {name} ?", parent=self.root)
        if confirm:
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                self.refresh()
                self.status_bar.config(text=f"{name} supprimé")
            except Exception as e:
                messagebox.showerror("Erreur", f"Échec de la suppression: {e}")
                self.status_bar.config(text=f"Échec de la suppression: {e}")

    def rename_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        old_path = self.tree.item(selected[0])['values'][0]
        old_name = os.path.basename(old_path)

        new_name = simpledialog.askstring("Renommer", "Nouveau nom :", initialvalue=old_name, parent=self.root)
        if new_name and new_name != old_name:
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            try:
                os.rename(old_path, new_path)
                self.refresh()
                self.status_bar.config(text=f"Renommé: {old_name} → {new_name}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Échec du renommage: {e}")
                self.status_bar.config(text=f"Échec du renommage: {e}")

    def create_folder(self):
        folder_name = simpledialog.askstring("Nouveau Dossier", "Nom du dossier :", parent=self.root)
        if folder_name:
            folder_path = os.path.join(self.current_path, folder_name)
            try:
                os.mkdir(folder_path)
                self.refresh()
                self.status_bar.config(text=f"Dossier créé: {folder_name}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Échec de la création: {e}")
                self.status_bar.config(text=f"Échec de la création: {e}")

    def refresh(self):
        self.load_directory()
        self.status_bar.config(text="Actualisé")

    def search_files(self):
        query = self.search_entry.get().lower()
        if not query:
            self.refresh()
            return

        try:
            self.tree.delete(*self.tree.get_children())
            items = os.listdir(self.current_path)
            matches = 0

            for item in items:
                if query in item.lower():
                    item_path = os.path.join(self.current_path, item)

                    if os.path.isdir(item_path):
                        icon = self.icons['folder']
                        filetype = "Dossier"
                        size = ""
                    else:
                        icon = self.get_file_icon(item)
                        filetype = "Fichier" + os.path.splitext(item)[1]
                        try:
                            size = self.get_file_size(os.path.getsize(item_path))
                        except:
                            size = "N/A"

                    self.tree.insert('', 'end', text=item, values=(item_path, filetype, size), image=icon)
                    matches += 1

            self.status_bar.config(text=f"{matches} résultats pour '{query}'")

        except Exception as e:
            messagebox.showerror("Erreur", str(e))
            self.status_bar.config(text=f"Erreur de recherche: {e}")

    def add_to_favorites(self):
        selected = self.tree.selection()
        if not selected:
            return
        path = self.tree.item(selected[0])['values'][0]
        if path not in self.favorites:
            self.favorites.append(path)
            self.update_favorites_list()
            self.status_bar.config(text=f"Ajouté aux favoris: {os.path.basename(path)}")

    def update_favorites_list(self):
        self.favorites_listbox.delete(0, tk.END)
        for fav in self.favorites:
            self.favorites_listbox.insert(tk.END, os.path.basename(fav))

    def open_favorite(self, event=None):
        selection = self.favorites_listbox.curselection()
        if not selection:
            return
        fav_name = self.favorites_listbox.get(selection[0])
        path = next((f for f in self.favorites if os.path.basename(f) == fav_name), None)

        if path and os.path.exists(path):
            if os.path.isdir(path):
                self.current_path = path
                self.load_directory()
            else:
                try:
                    os.startfile(path)
                except Exception as e:
                    messagebox.showerror("Erreur", f"Impossible d'ouvrir: {e}")
        else:
            messagebox.showwarning("Attention", "Le favori n'existe plus")
            self.favorites.remove(path)
            self.update_favorites_list()

    def show_info(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return

        path = self.tree.item(selected[0])['values'][0]
        try:
            stats = os.stat(path)
            size = self.get_file_size(stats.st_size)
            created = time.strftime("%d/%m/%Y %H:%M", time.localtime(stats.st_ctime))
            modified = time.strftime("%d/%m/%Y %H:%M", time.localtime(stats.st_mtime))

            info = f"Nom: {os.path.basename(path)} | Taille: {size} | Créé: {created} | Modifié: {modified}"
            self.status_bar.config(text=info)
        except Exception as e:
            self.status_bar.config(text=f"Erreur: {str(e)}")

    def show_properties(self):
        selected = self.tree.selection()
        if not selected:
            return

        path = self.tree.item(selected[0])['values'][0]
        try:
            stats = os.stat(path)
            is_dir = os.path.isdir(path)

            properties = [
                f"Nom: {os.path.basename(path)}",
                f"Type: {'Dossier' if is_dir else 'Fichier'}",
                f"Emplacement: {os.path.dirname(path)}",
                f"Taille: {self.get_file_size(stats.st_size)}",
                f"Côté: {time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(stats.st_ctime))}",
                f"Modifié: {time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(stats.st_mtime))}",
                f"Accédé: {time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(stats.st_atime))}"
            ]

            messagebox.showinfo("Propriétés", "\n".join(properties), parent=self.root)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'obtenir les propriétés: {e}", parent=self.root)


root = tk.Tk()
app = FileExplorer(root)
root.mainloop()