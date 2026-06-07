# main.py  —  Entry point
import sys, os, ctypes
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui     import QPixmap, QIcon, QPainter, QPen, QBrush
from PyQt5.QtCore    import Qt, QTimer

sys.path.insert(0, os.path.dirname(__file__))

from core.constants       import STICK_COLOR
from core.stickman_widget import StickmanWidget
from ui.settings_window   import SettingsWindow

_BAT = os.path.join(os.path.dirname(__file__),
                    "scripts", "Eliminar_Archivos_Temporales.bat")


def _tray_icon():
    px = QPixmap(32, 32); px.fill(Qt.transparent)
    p  = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing)
    pen = QPen(STICK_COLOR, 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(pen); p.setBrush(QBrush(STICK_COLOR))
    p.drawEllipse(11, 2, 10, 10)
    p.drawLine(16,12,16,22)
    p.drawLine(16,16, 9,21)
    p.drawLine(16,16,23,21)
    p.drawLine(16,22,10,30)
    p.drawLine(16,22,22,30)
    p.end()
    return QIcon(px)


class App:
    def __init__(self):
        self.app  = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.stick = StickmanWidget(bat_path=_BAT)
        self.stick.show()
        self._sw = None
        self._build_tray()
        self.tray.showMessage(
            "Stickman is here",
            "Right-click the tray icon for options.",
            QSystemTrayIcon.NoIcon, 2200
        )

    def _build_tray(self):
        self.tray = QSystemTrayIcon(_tray_icon())
        m = QMenu()
        def act(label, fn):
            a = QAction(label, m); a.triggered.connect(fn); m.addAction(a)
        act("Settings",              self._open_settings)
        m.addSeparator()
        act("Make him dance",        self.stick.trigger_dance)
        act("Scare him",             self.stick.trigger_scare)
        act("Simulate notification", self.stick.trigger_notif)
        act("Run cleanup animation", self.stick.trigger_cleanup)
        m.addSeparator()
        act("Quit",                  self._quit)
        self.tray.setContextMenu(m)
        self.tray.activated.connect(
            lambda r: self._open_settings() if r == QSystemTrayIcon.DoubleClick else None
        )
        self.tray.show()

    def _open_settings(self):
        if self._sw and self._sw.isVisible():
            self._sw.raise_(); self._sw.activateWindow(); return
        self._sw = SettingsWindow(stick=self.stick)
        self._sw.show()

    def _quit(self):
        self.stick.stop(); self.tray.hide(); self.app.quit()

    def run(self):
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "StickmanPet_v4_mutex")
    if ctypes.windll.kernel32.GetLastError() == 183:
        ctypes.windll.user32.MessageBoxW(
            0, "Stickman is already running.\nCheck the system tray.",
            "Stickman", 0x40
        )
        sys.exit(0)
    App().run()
