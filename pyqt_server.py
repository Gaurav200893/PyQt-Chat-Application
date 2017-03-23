import sys
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtNetwork import *


PORT = 9999
SIZEOF_UINT32 = 4


class ServerDlg(QPushButton):
	''' Server Class  '''
	def __init__(self, parent=None):
		super(ServerDlg, self).__init__("&Close Server", parent)


		# create socket
		self.TcpServer = QTcpServer(self)
		self.TcpServer.listen(QHostAddress.LocalHost, PORT)
		self.connect(self.TcpServer, SIGNAL("newConnection()"), self.addConnection)

		# important vars ;)
		self.connections = []
		self.self_connections = {}
		self.connected_users = set()

		self.connect(self, SIGNAL("clicked()"), self.close)

		self.setWindowTitle("Server")


	# add the incoming connections
	def addConnection(self):
		''' Listens to the connection and adds them in the list'''

		clientConnection = self.TcpServer.nextPendingConnection()

		clientConnection.nextBlockSize = 0
		self.connections.append(clientConnection)

		# send 
		for c in self.connections:
			self.connected_users.add(c.socketDescriptor())
		self.sendUserList(self.connected_users,c.socketDescriptor())
		self.connect(clientConnection, SIGNAL("readyRead()"), self.receiveMessage)

	
	def sendUserList(self,socketIds,current_socket):
		''' 
			send the connected user's list to clients
		'''

		for s in self.connections:
			# set message on the basis of socket id
	
			self.self_connections = {
			"disabled": [s.socketDescriptor()],
			"connections": socketIds
			}
			
			# convert the python object
			message = repr(self.self_connections)

			# create data stream object
			reply = QByteArray()
			stream = QDataStream(reply, QIODevice.WriteOnly)
			stream.setVersion(QDataStream.Qt_4_2)

			# get the block size and message
			stream.writeUInt32(0)
			stream.writeQString(message)
			stream.device().seek(0)
			stream.writeUInt32(reply.size() - SIZEOF_UINT32)

			# write encoded message
			s.write(reply)

	# recieve the message and pass it for sending
	def receiveMessage(self):
	    # get all the connections
	    for s in self.connections:
	        # check the size
	        if s.bytesAvailable() > 0:
	            # create stream object
	            stream = QDataStream(s)
	            stream.setVersion(QDataStream.Qt_4_2)

	            # read the block size from client of the send message
	            if s.nextBlockSize == 0:
	                if s.bytesAvailable() < SIZEOF_UINT32:
	                    return
	                s.nextBlockSize = stream.readUInt32()

	            if s.bytesAvailable() < s.nextBlockSize:
	                return
	            # read the client message
	            textFromClient = stream.readQString()
	            s.nextBlockSize = 0


	            # send the message to others
	            ''' textFromClient is the message and socketDescriptor 
	            will send from which client messages is sent '''
	            self.sendMessage(textFromClient,s.socketDescriptor())
	            s.nextBlockSize = 0

	# send the recived messages
	def sendMessage(self,client_data,socketId):
		data_client = eval(client_data)
		
		client_message = data_client['message']
		remote_connection = data_client['remote_socket']

		self.message_data = {}
		for s in self.connections:
            # set message on the basis of socket id

            # if user sends message
			if s.socketDescriptor() == socketId:
				message = str("You> ")+str(client_message)

				self.message_data = {
				"is_message": 1,
				"remote_socket": socketId,
				"message": message
				}

				msg_client = repr(self.message_data)
					# create data stream object
				reply = QByteArray()
				stream = QDataStream(reply, QIODevice.WriteOnly)
				stream.setVersion(QDataStream.Qt_4_2)

				# get the block size and message
				stream.writeUInt32(0)
				stream.writeQString(msg_client)
				stream.device().seek(0)
				stream.writeUInt32(reply.size() - SIZEOF_UINT32)

				# # write encoded message
				s.write(reply)


			elif s.socketDescriptor() == remote_connection:

				message = str(socketId)+"> "+str(client_message)

				self.message_data = {
				"is_message": 1,
				"remote_socket": socketId,
				"message": message
				}

				msg_client = repr(self.message_data)
					# create data stream object
				reply = QByteArray()
				stream = QDataStream(reply, QIODevice.WriteOnly)
				stream.setVersion(QDataStream.Qt_4_2)

				# get the block size and message
				stream.writeUInt32(0)
				stream.writeQString(msg_client)
				stream.device().seek(0)
				stream.writeUInt32(reply.size() - SIZEOF_UINT32)

				# # write encoded message
				s.write(reply)
		

app = QApplication(sys.argv)
form = ServerDlg()
form.show()
form.move(0,0)
app.exec_()