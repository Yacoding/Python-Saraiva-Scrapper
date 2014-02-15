from PyQt4 import QtGui
from PyQt4.QtCore import SIGNAL, Qt, QDir
from PyQt4.QtGui import *
import sys
from works.SaraivaScrapper import SaraivaScrapper

__author__ = 'Rabbi'


class Form(QMainWindow):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        self.createGui()
        self.fileName = None
        self.urlList = []

    def createGui(self):
        self.labelFile = QLabel('<b>Select File with url list: </b>')
        self.btnBrowse = QPushButton('&Browse')
        self.btnBrowse.clicked.connect(self.urlListSelected)

        self.labelHtmlFile = QLabel('<b>Select File with html tag: </b>')
        self.btnHtmlBrowse = QPushButton('&Browse')
        self.btnHtmlBrowse.clicked.connect(self.htmlTagSelected)

        self.labelReplaceTag = QLabel('<b>Tag to replace: </b>')
        self.inputReplaceTag = QLineEdit()

        self.labelUrl = QLabel('<b>URL: </b>')
        self.inputUrl = QLineEdit()

        self.labelCategory = QLabel('<b>Category: </b>')
        self.inputCategory = QLineEdit()

        self.btnScrap = QPushButton('&Scrap Saraiva Data')
        self.btnScrap.clicked.connect(self.scrapAction)

        layout = QGridLayout()
        layout.addWidget(self.labelFile, 0, 0, Qt.AlignRight)
        layout.addWidget(self.btnBrowse, 0, 1, Qt.AlignLeft)
        layout.addWidget(self.labelHtmlFile, 1, 0, Qt.AlignRight)
        layout.addWidget(self.btnHtmlBrowse, 1, 1, Qt.AlignLeft)
        layout.addWidget(self.labelReplaceTag, 2, 0, Qt.AlignRight)
        layout.addWidget(self.inputReplaceTag, 2, 1, Qt.AlignLeft)
        layout.addWidget(self.labelUrl, 3, 0, Qt.AlignRight)
        layout.addWidget(self.inputUrl, 3, 1)
        layout.addWidget(self.labelCategory, 4, 0, Qt.AlignRight)
        layout.addWidget(self.inputCategory, 4, 1)
        layout.addWidget(self.btnScrap, 5, 1, Qt.AlignLeft)

        self.browser = QTextBrowser()
        layoutMain = QVBoxLayout()
        layoutMain.addLayout(layout)
        layoutMain.addWidget(self.browser)
        widget = QWidget()
        widget.setLayout(layoutMain)

        self.setCentralWidget(widget)
        screen = QDesktopWidget().screenGeometry()
        self.resize(screen.width() - 200, screen.height() - 200)
        self.setWindowTitle('Saraiva Scraper.')

    def scrapAction(self):
        if len(str(self.inputCategory.text())) > 0:
            self.urlList.append(str(self.inputUrl.text()))
        self.saraiva = SaraivaScrapper(self.urlList, str(self.inputCategory.text()), str(self.htmlTag),
                                       str(self.inputReplaceTag.text()))
        self.saraiva.start()
        self.saraiva.notifySaraiva.connect(self.notifyInfo)

    def urlListSelected(self):
        self.fileName = QtGui.QFileDialog.getOpenFileName(self, "Select Text File", QDir.homePath() + "/Desktop")
        f = open(self.fileName, 'rb')
        self.lists = f.readlines()
        f.close()
        if self.lists is not None:
            for line in self.lists:
                self.urlList.append(line)

    def htmlTagSelected(self):
        try:
            self.htmlFileName = QtGui.QFileDialog.getOpenFileName(self, "Select Text File",
                                                                  QDir.homePath() + "/Desktop")
            f = open(self.htmlFileName, 'rb')
            self.htmlTag = f.read()
            f.close()
        except Exception, x:
            print x

    def notifyInfo(self, data):
        try:
            self.browser.document().setMaximumBlockCount(1000)
            self.browser.append(data)
        except Exception, x:
            print x


class MainView:
    def __init__(self):
        pass

    def showMainView(self):
        app = QApplication(sys.argv)
        form = Form()
        form.show()
        sys.exit(app.exec_())
