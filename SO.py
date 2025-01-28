import threading
from collections import deque
import tkinter as tk
from tkinter import ttk
import random

# Clase Proceso
class Proceso:
    def __init__(self, id_proceso, prioridad, tiempo_ejecucion, bloqueado=False):
        self.id = id_proceso
        self.prioridad = prioridad
        self.tiempo_ejecucion = tiempo_ejecucion
        self.estado = "Bloqueado" if bloqueado else "Nuevo"  # Estados: Nuevo, Listo, Ejecutando, Bloqueado, Terminado

    def __repr__(self):
        return f"Proceso(ID={self.id}, Prioridad={self.prioridad}, Tiempo={self.tiempo_ejecucion}, Estado={self.estado})"

# Clase Planificador
class Planificador:
    def __init__(self, algoritmo="FCFS", quantum=2):
        self.cola_listos = deque()
        self.cola_bloqueados = deque()
        self.cola_terminados = []
        self.algoritmo = algoritmo
        self.quantum = quantum
        self.lock = threading.Lock()

    def agregar_proceso(self, proceso):
        if proceso.estado == "Bloqueado":
            self.cola_bloqueados.append(proceso)
        else:
            proceso.estado = "Listo"
            self.cola_listos.append(proceso)

    def ejecutar_procesos(self, callback):
        if self.algoritmo == "FCFS":
            self.fcfs(callback)
        elif self.algoritmo == "Round Robin":
            self.round_robin(callback)

    def fcfs(self, callback):
        while self.cola_listos:
            proceso = self.cola_listos.popleft()
            proceso.estado = "Ejecutando"
            callback(f"Ejecutando {proceso}")
            with self.lock:
                proceso.tiempo_ejecucion -= 1
            if proceso.tiempo_ejecucion <= 0:
                proceso.estado = "Terminado"
                self.cola_terminados.append(proceso)
                callback(f"{proceso} ha terminado.")
            else:
                self.cola_listos.append(proceso)

    def round_robin(self, callback):
        while self.cola_listos:
            proceso = self.cola_listos.popleft()
            proceso.estado = "Ejecutando"
            callback(f"Ejecutando {proceso}")
            tiempo_ejecutado = min(self.quantum, proceso.tiempo_ejecucion)
            with self.lock:
                proceso.tiempo_ejecucion -= tiempo_ejecutado
            if proceso.tiempo_ejecucion > 0:
                proceso.estado = "Listo"
                self.cola_listos.append(proceso)
            else:
                proceso.estado = "Terminado"
                self.cola_terminados.append(proceso)
                callback(f"{proceso} ha terminado.")

    def desbloquear_proceso(self, proceso_id, callback):
        for proceso in list(self.cola_bloqueados):
            if proceso.id == proceso_id:
                self.cola_bloqueados.remove(proceso)
                proceso.estado = "Listo"
                self.cola_listos.append(proceso)
                callback(f"{proceso} ha sido desbloqueado.")
                return
        callback("Proceso no encontrado en la cola de bloqueados.")

    def limpiar_procesos(self):
        self.cola_listos.clear()
        self.cola_bloqueados.clear()
        self.cola_terminados.clear()

# Clase Memoria
class Memoria:
    def __init__(self, tamanio):
        self.tamanio = tamanio
        self.marcos = [None] * tamanio
        self.fallas = 0

    def asignar_pagina(self, proceso_id):
        if None in self.marcos:
            indice = self.marcos.index(None)
            self.marcos[indice] = proceso_id
        else:
            self.marcos.pop(0)  # Algoritmo FIFO
            self.marcos.append(proceso_id)
            self.fallas += 1

    def __repr__(self):
        return f"Memoria: {self.marcos} | Fallas: {self.fallas}"

# Interfaz de usuario
def interfaz_usuario():
    def agregar_proceso():
        try:
            id_proceso = int(entry_id.get())
            prioridad = int(entry_prioridad.get())
            tiempo_ejecucion = int(entry_tiempo.get())
            bloqueado = bloqueado_var.get() == 1
            proceso = Proceso(id_proceso, prioridad, tiempo_ejecucion, bloqueado)
            planificador.agregar_proceso(proceso)
            limpiar_output()
            mostrar_estado()
        except ValueError:
            output_text.insert(tk.END, "Error: Verifica los datos ingresados.\n")

    def desbloquear():
        if not planificador.cola_bloqueados:
            output_text.insert(tk.END, "No hay procesos bloqueados.\n")
            return

        def seleccionar_desbloqueo():
            proceso_id = int(entry_desbloquear.get())
            planificador.desbloquear_proceso(proceso_id, lambda mensaje: output_text.insert(tk.END, mensaje + "\n"))
            desbloquear_window.destroy()
            mostrar_estado()

        desbloquear_window = tk.Toplevel(root)
        desbloquear_window.title("Seleccionar Proceso para Desbloquear")
        tk.Label(desbloquear_window, text="Procesos Bloqueados:").pack()
        for proceso in planificador.cola_bloqueados:
            tk.Label(desbloquear_window, text=f"{proceso}").pack()
        tk.Label(desbloquear_window, text="ID del Proceso:").pack()
        entry_desbloquear = tk.Entry(desbloquear_window)
        entry_desbloquear.pack()
        tk.Button(desbloquear_window, text="Desbloquear", command=seleccionar_desbloqueo).pack()

    def limpiar_output():
        output_text.delete(1.0, tk.END)

    def mostrar_estado():
        output_text.insert(tk.END, "Cola de procesos listos:\n")
        for proceso in list(planificador.cola_listos):
            output_text.insert(tk.END, f"{proceso}\n")
        output_text.insert(tk.END, "\nProcesos bloqueados:\n")
        for proceso in list(planificador.cola_bloqueados):
            output_text.insert(tk.END, f"{proceso}\n")
        output_text.insert(tk.END, "\nProcesos terminados:\n")
        for proceso in planificador.cola_terminados:
            output_text.insert(tk.END, f"{proceso}\n")

    def ejecutar_procesos():
        planificador.ejecutar_procesos(lambda mensaje: output_text.insert(tk.END, mensaje + "\n"))
        limpiar_output()
        mostrar_estado()

    def cambiar_algoritmo(*args):
        planificador.algoritmo = combo_algoritmo.get()

    def borrar_procesos():
        planificador.limpiar_procesos()
        limpiar_output()
        output_text.insert(tk.END, "Todos los procesos han sido eliminados.\n")

    root = tk.Tk()
    root.title("Simulador de Planificación de Procesos")

    # Entradas
    frame_inputs = tk.Frame(root)
    frame_inputs.pack(pady=10)

    tk.Label(frame_inputs, text="ID Proceso").grid(row=0, column=0)
    entry_id = tk.Entry(frame_inputs)
    entry_id.grid(row=0, column=1)

    tk.Label(frame_inputs, text="Prioridad").grid(row=1, column=0)
    entry_prioridad = tk.Entry(frame_inputs)
    entry_prioridad.grid(row=1, column=1)

    tk.Label(frame_inputs, text="Tiempo de Ejecución").grid(row=2, column=0)
    entry_tiempo = tk.Entry(frame_inputs)
    entry_tiempo.grid(row=2, column=1)

    bloqueado_var = tk.IntVar()
    tk.Checkbutton(frame_inputs, text="Bloqueado", variable=bloqueado_var).grid(row=3, columnspan=2)

    tk.Button(frame_inputs, text="Agregar Proceso", command=agregar_proceso).grid(row=4, columnspan=2, pady=5)

    # Algoritmo de planificación
    tk.Label(root, text="Algoritmo de Planificación:").pack()
    combo_algoritmo = ttk.Combobox(root, values=["FCFS", "Round Robin"])
    combo_algoritmo.current(0)
    combo_algoritmo.pack()
    combo_algoritmo.bind("<<ComboboxSelected>>", cambiar_algoritmo)

    # Salida
    output_text = tk.Text(root, height=20, width=60)
    output_text.pack(pady=10)

    # Botones de control
    tk.Button(root, text="Ejecutar Procesos", command=ejecutar_procesos).pack(pady=5)
    tk.Button(root, text="Desbloquear Procesos", command=desbloquear).pack(pady=5)
    tk.Button(root, text="Borrar Procesos", command=borrar_procesos).pack(pady=5)

    root.mainloop()

# Prueba inicial
def main():
    global planificador
    planificador = Planificador()
    interfaz_usuario()

if __name__ == "__main__":
    main()
