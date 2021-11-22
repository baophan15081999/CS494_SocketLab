import socket
import select
import random
import sys
import time
from Questions import QandA
from _thread import *

MSG_LEN = 5
random.shuffle(QandA)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

if len(sys.argv) != 3:
	exit()

number_of_participants = int(input("Please enter the number of participants(at least 2 and at most 10): "))  
number_joined = 0

if number_of_participants > 10 or number_of_participants < 1:
	while number_of_participants > 10 or number_of_participants < 1:
		number_of_participants = int(input("Please input valid number of participants: "))



IP_address = str(sys.argv[1])
Port = int(sys.argv[2])
server.bind((IP_address, Port))
server.listen(10)
print("Server started!")

print(f"Waiting for connection on IP address and Port number: {IP_address}, {Port}")
order = 0
clients_list = []
participants = {}
playOrder = {}
marks = {}
mapping = {}
Person = [server]
answer = [-1]
newOrder = 0
orderWithIndex = {}
mod = 0
def receive_message(client_socket):
	message = client_socket.recv(1024).decode('utf-8')
	return message

def send_to_one(receiver, message):
	message = f"{len(message):<{MSG_LEN}}" + message 
	try:
		receiver.send(bytes(message, 'utf-8'))
	except:
		receiver.close()
		clients_list.remove(receiver)

def send_to_all(sender, message):
	message = f"{len(message):<{MSG_LEN}}" + message
	for socket in clients_list:
		if (socket != server and socket != sender):
			try:
				socket.send(bytes(message, 'utf-8'))
			except:
				socket.close()
				clients_list.remove(socket)

def update_marks(player, number):
	print(participants[mapping[player]])
	marks[participants[mapping[player]]] += number
	print(marks)

def end_quiz():
	send_to_all(server, "GAME OVER\n")
	print("GAME OVER\n")
	max_score = max(marks, key=marks.get)
	send_to_all(server, "WINNER IS: " + str(max_score))
	send_to_all(server, "Scoreboard:")
	print("Scoreboard: ")
	for i in marks:
		send_to_all(server, ">> " + str(i) + ": " + str(marks[i]))
		print(">> " + str(i) + ": " + str(marks[i]))
	sys.exit()

def ask_question():
	if len(QandA) != 0:
		question_and_answer = QandA[0]
		question = question_and_answer[0]
		options = question_and_answer[1]
		Answer = question_and_answer[2]

		random.shuffle(options)
		option_number = 1
		mod = newOrder % number_of_participants
		if mod not in orderWithIndex.keys():
			mod += 1
		newMod = orderWithIndex[mod]
		send_to_one(playOrder[newMod], "\nQ. " + str(question))
		print("\nQ. " + str(question))
		for j in range(len(options)):
			send_to_one(playOrder[newMod], "   " + str(option_number) + ") " + str(options[j]))
			print("   " + str(option_number) + ") " + str(options[j]))
			if options[j] == Answer: 
				answer.pop(0)
				answer.append(int(option_number))
			option_number += 1
		send_to_one(playOrder[newMod], "\t\t\tIT IS YOUR TURN NOW. YOU HAVE 10 SECONDS TO ANSWER")
		send_to_one(playOrder[newMod], "\nHit Enter to answer")
		print("answer: option number " + str(answer))	
	else:
		send_to_all(server, "All questions asked!")
		end_quiz()
		sys.exit()

def quiz():
		Person[0] = server
		random.shuffle(QandA)
		ask_question()
		keypress = select.select(clients_list, [], [], 10)
		if len(keypress[0]) > 0:
			playerTurn = keypress[0][0]
			send_to_one(playerTurn, "ENTER YOUR ANSWER: ")
			time.sleep(0.01)
			Person.pop(0)
			Person.append(playerTurn)
			t0 = time.time()
			QandA.pop(0)

			answering = select.select(Person, [], [], 10)
			if len(answering) > 0:
				if time.time() - t0 >= 10:
					send_to_one(playerTurn, "NOT ANSWERED!")
					send_to_all(server, str(participants[mapping[playerTurn]]) + " -0.5")
					print(str(participants[mapping[playerTurn]]) + " -0.5")
					update_marks(playerTurn, -0.5)
					time.sleep(3)
					quiz()
				else:
					time.sleep(3)
					quiz()
			else:
				print("NOTHING!")						
		else:
			time.sleep(3)
			QandA.pop(0)
			quiz()

clients_list.append(server)

while True:
	rList, wList, error_sockets = select.select(clients_list, [], [])
	for socket in rList:
		if socket == server:
			client_socket, client_address = server.accept()
			if number_joined == number_of_participants:
				send_to_one(client_socket, "Cannot join")
				client_socket.close()
			else:
				name = receive_message(client_socket)
				if name:
					if name in participants.values():
						send_to_one(client_socket, "This name is already taken. Please choose a different one and join again!")
						client_socket.close()
					else:
						
						participants[client_address] = name
						playOrder[order] = client_socket
						marks[name] = 0
						orderWithIndex[order] = order 
						order += 1
						number_joined += 1
						mapping[client_socket] = client_address
						clients_list.append(client_socket)
						print("Participant connected: " + str(client_address) +" [ " + participants[client_address] + " ]" )
						send_to_one(client_socket, "Registration Completed Successfully " + name + "!\nPlease wait for other participants to join...")
						send_to_one(client_socket, "Your order: " + str(order))
						if number_joined == number_of_participants:
							time.sleep(1)
							send_to_all(server, "\n Welcome to the game WHO WANTS TO BE A MILLIONARE?")
							msg1 = "There are " + str(number_joined) + " participants joined:"
							send_to_all(server, msg1)
							for i in participants:
								send_to_all(server,">> " + participants[i])
							send_to_all(server, "\nThe quiz will begin soon. Prepare for when in turn\n")
							print("\n" + str(number_of_participants) + " participant(s) connected! The quiz will begin in 5 seconds")
							time.sleep(5)
							start_new_thread(quiz, ())
		else:  
			msg = receive_message(socket)
			print(msg)
			if socket == Person[0]:
				mod = newOrder % number_of_participants
				if mod not in orderWithIndex.keys():
					mod += 1
					
					newOrder += 1
				newOrder += 1
				try:
					ans = int(msg)
					if ans == answer[0]:
						send_to_one(socket, "CORRECT ANSWER. WAITING FOR YOUR NEXT TURN")
						update_marks(socket, 5)
						Person[0] = server
						if number_joined == 1:
							end_quiz()
										
					else:
						if number_joined == 1:
							end_quiz()
						else:
							send_to_one(socket, "WRONG ANSWER. YOU ARE OUT")
							number_joined -= 1
							orderWithIndex.pop(mod)
							Person[0] = server
				except ValueError:
					send_to_one(socket, "INVALID OPTION")
					Person[0] = server		

			elif Person[0] != server:
				send_to_one(socket, "OUT")

			
client_socket.close()
server.close()
