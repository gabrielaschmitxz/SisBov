"""
SISBOV - Sistema de Informação Sanitária e Movimentação Bovina
Aplicativo desktop usando Tkinter
"""
import sys
import os
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import threading
from functools import lru_cache
from src.services.database import init_database
from src.services.property_service import get_all_properties, create_property, get_property
from src.services.animal_service import get_total_animals

class SISBOVApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SISBOV - Sistema de Informação Sanitária e Movimentação Bovina")
        self.root.geometry("800x600")
        
        # Estado da aplicação
        self.current_property_id = None
        self.data_cache = {}  # Cache simples para dados já carregados
        self.loading_indicators = {}  # Controle de indicadores de carregamento
        
        # Inicializar banco de dados
        try:
            init_database()
        except Exception as e:
            error_msg = str(e)
            if "could not translate host name" in error_msg or "name resolution" in error_msg:
                messagebox.showerror("Erro de Conexão", 
                    f"Erro ao conectar ao banco de dados:\n{error_msg}\n\n"
                    "Verifique:\n"
                    "- Sua conexão com a internet\n"
                    "- Se o banco de dados Neon está ativo\n"
                    "- Se a URL de conexão está correta no arquivo .env")
            else:
                messagebox.showerror("Erro", f"Erro ao conectar ao banco de dados:\n{error_msg}")
            return
        
        # Carregar tela inicial
        self.show_properties_screen()
    
    def clear_window(self):
        """Limpa a janela"""
        for widget in self.root.winfo_children():
            widget.destroy()
        # Não limpa cache completamente - mantém dados para performance
        # Cache será limpo seletivamente quando necessário
    
    def invalidate_cache(self, pattern=None):
        """Invalida cache - remove entradas que correspondem ao padrão"""
        if pattern is None:
            # Remove apenas cache relacionado à propriedade atual
            if self.current_property_id:
                keys_to_remove = [k for k in self.data_cache.keys() if str(self.current_property_id) in k]
                for key in keys_to_remove:
                    del self.data_cache[key]
        else:
            # Remove cache que corresponde ao padrão
            keys_to_remove = [k for k in self.data_cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self.data_cache[key]
    
    def load_data_async(self, load_func, update_func, cache_key=None, show_loading=True):
        """Carrega dados de forma assíncrona em uma thread separada"""
        def load_in_thread():
            try:
                # Verifica cache se existe
                if cache_key and cache_key in self.data_cache:
                    data = self.data_cache[cache_key]
                    self.root.after(0, lambda: update_func(data))
                    return
                
                # Mostra indicador de carregamento
                if show_loading:
                    self.root.after(0, self._show_loading_indicator)
                
                # Carrega dados
                data = load_func()
                
                # Atualiza cache
                if cache_key:
                    self.data_cache[cache_key] = data
                
                # Atualiza interface na thread principal
                self.root.after(0, lambda: self._hide_loading_indicator())
                self.root.after(0, lambda: update_func(data))
            except Exception as e:
                self.root.after(0, lambda: self._hide_loading_indicator())
                self.root.after(0, lambda: messagebox.showerror("Erro", f"Erro ao carregar dados:\n{str(e)}"))
        
        thread = threading.Thread(target=load_in_thread, daemon=True)
        thread.start()
    
    def _show_loading_indicator(self):
        """Mostra indicador de carregamento"""
        # Pode ser implementado com um label ou progressbar se necessário
        pass
    
    def _hide_loading_indicator(self):
        """Esconde indicador de carregamento"""
        pass
    
    def load_tree_data_async(self, data_loader, tree_widget, value_extractor, cache_key=None):
        """Carrega dados em uma treeview de forma assíncrona"""
        def load_data():
            try:
                if cache_key and cache_key in self.data_cache:
                    return self.data_cache[cache_key]
                data = data_loader()
                if cache_key:
                    self.data_cache[cache_key] = data
                return data
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Erro", f"Erro ao carregar dados:\n{str(e)}"))
                return []
        
        def update_tree(data):
            tree_widget.delete(*tree_widget.get_children())
            for item in data:
                values = value_extractor(item)
                tree_widget.insert("", tk.END, values=values)
        
        def load_thread():
            data = load_data()
            self.root.after(0, lambda: update_tree(data))
        
        threading.Thread(target=load_thread, daemon=True).start()
    
    def show_properties_screen(self):
        """Mostra a tela de propriedades"""
        self.clear_window()
        
        # Cabeçalho
        header = tk.Frame(self.root, bg="#0D4F14", height=60)
        header.pack(fill=tk.X)
        tk.Label(header, text="🏠 SISBOV - Sistema de Informação Sanitária e Movimentação Bovina", font=("Arial", 14, "bold"), 
                bg="#0D4F14", fg="white").pack(pady=15)
        
        # Container principal
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Botão nova propriedade
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 20))
        tk.Button(btn_frame, text="➕ Nova Propriedade", command=self.open_new_property_dialog,
                 bg="#0D4F14", fg="white", font=("Arial", 10, "bold"), padx=15, pady=8).pack(side=tk.LEFT)
        
        # Lista de propriedades
        list_frame = tk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Listbox
        self.properties_listbox = tk.Listbox(list_frame, font=("Arial", 11, "bold"), 
                                            yscrollcommand=scrollbar.set)
        self.properties_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.properties_listbox.yview)
        
        # Botões de ação
        action_frame = tk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=10)
        tk.Button(action_frame, text="✓ Selecionar", command=self.select_property,
                 bg="#2196F3", fg="white", font=("Arial", 11, "bold"), padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="✏️ Editar", command=self.edit_property,
                 bg="#FF9800", fg="white", font=("Arial", 11, "bold"), padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="🗑️ Excluir", command=self.delete_property,
                 bg="#F44336", fg="white", font=("Arial", 11, "bold"), padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        # Carregar propriedades
        self.load_properties()
    
    def load_properties(self):
        """Carrega a lista de propriedades"""
        cache_key = "properties_all"
        
        def load_data():
            try:
                if cache_key in self.data_cache:
                    return self.data_cache[cache_key]
                properties = get_all_properties()
                self.data_cache[cache_key] = properties
                return properties
            except Exception as e:
                return None, str(e)
        
        def update_listbox(result):
            if result is None:
                return
            if isinstance(result, tuple) and len(result) == 2:
                error = result[1]
                messagebox.showerror("Erro", f"Erro ao carregar propriedades:\n{error}")
                return
            
            self.properties_listbox.delete(0, tk.END)
            self.properties_data = {}
            
            if not result:
                self.properties_listbox.insert(0, "Nenhuma propriedade cadastrada")
            else:
                for prop in result:
                    # Apenas Nome da Propriedade e Titular
                    prop_name = prop['name'] if prop.get('name') else ""
                    owner_name = prop['owner_name'] if prop.get('owner_name') else ""
                    display_text = f"{prop_name} - {owner_name}"
                    self.properties_listbox.insert(tk.END, display_text)
                    self.properties_data[display_text] = prop['id']
        
        def load_thread():
            result = load_data()
            self.root.after(0, lambda: update_listbox(result))
        
        threading.Thread(target=load_thread, daemon=True).start()
    
    def open_new_property_dialog(self):
        """Abre diálogo para nova propriedade"""
        self.property_dialog(None)
    
    def property_dialog(self, property_id=None):
        """Diálogo para criar/editar propriedade"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Nova Propriedade" if not property_id else "Editar Propriedade")
        dialog.geometry("550x550")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Campos
        tk.Label(dialog, text="Nome da Propriedade *", font=("Arial", 10)).grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        name_entry = tk.Entry(dialog, width=40, font=("Arial", 10))
        name_entry.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(dialog, text="Titular *", font=("Arial", 10)).grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        owner_entry = tk.Entry(dialog, width=40, font=("Arial", 10))
        owner_entry.grid(row=1, column=1, padx=10, pady=5)
        
        tk.Label(dialog, text="CPF ou CNPJ", font=("Arial", 10)).grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        cpf_cnpj_entry = tk.Entry(dialog, width=40, font=("Arial", 10))
        cpf_cnpj_entry.grid(row=2, column=1, padx=10, pady=5)
        
        def format_cpf_cnpj(event=None):
            """Formata CPF/CNPJ automaticamente"""
            value = cpf_cnpj_entry.get().replace(".", "").replace("-", "").replace("/", "")
            if len(value) <= 11:  # CPF
                if len(value) <= 3:
                    formatted = value
                elif len(value) <= 6:
                    formatted = f"{value[:3]}.{value[3:]}"
                elif len(value) <= 9:
                    formatted = f"{value[:3]}.{value[3:6]}.{value[6:]}"
                else:
                    formatted = f"{value[:3]}.{value[3:6]}.{value[6:9]}-{value[9:11]}"
            else:  # CNPJ
                if len(value) <= 2:
                    formatted = value
                elif len(value) <= 5:
                    formatted = f"{value[:2]}.{value[2:]}"
                elif len(value) <= 8:
                    formatted = f"{value[:2]}.{value[2:5]}.{value[5:]}"
                elif len(value) <= 12:
                    formatted = f"{value[:2]}.{value[2:5]}.{value[5:8]}/{value[8:]}"
                else:
                    formatted = f"{value[:2]}.{value[2:5]}.{value[5:8]}/{value[8:12]}-{value[12:14]}"
            
            # Atualizar o campo apenas se o valor mudou
            current_pos = cpf_cnpj_entry.index(tk.INSERT)
            cpf_cnpj_entry.delete(0, tk.END)
            cpf_cnpj_entry.insert(0, formatted)
            # Reposicionar cursor
            try:
                new_pos = min(current_pos + (len(formatted) - len(value)), len(formatted))
                cpf_cnpj_entry.icursor(new_pos)
            except:
                cpf_cnpj_entry.icursor(tk.END)
        
        cpf_cnpj_entry.bind("<KeyRelease>", format_cpf_cnpj)
        
        tk.Label(dialog, text="Endereço da Propriedade", font=("Arial", 10)).grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        address_text = tk.Text(dialog, width=40, height=3, font=("Arial", 10))
        address_text.grid(row=3, column=1, padx=10, pady=5)
        
        tk.Label(dialog, text="Município *", font=("Arial", 10)).grid(row=4, column=0, sticky=tk.W, padx=10, pady=5)
        city_entry = tk.Entry(dialog, width=40, font=("Arial", 10))
        city_entry.grid(row=4, column=1, padx=10, pady=5)
        
        tk.Label(dialog, text="Estado *", font=("Arial", 10)).grid(row=5, column=0, sticky=tk.W, padx=10, pady=5)
        state_entry = tk.Entry(dialog, width=40, font=("Arial", 10))
        state_entry.grid(row=5, column=1, padx=10, pady=5)
        
        tk.Label(dialog, text="Área (hectares)", font=("Arial", 10)).grid(row=6, column=0, sticky=tk.W, padx=10, pady=5)
        area_entry = tk.Entry(dialog, width=40, font=("Arial", 10))
        area_entry.grid(row=6, column=1, padx=10, pady=5)
        
        tk.Label(dialog, text="Área de pastagem natural (ha)", font=("Arial", 10)).grid(row=7, column=0, sticky=tk.W, padx=10, pady=5)
        natural_pasture_entry = tk.Entry(dialog, width=40, font=("Arial", 10))
        natural_pasture_entry.grid(row=7, column=1, padx=10, pady=5)
        
        tk.Label(dialog, text="Área de pastagem cultivada (ha)", font=("Arial", 10)).grid(row=8, column=0, sticky=tk.W, padx=10, pady=5)
        cultivated_pasture_entry = tk.Entry(dialog, width=40, font=("Arial", 10))
        cultivated_pasture_entry.grid(row=8, column=1, padx=10, pady=5)
        
        # Preencher campos se estiver editando
        if property_id:
            prop = get_property(property_id)
            if prop:
                name_entry.insert(0, prop['name'])
                owner_entry.insert(0, prop['owner_name'])
                if prop.get('cpf_cnpj'):
                    cpf_cnpj_entry.insert(0, prop['cpf_cnpj'])
                if prop.get('address'):
                    address_text.insert("1.0", prop['address'])
                city_entry.insert(0, prop['city'])
                state_entry.insert(0, prop['state'])
                if prop.get('area'):
                    area_entry.insert(0, str(prop['area']))
                if prop.get('natural_pasture_area'):
                    natural_pasture_entry.insert(0, str(prop['natural_pasture_area']))
                if prop.get('cultivated_pasture_area'):
                    cultivated_pasture_entry.insert(0, str(prop['cultivated_pasture_area']))
        
        def save():
            if not all([name_entry.get(), owner_entry.get(), city_entry.get(), state_entry.get()]):
                messagebox.showwarning("Aviso", "Preencha todos os campos obrigatórios!")
                return
            
            try:
                area = float(area_entry.get()) if area_entry.get() else None
                natural_pasture = float(natural_pasture_entry.get()) if natural_pasture_entry.get() else None
                cultivated_pasture = float(cultivated_pasture_entry.get()) if cultivated_pasture_entry.get() else None
                # Remover formatação do CPF/CNPJ antes de salvar
                cpf_cnpj_raw = cpf_cnpj_entry.get().replace(".", "").replace("-", "").replace("/", "").strip()
                cpf_cnpj = cpf_cnpj_raw if cpf_cnpj_raw else None
                address = address_text.get("1.0", tk.END).strip() if address_text.get("1.0", tk.END).strip() else None
                
                if property_id:
                    from src.services.property_service import update_property
                    update_property(property_id, name_entry.get(), owner_entry.get(), 
                                  city_entry.get(), state_entry.get(), cpf_cnpj, address, area,
                                  natural_pasture, cultivated_pasture)
                    messagebox.showinfo("Sucesso", "Propriedade atualizada com sucesso!")
                else:
                    create_property(name_entry.get(), owner_entry.get(), 
                                  city_entry.get(), state_entry.get(), cpf_cnpj, address, area,
                                  natural_pasture, cultivated_pasture)
                    messagebox.showinfo("Sucesso", "Propriedade cadastrada com sucesso!")
                
                dialog.destroy()
                self.load_properties()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar propriedade:\n{str(e)}")
        
        # Botões
        btn_frame = tk.Frame(dialog)
        btn_frame.grid(row=9, column=0, columnspan=2, pady=20)
        tk.Button(btn_frame, text="💾 Salvar", command=save, bg="#66BB6A", fg="white",
                 font=("Arial", 11), padx=20, pady=5).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="❌ Cancelar", command=dialog.destroy, bg="#9E9E9E", fg="white",
                 font=("Arial", 11), padx=20, pady=5).pack(side=tk.LEFT, padx=5)
    
    def select_property(self):
        """Seleciona uma propriedade"""
        selection = self.properties_listbox.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma propriedade!")
            return
        
        selected_text = self.properties_listbox.get(selection[0])
        if selected_text in self.properties_data:
            self.current_property_id = self.properties_data[selected_text]
            self.show_home_screen()
    
    def edit_property(self):
        """Edita uma propriedade"""
        selection = self.properties_listbox.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma propriedade para editar!")
            return
        
        selected_text = self.properties_listbox.get(selection[0])
        if selected_text in self.properties_data:
            self.property_dialog(self.properties_data[selected_text])
    
    def delete_property(self):
        """Exclui uma propriedade"""
        selection = self.properties_listbox.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma propriedade para excluir!")
            return
        
        selected_text = self.properties_listbox.get(selection[0])
        if selected_text in self.properties_data:
            if messagebox.askyesno("Confirmar", "Deseja realmente excluir esta propriedade?\n\nTodos os dados relacionados serão perdidos!"):
                try:
                    from src.services.property_service import delete_property
                    delete_property(self.properties_data[selected_text])
                    messagebox.showinfo("Sucesso", "Propriedade excluída com sucesso!")
                    self.load_properties()
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao excluir propriedade:\n{str(e)}")
    
    def show_home_screen(self):
        """Mostra a tela inicial"""
        self.clear_window()
        
        # Cabeçalho - Estilo Web (#0D4F14)
        header = tk.Frame(self.root, bg="#0D4F14", height=80)
        header.pack(fill=tk.X)
        
        header_content = tk.Frame(header, bg="#0D4F14")
        header_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Labels que serão atualizados
        prop_label = tk.Label(header_content, text="🏠 Carregando...", font=("Arial", 16, "bold"), 
                bg="#0D4F14", fg="white")
        prop_label.pack(anchor=tk.W)
        total_label = tk.Label(header_content, text="🐄 Total de Animais: Carregando...", 
                font=("Arial", 11), bg="#0D4F14", fg="white")
        total_label.pack(anchor=tk.W)
        
        # Carregar dados de forma assíncrona
        def load_header_data():
            try:
                cache_key = f"property_{self.current_property_id}"
                if cache_key in self.data_cache:
                    prop = self.data_cache[cache_key]
                else:
                    prop = get_property(self.current_property_id)
                    self.data_cache[cache_key] = prop
                
                cache_key_total = f"total_animals_{self.current_property_id}"
                if cache_key_total in self.data_cache:
                    total_animals = self.data_cache[cache_key_total]
                else:
                    total_animals = get_total_animals(self.current_property_id)
                    self.data_cache[cache_key_total] = total_animals
                
                return prop, total_animals
            except Exception as e:
                return None, None
        
        def update_header(result):
            prop, total_animals = result
            prop_name = prop['name'] if prop else "Propriedade não encontrada"
            total = total_animals if total_animals is not None else 0
            prop_label.config(text=f"🏠 {prop_name}")
            total_label.config(text=f"🐄 Total de Animais: {total}")
        
        def load_thread():
            result = load_header_data()
            self.root.after(0, lambda: update_header(result))
        
        threading.Thread(target=load_thread, daemon=True).start()
        
        tk.Button(header_content, text="🔄 Trocar Propriedade", command=self.show_properties_screen,
                 bg="#9E9E9E", fg="white", font=("Arial", 10, "bold")).pack(side=tk.RIGHT, padx=10)
        
        # Menu principal
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Ordem e cores específicas conforme solicitado
        buttons = [
            # Verde vivo - Grupo 1
            ("🐄 Cadastrar Animais", "#2E7D32", self.show_animals_screen),  # Verde vivo escuro
            ("⭐ Nascimentos", "#2E7D32", self.show_births_screen),  # Verde vivo escuro
            ("💉 Controle Sanitário / Vacinação", "#2E7D32", self.show_health_screen),  # Verde vivo escuro
            
            # Verde oliva - Grupo 2
            ("🛒 Vendas", "#6B8E23", self.show_sales_screen),  # Verde oliva
            ("🛍️ Compras", "#6B8E23", self.show_purchases_screen),  # Verde oliva
            ("📄 Controle de GTA", "#6B8E23", self.show_gta_screen),  # Verde oliva
            
            # Vermelho vinho vivo - Grupo 3
            ("💀 Mortes", "#B22222", self.show_deaths_screen),  # Vermelho vinho vivo
            ("🐾 Outros Animais", "#B22222", self.show_other_animals_screen),  # Vermelho vinho vivo
            
            # Cinza escuro - Grupo 4
            ("📊 Relatórios", "#616161", self.show_reports_screen),  # Cinza escuro
        ]
        
        for i, (text, color, command) in enumerate(buttons):
            row = i // 2
            col = i % 2
            btn = tk.Button(main_frame, text=text, command=command, bg=color, fg="white",
                          font=("Arial", 12, "bold"), width=25, height=3)
            btn.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
    
    def show_animals_screen(self):
        """Mostra a tela de cadastro de animais"""
        self.clear_window()
        
        # Cabeçalho - Estilo Web (#0D4F14)
        header = tk.Frame(self.root, bg="#0D4F14", height=60)
        header.pack(fill=tk.X)
        tk.Label(header, text="🐄 Cadastro de Animais", font=("Arial", 18, "bold"), 
                bg="#0D4F14", fg="white").pack(pady=15)
        
        # Botão voltar
        back_frame = tk.Frame(self.root)
        back_frame.pack(fill=tk.X, padx=20, pady=10)
        tk.Button(back_frame, text="← Voltar", command=self.show_home_screen,
                 bg="#9E9E9E", fg="white", font=("Arial", 10)).pack(side=tk.LEFT)
        
        # Container principal
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Formulário
        form_frame = tk.LabelFrame(main_frame, text="Cadastrar Grupo de Animais", font=("Arial", 12, "bold"))
        form_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(form_frame, text="Finalidade *", font=("Arial", 10)).grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        purpose_var = tk.StringVar(value="Corte")
        purpose_combo = ttk.Combobox(form_frame, textvariable=purpose_var, 
                                     values=["Corte", "Leite"],
                                     width=37, state="readonly")
        purpose_combo.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(form_frame, text="Categoria *", font=("Arial", 10)).grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        category_var = tk.StringVar(value="Bezerro")
        category_combo = ttk.Combobox(form_frame, textvariable=category_var, 
                                     values=["Bezerro", "Bezerra", "Novilho", "Novilha", "Touro", "Vaca", "Boi", "Terneiro", "Terneira"],
                                     width=37, state="readonly")
        category_combo.grid(row=1, column=1, padx=10, pady=5)
        
        tk.Label(form_frame, text="Sexo *", font=("Arial", 10)).grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        sex_var = tk.StringVar(value="Macho")
        sex_combo = ttk.Combobox(form_frame, textvariable=sex_var, values=["Macho", "Fêmea"], width=37, state="readonly")
        sex_combo.grid(row=2, column=1, padx=10, pady=5)
        
        tk.Label(form_frame, text="Faixa Etária *", font=("Arial", 10)).grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        age_range_var = tk.StringVar(value="0 a 6 meses")
        age_range_combo = ttk.Combobox(form_frame, textvariable=age_range_var, 
                                       values=["0 a 6 meses", "7 a 12 meses", "13 a 24 meses", "25 a 36 meses", "Acima de 36 meses"],
                                       width=37, state="readonly")
        age_range_combo.grid(row=3, column=1, padx=10, pady=5)
        
        tk.Label(form_frame, text="Quantidade *", font=("Arial", 10)).grid(row=4, column=0, sticky=tk.W, padx=10, pady=5)
        quantity_entry = tk.Entry(form_frame, width=40, font=("Arial", 10))
        quantity_entry.grid(row=4, column=1, padx=10, pady=5)
        
        def save_animal():
            if not quantity_entry.get():
                messagebox.showwarning("Aviso", "Informe a quantidade!")
                return
            try:
                from src.services.animal_service import create_animal_group
                quantity = int(quantity_entry.get())
                create_animal_group(self.current_property_id, purpose_var.get(), 
                                  category_var.get(), sex_var.get(), quantity, age_range_var.get(), None)
                # Invalidar cache relacionado a animais
                self.invalidate_cache(f"animals_{self.current_property_id}")
                self.invalidate_cache(f"total_animals_{self.current_property_id}")
                messagebox.showinfo("Sucesso", "Animais cadastrados com sucesso!")
                quantity_entry.delete(0, tk.END)
                load_animals_list()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar:\n{str(e)}")
        
        tk.Button(form_frame, text="💾 Salvar", command=save_animal, bg="#0D4F14", fg="white",
                 font=("Arial", 11), padx=20, pady=5).grid(row=5, column=0, columnspan=2, pady=10)
        
        # Lista de animais
        list_frame = tk.LabelFrame(main_frame, text="Animais Cadastrados", font=("Arial", 12, "bold"))
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview para lista
        columns = ("Finalidade", "Categoria", "Sexo", "Faixa Etária", "Quantidade")
        animals_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        for col in columns:
            animals_tree.heading(col, text=col)
            animals_tree.column(col, width=120)
        animals_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar_tree = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=animals_tree.yview)
        scrollbar_tree.pack(side=tk.RIGHT, fill=tk.Y)
        animals_tree.configure(yscrollcommand=scrollbar_tree.set)
        
        def load_animals_list():
            cache_key = f"animals_{self.current_property_id}"
            
            def load_data():
                try:
                    from src.services.animal_service import get_animals_by_property
                    if cache_key in self.data_cache:
                        return self.data_cache[cache_key]
                    animals = get_animals_by_property(self.current_property_id)
                    self.data_cache[cache_key] = animals
                    return animals
                except Exception as e:
                    return None, str(e)
            
            def update_tree(result):
                if result is None:
                    return
                if isinstance(result, tuple) and len(result) == 2:
                    error = result[1]
                    messagebox.showerror("Erro", f"Erro ao carregar animais:\n{error}")
                    return
                animals_tree.delete(*animals_tree.get_children())
                for animal in result:
                    animals_tree.insert("", tk.END, values=(
                        animal.get('purpose', '') or '', animal['category'], animal['sex'], 
                        animal.get('age_range', '') or '', animal['quantity']
                    ))
            
            def load_thread():
                result = load_data()
                self.root.after(0, lambda: update_tree(result))
            
            threading.Thread(target=load_thread, daemon=True).start()
        
        load_animals_list()
    
    def show_births_screen(self):
        """Mostra a tela de nascimentos"""
        self.clear_window()
        
        header = tk.Frame(self.root, bg="#0D4F14", height=60)
        header.pack(fill=tk.X)
        tk.Label(header, text="⭐ Registro de Nascimentos", font=("Arial", 18, "bold"), 
                bg="#0D4F14", fg="white").pack(pady=15)
        
        back_frame = tk.Frame(self.root)
        back_frame.pack(fill=tk.X, padx=20, pady=10)
        tk.Button(back_frame, text="← Voltar", command=self.show_home_screen,
                 bg="#9E9E9E", fg="white", font=("Arial", 10)).pack(side=tk.LEFT)
        
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        form_frame = tk.LabelFrame(main_frame, text="Registrar Nascimento", font=("Arial", 12, "bold"))
        form_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(form_frame, text="Data *", font=("Arial", 10)).grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        date_entry = tk.Entry(form_frame, width=40, font=("Arial", 10))
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        date_entry.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(form_frame, text="Sexo *", font=("Arial", 10)).grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        sex_var = tk.StringVar(value="Macho")
        sex_combo = ttk.Combobox(form_frame, textvariable=sex_var, values=["Macho", "Fêmea"], width=37, state="readonly")
        sex_combo.grid(row=1, column=1, padx=10, pady=5)
        
        tk.Label(form_frame, text="Faixa Etária *", font=("Arial", 10)).grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        age_range_var = tk.StringVar(value="0 a 6 meses")
        age_range_combo = ttk.Combobox(form_frame, textvariable=age_range_var, 
                                       values=["0 a 6 meses", "7 a 12 meses", "13 a 24 meses", "25 a 36 meses", "Acima de 36 meses"],
                                       width=37, state="readonly")
        age_range_combo.grid(row=2, column=1, padx=10, pady=5)
        
        tk.Label(form_frame, text="Quantidade *", font=("Arial", 10)).grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        quantity_entry = tk.Entry(form_frame, width=40, font=("Arial", 10))
        quantity_entry.grid(row=3, column=1, padx=10, pady=5)
        
        def save_birth():
            if not all([date_entry.get(), quantity_entry.get()]):
                messagebox.showwarning("Aviso", "Preencha todos os campos obrigatórios!")
                return
            try:
                from src.services.animal_service import register_birth
                quantity = int(quantity_entry.get())
                register_birth(self.current_property_id, date_entry.get(), sex_var.get(), age_range_var.get(), quantity, None)
                messagebox.showinfo("Sucesso", "Nascimento registrado com sucesso!")
                date_entry.delete(0, tk.END)
                date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
                quantity_entry.delete(0, tk.END)
                load_births_list()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar:\n{str(e)}")
        
        tk.Button(form_frame, text="💾 Salvar", command=save_birth, bg="#81C784", fg="white",
                 font=("Arial", 11), padx=20, pady=5).grid(row=4, column=0, columnspan=2, pady=10)
        
        list_frame = tk.LabelFrame(main_frame, text="Histórico de Nascimentos", font=("Arial", 12, "bold"))
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("Data", "Sexo", "Faixa Etária", "Quantidade")
        births_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        for col in columns:
            births_tree.heading(col, text=col)
            births_tree.column(col, width=150)
        births_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        def load_births_list():
            births_tree.delete(*births_tree.get_children())
            try:
                from src.services.animal_service import get_births_by_property
                births = get_births_by_property(self.current_property_id)
                for birth in births:
                    births_tree.insert("", tk.END, values=(
                        birth['date'], birth['sex'], birth.get('age_range', '') or '', birth['quantity']
                    ))
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar nascimentos:\n{str(e)}")
        
        load_births_list()
    
    def show_sales_screen(self):
        """Mostra a tela de vendas"""
        self.clear_window()
        
        header = tk.Frame(self.root, bg="#0D4F14", height=60)
        header.pack(fill=tk.X)
        tk.Label(header, text="🛒 Registro de Vendas", font=("Arial", 18, "bold"), 
                bg="#0D4F14", fg="white").pack(pady=15)
        
        back_frame = tk.Frame(self.root)
        back_frame.pack(fill=tk.X, padx=20, pady=10)
        tk.Button(back_frame, text="← Voltar", command=self.show_home_screen,
                 bg="#9E9E9E", fg="white", font=("Arial", 10)).pack(side=tk.LEFT)
        
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        form_frame = tk.LabelFrame(main_frame, text="Registrar Venda", font=("Arial", 12, "bold"))
        form_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(form_frame, text="Data *", font=("Arial", 10)).grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        date_entry = tk.Entry(form_frame, width=40, font=("Arial", 10))
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        date_entry.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(form_frame, text="Categoria *", font=("Arial", 10)).grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        category_var = tk.StringVar(value="Bezerro")
        category_combo = ttk.Combobox(form_frame, textvariable=category_var, 
                                     values=["Bezerro", "Bezerra", "Novilho", "Novilha", "Touro", "Vaca", "Boi", "Terneiro", "Terneira"],
                                     width=37, state="readonly")
        category_combo.grid(row=1, column=1, padx=10, pady=5)
        
        tk.Label(form_frame, text="Sexo *", font=("Arial", 10)).grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        sex_var = tk.StringVar(value="Macho")
        sex_combo = ttk.Combobox(form_frame, textvariable=sex_var, values=["Macho", "Fêmea"], width=37, state="readonly")
        sex_combo.grid(row=2, column=1, padx=10, pady=5)
        
        tk.Label(form_frame, text="Faixa Etária *", font=("Arial", 10)).grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        age_range_var = tk.StringVar(value="0 a 6 meses")
        age_range_combo = ttk.Combobox(form_frame, textvariable=age_range_var, 
                                       values=["0 a 6 meses", "7 a 12 meses", "13 a 24 meses", "25 a 36 meses", "Acima de 36 meses"],
                                       width=37, state="readonly")
        age_range_combo.grid(row=3, column=1, padx=10, pady=5)
        
        tk.Label(form_frame, text="Quantidade *", font=("Arial", 10)).grid(row=4, column=0, sticky=tk.W, padx=10, pady=5)
        quantity_entry = tk.Entry(form_frame, width=40, font=("Arial", 10))
        quantity_entry.grid(row=4, column=1, padx=10, pady=5)
        
        has_gta_var = tk.BooleanVar()
        tk.Checkbutton(form_frame, text="Possui GTA", variable=has_gta_var, font=("Arial", 10)).grid(row=5, column=0, columnspan=2, sticky=tk.W, padx=10, pady=5)
        
        tk.Label(form_frame, text="Número da GTA", font=("Arial", 10)).grid(row=6, column=0, sticky=tk.W, padx=10, pady=5)
        gta_entry = tk.Entry(form_frame, width=40, font=("Arial", 10))
        gta_entry.grid(row=6, column=1, padx=10, pady=5)
        
        tk.Label(form_frame, text="Destino da GTA", font=("Arial", 10)).grid(row=7, column=0, sticky=tk.W, padx=10, pady=5)
        tk.Label(form_frame, text="(Ex: Fazenda XYZ, Cidade/Estado)", font=("Arial", 8), fg="gray").grid(row=7, column=1, sticky=tk.W, padx=10, pady=0)
        destination_entry = tk.Entry(form_frame, width=40, font=("Arial", 10))
        destination_entry.grid(row=8, column=1, padx=10, pady=5)
        
        def save_sale():
            if not all([date_entry.get(), quantity_entry.get()]):
                messagebox.showwarning("Aviso", "Preencha todos os campos obrigatórios!")
                return
            try:
                from src.services.movement_service import register_sale
                quantity = int(quantity_entry.get())
                gta_number = gta_entry.get().strip() if has_gta_var.get() and gta_entry.get() else None
                destination = destination_entry.get().strip() if destination_entry.get() and destination_entry.get().strip() else None
                register_sale(self.current_property_id, date_entry.get(), category_var.get(), 
                            sex_var.get(), age_range_var.get(), quantity, has_gta_var.get(), gta_number, destination)
                messagebox.showinfo("Sucesso", "Venda registrada com sucesso!")
                date_entry.delete(0, tk.END)
                date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
                quantity_entry.delete(0, tk.END)
                gta_entry.delete(0, tk.END)
                destination_entry.delete(0, tk.END)
                has_gta_var.set(False)
                load_sales_list()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar:\n{str(e)}")
        
        tk.Button(form_frame, text="💾 Salvar", command=save_sale, bg="#A5D6A7", fg="white",
                 font=("Arial", 11), padx=20, pady=5).grid(row=9, column=0, columnspan=2, pady=10)
        
        list_frame = tk.LabelFrame(main_frame, text="Histórico de Vendas", font=("Arial", 12, "bold"))
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("Data", "Categoria", "Sexo", "Faixa Etária", "Quantidade", "GTA", "Destino")
        sales_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        for col in columns:
            sales_tree.heading(col, text=col)
            sales_tree.column(col, width=120)
        sales_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        def load_sales_list():
            sales_tree.delete(*sales_tree.get_children())
            try:
                from src.services.movement_service import get_sales_by_property
                sales = get_sales_by_property(self.current_property_id)
                for sale in sales:
                    sales_tree.insert("", tk.END, values=(
                        sale['date'], sale['category'], sale['sex'], sale.get('age_range', '') or '',
                        sale['quantity'], sale['gta_number'] if sale['has_gta'] else 'Não', sale.get('destination', '') or ''
                    ))
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar vendas:\n{str(e)}")
        
        load_sales_list()
    
    def show_purchases_screen(self):
        """Mostra a tela de compras"""
        self.clear_window()
        
        header = tk.Frame(self.root, bg="#0D4F14", height=60)
        header.pack(fill=tk.X)
        tk.Label(header, text="🛍️ Registro de Compras", font=("Arial", 18, "bold"), 
                bg="#0D4F14", fg="white").pack(pady=15)
        
        back_frame = tk.Frame(self.root)
        back_frame.pack(fill=tk.X, padx=20, pady=10)
        tk.Button(back_frame, text="← Voltar", command=self.show_home_screen,
                 bg="#9E9E9E", fg="white", font=("Arial", 10)).pack(side=tk.LEFT)
        
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        form_frame = tk.LabelFrame(main_frame, text="Registrar Compra", font=("Arial", 12, "bold"))
        form_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(form_frame, text="Data *", font=("Arial", 10)).grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        date_entry = tk.Entry(form_frame, width=40, font=("Arial", 10))
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        date_entry.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(form_frame, text="Origem da GTA *", font=("Arial", 10)).grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        tk.Label(form_frame, text="(Ex: Fazenda ABC, Cidade/Estado)", font=("Arial", 8), fg="gray").grid(row=1, column=1, sticky=tk.W, padx=10, pady=0)
        origin_entry = tk.Entry(form_frame, width=40, font=("Arial", 10))
        origin_entry.grid(row=2, column=1, padx=10, pady=5)
        
        tk.Label(form_frame, text="Categoria *", font=("Arial", 10)).grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        category_var = tk.StringVar(value="Bezerro")
        category_combo = ttk.Combobox(form_frame, textvariable=category_var, 
                                     values=["Bezerro", "Bezerra", "Novilho", "Novilha", "Touro", "Vaca", "Boi", "Terneiro", "Terneira"],
                                     width=37, state="readonly")
        category_combo.grid(row=3, column=1, padx=10, pady=5)
        
        tk.Label(form_frame, text="Sexo *", font=("Arial", 10)).grid(row=4, column=0, sticky=tk.W, padx=10, pady=5)
        sex_var = tk.StringVar(value="Macho")
        sex_combo = ttk.Combobox(form_frame, textvariable=sex_var, values=["Macho", "Fêmea"], width=37, state="readonly")
        sex_combo.grid(row=4, column=1, padx=10, pady=5)
        
        tk.Label(form_frame, text="Faixa Etária *", font=("Arial", 10)).grid(row=5, column=0, sticky=tk.W, padx=10, pady=5)
        age_range_var = tk.StringVar(value="0 a 6 meses")
        age_range_combo = ttk.Combobox(form_frame, textvariable=age_range_var, 
                                       values=["0 a 6 meses", "7 a 12 meses", "13 a 24 meses", "25 a 36 meses", "Acima de 36 meses"],
                                       width=37, state="readonly")
        age_range_combo.grid(row=5, column=1, padx=10, pady=5)
        
        tk.Label(form_frame, text="Quantidade *", font=("Arial", 10)).grid(row=6, column=0, sticky=tk.W, padx=10, pady=5)
        quantity_entry = tk.Entry(form_frame, width=40, font=("Arial", 10))
        quantity_entry.grid(row=6, column=1, padx=10, pady=5)
        
        has_gta_var = tk.BooleanVar()
        tk.Checkbutton(form_frame, text="Possui GTA", variable=has_gta_var, font=("Arial", 10)).grid(row=7, column=0, columnspan=2, sticky=tk.W, padx=10, pady=5)
        
        tk.Label(form_frame, text="Número da GTA", font=("Arial", 10)).grid(row=8, column=0, sticky=tk.W, padx=10, pady=5)
        gta_entry = tk.Entry(form_frame, width=40, font=("Arial", 10))
        gta_entry.grid(row=8, column=1, padx=10, pady=5)
        
        def save_purchase():
            if not all([date_entry.get(), origin_entry.get(), quantity_entry.get()]):
                messagebox.showwarning("Aviso", "Preencha todos os campos obrigatórios!")
                return
            try:
                from src.services.movement_service import register_purchase
                quantity = int(quantity_entry.get())
                gta_number = gta_entry.get().strip() if has_gta_var.get() and gta_entry.get() else None
                register_purchase(self.current_property_id, date_entry.get(), origin_entry.get(), 
                                category_var.get(), sex_var.get(), age_range_var.get(), quantity, has_gta_var.get(), gta_number)
                messagebox.showinfo("Sucesso", "Compra registrada com sucesso!")
                date_entry.delete(0, tk.END)
                date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
                origin_entry.delete(0, tk.END)
                quantity_entry.delete(0, tk.END)
                gta_entry.delete(0, tk.END)
                has_gta_var.set(False)
                load_purchases_list()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar:\n{str(e)}")
        
        tk.Button(form_frame, text="💾 Salvar", command=save_purchase, bg="#66BB6A", fg="white",
                 font=("Arial", 11), padx=20, pady=5).grid(row=9, column=0, columnspan=2, pady=10)
        
        list_frame = tk.LabelFrame(main_frame, text="Histórico de Compras", font=("Arial", 12, "bold"))
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("Data", "Origem", "Categoria", "Sexo", "Faixa Etária", "Quantidade", "GTA")
        purchases_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        for col in columns:
            purchases_tree.heading(col, text=col)
            purchases_tree.column(col, width=120)
        purchases_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        def load_purchases_list():
            purchases_tree.delete(*purchases_tree.get_children())
            try:
                from src.services.movement_service import get_purchases_by_property
                purchases = get_purchases_by_property(self.current_property_id)
                for purchase in purchases:
                    purchases_tree.insert("", tk.END, values=(
                        purchase['date'], purchase['origin'], purchase['category'], purchase['sex'],
                        purchase.get('age_range', '') or '', purchase['quantity'], 
                        purchase['gta_number'] if purchase['has_gta'] else 'Não'
                    ))
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar compras:\n{str(e)}")
        
        load_purchases_list()
    
    def show_deaths_screen(self):
        """Mostra a tela de mortes"""
        self.clear_window()
        
        header = tk.Frame(self.root, bg="#0D4F14", height=60)
        header.pack(fill=tk.X)
        tk.Label(header, text="💀 Registro de Mortes", font=("Arial", 18, "bold"), 
                bg="#0D4F14", fg="white").pack(pady=15)
        
        back_frame = tk.Frame(self.root)
        back_frame.pack(fill=tk.X, padx=20, pady=10)
        tk.Button(back_frame, text="← Voltar", command=self.show_home_screen,
                 bg="#9E9E9E", fg="white", font=("Arial", 10)).pack(side=tk.LEFT)
        
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        form_frame = tk.LabelFrame(main_frame, text="Registrar Morte", font=("Arial", 12, "bold"))
        form_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(form_frame, text="Data *", font=("Arial", 10)).grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        date_entry = tk.Entry(form_frame, width=40, font=("Arial", 10))
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        date_entry.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(form_frame, text="Categoria *", font=("Arial", 10)).grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        category_var = tk.StringVar(value="Bezerro")
        category_combo = ttk.Combobox(form_frame, textvariable=category_var, 
                                     values=["Bezerro", "Bezerra", "Novilho", "Novilha", "Touro", "Vaca", "Boi", "Terneiro", "Terneira"],
                                     width=37, state="readonly")
        category_combo.grid(row=1, column=1, padx=10, pady=5)
        
        tk.Label(form_frame, text="Sexo *", font=("Arial", 10)).grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        sex_var = tk.StringVar(value="Macho")
        sex_combo = ttk.Combobox(form_frame, textvariable=sex_var, values=["Macho", "Fêmea"], width=37, state="readonly")
        sex_combo.grid(row=2, column=1, padx=10, pady=5)
        
        tk.Label(form_frame, text="Faixa Etária *", font=("Arial", 10)).grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        age_range_var = tk.StringVar(value="0 a 6 meses")
        age_range_combo = ttk.Combobox(form_frame, textvariable=age_range_var, 
                                       values=["0 a 6 meses", "7 a 12 meses", "13 a 24 meses", "25 a 36 meses", "Acima de 36 meses"],
                                       width=37, state="readonly")
        age_range_combo.grid(row=3, column=1, padx=10, pady=5)
        
        tk.Label(form_frame, text="Quantidade *", font=("Arial", 10)).grid(row=4, column=0, sticky=tk.W, padx=10, pady=5)
        quantity_entry = tk.Entry(form_frame, width=40, font=("Arial", 10))
        quantity_entry.grid(row=4, column=1, padx=10, pady=5)
        
        tk.Label(form_frame, text="Causa da Morte", font=("Arial", 10)).grid(row=5, column=0, sticky=tk.W, padx=10, pady=5)
        tk.Label(form_frame, text="(Ex: Paralisia, Problema digestivo, Acidente)", font=("Arial", 8), fg="gray").grid(row=5, column=1, sticky=tk.W, padx=10, pady=0)
        cause_text = tk.Text(form_frame, width=40, height=3, font=("Arial", 10))
        cause_text.grid(row=6, column=1, padx=10, pady=5)
        
        def save_death():
            if not all([date_entry.get(), quantity_entry.get()]):
                messagebox.showwarning("Aviso", "Preencha todos os campos obrigatórios!")
                return
            try:
                from src.services.animal_service import register_death
                quantity = int(quantity_entry.get())
                cause = cause_text.get("1.0", tk.END).strip() if cause_text.get("1.0", tk.END).strip() else None
                register_death(self.current_property_id, date_entry.get(), category_var.get(), 
                             sex_var.get(), age_range_var.get(), quantity, cause)
                messagebox.showinfo("Sucesso", "Morte registrada com sucesso!")
                date_entry.delete(0, tk.END)
                date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
                quantity_entry.delete(0, tk.END)
                cause_text.delete("1.0", tk.END)
                load_deaths_list()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar:\n{str(e)}")
        
        tk.Button(form_frame, text="💾 Salvar", command=save_death, bg="#8D6E63", fg="white",
                 font=("Arial", 11), padx=20, pady=5).grid(row=7, column=0, columnspan=2, pady=10)
        
        list_frame = tk.LabelFrame(main_frame, text="Histórico de Mortes", font=("Arial", 12, "bold"))
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("Data", "Categoria", "Sexo", "Faixa Etária", "Quantidade", "Causa")
        deaths_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        for col in columns:
            deaths_tree.heading(col, text=col)
            deaths_tree.column(col, width=150)
        deaths_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        def load_deaths_list():
            deaths_tree.delete(*deaths_tree.get_children())
            try:
                from src.services.animal_service import get_deaths_by_property
                deaths = get_deaths_by_property(self.current_property_id)
                for death in deaths:
                    deaths_tree.insert("", tk.END, values=(
                        death['date'], death['category'], death['sex'], death.get('age_range', '') or '',
                        death['quantity'], death.get('cause', '') or ''
                    ))
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar mortes:\n{str(e)}")
        
        load_deaths_list()
    
    def show_health_screen(self):
        """Mostra a tela de controle sanitário"""
        self.clear_window()
        
        header = tk.Frame(self.root, bg="#0D4F14", height=60)
        header.pack(fill=tk.X)
        tk.Label(header, text="💉 Controle Sanitário / Vacinação", font=("Arial", 18, "bold"), 
                bg="#0D4F14", fg="white").pack(pady=15)
        
        back_frame = tk.Frame(self.root)
        back_frame.pack(fill=tk.X, padx=20, pady=10)
        tk.Button(back_frame, text="← Voltar", command=self.show_home_screen,
                 bg="#9E9E9E", fg="white", font=("Arial", 10)).pack(side=tk.LEFT)
        
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        form_frame = tk.LabelFrame(main_frame, text="Registrar Procedimento Sanitário", font=("Arial", 12, "bold"))
        form_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(form_frame, text="Tipo de Procedimento *", font=("Arial", 10)).grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        procedure_var = tk.StringVar(value="Vacinação")
        procedure_combo = ttk.Combobox(form_frame, textvariable=procedure_var, 
                                      values=["Vacinação", "Vermifugação", "Medicamento", "Aplicação de Vitamina", "Outro Procedimento"],
                                      width=37, state="readonly")
        procedure_combo.grid(row=0, column=1, padx=10, pady=5)
        
        # Campo de Tipo de Vacinação (aparece apenas quando Vacinação é selecionado)
        vaccination_type_label = tk.Label(form_frame, text="Tipo de Vacinação *", font=("Arial", 10))
        vaccination_type_var = tk.StringVar(value="Aftosa")
        vaccination_type_combo = ttk.Combobox(form_frame, textvariable=vaccination_type_var, 
                                              values=["Aftosa", "Brucelose", "Raiva", "Outra"],
                                              width=37, state="readonly")
        
        # Campo para digitar o tipo quando "Outra" é selecionado
        other_vaccination_label = tk.Label(form_frame, text="Qual Tipo de Vacinação? *", font=("Arial", 10))
        other_vaccination_entry = tk.Entry(form_frame, width=40, font=("Arial", 10))
        
        # Labels de exemplo (criados uma vez e reutilizados)
        purpose_example_label = tk.Label(form_frame, text="(Ex: Verminose, Pneumonia, Mastite)", font=("Arial", 8), fg="gray")
        product_example_label = tk.Label(form_frame, text="(Ex: Ivermectina 1%, Vitamina ADE, Antibiótico)", font=("Arial", 8), fg="gray")
        
        # Criar todos os widgets primeiro
        purpose_label = tk.Label(form_frame, text="Finalidade/Doença *", font=("Arial", 10))
        purpose_entry = tk.Entry(form_frame, width=40, font=("Arial", 10))
        
        product_label = tk.Label(form_frame, text="Produto Utilizado *", font=("Arial", 10))
        product_entry = tk.Entry(form_frame, width=40, font=("Arial", 10))
        
        date_label = tk.Label(form_frame, text="Data da Aplicação *", font=("Arial", 10))
        date_entry = tk.Entry(form_frame, width=40, font=("Arial", 10))
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        category_label = tk.Label(form_frame, text="Categoria *", font=("Arial", 10))
        category_var = tk.StringVar(value="Bezerro")
        category_combo = ttk.Combobox(form_frame, textvariable=category_var, 
                                     values=["Bezerro", "Bezerra", "Novilho", "Novilha", "Touro", "Vaca", "Boi", "Terneiro", "Terneira"],
                                     width=37, state="readonly")
        
        sex_label = tk.Label(form_frame, text="Sexo *", font=("Arial", 10))
        sex_var = tk.StringVar(value="Macho")
        sex_combo = ttk.Combobox(form_frame, textvariable=sex_var, values=["Macho", "Fêmea"], width=37, state="readonly")
        
        age_range_label = tk.Label(form_frame, text="Faixa Etária *", font=("Arial", 10))
        age_range_var = tk.StringVar(value="0 a 6 meses")
        age_range_combo = ttk.Combobox(form_frame, textvariable=age_range_var, 
                                       values=["0 a 6 meses", "7 a 12 meses", "13 a 24 meses", "25 a 36 meses", "Acima de 36 meses"],
                                       width=37, state="readonly")
        
        quantity_label = tk.Label(form_frame, text="Quantidade de Animais *", font=("Arial", 10))
        quantity_entry = tk.Entry(form_frame, width=40, font=("Arial", 10))
        
        next_date_label = tk.Label(form_frame, text="Data da Próxima Aplicação", font=("Arial", 10))
        next_date_entry = tk.Entry(form_frame, width=40, font=("Arial", 10))
        
        notes_label = tk.Label(form_frame, text="Observações", font=("Arial", 10))
        notes_text = tk.Text(form_frame, width=40, height=3, font=("Arial", 10))
        
        save_button = tk.Button(form_frame, text="💾 Salvar", command=None, bg="#388E3C", fg="white",
                 font=("Arial", 11), padx=20, pady=5)
        
        def update_field_positions():
            """Atualiza as posições de todos os campos dinamicamente"""
            current_row = 1  # Começa após "Tipo de Procedimento" (row 0)
            
            # Campos condicionais de vacinação - reposicionar se estiverem visíveis
            if procedure_var.get() == "Vacinação":
                vaccination_type_label.grid(row=current_row, column=0, sticky=tk.W, padx=10, pady=5)
                vaccination_type_combo.grid(row=current_row, column=1, padx=10, pady=5)
                current_row += 1
                if vaccination_type_var.get() == "Outra":
                    other_vaccination_label.grid(row=current_row, column=0, sticky=tk.W, padx=10, pady=5)
                    other_vaccination_entry.grid(row=current_row, column=1, padx=10, pady=5)
                    current_row += 1
            
            # Finalidade/Doença
            purpose_label.grid(row=current_row, column=0, sticky=tk.W, padx=10, pady=5)
            purpose_example_label.grid(row=current_row, column=1, sticky=tk.W, padx=10, pady=0)
            purpose_entry.grid(row=current_row+1, column=1, padx=10, pady=5)
            current_row += 2
            
            # Produto Utilizado
            product_label.grid(row=current_row, column=0, sticky=tk.W, padx=10, pady=5)
            product_example_label.grid(row=current_row, column=1, sticky=tk.W, padx=10, pady=0)
            product_entry.grid(row=current_row+1, column=1, padx=10, pady=5)
            current_row += 2
            
            # Data da Aplicação
            date_label.grid(row=current_row, column=0, sticky=tk.W, padx=10, pady=5)
            date_entry.grid(row=current_row, column=1, padx=10, pady=5)
            current_row += 1
            
            # Categoria
            category_label.grid(row=current_row, column=0, sticky=tk.W, padx=10, pady=5)
            category_combo.grid(row=current_row, column=1, padx=10, pady=5)
            current_row += 1
            
            # Sexo
            sex_label.grid(row=current_row, column=0, sticky=tk.W, padx=10, pady=5)
            sex_combo.grid(row=current_row, column=1, padx=10, pady=5)
            current_row += 1
            
            # Faixa Etária
            age_range_label.grid(row=current_row, column=0, sticky=tk.W, padx=10, pady=5)
            age_range_combo.grid(row=current_row, column=1, padx=10, pady=5)
            current_row += 1
            
            # Quantidade
            quantity_label.grid(row=current_row, column=0, sticky=tk.W, padx=10, pady=5)
            quantity_entry.grid(row=current_row, column=1, padx=10, pady=5)
            current_row += 1
            
            # Data Próxima Aplicação
            next_date_label.grid(row=current_row, column=0, sticky=tk.W, padx=10, pady=5)
            next_date_entry.grid(row=current_row, column=1, padx=10, pady=5)
            current_row += 1
            
            # Observações
            notes_label.grid(row=current_row, column=0, sticky=tk.W, padx=10, pady=5)
            notes_text.grid(row=current_row, column=1, padx=10, pady=5)
            current_row += 1
            
            # Botão Salvar
            save_button.grid(row=current_row, column=0, columnspan=2, pady=10)
        
        def toggle_vaccination_type(*args):
            if procedure_var.get() != "Vacinação":
                vaccination_type_label.grid_remove()
                vaccination_type_combo.grid_remove()
                other_vaccination_label.grid_remove()
                other_vaccination_entry.grid_remove()
            update_field_positions()
        
        def toggle_other_vaccination(*args):
            if procedure_var.get() != "Vacinação" or vaccination_type_var.get() != "Outra":
                other_vaccination_label.grid_remove()
                other_vaccination_entry.grid_remove()
            update_field_positions()
        
        procedure_var.trace('w', toggle_vaccination_type)
        vaccination_type_var.trace('w', toggle_other_vaccination)
        toggle_vaccination_type()  # Inicializa o estado
        
        def save_health():
            purpose_value = purpose_entry.get().strip()
            product_value = product_entry.get().strip()
            if not all([purpose_value, product_value, date_entry.get(), quantity_entry.get()]):
                messagebox.showwarning("Aviso", "Preencha todos os campos obrigatórios!")
                return
            if procedure_var.get() == "Vacinação":
                if not vaccination_type_var.get():
                    messagebox.showwarning("Aviso", "Selecione o tipo de vacinação!")
                    return
                if vaccination_type_var.get() == "Outra" and not other_vaccination_entry.get().strip():
                    messagebox.showwarning("Aviso", "Informe o tipo de vacinação!")
                    return
            try:
                from src.services.health_service import register_health_procedure
                quantity = int(quantity_entry.get())
                next_date = next_date_entry.get().strip() if next_date_entry.get() else None
                notes = notes_text.get("1.0", tk.END).strip() if notes_text.get("1.0", tk.END).strip() else None
                if procedure_var.get() == "Vacinação":
                    if vaccination_type_var.get() == "Outra":
                        vaccination_type = other_vaccination_entry.get().strip()
                    else:
                        vaccination_type = vaccination_type_var.get()
                else:
                    vaccination_type = None
                register_health_procedure(self.current_property_id, procedure_var.get(), vaccination_type,
                                        purpose_value, product_value, date_entry.get(), category_var.get(), sex_var.get(),
                                        age_range_var.get(), quantity, next_date, notes)
                messagebox.showinfo("Sucesso", "Procedimento registrado com sucesso!")
                date_entry.delete(0, tk.END)
                date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
                purpose_entry.delete(0, tk.END)
                product_entry.delete(0, tk.END)
                quantity_entry.delete(0, tk.END)
                next_date_entry.delete(0, tk.END)
                notes_text.delete("1.0", tk.END)
                other_vaccination_entry.delete(0, tk.END)
                load_health_list()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar:\n{str(e)}")
        
        save_button.config(command=save_health)
        
        list_frame = tk.LabelFrame(main_frame, text="Histórico de Procedimentos", font=("Arial", 12, "bold"))
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("Data", "Tipo", "Produto", "Categoria", "Sexo", "Faixa Etária", "Quantidade", "Próxima")
        health_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        for col in columns:
            health_tree.heading(col, text=col)
            health_tree.column(col, width=120)
        health_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        def load_health_list():
            health_tree.delete(*health_tree.get_children())
            try:
                from src.services.health_service import get_health_procedures_by_property
                procedures = get_health_procedures_by_property(self.current_property_id)
                for proc in procedures:
                    health_tree.insert("", tk.END, values=(
                        proc['application_date'], proc['procedure_type'], proc['product'],
                        proc['category'], proc['sex'], proc.get('age_range', '') or '',
                        proc['quantity'], proc.get('next_application_date', '') or ''
                    ))
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar procedimentos:\n{str(e)}")
        
        load_health_list()
    
    def show_gta_screen(self):
        """Mostra a tela de controle de GTA"""
        self.clear_window()
        
        header = tk.Frame(self.root, bg="#0D4F14", height=60)
        header.pack(fill=tk.X)
        tk.Label(header, text="📄 Controle de GTA", font=("Arial", 18, "bold"), 
                bg="#0D4F14", fg="white").pack(pady=15)
        
        back_frame = tk.Frame(self.root)
        back_frame.pack(fill=tk.X, padx=20, pady=10)
        tk.Button(back_frame, text="← Voltar", command=self.show_home_screen,
                 bg="#9E9E9E", fg="white", font=("Arial", 10)).pack(side=tk.LEFT)
        
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        form_frame = tk.LabelFrame(main_frame, text="Registrar GTA", font=("Arial", 12, "bold"))
        form_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(form_frame, text="Tipo de Movimentação *", font=("Arial", 10)).grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        movement_var = tk.StringVar(value="Compra")
        movement_combo = ttk.Combobox(form_frame, textvariable=movement_var, 
                                     values=["Compra", "Venda", "Embarque", "Desembarque", "Trânsito", "Exposição", "Outro"],
                                     width=37, state="readonly")
        movement_combo.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(form_frame, text="Número da GTA *", font=("Arial", 10)).grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        gta_entry = tk.Entry(form_frame, width=40, font=("Arial", 10))
        gta_entry.grid(row=1, column=1, padx=10, pady=5)
        
        tk.Label(form_frame, text="Data de Emissão *", font=("Arial", 10)).grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        date_entry = tk.Entry(form_frame, width=40, font=("Arial", 10))
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        date_entry.grid(row=2, column=1, padx=10, pady=5)
        
        tk.Label(form_frame, text="Quantidade de Animais *", font=("Arial", 10)).grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        quantity_entry = tk.Entry(form_frame, width=40, font=("Arial", 10))
        quantity_entry.grid(row=3, column=1, padx=10, pady=5)
        
        tk.Label(form_frame, text="Faixa Etária", font=("Arial", 10)).grid(row=4, column=0, sticky=tk.W, padx=10, pady=5)
        age_range_var = tk.StringVar(value="0 a 6 meses")
        age_range_combo = ttk.Combobox(form_frame, textvariable=age_range_var, 
                                       values=["0 a 6 meses", "7 a 12 meses", "13 a 24 meses", "25 a 36 meses", "Acima de 36 meses"],
                                       width=37, state="readonly")
        age_range_combo.grid(row=4, column=1, padx=10, pady=5)
        
        tk.Label(form_frame, text="Origem/Destino *", font=("Arial", 10)).grid(row=5, column=0, sticky=tk.W, padx=10, pady=5)
        origin_dest_entry = tk.Entry(form_frame, width=40, font=("Arial", 10))
        origin_dest_entry.grid(row=5, column=1, padx=10, pady=5)
        
        tk.Label(form_frame, text="Observações", font=("Arial", 10)).grid(row=6, column=0, sticky=tk.W, padx=10, pady=5)
        notes_text = tk.Text(form_frame, width=40, height=3, font=("Arial", 10))
        notes_text.grid(row=6, column=1, padx=10, pady=5)
        
        def save_gta():
            if not all([gta_entry.get(), date_entry.get(), quantity_entry.get(), origin_dest_entry.get()]):
                messagebox.showwarning("Aviso", "Preencha todos os campos obrigatórios!")
                return
            try:
                from src.services.gta_service import register_gta
                quantity = int(quantity_entry.get())
                age_range = age_range_var.get() if age_range_var.get() else None
                notes = notes_text.get("1.0", tk.END).strip() if notes_text.get("1.0", tk.END).strip() else None
                register_gta(self.current_property_id, movement_var.get(), gta_entry.get(),
                           date_entry.get(), quantity, origin_dest_entry.get(), age_range, notes)
                messagebox.showinfo("Sucesso", "GTA registrada com sucesso!")
                date_entry.delete(0, tk.END)
                date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
                gta_entry.delete(0, tk.END)
                quantity_entry.delete(0, tk.END)
                age_range_var.set("0 a 6 meses")
                origin_dest_entry.delete(0, tk.END)
                notes_text.delete("1.0", tk.END)
                load_gta_list()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar:\n{str(e)}")
        
        tk.Button(form_frame, text="💾 Salvar", command=save_gta, bg="#5D4037", fg="white",
                 font=("Arial", 11), padx=20, pady=5).grid(row=7, column=0, columnspan=2, pady=10)
        
        list_frame = tk.LabelFrame(main_frame, text="Histórico de GTAs", font=("Arial", 12, "bold"))
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("Data", "Tipo", "Número GTA", "Quantidade", "Faixa Etária", "Origem/Destino")
        gta_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        for col in columns:
            gta_tree.heading(col, text=col)
            gta_tree.column(col, width=120)
        gta_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        def load_gta_list():
            gta_tree.delete(*gta_tree.get_children())
            try:
                from src.services.gta_service import get_gtas_by_property
                gtas = get_gtas_by_property(self.current_property_id)
                for gta in gtas:
                    gta_tree.insert("", tk.END, values=(
                        gta['emission_date'], gta['movement_type'], gta['gta_number'],
                        gta['quantity'], gta.get('age_range', '') or '', gta['origin_destination']
                    ))
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar GTAs:\n{str(e)}")
        
        load_gta_list()
    
    def show_other_animals_screen(self):
        """Mostra a tela de outros animais"""
        self.clear_window()
        
        header = tk.Frame(self.root, bg="#0D4F14", height=60)
        header.pack(fill=tk.X)
        tk.Label(header, text="🐾 Outros Animais", font=("Arial", 18, "bold"), 
                bg="#0D4F14", fg="white").pack(pady=15)
        
        back_frame = tk.Frame(self.root)
        back_frame.pack(fill=tk.X, padx=20, pady=10)
        tk.Button(back_frame, text="← Voltar", command=self.show_home_screen,
                 bg="#9E9E9E", fg="white", font=("Arial", 10)).pack(side=tk.LEFT)
        
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        form_frame = tk.LabelFrame(main_frame, text="Cadastrar Outros Animais", font=("Arial", 12, "bold"))
        form_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(form_frame, text="Espécie *", font=("Arial", 10)).grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        species_var = tk.StringVar(value="Ovinos")
        species_combo = ttk.Combobox(form_frame, textvariable=species_var, 
                                    values=["Ovinos", "Caprinos", "Equinos", "Muares", "Asininos", "Suínos", "Aves", "Caninos", "Felinos"],
                                    width=37, state="readonly")
        species_combo.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(form_frame, text="Sexo *", font=("Arial", 10)).grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        sex_var = tk.StringVar(value="Macho")
        sex_combo = ttk.Combobox(form_frame, textvariable=sex_var, values=["Macho", "Fêmea"], width=37, state="readonly")
        sex_combo.grid(row=1, column=1, padx=10, pady=5)
        
        tk.Label(form_frame, text="Quantidade *", font=("Arial", 10)).grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        quantity_entry = tk.Entry(form_frame, width=40, font=("Arial", 10))
        quantity_entry.grid(row=2, column=1, padx=10, pady=5)
        
        tk.Label(form_frame, text="Classificação", font=("Arial", 10)).grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        classification_var = tk.StringVar(value="")
        classification_combo = ttk.Combobox(form_frame, textvariable=classification_var, 
                                           values=["", "Reprodutor", "Matriz", "Animal de Trabalho", "Animal de Lazer", "Outro"],
                                           width=37, state="readonly")
        classification_combo.grid(row=3, column=1, padx=10, pady=5)
        
        def save_other_animal():
            if not quantity_entry.get():
                messagebox.showwarning("Aviso", "Informe a quantidade!")
                return
            try:
                from src.services.other_animals_service import create_other_animal_group
                quantity = int(quantity_entry.get())
                classification = classification_var.get().strip() if classification_var.get() else None
                create_other_animal_group(self.current_property_id, species_var.get(), 
                                         sex_var.get(), quantity, classification)
                messagebox.showinfo("Sucesso", "Animais cadastrados com sucesso!")
                quantity_entry.delete(0, tk.END)
                classification_var.set("")
                load_other_animals_list()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar:\n{str(e)}")
        
        tk.Button(form_frame, text="💾 Salvar", command=save_other_animal, bg="#795548", fg="white",
                 font=("Arial", 11), padx=20, pady=5).grid(row=4, column=0, columnspan=2, pady=10)
        
        # Lista de outros animais
        list_frame = tk.LabelFrame(main_frame, text="Outros Animais Cadastrados", font=("Arial", 12, "bold"))
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("Espécie", "Sexo", "Quantidade", "Classificação")
        other_animals_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        for col in columns:
            other_animals_tree.heading(col, text=col)
            other_animals_tree.column(col, width=150)
        other_animals_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar_tree = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=other_animals_tree.yview)
        scrollbar_tree.pack(side=tk.RIGHT, fill=tk.Y)
        other_animals_tree.configure(yscrollcommand=scrollbar_tree.set)
        
        def load_other_animals_list():
            other_animals_tree.delete(*other_animals_tree.get_children())
            try:
                from src.services.other_animals_service import get_other_animals_by_property
                animals = get_other_animals_by_property(self.current_property_id)
                for animal in animals:
                    other_animals_tree.insert("", tk.END, values=(
                        animal['species'], animal['sex'], animal['quantity'],
                        animal.get('classification', '') or ''
                    ))
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar animais:\n{str(e)}")
        
        load_other_animals_list()
    
    def show_reports_screen(self):
        """Mostra a tela de relatórios"""
        self.clear_window()
        
        header = tk.Frame(self.root, bg="#0D4F14", height=60)
        header.pack(fill=tk.X)
        tk.Label(header, text="📊 Relatórios", font=("Arial", 18, "bold"), 
                bg="#0D4F14", fg="white").pack(pady=15)
        
        back_frame = tk.Frame(self.root)
        back_frame.pack(fill=tk.X, padx=20, pady=10)
        tk.Button(back_frame, text="← Voltar", command=self.show_home_screen,
                 bg="#9E9E9E", fg="white", font=("Arial", 10)).pack(side=tk.LEFT)
        
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Seção de resumo - dados principais
        summary_frame = tk.LabelFrame(main_frame, text="Resumo Geral", font=("Arial", 12, "bold"))
        summary_frame.pack(fill=tk.X, pady=(0, 20))
        
        summary_inner = tk.Frame(summary_frame)
        summary_inner.pack(fill=tk.X, padx=10, pady=10)
        
        # Labels de resumo que serão atualizados
        self.summary_labels = {}
        
        # Paleta harmoniosa de verdes e marrons
        summary_items = [
            ("🐄 Total de Animais", "total_animals", "#66BB6A"),  # Verde claro
            ("⭐ Total de Nascimentos", "total_births", "#81C784"),  # Verde médio
            ("💀 Total de Mortes", "total_deaths", "#8D6E63"),  # Marrom claro
            ("🛒 Total de Vendas", "total_sales", "#A5D6A7"),  # Verde muito claro
            ("🛍️ Total de Compras", "total_purchases", "#0D4F14"),  # Verde padrão
            ("💉 Procedimentos Sanitários", "total_health", "#388E3C"),  # Verde escuro
            ("🐾 Outros Animais", "total_other_animals", "#795548"),  # Marrom padrão
        ]
        
        for i, (label_text, key, color) in enumerate(summary_items):
            row = i // 3
            col = i % 3
            
            card = tk.Frame(summary_inner, bg=color, relief=tk.RAISED, bd=2)
            card.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
            
            tk.Label(card, text=label_text, font=("Arial", 9), bg=color, fg="white").pack(pady=(5, 0))
            value_label = tk.Label(card, text="Carregando...", font=("Arial", 14, "bold"), 
                                  bg=color, fg="white")
            value_label.pack(pady=(0, 5))
            self.summary_labels[key] = value_label
        
        summary_inner.grid_columnconfigure(0, weight=1)
        summary_inner.grid_columnconfigure(1, weight=1)
        summary_inner.grid_columnconfigure(2, weight=1)
        
        # Botão do relatório anual
        report_button_frame = tk.Frame(main_frame)
        report_button_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Button(report_button_frame, text="📋 Relatório Anual", command=self.show_annual_report,
                 bg="#388E3C", fg="white", font=("Arial", 14, "bold"), width=30, height=2,
                 cursor="hand2").pack(pady=10)
        
        # Área de exibição do relatório
        report_text_frame = tk.Frame(main_frame)
        report_text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.report_text = tk.Text(report_text_frame, font=("Courier", 10), wrap=tk.WORD, height=20)
        self.report_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar_report = tk.Scrollbar(report_text_frame, orient=tk.VERTICAL, command=self.report_text.yview)
        scrollbar_report.pack(side=tk.RIGHT, fill=tk.Y)
        self.report_text.configure(yscrollcommand=scrollbar_report.set)
        
        # Carregar dados de resumo de forma assíncrona
        self.load_summary_data()
    
    def load_summary_data(self):
        """Carrega dados de resumo para a tela de relatórios - otimizado com consultas diretas"""
        def load_data():
            try:
                from src.services.database import get_connection
                from psycopg2.extras import RealDictCursor
                
                conn = get_connection()
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                summary = {}
                
                # Total de animais - consulta direta otimizada
                cursor.execute("SELECT COALESCE(SUM(quantity), 0) as total FROM animals WHERE property_id = %s", 
                             (self.current_property_id,))
                result = cursor.fetchone()
                summary['total_animals'] = result['total'] if result else 0
                
                # Total de nascimentos - consulta direta otimizada
                cursor.execute("SELECT COALESCE(SUM(quantity), 0) as total FROM births WHERE property_id = %s", 
                             (self.current_property_id,))
                result = cursor.fetchone()
                summary['total_births'] = result['total'] if result else 0
                
                # Total de mortes - consulta direta otimizada
                cursor.execute("SELECT COALESCE(SUM(quantity), 0) as total FROM deaths WHERE property_id = %s", 
                             (self.current_property_id,))
                result = cursor.fetchone()
                summary['total_deaths'] = result['total'] if result else 0
                
                # Total de vendas - consulta direta otimizada
                cursor.execute("SELECT COALESCE(SUM(quantity), 0) as total FROM sales WHERE property_id = %s", 
                             (self.current_property_id,))
                result = cursor.fetchone()
                summary['total_sales'] = result['total'] if result else 0
                
                # Total de compras - consulta direta otimizada
                cursor.execute("SELECT COALESCE(SUM(quantity), 0) as total FROM purchases WHERE property_id = %s", 
                             (self.current_property_id,))
                result = cursor.fetchone()
                summary['total_purchases'] = result['total'] if result else 0
                
                # Total de procedimentos sanitários - consulta direta otimizada
                cursor.execute("SELECT COUNT(*) as total FROM health_procedures WHERE property_id = %s", 
                             (self.current_property_id,))
                result = cursor.fetchone()
                summary['total_health'] = result['total'] if result else 0
                
                # Total de outros animais - consulta direta otimizada
                cursor.execute("SELECT COALESCE(SUM(quantity), 0) as total FROM other_animals WHERE property_id = %s", 
                             (self.current_property_id,))
                result = cursor.fetchone()
                summary['total_other_animals'] = result['total'] if result else 0
                
                cursor.close()
                conn.close()
                
                return summary
            except Exception as e:
                return None, str(e)
        
        def update_labels(result):
            if result is None:
                return
            if isinstance(result, tuple) and len(result) == 2:
                error = result[1]
                messagebox.showerror("Erro", f"Erro ao carregar dados de resumo:\n{error}")
                return
            
            if 'total_animals' in self.summary_labels:
                self.summary_labels['total_animals'].config(text=f"{result.get('total_animals', 0)}")
            if 'total_births' in self.summary_labels:
                self.summary_labels['total_births'].config(text=f"{result.get('total_births', 0)}")
            if 'total_deaths' in self.summary_labels:
                self.summary_labels['total_deaths'].config(text=f"{result.get('total_deaths', 0)}")
            if 'total_sales' in self.summary_labels:
                self.summary_labels['total_sales'].config(text=f"{result.get('total_sales', 0)}")
            if 'total_purchases' in self.summary_labels:
                self.summary_labels['total_purchases'].config(text=f"{result.get('total_purchases', 0)}")
            if 'total_health' in self.summary_labels:
                self.summary_labels['total_health'].config(text=f"{result.get('total_health', 0)}")
            if 'total_other_animals' in self.summary_labels:
                self.summary_labels['total_other_animals'].config(text=f"{result.get('total_other_animals', 0)}")
        
        def load_thread():
            result = load_data()
            self.root.after(0, lambda: update_labels(result))
        
        threading.Thread(target=load_thread, daemon=True).start()
    
    def show_herd_report(self):
        """Mostra relatório de composição do rebanho"""
        try:
            from src.services.report_service import generate_herd_composition_report
            report = generate_herd_composition_report(self.current_property_id)
            self.report_text.delete("1.0", tk.END)
            self.report_text.insert("1.0", f"RELATÓRIO: {report['type']}\n")
            self.report_text.insert(tk.END, f"Total de Animais: {report['total']}\n\n")
            self.report_text.insert(tk.END, "Detalhamento:\n")
            for item in report['data']:
                self.report_text.insert(tk.END, f"- {item['purpose']} | {item['category']} | {item['sex']}: {item['quantity']}\n")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar relatório:\n{str(e)}")
    
    def show_births_report(self):
        """Mostra relatório de nascimentos"""
        try:
            from src.services.report_service import generate_births_report
            report = generate_births_report(self.current_property_id)
            self.report_text.delete("1.0", tk.END)
            self.report_text.insert("1.0", f"RELATÓRIO: {report['type']}\n")
            self.report_text.insert(tk.END, f"Total: {report['total']}\n\n")
            for item in report['data']:
                self.report_text.insert(tk.END, f"Data: {item['date']} | Sexo: {item['sex']} | Quantidade: {item['quantity']}\n")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar relatório:\n{str(e)}")
    
    def show_deaths_report(self):
        """Mostra relatório de mortes"""
        try:
            from src.services.report_service import generate_deaths_report
            report = generate_deaths_report(self.current_property_id)
            self.report_text.delete("1.0", tk.END)
            self.report_text.insert("1.0", f"RELATÓRIO: {report['type']}\n")
            self.report_text.insert(tk.END, f"Total: {report['total']}\n\n")
            for item in report['data']:
                self.report_text.insert(tk.END, f"Data: {item['date']} | {item['category']} | {item['sex']} | Quantidade: {item['quantity']} | Causa: {item.get('cause', 'N/A')}\n")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar relatório:\n{str(e)}")
    
    def show_sales_report(self):
        """Mostra relatório de vendas"""
        try:
            from src.services.report_service import generate_sales_report
            report = generate_sales_report(self.current_property_id)
            self.report_text.delete("1.0", tk.END)
            self.report_text.insert("1.0", f"RELATÓRIO: {report['type']}\n")
            self.report_text.insert(tk.END, f"Total: {report['total']}\n\n")
            for item in report['data']:
                self.report_text.insert(tk.END, f"Data: {item['date']} | {item['category']} | {item['sex']} | Quantidade: {item['quantity']} | GTA: {item['gta_number'] or 'N/A'}\n")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar relatório:\n{str(e)}")
    
    def show_purchases_report(self):
        """Mostra relatório de compras"""
        try:
            from src.services.report_service import generate_purchases_report
            report = generate_purchases_report(self.current_property_id)
            self.report_text.delete("1.0", tk.END)
            self.report_text.insert("1.0", f"RELATÓRIO: {report['type']}\n")
            self.report_text.insert(tk.END, f"Total: {report['total']}\n\n")
            for item in report['data']:
                self.report_text.insert(tk.END, f"Data: {item['date']} | Origem: {item['origin']} | {item['category']} | {item['sex']} | Quantidade: {item['quantity']}\n")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar relatório:\n{str(e)}")
    
    def show_health_report(self):
        """Mostra relatório sanitário"""
        try:
            from src.services.report_service import generate_health_report
            report = generate_health_report(self.current_property_id)
            self.report_text.delete("1.0", tk.END)
            self.report_text.insert("1.0", f"RELATÓRIO: {report['type']}\n")
            self.report_text.insert(tk.END, f"Total de Procedimentos: {report['total_procedures']}\n")
            self.report_text.insert(tk.END, f"Total de Animais Atendidos: {report['total_animals']}\n\n")
            for item in report['data']:
                self.report_text.insert(tk.END, f"Data: {item['application_date']} | {item['procedure_type']} | {item['product']} | Quantidade: {item['quantity']}\n")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar relatório:\n{str(e)}")
    
    def show_annual_report(self):
        """Mostra relatório anual consolidado - otimizado com carregamento assíncrono"""
        # Limpar área de texto e mostrar mensagem de carregamento
        self.report_text.delete("1.0", tk.END)
        self.report_text.insert("1.0", "Gerando relatório anual...\nPor favor, aguarde...")
        self.report_text.update()
        
        def load_report():
            try:
                from src.services.report_service import generate_annual_report
                year = datetime.now().year
                report = generate_annual_report(self.current_property_id, year)
                return report, year
            except Exception as e:
                return None, str(e)
        
        def update_report(result):
            if result is None:
                messagebox.showerror("Erro", "Erro ao gerar relatório anual.")
                return
            
            if isinstance(result, tuple) and len(result) == 2:
                report, year = result
                if isinstance(year, str) and ("Erro" in year or "erro" in year.lower()):
                    messagebox.showerror("Erro", f"Erro ao gerar relatório:\n{year}")
                    self.report_text.delete("1.0", tk.END)
                    return
                
                self.report_text.delete("1.0", tk.END)
                self.report_text.insert("1.0", f"RELATÓRIO ANUAL CONSOLIDADO - {year}\n")
                self.report_text.insert(tk.END, "=" * 70 + "\n\n")
                
                # Composição do Rebanho
                self.report_text.insert(tk.END, f"1. COMPOSIÇÃO DO REBANHO\n")
                self.report_text.insert(tk.END, f"   Total de Animais: {report['herd_composition']['total']}\n")
                if report['herd_composition']['data']:
                    self.report_text.insert(tk.END, "   Detalhamento:\n")
                    for item in report['herd_composition']['data']:
                        purpose = item.get('purpose', '') or ''
                        age_range = f" | {item.get('age_range', '')}" if item.get('age_range') else ""
                        self.report_text.insert(tk.END, f"     • {purpose} | {item['category']} | {item['sex']}{age_range}: {item['quantity']}\n")
                else:
                    self.report_text.insert(tk.END, "   Nenhum animal cadastrado\n")
                self.report_text.insert(tk.END, "\n")
                
                # Nascimentos
                self.report_text.insert(tk.END, f"2. NASCIMENTOS\n")
                self.report_text.insert(tk.END, f"   Total: {report['births']['total']}\n")
                if report['births']['data']:
                    self.report_text.insert(tk.END, "   Detalhamento:\n")
                    for item in report['births']['data']:
                        age_range = f" | Faixa Etária: {item.get('age_range', '')}" if item.get('age_range') else ""
                        self.report_text.insert(tk.END, f"     • Data: {item['date']} | Sexo: {item['sex']}{age_range} | Quantidade: {item['quantity']}\n")
                else:
                    self.report_text.insert(tk.END, "   Nenhum nascimento registrado\n")
                self.report_text.insert(tk.END, "\n")
                
                # Mortes
                self.report_text.insert(tk.END, f"3. MORTES\n")
                self.report_text.insert(tk.END, f"   Total: {report['deaths']['total']}\n")
                if report['deaths']['data']:
                    self.report_text.insert(tk.END, "   Detalhamento:\n")
                    for item in report['deaths']['data']:
                        age_range = f" | Faixa Etária: {item.get('age_range', '')}" if item.get('age_range') else ""
                        cause = f" | Causa: {item.get('cause', '')}" if item.get('cause') else ""
                        self.report_text.insert(tk.END, f"     • Data: {item['date']} | {item['category']} | {item['sex']}{age_range} | Quantidade: {item['quantity']}{cause}\n")
                else:
                    self.report_text.insert(tk.END, "   Nenhuma morte registrada\n")
                self.report_text.insert(tk.END, "\n")
                
                # Vendas
                self.report_text.insert(tk.END, f"4. VENDAS\n")
                self.report_text.insert(tk.END, f"   Total: {report['sales']['total']}\n")
                if report['sales']['data']:
                    self.report_text.insert(tk.END, "   Detalhamento:\n")
                    for item in report['sales']['data']:
                        age_range = f" | Faixa Etária: {item.get('age_range', '')}" if item.get('age_range') else ""
                        gta = f" | GTA: {item.get('gta_number', 'N/A')}" if item.get('has_gta') else " | GTA: Não"
                        destination = f" | Destino: {item.get('destination', '')}" if item.get('destination') else ""
                        self.report_text.insert(tk.END, f"     • Data: {item['date']} | {item['category']} | {item['sex']}{age_range} | Quantidade: {item['quantity']}{gta}{destination}\n")
                else:
                    self.report_text.insert(tk.END, "   Nenhuma venda registrada\n")
                self.report_text.insert(tk.END, "\n")
                
                # Compras
                self.report_text.insert(tk.END, f"5. COMPRAS\n")
                self.report_text.insert(tk.END, f"   Total: {report['purchases']['total']}\n")
                if report['purchases']['data']:
                    self.report_text.insert(tk.END, "   Detalhamento:\n")
                    for item in report['purchases']['data']:
                        age_range = f" | Faixa Etária: {item.get('age_range', '')}" if item.get('age_range') else ""
                        gta = f" | GTA: {item.get('gta_number', 'N/A')}" if item.get('has_gta') else " | GTA: Não"
                        self.report_text.insert(tk.END, f"     • Data: {item['date']} | Origem: {item['origin']} | {item['category']} | {item['sex']}{age_range} | Quantidade: {item['quantity']}{gta}\n")
                else:
                    self.report_text.insert(tk.END, "   Nenhuma compra registrada\n")
                self.report_text.insert(tk.END, "\n")
                
                # Procedimentos Sanitários
                self.report_text.insert(tk.END, f"6. PROCEDIMENTOS SANITÁRIOS\n")
                self.report_text.insert(tk.END, f"   Total de Procedimentos: {report['health']['total_procedures']}\n")
                self.report_text.insert(tk.END, f"   Total de Animais Atendidos: {report['health']['total_animals']}\n")
                if report['health']['data']:
                    self.report_text.insert(tk.END, "   Detalhamento:\n")
                    for item in report['health']['data']:
                        vaccination_type = f" | Tipo Vacinação: {item.get('vaccination_type', '')}" if item.get('vaccination_type') else ""
                        age_range = f" | Faixa Etária: {item.get('age_range', '')}" if item.get('age_range') else ""
                        next_date = f" | Próxima Aplicação: {item.get('next_application_date', '')}" if item.get('next_application_date') else ""
                        self.report_text.insert(tk.END, f"     • Data: {item['application_date']} | {item['procedure_type']}{vaccination_type} | {item['product']} | {item['category']} | {item['sex']}{age_range} | Quantidade: {item['quantity']}{next_date}\n")
                else:
                    self.report_text.insert(tk.END, "   Nenhum procedimento registrado\n")
                self.report_text.insert(tk.END, "\n")
                
                # Outros Animais
                self.report_text.insert(tk.END, f"7. OUTROS ANIMAIS\n")
                self.report_text.insert(tk.END, f"   Total: {report['other_animals']['total']} animais\n")
                if report['other_animals']['data']:
                    self.report_text.insert(tk.END, "   Detalhamento:\n")
                    for animal in report['other_animals']['data']:
                        classification = f" | Classificação: {animal.get('classification', '')}" if animal.get('classification') else ""
                        self.report_text.insert(tk.END, f"     • {animal['species']} | {animal['sex']} | Quantidade: {animal['quantity']}{classification}\n")
                else:
                    self.report_text.insert(tk.END, "   Nenhum outro animal cadastrado\n")
        
        def load_thread():
            result = load_report()
            self.root.after(0, lambda: update_report(result))
        
        threading.Thread(target=load_thread, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = SISBOVApp(root)
    root.mainloop()

