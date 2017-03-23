import sys
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtNetwork import *
import time

from functools import partial

# important vars
PORTS = (9999, 9998)
PORT = 9999
SIZEOF_INT32 = 4


class Form(QDialog):
	'''
		Generate the form for listing the connection
	'''
	def __init__(self, parent=None):
		super(Form, self).__init__(parent)

		self.message_container = None

		self.socket = QTcpSocket()
		self.nextBlockSize = 0
		self.request = None


		self.connectToServer()
		# get group box
		self.group_box = QGroupBox()
		self.group_box1 = QGroupBox()
		
		# create buttons
		self.btn1 = QLabel("Connecting...") #QPushButton("Connecting...")

		self.del_btn = QPushButton("close")
		self.del_btn.clicked.connect(self.close)
		

		# create layout for widgets(button)
		self.vbox = QVBoxLayout()
		self.vbox.addWidget(self.btn1)
		# self.vbox.addStretch(0)

		# set the group layout with button layout
		self.group_box.setLayout(self.vbox)

		scroll = QScrollArea()
		scroll.setWidget(self.group_box)
		scroll.setWidgetResizable(True)
		scroll.setFixedHeight(230)
		scroll.setFixedWidth(300)

		# add the updated connection
		# self.del_btn.clicked.connect(self.clearUI)


		vbox1 = QVBoxLayout()
		vbox1.addWidget(self.del_btn)
		vbox1.addStretch(1)

		self.group_box1.setLayout(vbox1)

		# create main layout
		self.main_layout = QVBoxLayout()
		# add other layouts
		# self.main_layout.addWidget(self.group_box)
		self.main_layout.addWidget(scroll)
		self.main_layout.addWidget(self.group_box1)

		# set the main layout
		self.setLayout(self.main_layout)

		self.socket.readyRead.connect(self.readFromServer)


	def connectToServer(self):
		''' connect to server '''
		self.socket.connectToHost("localhost", PORT)
		

	def readFromServer(self):
		''' get List from server '''

		stream = QDataStream(self.socket)
		stream.setVersion(QDataStream.Qt_4_2)

		# loop for the data
		while True:

			if self.nextBlockSize == 0:
                # if not the byte size there is no data
				if self.socket.bytesAvailable() < SIZEOF_INT32:
				    break
				# read the block size
				self.nextBlockSize = stream.readUInt32()

            # if no block size then no data
			if self.socket.bytesAvailable() < self.nextBlockSize:
			    break

			# read the data from the server stream
			textFromServer = stream.readQString()
			self.updateUI(textFromServer)
			self.nextBlockSize = 0



	def updateUI(self,connected_users):
		''' update the UI '''
		# reconstruct python object
		all_users = eval(connected_users)

		# check if it is message
		is_message = 0
		if "is_message" in all_users:
			is_message = 1

		if is_message==0:

			# remove all the connected listed users
			for i in reversed(range(self.vbox.count())): 
				item = self.vbox.itemAt(i)
				if isinstance(item, QWidgetItem):
					self.vbox.itemAt(i).widget().setParent(None)

			# get connected users
			self_id = all_users['disabled'][0]
			all_connections= all_users['connections']

			# generate user buttons
			self.buttons = []
			i=1
			for socketId in all_connections:
				
				if self_id != socketId:
					btn_name = str(socketId)
					btn_name = "user "+btn_name

					btn_obj = QPushButton(btn_name)
					btn_obj.clicked.connect(partial(self.handleButton, remote_socket=socketId,self_socket=self.socket))
					self.vbox.addWidget(btn_obj)
					i+=1
		else:

			client_id = all_users['remote_socket']
			client_msg = all_users['message']

			if self.message_container is not None:
	
				message_dialog = self.message_container
				message_dialog.setMessageBox(client_msg)
				message_dialog.show()
			else:

				# create the new dialog and update the message

				dialog = Dialog(self)
				self.message_container = dialog
				dialog.initUI(client_id,self.socket)
				self.message_container.setMessageBox(client_msg)
				dialog.show()
				


	def handleButton(self, remote_socket=0,self_socket=0):
		'''	initiate the chat box '''

		dialog = Dialog(self)
		self.message_container = dialog
		dialog.initUI(remote_socket,self_socket)
		# dialog.exec_()
		dialog.show()

class Dialog(QDialog):
	'''	chat box class '''

	def __init__(self, parent=None):
		super(Dialog, self).__init__(parent)

		# socket created
		self.socket=None


	
	def initUI(self, remote_socket, self_socket):
		'''	create and use the ui '''

		self.msg_layout = QVBoxLayout()
		# add other layouts
		soc = str(remote_socket)

		self.remote_socket = remote_socket
		# set socket
		self.socket = self_socket
		
		self.browser = QTextBrowser()
		self.lineedit = QLineEdit("Enter message")
		self.lineedit.selectAll()

		self.msg_layout.addWidget(self.browser)
		self.msg_layout.addWidget(self.lineedit)


		# set the main layout
		self.setLayout(self.msg_layout)

		self.lineedit.returnPressed.connect(partial(self.issueRequest, sock=self_socket))


	def issueRequest(self,sock):
		'''	issue server request '''

		# set request type
		self.request = QByteArray()

		# get data stream
		stream = QDataStream(self.request, QIODevice.WriteOnly)
		stream.setVersion(QDataStream.Qt_4_2)

		# get q string
		stream.writeUInt32(0)

		message_server = self.lineedit.text()     

		self.message_details = {
			"remote_socket": self.remote_socket,
			"message": message_server
			}

		message_server = repr(self.message_details)

		stream.writeQString(message_server)
		stream.device().seek(0)

		# get size of the bytes and write the data to server
		stream.writeUInt32(self.request.size() - SIZEOF_INT32)
		sock.write(self.request)

		# reset the variables
		self.nextBlockSize = 0
		self.request = None
		self.lineedit.setText("")

	def setMessageBox(self,message):
		''' set the message to the message box '''
		self.browser.append(message)

	def closeEvent(self, event):
		reply = QMessageBox.question(self, 'Message', "Are you sure to quit? ", 
			QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
		if reply == QMessageBox.Yes:
			event.accept()
			self.message_container = None
		else:
			event.ignore()



''' init the app loop '''
app = QApplication(sys.argv)

# Create and display the splash screen
splash_pix = QPixmap('qt_logo.png')

splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
# adding progress bar
progressBar = QProgressBar(splash)
progressBar.setGeometry(60, 215, 100, 20)

splash.setMask(splash_pix.mask())


splash.show()
for i in range(0, 100):
	progressBar.setValue(i)
	t = time.time()
	while time.time() < t + 0.1:
		app.processEvents()



# Simulate something that takes time
time.sleep(1)

form = Form()
form.show()
splash.finish(form)
app.exec_()