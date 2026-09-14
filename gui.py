#!/usr/bin/env python3
from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from savevideo import download_video, inspect_video


class SaveVideoGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("SaveVideo")
        self.geometry("760x620")
        self.minsize(660, 520)
        self.configure(bg="#071422")

        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure("Card.TFrame", background="#0f1b2d")
        self.style.configure("Header.TFrame", background="#132842")
        self.style.configure("TLabel", background="#0f1b2d", foreground="#e5eefb")
        self.style.configure("Muted.TLabel", background="#0f1b2d", foreground="#8ea7c7")
        self.style.configure("TCheckbutton", background="#0f1b2d", foreground="#e5eefb")

        self.main = tk.Frame(self, bg="#071422", padx=26, pady=24)
        self.main.pack(fill="both", expand=True)

        header = tk.Frame(self.main, bg="#132842", bd=0, highlightthickness=0, padx=18, pady=18)
        header.pack(fill="x", pady=(0, 20))

        icon = tk.Label(header, text="▶", bg="#132842", fg="#7dd3fc", font=("Segoe UI", 18, "bold"))
        icon.pack(side="left")

        title = tk.Label(header, text="SaveVideo", bg="#132842", fg="#f8fbff", font=("Segoe UI", 24, "bold"))
        title.pack(side="left", padx=(12, 0))

        subtitle = tk.Label(header, text="Baixe vídeos e áudios em poucos cliques", bg="#132842", fg="#9cc4f5", font=("Segoe UI", 9, "normal"))
        subtitle.pack(side="right")

        card = tk.Frame(self.main, bg="#0f1b2d", bd=0, highlightbackground="#1d3557", highlightthickness=1)
        card.pack(fill="both", expand=True)

        content = tk.Frame(card, bg="#0f1b2d", padx=18, pady=18)
        content.pack(fill="both", expand=True)

        tk.Label(content, text="URL do vídeo", bg="#0f1b2d", fg="#dfeafc", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.url_var = tk.StringVar()
        url_row = tk.Frame(content, bg="#0f1b2d")
        url_row.pack(fill="x", pady=(6, 14))
        self.url_entry = tk.Entry(
            url_row,
            textvariable=self.url_var,
            width=80,
            bg="#0b1423",
            fg="#f8fbff",
            insertbackground="#7dd3fc",
            relief="flat",
            highlightthickness=1,
            highlightbackground="#264a73",
            highlightcolor="#60a5fa",
            font=("Segoe UI", 11),
            bd=0,
        )
        self.url_entry.pack(side="left", fill="x", expand=True)

        self.inspect_button = tk.Button(
            url_row,
            text="Pesquisar",
            command=self.analyze_url,
            bg="#1d4ed8",
            fg="#eff6ff",
            activebackground="#2563eb",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            font=("Segoe UI", 10, "bold"),
            padx=18,
            pady=10,
            cursor="hand2",
        )
        self.inspect_button.pack(side="right", padx=(10, 0))

        self.video_info_var = tk.StringVar(value="Cole o link e clique em Pesquisar para consultar o vídeo.")
        self.video_info_label = tk.Label(
            content,
            textvariable=self.video_info_var,
            bg="#112233",
            fg="#9cc4f5",
            font=("Segoe UI", 9),
            padx=12,
            pady=9,
            anchor="w",
            justify="left",
        )
        self.video_info_label.pack(fill="x", pady=(0, 14))

        folder_row = tk.Frame(content, bg="#0f1b2d")
        folder_row.pack(fill="x", pady=(0, 12))

        tk.Label(folder_row, text="Pasta de destino", bg="#0f1b2d", fg="#dfeafc", font=("Segoe UI", 10, "bold")).pack(anchor="w")

        out_frame = tk.Frame(folder_row, bg="#0f1b2d")
        out_frame.pack(fill="x", pady=(6, 0))

        self.output_var = tk.StringVar(value="downloads")
        self.output_entry = tk.Entry(
            out_frame,
            textvariable=self.output_var,
            bg="#0b1423",
            fg="#f8fbff",
            insertbackground="#7dd3fc",
            relief="flat",
            highlightthickness=1,
            highlightbackground="#264a73",
            highlightcolor="#60a5fa",
            font=("Segoe UI", 10),
            bd=0,
        )
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.browse_button = tk.Button(
            out_frame,
            text="Procurar",
            command=self.choose_folder,
            bg="#1d4ed8",
            fg="#eff6ff",
            activebackground="#2563eb",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            font=("Segoe UI", 10, "bold"),
            padx=18,
            pady=10,
            cursor="hand2",
        )
        self.browse_button.pack(side="right")

        options = tk.Frame(content, bg="#0f1b2d")
        options.pack(fill="x", pady=(8, 14))

        self.audio_only = tk.BooleanVar(value=False)
        self.no_playlist = tk.BooleanVar(value=False)
        self.no_watermark = tk.BooleanVar(value=False)

        self.make_checkbox(options, "Áudio só (MP3)", self.audio_only)
        self.make_checkbox(options, "Baixar só o primeiro item da playlist", self.no_playlist)
        self.make_checkbox(options, "Tentar sem marca d'água", self.no_watermark)

        quality_row = tk.Frame(content, bg="#0f1b2d")
        quality_row.pack(fill="x", pady=(2, 8))
        tk.Label(quality_row, text="Qualidade", bg="#0f1b2d", fg="#dfeafc", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.quality_var = tk.StringVar(value="Pesquise um vídeo primeiro")
        self.quality_formats = {"Pesquise um vídeo primeiro": "bestvideo+bestaudio/best"}
        self.quality_menu = ttk.Combobox(
            quality_row,
            textvariable=self.quality_var,
            values=["Pesquise um vídeo primeiro"],
            state="readonly",
            width=28,
            font=("Segoe UI", 10),
        )
        self.quality_menu.pack(side="right")

        status_frame = tk.Frame(content, bg="#0f1b2d")
        status_frame.pack(fill="x", pady=(8, 0))
        self.status_var = tk.StringVar(value="Pronto para baixar.")
        self.status_label = tk.Label(
            status_frame,
            textvariable=self.status_var,
            bg="#112233",
            fg="#dbeafe",
            font=("Segoe UI", 10),
            padx=12,
            pady=8,
            relief="flat",
            anchor="w",
        )
        self.status_label.pack(fill="x")

        button_row = tk.Frame(content, bg="#0f1b2d")
        button_row.pack(fill="x", pady=(18, 0))

        self.download_button = tk.Button(
            button_row,
            text="Baixar agora",
            command=self.start_download,
            bg="#38bdf8",
            fg="#082f49",
            activebackground="#7dd3fc",
            activeforeground="#082f49",
            relief="flat",
            bd=0,
            font=("Segoe UI", 10, "bold"),
            padx=22,
            pady=11,
            cursor="hand2",
        )
        self.download_button.pack(side="left")

        self.clear_button = tk.Button(
            button_row,
            text="Limpar",
            command=self.clear_fields,
            bg="#1e293b",
            fg="#e2e8f0",
            activebackground="#334155",
            activeforeground="#f8fafc",
            relief="flat",
            bd=0,
            font=("Segoe UI", 10, "bold"),
            padx=18,
            pady=11,
            cursor="hand2",
        )
        self.clear_button.pack(side="left", padx=(12, 0))

        self.url_entry.focus_set()

    def make_checkbox(self, parent, text, variable):
        frame = tk.Frame(parent, bg="#0f1b2d", pady=4)
        frame.pack(anchor="w", fill="x")

        checkbox = tk.Checkbutton(
            frame,
            text=text,
            variable=variable,
            onvalue=True,
            offvalue=False,
            bg="#0f1b2d",
            fg="#dfeafc",
            activebackground="#0f1b2d",
            activeforeground="#f8fbff",
            selectcolor="#112233",
            highlightthickness=0,
            bd=0,
            font=("Segoe UI", 10),
        )
        checkbox.pack(anchor="w")
        return checkbox

    def analyze_url(self) -> None:
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("URL vazia", "Cole uma URL antes de pesquisar.")
            return

        self.inspect_button.config(state="disabled")
        self.video_info_var.set("Pesquisando informações do vídeo...")
        self.status_var.set("Consultando título e qualidades disponíveis...")
        threading.Thread(target=self.run_analysis, args=(url, self.no_watermark.get()), daemon=True).start()

    def run_analysis(self, url: str, no_watermark: bool) -> None:
        try:
            info = inspect_video(url, no_watermark=no_watermark)
            heights = info["heights"]
            quality_formats = {"Melhor qualidade": "bestvideo+bestaudio/best"}
            quality_values = ["Melhor qualidade"]
            for height in heights:
                label = f"{height}p"
                quality_values.append(label)
                quality_formats[label] = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"

            duration = info.get("duration")
            if duration:
                minutes, seconds = divmod(int(duration), 60)
                duration_text = f"{minutes}:{seconds:02d}"
            else:
                duration_text = "não informado"

            uploader = f" | Canal: {info['uploader']}" if info["uploader"] else ""
            details = f"Título: {info['title']}{uploader}\nDuração: {duration_text} | Qualidades: {', '.join(quality_values)}"

            def update_interface() -> None:
                self.quality_formats = quality_formats
                self.quality_menu["values"] = quality_values
                self.quality_var.set("Melhor qualidade")
                self.video_info_var.set(details)
                self.status_var.set("Vídeo encontrado. Escolha a qualidade e clique em Baixar agora.")
                self.inspect_button.config(state="normal")

            self.after(0, update_interface)
        except Exception as exc:  # pragma: no cover - interface feedback
            error_message = str(exc)

            def show_error() -> None:
                self.video_info_var.set("Não foi possível consultar este link.")
                self.status_var.set("Verifique a URL e tente pesquisar novamente.")
                self.inspect_button.config(state="normal")
                messagebox.showerror("Erro ao pesquisar", error_message)

            self.after(0, show_error)

    def choose_folder(self) -> None:
        directory = filedialog.askdirectory(title="Escolha a pasta de destino")
        if directory:
            self.output_var.set(directory)

    def clear_fields(self) -> None:
        self.url_var.set("")
        self.output_var.set("downloads")
        self.audio_only.set(False)
        self.no_playlist.set(False)
        self.no_watermark.set(False)
        self.quality_formats = {"Pesquise um vídeo primeiro": "bestvideo+bestaudio/best"}
        self.quality_menu["values"] = ["Pesquise um vídeo primeiro"]
        self.quality_var.set("Pesquise um vídeo primeiro")
        self.video_info_var.set("Cole o link e clique em Pesquisar para consultar o vídeo.")
        self.status_var.set("Campos limpos.")
        self.url_entry.focus_set()

    def start_download(self) -> None:
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("URL vazia", "Informe uma URL válida antes de baixar.")
            return

        folder = self.output_var.get().strip() or "downloads"
        output_path = Path(folder)
        output_path.mkdir(parents=True, exist_ok=True)

        self.download_button.config(state="disabled")
        self.status_var.set("Baixando... aguarde.")
        format_string = self.quality_formats.get(self.quality_var.get(), "bestvideo+bestaudio/best")

        threading.Thread(
            target=self.run_download,
            args=(url, str(output_path), format_string, self.audio_only.get(), self.no_playlist.get(), self.no_watermark.get()),
            daemon=True,
        ).start()

    def run_download(self, url: str, output_dir: str, format_string: str, audio_only: bool, no_playlist: bool, no_watermark: bool) -> None:
        try:
            download_video(
                url=url,
                output_dir=output_dir,
                format_string=format_string,
                audio_only=audio_only,
                no_playlist=no_playlist,
                no_watermark=no_watermark,
                cookie_file=None,
            )
            self.after(0, lambda: self.status_var.set("Download concluído!"))
            self.after(0, lambda: self.download_button.config(state="normal"))
        except SystemExit:
            self.after(0, lambda: self.status_var.set("Download cancelado ou falhou."))
            self.after(0, lambda: self.download_button.config(state="normal"))
        except Exception as exc:  # pragma: no cover - interface feedback
            self.after(0, lambda: messagebox.showerror("Erro no download", str(exc)))
            self.after(0, lambda: self.status_var.set("Ocorreu um erro ao baixar."))
            self.after(0, lambda: self.download_button.config(state="normal"))


def main() -> None:
    app = SaveVideoGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
