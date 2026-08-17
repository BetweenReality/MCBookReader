from __future__ import annotations

import inspect
import os
from pathlib import Path
from random import Random
import sys
from types import SimpleNamespace
from typing import Any, NamedTuple, TypeAlias, cast, final

from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import QEvent, QUrl, QSize, QPoint
from PyQt6.QtGui import QPixmap, QPainter, QTextDocument, QIcon, QTextCursor, QFont
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QAbstractButton, QGroupBox, QFrame, QWidget, QLayout
from PyQt6.QtMultimedia import QSoundEffect

import nbtlib
# from fontTools.ttLib import TTFont
# from fontTools.ttLib.tables import _c_m_a_p

MaybeNone: TypeAlias = Any

def base_path() -> str:
    # if getattr(sys, "frozen", False):
    #     return str(Path(sys.executable).resolve().parent)
    return str(Path(__file__).resolve().parent)

BASE_DIR = base_path()

APPLICATION_NAME = "BookReader"
APPLICATION_VERSION: str = "1.0.0"
FAKE_APP_ID: str = u"br.mc." + APPLICATION_NAME + "." + APPLICATION_VERSION

IMG_BOOK_ICON: str       = BASE_DIR + "/resources/images/written_book.ico"
IMG_BOOK: str            = BASE_DIR + "/resources/images/book.png"
IMG_PAGE_NEXT: str       = BASE_DIR + "/resources/images/page_forward.png"
IMG_PAGE_PREV: str       = BASE_DIR + "/resources/images/page_backward.png"
IMG_PAGE_NEXT_HOVER: str = BASE_DIR + "/resources/images/page_forward_highlighted.png"
IMG_PAGE_PREV_HOVER: str = BASE_DIR + "/resources/images/page_backward_highlighted.png"
IMG_QUIT: str            = BASE_DIR + "/resources/images/reject.png"
IMG_QUIT_HOVER: str      = BASE_DIR + "/resources/images/reject_highlighted.png"

FONT_DIR: str = BASE_DIR + "/resources/fonts"

# NOTE: Original files are ogg, but QSoundEffect can't read that
SOUNDS: tuple[str, str, str] = (
    BASE_DIR + "/resources/sounds/open_flip1.wav",
    BASE_DIR + "/resources/sounds/open_flip2.wav",
    BASE_DIR + "/resources/sounds/open_flip3.wav",
)

# Minecraft spaces lines by 1 relative pixel. The HTML seems to only like percentages best, so we approximate the percentage for the html
# TODO: Probably bad for other scale factors maybe
# LINE_HEIGHT_APPROX: float = 62
LINE_HEIGHT_APPROX: float = 82

def error(title: str, msg: str) -> int:
    print(f"{title}: {msg}")
    box = QtWidgets.QMessageBox()
    box.setIcon(QtWidgets.QMessageBox.Icon.Critical)
    box.setWindowTitle(title)
    box.setText(msg)
    _=box.exec()
    return 1

def main():
    app: QApplication = QApplication(sys.argv)
    window: MainWindow = MainWindow()
    
    app.setApplicationName(APPLICATION_NAME)
    app.setApplicationVersion(APPLICATION_VERSION)
    
    window.setWindowTitle("Minecraft Book Reader")
    app.setWindowIcon(QIcon(IMG_BOOK_ICON))
    
    # Dumb windows thing to set taskbar icon
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(FAKE_APP_ID)
    
    if (len(sys.argv) == 1):
        sys.exit(error("Error", "No file specified!"))
    
    book: Book = Book(sys.argv[1])
    bookKeeper: BookKeeper = BookKeeper(book)
    window.setBookKeeper(bookKeeper)
    bookKeeper.setMainWindow(window)
    
    window.show()
    sys.exit(app.exec())

# TODO: DPI scaling. Right now we force it to 2
SCALE_FACTOR: int = 2
def scaledVal(val: int) -> int:
    # TODO: Make this adjustable
    return val*SCALE_FACTOR

# TODO: Minecraft's text obfuscation is annoying
# class Obfuscator:
#     fontPath: str
    
#     _cmap_formats = _c_m_a_p.cmap_format_0 | _c_m_a_p.cmap_format_2 | _c_m_a_p.cmap_format_4 | _c_m_a_p.cmap_format_6 | _c_m_a_p.cmap_format_12 | _c_m_a_p.cmap_format_13 | _c_m_a_p.cmap_format_14 | _c_m_a_p.cmap_format_unknown
    
#     def __init__(self, fontPath: str):
#         super().__init__()
        
#         self.fontPath = fontPath
    
#     def load_glyph_chars(self, font_path: str) -> list[str]:
#         font: TTFont = TTFont(font_path)
#         chars: set[str] = set()
        
#         tables: list[Obfuscator._cmap_formats] = font["cmap"].tables # pyright: ignore[reportUnknownMemberType]
#         for table in tables:
#             cmap: dict[int, str] = table.cmap # pyright: ignore[reportUnknownMemberType]
#             chars.update(chr(cp) for cp in cmap.keys())
        
#         return [c for c in chars if c.isprintable() and not c.isspace()]

@final
class Formatter(SimpleNamespace):
    class Formats:
        class _fmt(NamedTuple):
            code: str
            color: str = ""
        
        obfuscated: _fmt    = _fmt("§k")
        bold: _fmt          = _fmt("§l")
        strikethrough: _fmt = _fmt("§m")
        underlined: _fmt    = _fmt("§n")
        italic: _fmt        = _fmt("§o")
        reset: _fmt         = _fmt("§r") # Resets all styles
        
        black: _fmt        = _fmt("§0", "#000000")
        dark_blue: _fmt    = _fmt("§1", "#0000AA")
        dark_green: _fmt   = _fmt("§2", "#00AA00")
        dark_aqua: _fmt    = _fmt("§3", "#00AAAA")
        dark_red: _fmt     = _fmt("§4", "#AA0000")
        dark_purple: _fmt  = _fmt("§5", "#AA00AA")
        gold: _fmt         = _fmt("§6", "#FFAA00")
        gray: _fmt         = _fmt("§7", "#AAAAAA")
        dark_gray: _fmt    = _fmt("§8", "#555555")
        blue: _fmt         = _fmt("§9", "#5555FF")
        green: _fmt        = _fmt("§a", "#55FF55")
        aqua: _fmt         = _fmt("§b", "#55FFFF")
        red: _fmt          = _fmt("§c", "#FF5555")
        light_purple: _fmt = _fmt("§d", "#FF55FF")
        yellow: _fmt       = _fmt("§e", "#FFFF55")
        white: _fmt        = _fmt("§f", "#FFFFFF")
        
        # Yes I know this is inefficient
        vars = {
            black,
            dark_blue,
            dark_green,
            dark_aqua,
            dark_red,
            dark_purple,
            gold,
            gray,
            dark_gray,
            blue,
            green,
            aqua,
            red,
            light_purple,
            yellow,
            white,
            obfuscated,
            bold,
            strikethrough,
            underlined,
            italic,
            reset,
        }
        
        format_codes = {
            obfuscated.code,
            bold.code,
            strikethrough.code,
            underlined.code,
            italic.code,
            reset.code,
        }
        
        # NOTE: Java Edition only
        color_codes = {
            black.code,
            dark_blue.code,
            dark_green.code,
            dark_aqua.code,
            dark_red.code,
            dark_purple.code,
            gold.code,
            gray.code,
            dark_gray.code,
            blue.code,
            green.code,
            aqua.code,
            red.code,
            light_purple.code,
            yellow.code,
            white.code,
        }
        
        @classmethod
        def getFromCode(cls, item: str) -> _fmt|MaybeNone:
            for v in cls.vars:
                if (item == v.code): return v
            return None
            
    @staticmethod
    def mc_format_to_html(text: str) -> str:
        hasColor: bool = False
        hasFormats: list[str] = []
        
        def clear_formats() -> str:
            insertion: str = ""
            for fmt in hasFormats:
                match fmt:
                    case Formatter.Formats.obfuscated.code:    insertion += "</span>"
                    case Formatter.Formats.bold.code:          insertion += "</b>"
                    case Formatter.Formats.strikethrough.code: insertion += "</s>"
                    case Formatter.Formats.underlined.code:    insertion += "</u>"
                    case Formatter.Formats.italic.code:        insertion += "</i>"
            hasFormats.clear()
            return insertion
        
        def clear_colors() -> str:
            insertion: str = "</span>"
            return insertion
        
        def invalid_format(formatCode: str):
            print(f"Warning: Invalid format code found: {formatCode}")
        
        i: int = 0
        while i < len(text):
            c: str = text[i]
            i+=1
            if (c != "§" or i >= len(text)): continue
            
            formatCode: str = c+text[i]
            insertion: str = ""
            
            if (formatCode in Formatter.Formats.format_codes):
                # print(f"Format Code Found: {formatCode}") # DEBUG
                
                insertion: str = ""
                match (formatCode):
                    case Formatter.Formats.obfuscated.code:
                        hasFormats.append(formatCode)
                        # TODO: Obfuscation just changes background color for now. I used the Wiki's obfuscation highlighted bg color
                        insertion += f"<span style=\"background-color: #B1F54E\";>"
                    
                    case Formatter.Formats.bold.code:
                        hasFormats.append(formatCode)
                        insertion += "<b>"
                    case Formatter.Formats.strikethrough.code:
                        hasFormats.append(formatCode)
                        insertion += "<s>"
                    case Formatter.Formats.underlined.code:
                        hasFormats.append(formatCode)
                        insertion += "<u>"
                    # BUG: Italics at the start of the line can clip the first character
                    # FIXME: Either this font or this HTML method of applying italics is incorrect (it does NOT look like Minecraft's). Might be the same for the other formats too
                    # This is probably why the italics clip to begin with. I should be using a cursor to render this.
                    case Formatter.Formats.italic.code:
                        hasFormats.append(formatCode)
                        insertion += "<i>"
                    
                    case Formatter.Formats.reset.code:
                        if (hasColor):
                            insertion += clear_colors()
                            hasColor = False
                        
                        insertion += clear_formats()
                    
                    case _: invalid_format(formatCode)
            elif (formatCode in Formatter.Formats.color_codes):
                # print(f"Color Code Found: {formatCode}") # DEBUG
                
                # "If a color code is used after a formatting code, the formatting code is disabled beyond the color code point." - Wiki
                if (len(hasFormats) > 0): insertion += clear_formats()
                if (hasColor): insertion += clear_colors()
                hasColor = True
                
                insertion += f"<span style=\"color:{Formatter.Formats.getFromCode(formatCode).color}\";>"
            else:
                invalid_format(formatCode)
            
            if (len(insertion) > 0):
                text = text[:i-1] + insertion + text[i+1:]
                i = (i-1) + len(insertion)
        
        if (len(hasFormats) > 0): text += clear_formats()
        if (hasColor): text += clear_colors()
        
        return text

class Book:
    src: str = ""
    pages: list[str] = []
    pageCount: int = 0
    author: str = ""
    
    def __init__(self, book: str):
        super().__init__()
        
        self.src = book
        
        self.load_book()
    
    def load_book(self, book: str|None = None):
        if (book == None): book = self.src
        else: self.src = book
        
        print(f"Loading book {self.src}")
        
        # TODO: Different loaders for different file types.
        # Basic loader is based off of the Scribble mod (and by extent, Minecraft's internal storage), but other mods may export differently
        # TODO: Does NBT even have a signature or are these bytes just coincidentally the same for this specific book format
        NBT_FILE_SIG = b"\x0A\x00\x00\x09"
        with open(self.src, "rb") as file:
            if (file.read(4) == NBT_FILE_SIG): self._load_book_nbt()
            else: sys.exit(error("Error", "Invalid file type!\nExpected one of: NBT"))
    
    def _load_book_nbt(self):
        file: nbtlib.File = nbtlib.load(self.src)
        
        self.pages: list[str] = file["pages"]
        # Scribble mod has an author entry (although it's always inaccurate since it uses the name of the player who exported, and you can't export written_book)
        if (file["author"] != None): author = file["author"]
        self.pageCount = len(self.pages)

class BookKeeper:
    mainWindow: MainWindow|None
        
    book: Book
    lastPage: int
    
    current_page: int = 1
    
    MIN_PAGES: int = 1
    MAX_PAGES: int = 100
    
    activeSounds: list[QSoundEffect]
    cachedSounds: tuple[QUrl, QUrl, QUrl]
    
    class PageTurn:
        BACKWARD: int = -1
        FORWARD: int = 1
    
    def __init__(self, book: Book, mainWindow: MainWindow|None = None):
        super().__init__()
        
        self.mainWindow = mainWindow
        
        self.book = book
        self.lastPage = len(book.pages)
        
        self.activeSounds = []
        self.cachedSounds = (
            QUrl.fromLocalFile(SOUNDS[0]),
            QUrl.fromLocalFile(SOUNDS[1]),
            QUrl.fromLocalFile(SOUNDS[2]),
        )
        
        if (self.mainWindow != None): self.update_book()
    
    def setMainWindow(self, mainWindow: MainWindow):
        self.mainWindow = mainWindow
        self.update_book()
    
    def _test_mainWindow(self) -> bool:
        if (self.mainWindow == None):
            print(f"Warning: {inspect.stack()[0][4]} called before mainWindow was set!")
            return False
        return True
    
    def update_book(self):
        if (not self._test_mainWindow()): return
        self.test_enable_buttons()
        self.update_page_text()
    
    def update_page_text(self):
        if (not self._test_mainWindow()): return
        assert self.mainWindow is not None
        
        self.mainWindow.pageCounterLabel.setText(f"Page {self.current_page} of {self.lastPage}")
        
        text = self.book.pages[self.current_page-1]
        text = Formatter.mc_format_to_html(text)
        text = text.replace('\n', '<br>') # Not "BetweenReality", but "break"
        
        # BUG: If a line is too long but contains spaces at the wrapping point, the spaces will be trimmed when wrapping to the next line. Lines with leading spaces function properly however
        
        # This is annoying, but we need to control line height so we have to display the text as HTML. This also means newlines don't work properly so we gotta fix that too
        # There's probably a better way to do this but I don't feel like doing that right now
        html = f"<div style=\"line-height: {LINE_HEIGHT_APPROX}%; white-space: pre-wrap;\">{text}</div>"
        
        self.mainWindow.textArea.setText(html)
    
    # Tests if the page flip buttons should be enabled right now based on the provided page
    def test_enable_buttons(self):
        if (not self._test_mainWindow()): return
        assert self.mainWindow is not None
        
        if (self.current_page <= self.MIN_PAGES): self.mainWindow.prev_page_button.setDisabled(True)
        else: self.mainWindow.prev_page_button.setDisabled(False)
        if (self.current_page >= self.lastPage): self.mainWindow.next_page_button.setDisabled(True)
        else: self.mainWindow.next_page_button.setDisabled(False)
    
    def prev_page_press(self, event: QEvent):
        self._page_flip(self.PageTurn.BACKWARD)
    
    def next_page_press(self, event: QEvent):
        self._page_flip(self.PageTurn.FORWARD)
    
    def _page_flip(self, pageIncrement: int):
        if ((self.current_page == self.MIN_PAGES and pageIncrement < 0) or (self.current_page == self.lastPage and pageIncrement > 0)): return
        
        page = self.current_page + pageIncrement
        self.current_page = page
        
        self.update_book()
        self._play_flip_sound()
    
    def _play_flip_sound(self):
        sound = QSoundEffect()
        
        sound.setSource(self.cachedSounds[Random().randint(0, 2)])
        sound.play()
        
        self.activeSounds.append(sound)
        _=sound.playingChanged.connect(lambda: self.cleanup_sound(sound)) # pyright: ignore[reportUnknownMemberType]
    
    def cleanup_sound(self, sound: QSoundEffect):
        if (not sound.isPlaying() and sound in self.activeSounds):
            self.activeSounds.remove(sound)
    
    def cleanup_all_sounds(self):
        for sound in self.activeSounds:
            sound.stop()
            if (sound in self.activeSounds): self.activeSounds.remove(sound)

class PicButton(QAbstractButton):
    def __init__(self, pixmap: QPixmap, pixmap_hover: QPixmap, pixmap_pressed: QPixmap|None = None, parent: QWidget|None=None):
        super(PicButton, self).__init__(parent)
        self.pixmap: QPixmap = pixmap
        self.pixmap_hover: QPixmap = pixmap_hover
        if (pixmap_pressed == None): self.pixmap_pressed: QPixmap = pixmap_hover
        else: self.pixmap_pressed = pixmap_pressed
        
        _=self.pressed.connect(self.update) # pyright: ignore[reportUnknownMemberType]
        _=self.released.connect(self.update) # pyright: ignore[reportUnknownMemberType]
    
    def paintEvent(self, e: QtGui.QPaintEvent|None):
        if (not self.isEnabled() or e == None): return
        
        pix: QPixmap = self.pixmap_hover if self.underMouse() else self.pixmap
        if self.isDown(): pix = self.pixmap_pressed
        
        painter: QPainter = QPainter(self)
        painter.drawPixmap(e.rect(), pix)
    
    def sizeHint(self) -> QSize:
        return self.pixmap.size()
    
    def enterEvent(self, event: QEvent|None):
        self.update()
    
    def leaveEvent(self, a0: QEvent|None):
        self.update()

# QLabel doesn't wrap long words, so this does it instead
# https://stackoverflow.com/a/68891355
class WrappingQLabel(QLabel):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        
        self.textalignment = QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.TextFlag.TextWrapAnywhere
        self.isTextLabel = True
        self.align = None
    
    def paintEvent(self, a0: QtGui.QPaintEvent|None):
        opt = QtWidgets.QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)
        
        # I don't know Qt enough to know if this is really required, seems to work just fine without it
        # self.style().drawPrimitive(QtWidgets.QStyle.PrimitiveElement.PE_Widget, opt, painter, self)
        
        rect = self.contentsRect()
        
        doc = QTextDocument()
        # This dumb doesn't inherit anything so we have to manually specify it
        doc.setDefaultFont(self.font())
        doc.setDocumentMargin(0)
        doc.setDefaultStyleSheet(f"div {{ color: {self.palette().color(QtGui.QPalette.ColorRole.WindowText).name()}}}")
        doc.setHtml(self.text())
        doc.setTextWidth(rect.width())
        
        opt_text = doc.defaultTextOption()
        opt_text.setWrapMode(QtGui.QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        doc.setDefaultTextOption(opt_text)
        
        painter.save()
        painter.translate(rect.topLeft())
        doc.drawContents(painter, QtCore.QRectF(0, 0, rect.width(), rect.height()))
        painter.restore()

@final
class MainWindow(QMainWindow):
    BASE_MARGIN: QtCore.QMargins = QtCore.QMargins(scaledVal(2), scaledVal(2), scaledVal(2), scaledVal(2))
    
    windowOffset: QPoint|None = None # For moving the window
    bookKeeper: BookKeeper|None = None
    
    background: QLabel
    mainLayout: QtWidgets.QVBoxLayout
    
    topTextContainer: QWidget
    quitButton: PicButton
    pageCounterLabel: QLabel
    
    textAreaSpace: QLabel
    textArea: WrappingQLabel
    
    prev_page_button: PicButton
    next_page_button: PicButton
    
    def __init__(self):
        super().__init__()
        
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Minecraft's space width is 5px, but "Minecraft Seven" seems to be 4px.
        # "Minecraft Default" is correct, but the font size needs to be higher (18 instead of 15).
        # Second one is more accurate since the game font size seems to be ~9 pixels in height, and our default scale factor is 2x
        # This is important since each page can only hold a specific amount of text, which is based on the text width itself
        fontID: int = QtGui.QFontDatabase.addApplicationFont(FONT_DIR + "/MinecraftDefault-Regular.ttf")
        fontFamilies: list[str] = QtGui.QFontDatabase.applicationFontFamilies(fontID)
        font: QFont = QFont(fontFamilies[0], scaledVal(9))
        
        font.setStyleStrategy(QFont.StyleStrategy.NoAntialias)
        self.setFont(font)
        
        palette = self.palette()
        palette.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColorConstants.Black)
        self.setPalette(palette)
        
        backgroundImg: QPixmap = QPixmap(IMG_BOOK)
        backgroundImg: QPixmap = backgroundImg.scaled(scaledVal(backgroundImg.width()), scaledVal(backgroundImg.height()))
        
        self.setFixedSize(backgroundImg.width(), backgroundImg.height()) # TODO: DPI scaling
        self.resize(backgroundImg.width(), backgroundImg.height())
        
        self.background = QLabel(self)
        self.background.resize(backgroundImg.width(), backgroundImg.height())
        self.background.setPixmap(backgroundImg.scaled(self.background.size(), QtCore.Qt.AspectRatioMode.IgnoreAspectRatio))
        self.background.installEventFilter(self)
        self.setCentralWidget(self.background)
        
        self.mainLayout = QtWidgets.QVBoxLayout(self.background)
        self.mainLayout.setSpacing(0)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        
        self._createTopText()
        self._createMainTextArea()
        self._createPageButtons()
    
    def _createTopText(self):
        layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        layout.setSpacing(0)
        # Magic numbers: Matching Minecraft's positions
        layout.setContentsMargins(scaledVal(16), scaledVal(12), scaledVal(18), self.BASE_MARGIN.bottom())
        
        self.topTextContainer = QWidget(self.background)
        
        self.quitButton = PicButton(QPixmap(IMG_QUIT), QPixmap(IMG_QUIT_HOVER), parent=self.topTextContainer)
        self.quitButton.setToolTip("Quit")
        self.quitButton.setFixedSize(self._getScaledSize(self.quitButton.pixmap.size()))
        self.quitButton.setMinimumSize(self._getScaledSize(self.quitButton.pixmap.size()))
        
        self.pageCounterLabel = QLabel(self.topTextContainer)
        self.pageCounterLabel.setPalette(self.palette())
        
        self.topTextContainer.setFixedHeight(self.quitButton.height()+layout.contentsMargins().top()+layout.contentsMargins().bottom())
        
        layout.addWidget(self.quitButton, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.pageCounterLabel, 0, QtCore.Qt.AlignmentFlag.AlignRight)
        
        self.topTextContainer.setLayout(layout)
        self.mainLayout.addWidget(self.topTextContainer)
    
    def _createMainTextArea(self):
        # Padding between the top and bottom widgets
        # TODO: QT has a spacer, maybe that could work for this purpose
        self.textAreaSpace = QLabel(self.background)
        self.mainLayout.addWidget(self.textAreaSpace)
        
        self.textArea = WrappingQLabel(self.background)
        # Magic numbers: Matching Minecraft's positions
        self.textArea.setContentsMargins(scaledVal(16), 0, scaledVal(16), self.BASE_MARGIN.bottom())
        self.textArea.move(0, self.topTextContainer.height())
        self.textArea.setWordWrap(True)
        self.textArea.setTextFormat(QtCore.Qt.TextFormat.RichText)
        
        # We don't have text editing capability yet
        self.textArea.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        
        # Not exact, but will always be enough to overflow downward as much as we need
        # You're not supposed to go down that far anyway but Minecraft allows it in specific cases so I need to replicate that behavior
        self.textArea.setFixedSize(self.background.size())
    
    def _createPageButtons(self):
        layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(scaledVal(26), self.BASE_MARGIN.top(), scaledVal(29), scaledVal(12))
        
        buttonContainer: QWidget = QWidget(self.background)
        
        self.prev_page_button = PicButton(QPixmap(IMG_PAGE_PREV), QPixmap(IMG_PAGE_PREV_HOVER), parent=buttonContainer)
        self.prev_page_button.setToolTip("Previous page")
        self.prev_page_button.setFixedSize(self._getScaledSize(self.prev_page_button.pixmap.size()))
        
        self.next_page_button = PicButton(QPixmap(IMG_PAGE_NEXT), QPixmap(IMG_PAGE_NEXT_HOVER), parent=buttonContainer)
        self.next_page_button.setToolTip("Next page")
        self.next_page_button.setFixedSize(self._getScaledSize(self.next_page_button.pixmap.size()))
        
        buttonContainer.setFixedHeight(self.prev_page_button.height()+layout.contentsMargins().top()+layout.contentsMargins().bottom())
        
        layout.addWidget(self.prev_page_button, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.next_page_button, 0, QtCore.Qt.AlignmentFlag.AlignRight)
        
        buttonContainer.setLayout(layout)
        self.mainLayout.addWidget(buttonContainer)
    
    def setBookKeeper(self, bookKeeper: BookKeeper):
        self.bookKeeper = bookKeeper
        _=self.prev_page_button.clicked.connect(self.bookKeeper.prev_page_press) # pyright: ignore[reportUnknownMemberType]
        _=self.next_page_button.clicked.connect(self.bookKeeper.next_page_press) # pyright: ignore[reportUnknownMemberType]
        _=self.quitButton.clicked.connect(self.bookKeeper.cleanup_all_sounds) # pyright: ignore[reportUnknownMemberType]
        _=self.quitButton.clicked.connect(self.close) # pyright: ignore[reportUnknownMemberType]
    
    def eventFilter(self, a0: QtCore.QObject|None, a1: QEvent|None) -> bool:
        # Allow moving window by clicking anywhere
        if a0 == self.background:
            assert a1 is not None
            if a1.type() == QEvent.Type.MouseButtonPress:
                self.windowOffset = a1.pos() # pyright: ignore[reportGeneralTypeIssues, reportUnknownMemberType]
            elif a1.type() == QEvent.Type.MouseMove and self.windowOffset is not None:
                self.move(self.pos() - self.windowOffset + a1.pos()) # pyright: ignore[reportGeneralTypeIssues, reportUnknownArgumentType, reportUnknownMemberType]
                return True
            elif a1.type() == QEvent.Type.MouseButtonRelease:
                self.windowOffset = None
        
        return super().eventFilter(a0, a1)
    
    def _getScaledSize(self, size: QtCore.QSize) -> QSize:
        return QtCore.QSize(scaledVal(size.width()), scaledVal(size.height()))
    
if __name__ == "__main__": main()