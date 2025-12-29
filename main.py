import sys
import os
import json
import shutil
import subprocess
import time
from pathlib import Path
from datetime import timedelta

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QRadioButton, QFileDialog, QMessageBox,
    QProgressBar, QAbstractItemView, QGroupBox, QComboBox
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QDesktopServices, QIcon

# === Скрыть консольное окно на Windows ===
if sys.platform == "win32":
    STARTUPINFO = subprocess.STARTUPINFO()
    STARTUPINFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    STARTUPINFO.wShowWindow = subprocess.SW_HIDE
else:
    STARTUPINFO = None

# === Вспомогательная функция для PyInstaller ===
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = Path(__file__).parent
    return Path(base_path) / relative_path

# === Пути проекта ===
PROJECT_DIR = Path(resource_path("."))
TOOLS_DIR = PROJECT_DIR / "tools"
YT_DLP = TOOLS_DIR / "yt-dlp.exe"

if not YT_DLP.exists():
    print("❌ ОШИБКА: Файл 'yt-dlp.exe' не найден в папке 'tools/'.")
    input("\nНажмите Enter для выхода...")
    sys.exit(1)

FFMPEG_CANDIDATES = [
    TOOLS_DIR / "ffmpeg.exe",
    TOOLS_DIR / "bin" / "ffmpeg.exe",
    TOOLS_DIR / "ffmpeg" / "ffmpeg.exe",
    TOOLS_DIR / "ffmpeg" / "bin" / "ffmpeg.exe",
]

FFMPEG_BIN = None
FFMPEG_DIR = None
for path in FFMPEG_CANDIDATES:
    if path.exists():
        FFMPEG_BIN = path
        FFMPEG_DIR = path.parent
        break

if FFMPEG_BIN is None:
    print("❌ ОШИБКА: Файл 'ffmpeg.exe' не найден.")
    input("\nНажмите Enter для выхода...")
    sys.exit(1)

env = os.environ.copy()
env["PATH"] = str(FFMPEG_DIR) + os.pathsep + env["PATH"]


class VideoInfo:
    def __init__(self, url, title="", duration=0, video_id=""):
        self.url = url
        self.title = title
        self.duration = duration
        self.video_id = video_id
        self.status = "queued"


class FetchInfoWorker(QThread):
    finished = pyqtSignal(list, str)

    def __init__(self, url):
        super().__init__()
        self.url = url.strip()

    def run(self):
        try:
            cmd = [
                str(YT_DLP),
                "--no-playlist",
                "--print", "%(webpage_url)s;%(title)s;%(duration)s;%(id)s",
                self.url
            ]
            result = subprocess.run(
                cmd,
                cwd=str(TOOLS_DIR),
                capture_output=True,
                text=True,
                env=env,
                timeout=10,
                startupinfo=STARTUPINFO
            )

            if result.returncode != 0:
                err_text = (result.stderr or result.stdout).strip()
                self.finished.emit([], f"Ошибка YouTube: {err_text[:150]}")
                return

            line = result.stdout.strip()
            if not line:
                self.finished.emit([], "Не удалось получить данные видео")
                return

            parts = line.split(';', 3)
            if len(parts) != 4:
                self.finished.emit([], "Получены некорректные данные от YouTube")
                return

            v_url, title, dur_str, vid = parts
            duration = int(dur_str) if dur_str.isdigit() else 0
            video = VideoInfo(v_url, title, duration, vid)
            self.finished.emit([video], "")

        except subprocess.TimeoutExpired:
            self.finished.emit([], "Таймаут: YouTube не отвечает. Попробуйте позже.")
        except Exception as e:
            self.finished.emit([], f"Внутренняя ошибка: {str(e)[:100]}")


class DownloadWorker(QThread):
    progress = pyqtSignal(int)
    finished_item = pyqtSignal(str, bool)

    def __init__(self, video_info, save_path, format_type, quality):
        super().__init__()
        self.video_info = video_info
        self.save_path = save_path
        self.format_type = format_type
        self.quality = quality
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        try:
            Path(self.save_path).mkdir(parents=True, exist_ok=True)

            cmd = [
                str(YT_DLP),
                "--no-playlist",
                "--ffmpeg-location", str(FFMPEG_BIN.parent),
                "--no-warnings",
                "--no-check-certificate"
            ]

            if self.format_type == "mp3":
                cmd += ["--extract-audio", "--audio-format", "mp3", "--audio-quality", "0"]
                ext = "mp3"
            else:
                if self.quality == "max":
                    format_spec = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]"
                else:
                    height = self.quality.replace("p", "")
                    format_spec = (
                        f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/"
                        f"best[height<={height}][ext=mp4]"
                    )
                cmd += ["-f", format_spec]
                cmd += ["--merge-output-format", "mp4"]
                ext = "mp4"

            safe_title = "".join(c for c in self.video_info.title[:50] if c not in '<>:"/\\|?*')
            filename = f"{safe_title}_{self.video_info.video_id}.{ext}"
            output_path = Path(self.save_path) / filename

            if output_path.exists():
                self.finished_item.emit(self.video_info.video_id, False)
                return

            cmd += ["-o", str(output_path), self.video_info.url]

            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(TOOLS_DIR),
                env=env,
                startupinfo=STARTUPINFO
            )

            while True:
                if self._stop:
                    proc.terminate()
                    proc.wait()
                    return

                line = proc.stdout.readline()
                if not line and proc.poll() is not None:
                    break

                if "[download]" in line and "%" in line:
                    try:
                        percent_part = line.split("%")[0].split()[-1]
                        percent = min(100, max(0, int(float(percent_part))))
                        self.progress.emit(percent)
                    except:
                        pass

            success = (proc.returncode == 0)
            self.finished_item.emit(self.video_info.video_id, success)

        except Exception:
            self.finished_item.emit(self.video_info.video_id, False)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Download YouTube Videos")
        self.resize(1000, 650)

        icon_path = resource_path("icon.png")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.setStyleSheet(self.get_gray_theme())

        self.load_settings()
        self.queue = []
        self.fetch_worker = None
        self.current_worker = None
        self.is_downloading = False

        self.load_queue()
        self.init_ui()
        self.update_info_panel()

    def get_gray_theme(self):
        return """
        QMainWindow, QWidget {
            background-color: #202020;
            color: #cccccc;
        }
        QLineEdit {
            background-color: #2a2a2a;
            border: 1px solid #444;
            color: #eeeeee;
            padding: 6px;
            border-radius: 4px;
        }
        QPushButton {
            background-color: #333333;
            color: #dddddd;
            border: 1px solid #444;
            padding: 6px 12px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #3c3c3c;
            border: 1px solid #555;
        }
        QPushButton:disabled {
            color: #666666;
            background-color: #282828;
            border: 1px solid #333;
        }
        QTableWidget {
            background-color: #252525;
            gridline-color: #353535;
            alternate-background-color: #2a2a2a;
        }
        QHeaderView::section {
            background-color: #282828;
            color: #bbbbbb;
            padding: 4px;
            border: 1px solid #353535;
        }
        QRadioButton, QLabel {
            color: #dddddd;
        }
        QProgressBar {
            text-align: center;
            color: #cccccc;
            border: 1px solid #444;
            border-radius: 4px;
            background: #282828;
        }
        QProgressBar::chunk {
            background: #555555;
            border-radius: 3px;
        }
        QGroupBox {
            border: 1px solid #444;
            border-radius: 6px;
            margin-top: 8px;
            padding: 8px;
        }
        QGroupBox::title {
            color: #aaaaaa;
        }
        """

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(15)

        left_panel = QVBoxLayout()
        left_panel.setSpacing(12)

        format_group = QGroupBox("Формат")
        mp4_radio = QRadioButton("MP4")
        mp3_radio = QRadioButton("MP3")
        mp4_radio.setChecked(True)
        mp4_radio.toggled.connect(lambda: setattr(self, 'format_type', 'mp4'))
        mp3_radio.toggled.connect(lambda: setattr(self, 'format_type', 'mp3'))
        format_layout = QVBoxLayout()
        format_layout.addWidget(mp4_radio)
        format_layout.addWidget(mp3_radio)
        format_group.setLayout(format_layout)
        left_panel.addWidget(format_group)

        left_panel.addWidget(QLabel("Качество:"))
        self.quality_combo = QComboBox()
        self.update_quality_options()
        left_panel.addWidget(self.quality_combo)

        left_panel.addWidget(QLabel("Папка сохранения:"))
        self.path_edit = QLineEdit(self.save_path)
        self.path_edit.setReadOnly(True)
        browse_btn = QPushButton("Обзор")
        browse_btn.clicked.connect(self.select_save_path)
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_btn)
        left_panel.addLayout(path_layout)

        left_panel.addWidget(QPushButton("Открыть папку", clicked=self.open_save_folder))
        left_panel.addWidget(QPushButton("GitHub", clicked=lambda: QDesktopServices.openUrl(QUrl("https://github.com/Endermanik13/DownloadYT"))))
        left_panel.addWidget(QPushButton("Telegram", clicked=lambda: QDesktopServices.openUrl(QUrl("https://t.me/aurums2347"))))
        left_panel.addStretch()

        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)

        input_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Вставьте ссылку на YouTube видео...")
        self.url_input.returnPressed.connect(self.add_url)
        add_btn = QPushButton("Добавить")
        add_btn.clicked.connect(self.add_url)
        input_layout.addWidget(add_btn)
        input_layout.addWidget(self.url_input)
        right_layout.addLayout(input_layout)

        control_layout = QHBoxLayout()
        self.start_btn = QPushButton("Начать скачивание")
        self.pause_btn = QPushButton("Пауза")
        self.cancel_btn = QPushButton("Отмена")

        self.start_btn.clicked.connect(self.start_download)
        self.pause_btn.clicked.connect(self.pause_download)
        self.cancel_btn.clicked.connect(self.cancel_download)

        self.pause_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)

        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.pause_btn)
        control_layout.addWidget(self.cancel_btn)
        right_layout.addLayout(control_layout)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Название", "Длительность", "Ссылка", "Удалить"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.itemSelectionChanged.connect(self.update_info_panel)
        right_layout.addWidget(self.table)

        self.info_label = QLabel("Очередь пуста")
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        right_layout.addWidget(self.info_label)
        right_layout.addWidget(self.progress_bar)

        signature_label = QLabel("By Aurum2347\nДелаем не по ГОСТ-у, а для людей")
        signature_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        signature_label.setStyleSheet("color: rgba(255,255,255,0.35); font-size: 10px;")
        right_layout.addWidget(signature_label)

        main_layout.addLayout(left_panel, 1)
        main_layout.addLayout(right_layout, 3)

        self.load_queue_to_table()

    def update_quality_options(self):
        self.quality_combo.clear()
        if getattr(self, 'format_type', 'mp4') == 'mp4':
            items = ["Максимальное", "1080p", "720p", "480p", "360p"]
            self.quality_combo.addItems(items)
            self.quality_combo.setCurrentText("Максимальное")
        else:
            items = ["Максимальное", "320 kbps", "192 kbps"]
            self.quality_combo.addItems(items)
            self.quality_combo.setCurrentText("Максимальное")

    def select_save_path(self):
        path = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения", self.save_path)
        if path:
            self.save_path = path
            self.path_edit.setText(path)
            self.save_settings()

    def open_save_folder(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.save_path))

    def format_duration(self, seconds):
        if seconds <= 0:
            return "—"
        return str(timedelta(seconds=int(seconds)))

    def add_url(self):
        url = self.url_input.text().strip()
        if not url:
            return
        self.url_input.clear()
        self.fetch_worker = FetchInfoWorker(url)
        self.fetch_worker.finished.connect(self.on_fetch_finished)
        self.fetch_worker.start()

    def on_fetch_finished(self, videos, error):
        if error:
            QMessageBox.critical(self, "Ошибка", error)
            return
        if not videos:
            return

        new_video = videos[0]
        if any(v.video_id == new_video.video_id for v in self.queue):
            QMessageBox.information(self, "Информация", "Это видео уже находится в очереди.")
            return

        if new_video.duration > 15 * 60:
            reply = QMessageBox.question(
                self,
                "Длинное видео",
                f"Видео «{new_video.title}» длится {self.format_duration(new_video.duration)}.\n"
                "Скачивание может занять много времени и места. Продолжить?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        self.queue.append(new_video)
        self.load_queue_to_table()

    def load_queue_to_table(self):
        self.table.setRowCount(0)
        for i, video in enumerate(self.queue):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(video.title))
            self.table.setItem(i, 1, QTableWidgetItem(self.format_duration(video.duration)))

            open_btn = QPushButton("Открыть")
            open_btn.clicked.connect(lambda _, url=video.url: QDesktopServices.openUrl(QUrl(url)))
            self.table.setCellWidget(i, 2, open_btn)

            remove_btn = QPushButton("Убрать")
            remove_btn.clicked.connect(lambda _, row=i: self.remove_row(row))
            self.table.setCellWidget(i, 3, remove_btn)

            self.table.setRowHeight(i, 0)
            self.animate_row_height(i, 0, 30)

        self.update_info_panel()

    def animate_row_height(self, row, current, target):
        if current < target:
            next_height = min(current + 4, target)
            self.table.setRowHeight(row, next_height)
            if next_height < target:
                QTimer.singleShot(5, lambda: self.animate_row_height(row, next_height, target))

    def remove_row(self, row):
        if 0 <= row < len(self.queue):
            del self.queue[row]
            self.load_queue_to_table()

    def update_info_panel(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            total_videos = len(self.queue)
            total_duration = sum(v.duration for v in self.queue)
            self.info_label.setText(
                f"Видео: {total_videos} | Общая длительность: {self.format_duration(total_duration)}"
            )
        else:
            selected_indices = [index.row() for index in selected_rows]
            selected_count = len(selected_indices)
            selected_duration = sum(self.queue[i].duration for i in selected_indices)
            self.info_label.setText(
                f"Видео: {len(self.queue)} (*Выделено: {selected_count}) | "
                f"Длительность выделенных: {self.format_duration(selected_duration)}"
            )

    def start_download(self):
        if not self.queue:
            QMessageBox.information(self, "Информация", "Очередь пуста.")
            return

        free_space = shutil.disk_usage(self.save_path).free
        if free_space < 100 * 1024 * 1024:
            QMessageBox.warning(self, "Мало места", "На диске осталось менее 100 МБ свободного места.")
            return

        self.is_downloading = True
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        self.process_next_in_queue()

    def process_next_in_queue(self):
        next_video = None
        for video in self.queue:
            if video.status == "queued":
                next_video = video
                break

        if next_video is None:
            self.on_queue_finished()
            return

        next_video.status = "downloading"
        self.load_queue_to_table()

        worker = DownloadWorker(
            next_video,
            self.save_path,
            getattr(self, 'format_type', 'mp4'),
            self.get_current_quality()
        )
        worker.finished_item.connect(self.on_download_finished)
        worker.progress.connect(self.update_progress)
        self.current_worker = worker
        worker.start()

    def get_current_quality(self):
        quality_text = self.quality_combo.currentText()
        if self.format_type == 'mp4':
            return "max" if quality_text == "Максимальное" else quality_text.replace("p", "") + "p"
        else:
            return "max" if quality_text == "Максимальное" else quality_text.split()[0]

    def pause_download(self):
        self.cancel_download()
        self.start_btn.setText("Продолжить")
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)

    def cancel_download(self):
        if hasattr(self, 'current_worker') and self.current_worker:
            self.current_worker.stop()
        self.is_downloading = False
        self.progress_bar.setValue(0)
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.start_btn.setText("Начать скачивание")
        for video in self.queue:
            if video.status == "downloading":
                video.status = "queued"
        self.load_queue_to_table()

    def update_progress(self, percent):
        self.progress_bar.setValue(percent)

    def on_download_finished(self, video_id, success):
        video_to_remove = None
        for video in self.queue:
            if video.video_id == video_id:
                if success:
                    video_to_remove = video
                else:
                    video.status = "Ошибка"
                break

        if video_to_remove:
            self.queue.remove(video_to_remove)

        self.load_queue_to_table()

        if self.is_downloading:
            self.process_next_in_queue()

    def on_queue_finished(self):
        self.is_downloading = False
        self.current_worker = None
        self.progress_bar.setValue(0)
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.start_btn.setText("Начать скачивание")
        self.load_queue_to_table()

    def save_settings(self):
        settings = {"save_path": self.save_path}
        with open("settings.json", "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)

    def load_settings(self):
        default_path = str(Path.home() / "Downloads")
        self.save_path = default_path
        self.format_type = "mp4"

        if os.path.exists("settings.json"):
            try:
                with open("settings.json", "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    self.save_path = settings.get("save_path", default_path)
            except Exception:
                pass

        Path(self.save_path).mkdir(parents=True, exist_ok=True)

    def save_queue(self):
        queue_data = []
        for video in self.queue:
            if video.status in ("queued", "error"):
                queue_data.append({
                    "url": video.url,
                    "title": video.title,
                    "duration": video.duration,
                    "video_id": video.video_id
                })
        with open("queue.json", "w", encoding="utf-8") as f:
            json.dump(queue_data, f, ensure_ascii=False, indent=2)

    def load_queue(self):
        if not os.path.exists("queue.json"):
            return
        try:
            with open("queue.json", "r", encoding="utf-8") as f:
                queue_data = json.load(f)
            for item in queue_data:
                video = VideoInfo(
                    url=item["url"],
                    title=item["title"],
                    duration=item["duration"],
                    video_id=item["video_id"]
                )
                self.queue.append(video)
        except Exception:
            pass

    def closeEvent(self, event):
        if self.is_downloading:
            reply = QMessageBox.question(
                self,
                "Подтверждение выхода",
                "Идёт скачивание. Отменить все загрузки и выйти?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

            if hasattr(self, 'current_worker') and self.current_worker:
                self.current_worker.stop()

        if (hasattr(self, 'fetch_worker') and
            self.fetch_worker is not None and
            self.fetch_worker.isRunning()):
            self.fetch_worker.terminate()
            self.fetch_worker.wait()

        self.save_queue()
        self.save_settings()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    try:
        from ctypes import windll
        app_id = "endermanik13.downloadyt.1"
        windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except ImportError:
        pass

    window = MainWindow()
    window.show()
    sys.exit(app.exec())