import markdown
from PyQt5 import QtWidgets, QtCore, QtWebEngineWidgets
from PyQt5.QtGui import QIcon

class Help_Window(QtWidgets.QDialog):
    '''
    This class is for the help window that displays the readme file
    to the user. It reads the readme file and displays the information
    as html using the markdown syntax.
    '''
    def __init__(self):
        super(Help_Window, self).__init__()
        self.setWindowTitle("Help")
        self.setWindowIcon(QIcon('hp_icon.png'))
        self.view = QtWebEngineWidgets.QWebEngineView(self)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.view)
        
        try:
            with open('README.md', 'r') as f:
                readme_text = f.read()
                html = markdown.markdown(readme_text)
                self.view.setHtml(html)
        except FileNotFoundError:
            self.view.setHtml("<h1>Error</h1><p>README.md not found.</p>")