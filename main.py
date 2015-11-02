# -*- coding: utf-8 -*-

import socket
import random
import time
import logging
import config
import threading

logging.basicConfig(filename="irclog.txt", filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s', datefmt='%H:%M:%S',
                    level=logging.DEBUG)


class IRCClient():
    def __init__(self):
        self._server = config.SERVER
        self._port = config.PORT
        self._channel = config.CHANNEL
        self._botnick = config.BOTNICK
        self._timeout = int(config.TIMEOUT)
        self._ircsocket = IRCsocket(self._server, self._port, self._channel, self._botnick, self._timeout)
        self._messageQueue = MessageQueue()
        self._messageProcessor = MessageReceivedProcessor(self._botnick)

    def processQueue(self):
        while not self._messageQueue.isEmpty():
            self._ircsocket.send(self._messageQueue.pop())

    def run(self):
        while 1:
            try:
                self._ircsocket.connect()
                self._messageQueue.insert(IRCMessage.authenticate(self._botnick))
                self._messageQueue.insert(IRCMessage.setUserName(self._botnick))
                self._messageQueue.insert(IRCMessage.joinchan(self._channel))
                self._messageQueue.insert(IRCMessage.ping())
                self.processQueue()
                while 1:
                    try :
                        ircmsg = self._ircsocket.recv()
                    except socket.timeout:
                        pass
                    action = self._messageProcessor.rawMessage(ircmsg)
                    self._messageQueue.insert(action)
                    self.processQueue()
            except KeyboardInterrupt:
                exit()
            except Exception, e:
                logging.exception(e)
                time.sleep(1)


class IRCsocket():
    def __init__(self, server, port, channel, botnick, timeout):
        self._server = server
        self._port = port
        self._channel = channel
        self._botnick = botnick
        self._timeout = timeout
        self._ircsock = None

    def connect(self):
        self._ircsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._ircsock.settimeout(self._timeout)
        self._ircsock.connect((self._server, self._port))

    def send(self, message):
        logging.debug(message)
        self._ircsock.send(message)

    def recv(self):
        return self._ircsock.recv(2048)

    def close(self):
        self._ircsock.close()


class IRCMessage():
    @staticmethod
    def pong():
        """PONG <server1> [<server2>]"""
        return "PONG :pingis\n"

    @staticmethod
    def ping():
        """PONG <server1> [<server2>]"""
        return "PING :pingis\n"

    @staticmethod
    def sendmsg(chan, msg):
        """ PRIVMSG <msgtarget> <message>
         <msgtarget> which is usually a user or channel"""
        return "PRIVMSG " + chan + " :" + msg + "\n"

    @staticmethod
    def joinchan(chan):
        """# JOIN <channels> [<keys>]"""
        return "JOIN " + chan + "\n"

    @staticmethod
    def kick(chan, nick):
        """  KICK <channel> <client> [<message>] """
        return "KICK " + chan + " " + nick + " \n"

    @staticmethod
    def authenticate(botnick):
        """USER <username> <hostname> <servername> <realname> """
        return "USER " + botnick + " " + botnick + " " + botnick + " :+" + botnick + "\n"

    @staticmethod
    def setUserName(botnick):
        """ NICK <nickname>
        """
        return "NICK " + botnick + "\n"



class MessageQueue():
    def __init__(self):
        self._list = []
        self._lock = threading.Lock()

    def insert(self,element):
        with self._lock:
            if type(element) != str:
                for e in element:
                    self._list.insert(0,e)
            else:
                self._list.insert(0,element)

    def pop(self):
        with self._lock:
            return self._list.pop()

    def isEmpty(self):
        with self._lock:
            return not bool(len(self._list))


class MessageReceivedProcessor():
    def __init__(self, botnick):
        self._socket = socket
        self._botnick = botnick

    def rawMessage(self, ircmsg):
        ircmsg = ircmsg.strip('\n\r')
        print(ircmsg)
        listQ = []
        if ircmsg.find(' PRIVMSG ') != -1:
            nick = ircmsg.split('!')[0][1:]
            channel = ircmsg.split(' PRIVMSG ')[-1].split(' :')[0]
            listQ.extend(self.messageReceived(nick, channel, ircmsg))
        if ircmsg.find(' JOIN ') != -1:
            nick = ircmsg.split('!')[0][1:]
            channel = ircmsg.split(' JOIN ')[-1].split(' :')[0]
            listQ.extend(self.join(nick, channel))
        if ircmsg.find("PING :") != -1:
            print("Ping <-> pong")
            listQ.append(IRCMessage.pong())
        return listQ

    def messageReceived(self,nick, channel, message):
        listQ = []
        if message.find(self._botnick + ':') != -1:
            msgPossible = ["Message"]
            listQ.append(IRCMessage.sendmsg(channel, nick + ": " + random.choice(msgPossible)))
        elif message.find(self._botnick) != -1:
            pass
        elif message.find("message") != -1:
            listQ.append(IRCMessage.sendmsg(channel, "message"))
        elif message.find(self._botnick + ': help') != -1 or message.find(self._botnick + ': man') != -1:
            listQ.append(IRCMessage.sendmsg(channel, "message"))
        return listQ

    def join(self, nick, channel):
        listQ = []
        if nick.find('username') != -1 or nick.find('username') != -1:
            listQ.append(IRCMessage.sendmsg(channel, "message"))
            listQ.append(IRCMessage.sendmsg(channel, "message " + nick))
            listQ.append(IRCMessage.kick(channel, nick))
        return listQ



if __name__ == '__main__':
    client = IRCClient()
    client.run()