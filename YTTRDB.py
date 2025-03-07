# -*- coding: utf-8 -*-

import sys
import sqlite3
import webbrowser
from PyQt6.QtCore import Qt, QObject, QAbstractTableModel, QModelIndex, QTimer, QThreadPool, QRunnable, pyqtSlot, pyqtSignal
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QHeaderView, QTableView, QStatusBar, QAbstractItemView, QDialog, QProgressBar
from PyQt6.QtGui import QShortcut, QKeySequence, QCursor
from PyQt6 import uic
from YTTRDBAddVideoDlg import Ui_Dialog
from YTTRDBdb import insert_title, list_data, fetch_transcript, list_videos
from YTTRDByt import getVideoTitle, getVideosInPlaylist, analyzeURL

URL = "https://www.youtube.com/watch?v=%s&t=%ds"
HTML = """
<html>
<body>
<h2>%s</h2>
<br/>
<strong>%s</strong>
</body>
</html>
"""

class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data, headers):
        super().__init__()
        self._data = data
        self._headers = headers

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            # See below for the nested-list data structure.
            # .row() indexes into the outer list,
            # .column() indexes into the sub-list
            return self._data[index.row()][index.column()]

    def rowCount(self, index):
        # The length of the outer list.
        return len(self._data)

    def columnCount(self, index):
        # The following takes the first sub-list, and returns
        # the length (only works if all rows are an equal length)
        return len(self._data[0])

    def headerData(self, section, orientation, role):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._headers[section]
        return None

class WorkerSignals(QObject):
    """Signals from a running worker thread.

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc())

    result
        object data returned from processing, anything

    progress
        float indicating % progress
    """

    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(float)

class Worker(QRunnable):
    """Worker thread."""
    def __init__(self, video_id):
        super().__init__()
        self.video_id = video_id
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        """Your long-running job goes in this method."""
        con = sqlite3.connect("YTTRDB.db")
        cur = con.cursor()
        fetch_transcript(con,cur,self.video_id,self.signals.progress)
        con.close()
        self.signals.finished.emit()

class AddVideoDlg(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Create an instance of the GUI
        self.ui = Ui_Dialog()
        # Run the .setupUi() method to show the GUI
        self.ui.setupUi(self)
        self.ui.pushButtonOK.clicked.connect(self.onOK)
        self.ui.pushButtonCancel.clicked.connect(self.onCancel)
        self.ui.textEdit.textChanged.connect(self.enableOKButton)
        self.video_id = ""

    def enableOKButton(self):
        self.ui.pushButtonOK.setEnabled(True)

    def onOK(self):
        self.video_id = self.ui.textEdit.toPlainText()
        self.accept()

    def onCancel(self):
        self.close()

class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()

        # Set some properties
        self.tableView = None
        self.bChanged = False
        self.sel = -1

        # Access database
        self.con = sqlite3.connect("YTTRDB.db")
        self.cur = self.con.cursor()

        # Load the ui file
        uic.loadUi("YTTRDB.ui", self)
        self.xButton.clicked.connect(self.onClear)
        self.searchButton.clicked.connect(self.onSearch)
        self.playButton.clicked.connect(self.onPlay)
        self.backButton.clicked.connect(self.onPrevious)
        self.forwardButton.clicked.connect(self.onNext)
        self.text1.setFocus()

        # Menu bindings
        self.actionAdd_video.triggered.connect(self.onAddVideo)
        self.actionExit.triggered.connect(self.closeEvent)

        # Key bindings
        self.onEnter = QShortcut(QKeySequence('Return'), self)
        self.onEnter.activated.connect(self.onSearch)
        self.onRight = QShortcut(QKeySequence('Right'), self)
        self.onRight.activated.connect(self.onNext)
        self.onLeft = QShortcut(QKeySequence('Left'), self)
        self.onLeft.activated.connect(self.onPrevious)
        self.onDown = QShortcut(QKeySequence('Down'), self)
        self.onDown.activated.connect(self.onNext)
        self.onUp = QShortcut(QKeySequence('Up'), self)
        self.onUp.activated.connect(self.onPrevious)

        # Set up status bar
        self.status = QStatusBar()
        self.progressBar = QProgressBar()
        self.setStatusBar(self.status)
        self.status.addPermanentWidget(self.progressBar)

        # Enable multithreading
        self.threadpool = QThreadPool()
        thread_count = self.threadpool.maxThreadCount()

        # Show the app
        self.show()
        self.status.showMessage("Loading data ... "  )
        self.timer = QTimer(self)
        self.timer.singleShot(100, self.loadData)
        self.timer.start()

    # def event(self, event):
    #     print(event.type())
    #     return True


    def loadData(self):
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))
        try:
            self.cnt = self.listRows()
            self.status.showMessage("%d record(s) and %d videos in database." % (self.cnt,len(self.videos)) )
        except FileNotFoundError:
            self.status.showMessage("Hey, welcome to YTTRDB.py !")
        QApplication.restoreOverrideCursor()

    def listRows(self,searchText=""):
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))
        self.data = list_data(self.cur,searchText)
        self.displayData = []
        for r in self.data:
            self.displayData.append([r[-1],r[1]])
        videos = list_videos(self.cur)
        self.videos = []
        for r in videos:
            self.videos.append(r[0])
        self.headers = ["Video", "Time"]
        if self.tableView:
            self.tableView.deleteLater()
        self.model = TableModel(self.displayData, self.headers)
        self.tableView = QTableView(self.mainFrame)
        self.tableView.resize(self.mainFrame.frameSize())
        self.tableView.setModel(self.model)
        self.tableView.resizeColumnsToContents()
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableView.clicked.connect(self.tableViewClicked)
        header = self.tableView.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tableView.show()
        self.onNext()
        QApplication.restoreOverrideCursor()
        return len(self.data)

    def tableViewClicked(self, index):
        self.sel = index.row()
        self.textBrowser.setText(HTML % (self.data[index.row()][-1],self.data[index.row()][-2]))

    def resizeEvent(self, event):
        if self.tableView:
            self.tableView.resize(self.mainFrame.frameSize())
        size = event.size()
        # print(self.size().width(),self.size().height())

    def onClear(self):
        self.text1.setText("")
        self.onSearch()

    def onSearch(self):
        self.cnt = self.listRows(self.text1.text())
        self.status.showMessage("%d record(s) shown." % self.cnt )

    def onPlay(self):
        values = self.data[self.sel][1].split(":")
        seconds = int(values[0])*60 + int(values[1])
        url = URL % (self.data[self.sel][0],seconds)
        webbrowser.open(url)

    def onNext(self):
        self.sel += 1
        if self.sel >= len(self.data):
            self.sel = 0
        self.tableView.selectRow(self.sel)
        self.textBrowser.setText(HTML % (self.data[self.sel][-1],self.data[self.sel][-2]))

    def onPrevious(self):
        self.sel -= 1
        if self.sel < 0:
            self.sel = len(self.data)-1
        self.tableView.selectRow(self.sel)
        self.textBrowser.setText(HTML % (self.data[self.sel][-1],self.data[self.sel][-2]))

    def onAddVideo(self, s):
        self.videoQueue = []
        self.pl_id = ""
        self.status.showMessage("%d record(s) and %d videos in database." % (self.cnt,len(self.videos) ))
        dlg = AddVideoDlg(self)
        dlg.exec()
        if dlg.video_id and dlg.video_id not in self.videos:
            if dlg.video_id.startswith("https://www.youtube.com/watch"):
                self.video_id,self.pl_id =  analyzeURL(dlg.video_id)
            else:
                self.video_id = dlg.video_id
            if self.pl_id:
                self.videoQueue = getVideosInPlaylist(self.pl_id)
            else:
                self.videoQueue.append(self.video_id)
            if self.videoQueue:
                self.noVideos = len(self.videoQueue)
                self.AddVideo()

    def AddVideo(self):
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))
        if self.noVideos > 1:
            l = len(self.videoQueue)
            self.status.showMessage("%d record(s) in database. Adding video %d/%d ..." % (self.cnt,self.noVideos - l + 1,self.noVideos ))
        else:
            self.status.showMessage("%d record(s) in database. Adding video %s ...." % (self.cnt,self.videoQueue[-1] ))
        worker = Worker(self.videoQueue[-1])
        worker.signals.finished.connect(self.onAddVideoDone)
        worker.signals.progress.connect(self.onAddVideoProgress)
        self.threadpool.start(worker)

    def onAddVideoDone(self):
        title = getVideoTitle(self.videoQueue[-1])
        insert_title(self.con,self.cur,self.videoQueue[-1],title)
        self.cnt = self.listRows(self.text1.text())
        self.status.showMessage("%d record(s) and %d videos in database after adding video %s." % (self.cnt,len(self.videos),self.videoQueue[-1] ) )
        self.progressBar.setValue(0)
        QApplication.restoreOverrideCursor()
        v = self.videoQueue.pop()
        if self.videoQueue:
            self.AddVideo()

    def onAddVideoProgress(self, n):
        self.progressBar.setValue(n*100)

    def closeEvent(self, ev):
        # Needs: pip install odfpy
        if self.bChanged:
            QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))
            self.con.close()
            QApplication.restoreOverrideCursor()
        sys.exit(0)


app = QApplication(sys.argv)
UIWindow = UI()
app.exec()






