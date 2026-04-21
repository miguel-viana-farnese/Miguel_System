import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
import sqlite3

class DatabaseManager:
    def __init__(self, db_name="miguel_system.db"): 
        self.conn = sqlite3.connect(db_name) 
        self.cursor = self.conn.cursor()
        self.create_tables() 
        self.seed_data()

    def create_tables(self): 
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS sales
                              (id INTEGER PRIMARY KEY AUTOINCREMENT, total REAL, date TEXT)''') 
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS products 
                              (name TEXT PRIMARY KEY, price REAL)''') 
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS sale_items 
                              (id INTEGER PRIMARY KEY AUTOINCREMENT, product_name TEXT, quantity INTEGER, price REAL)''') 
        self.conn.commit()

    def seed_data(self): 
        self.cursor.execute("SELECT count(*) FROM products") 
        if self.cursor.fetchone()[0] == 0: 
            sample_data = [("Item 1", 1.00), ("Item 2", 2.00), ("Item 3", 3.00)]
            self.cursor.executemany("INSERT INTO products VALUES (?, ?)", sample_data)
            self.conn.commit()

    def get_products(self): 
        self.cursor.execute("SELECT name, price FROM products ORDER BY name ASC")
        return self.cursor.fetchall()

    def add_product(self, name, price): 
        self.cursor.execute("INSERT OR REPLACE INTO products VALUES (?, ?)", (name, price))
        self.conn.commit()

    def delete_product(self, name): 
        self.cursor.execute("DELETE FROM products WHERE name=?", (name,))
        self.conn.commit()

    def save_sale(self, total, items_list): 
        self.cursor.execute("INSERT INTO sales (total, date) VALUES (?, ?)", (total, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        for item in items_list:
            self.cursor.execute("INSERT INTO sale_items (product_name, quantity, price) VALUES (?, ?, ?)", (item[0], item[2], item[1]))
        self.conn.commit()

    def get_sales_report(self): 
        self.cursor.execute('''SELECT product_name, SUM(quantity), SUM(quantity * price) 
                               FROM sale_items 
                               GROUP BY product_name''')
        return self.cursor.fetchall()

class POSCalculator:
    def __init__(self, root): 
        self.root = root
        self.root.title("Miguel System - v2.0")
        self.db = DatabaseManager()
        
        self.root.columnconfigure(0, weight=1)
        
        frame = ttk.Frame(root, padding="15")
        frame.grid(row=0, column=0, sticky="nsew")
        
        self.create_product_display(frame)
        self.create_inputs(frame)
        self.create_buttons(frame)

        self.tree = ttk.Treeview(frame, columns=("Produto", "Preço", "Qtd", "Total"), show="headings")
        for col in ("Produto", "Preço", "Qtd", "Total"):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        self.tree.grid(row=5, column=0, columnspan=2, pady=10, sticky="nsew") 
        
        self.label_grand_total = ttk.Label(frame, text="Total Geral: R$ 0.00", font=("Arial", 16, "bold")) 
        self.label_grand_total.grid(row=6, column=0, columnspan=2, pady=10)
        self.grand_total = 0.0
        
        self.root.bind('<Return>', lambda event: self.add_item())

    def _on_mousewheel(self, event): 
        if hasattr(self, 'canvas'):
            if event.widget.winfo_containing(event.x_root, event.y_root) == self.canvas or \
               self.canvas.winfo_containing(event.x_root, event.y_root):
                if event.num == 5: self.canvas.yview_scroll(1, "units")
                elif event.num == 4: self.canvas.yview_scroll(-1, "units")
                else: self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def create_product_display(self, parent): 
        self.btn_container = ttk.LabelFrame(parent, text="Produtos")
        self.btn_container.grid(row=0, column=0, columnspan=2, pady=5)
        
        self.canvas = tk.Canvas(self.btn_container, height=150, width=200) 
        self.scrollbar = ttk.Scrollbar(self.btn_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)
        self.root.bind_all("<Button-4>", self._on_mousewheel)
        self.root.bind_all("<Button-5>", self._on_mousewheel)
        
        self.refresh_product_buttons()

    def refresh_product_buttons(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        products = self.db.get_products()
        for name, price in products:
            btn = ttk.Button(self.scrollable_frame, text=name, 
                             command=lambda n=name, p=price: self.select_product(n, p))
            btn.pack(side="top", fill="x", padx=5, pady=2)

    def select_product(self, name, price):
        self.selected_product_name = name
        self.entry_price.delete(0, tk.END)
        self.entry_price.insert(0, f"{price:.2f}")
        self.entry_qty.focus_set()

    def create_inputs(self, parent):
        ttk.Label(parent, text="Preço (R$):").grid(row=1, column=0, padx=5, pady=5)
        self.entry_price = ttk.Entry(parent)
        self.entry_price.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(parent, text="Quantidade:").grid(row=2, column=0, padx=5, pady=5)
        self.entry_qty = ttk.Spinbox(parent, from_=1, to=999)
        self.entry_qty.grid(row=2, column=1, padx=5, pady=5)
        self.entry_qty.delete(0, "end")
        self.entry_qty.insert(0, "1")

    def create_buttons(self, parent):
        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
        buttons = [
            ("Adicionar", self.add_item), 
            ("Remover", self.remove_item), 
            ("Limpar", self.reset_sale), 
            ("Finalizar", self.finalize_sale),
            ("Gerir Prod", self.open_manage_products),
            ("Relatório", self.open_report)
        ]
        for text, cmd in buttons:
            ttk.Button(btn_frame, text=text, command=cmd).pack(side=tk.LEFT, padx=2)

    def open_manage_products(self):
        top = tk.Toplevel(self.root)
        top.title("Gerenciar Produtos")
        
        list_frame = ttk.LabelFrame(top, text="Lista de Produtos")
        list_frame.grid(row=0, column=0, rowspan=3, padx=10, pady=10, sticky="ns")
        
        product_listbox = tk.Listbox(list_frame, width=30, height=10)
        product_listbox.pack(padx=5, pady=5)
        
        products = self.db.get_products()
        for p in products:
            product_listbox.insert(tk.END, p[0])
            
        def delete_selected():
            selection = product_listbox.curselection()
            if selection:
                name = product_listbox.get(selection[0])
                self.db.delete_product(name)
                product_listbox.delete(selection[0])
                self.refresh_product_buttons()
        
        ttk.Button(list_frame, text="Deletar Selecionado", command=delete_selected).pack(fill="x", padx=5, pady=5)
        
        input_frame = ttk.LabelFrame(top, text="Adicionar/Atualizar")
        input_frame.grid(row=0, column=1, padx=10, pady=10, sticky="n")
        
        ttk.Label(input_frame, text="Nome:").grid(row=0, column=0, padx=5, pady=5)
        name_entry = ttk.Entry(input_frame)
        name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(input_frame, text="Preço:").grid(row=1, column=0, padx=5, pady=5)
        price_entry = ttk.Entry(input_frame)
        price_entry.grid(row=1, column=1, padx=5, pady=5)
        
        def save():
            try:
                self.db.add_product(name_entry.get().upper(), float(price_entry.get().replace(',', '.')))
                self.refresh_product_buttons()
                product_listbox.insert(tk.END, name_entry.get().upper())
                messagebox.showinfo("Sucesso", "Produto salvo!")
            except ValueError:
                messagebox.showerror("Erro", "Preço inválido")
            
        ttk.Button(input_frame, text="Salvar", command=save).grid(row=2, column=0, columnspan=2, pady=10)

    def open_report(self):
        top = tk.Toplevel(self.root)
        top.title("Relatório de Vendas")
        report_tree = ttk.Treeview(top, columns=("Produto", "Qtd Vendida", "Total Vendido"), show="headings")
        for col in ("Produto", "Qtd Vendida", "Total Vendido"):
            report_tree.heading(col, text=col)
        report_tree.pack(fill="both", expand=True, padx=10, pady=10)
        for row in self.db.get_sales_report():
            report_tree.insert("", "end", values=(row[0], row[1], f"R$ {row[2]:.2f}"))

    def add_item(self):
        name = getattr(self, 'selected_product_name', "Produto Desconhecido")
        try:
            price = float(self.entry_price.get().replace(',', '.'))
            qty = int(self.entry_qty.get())
            total = price * qty
            self.grand_total += total
            self.tree.insert("", "end", values=(name, f"{price:.2f}", qty, f"{total:.2f}"))
            self.update_total_display()
        except ValueError:
            messagebox.showerror("Erro", "Valores inválidos.")

    def remove_item(self):
        selected = self.tree.selection()
        if not selected: return
        for item in selected:
            self.grand_total -= float(self.tree.item(item, 'values')[3])
            self.tree.delete(item)
        self.update_total_display()

    def finalize_sale(self):
        if not self.tree.get_children(): return
        items = []
        for child in self.tree.get_children():
            values = self.tree.item(child, 'values')
            items.append((values[0], float(values[1]), int(values[2])))
        self.db.save_sale(self.grand_total, items)
        messagebox.showinfo("Sucesso", "Venda registrada!")
        self.reset_sale()

    def reset_sale(self):
        self.tree.delete(*self.tree.get_children())
        self.grand_total = 0.0
        self.update_total_display()

    def update_total_display(self):
        self.label_grand_total.config(text=f"Total Geral: R$ {self.grand_total:,.2f}")

if __name__ == "__main__": 
    root = tk.Tk()
    app = POSCalculator(root)
    root.mainloop()