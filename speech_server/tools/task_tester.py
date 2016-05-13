#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function #Py2

import requests
import sys
import json
import os

BASEURL = "http://127.0.0.1:9500/wsgi/"


class Tasks:

    def __init__(self):
        self.user_token = None
        self.task_id = None

    def login(self):
        """
            Login as user
            Place user 'token' in self.user_token
        """
        if self.user_token is None:
            headers = {"Content-Type" : "application/json"}
            data = {"username": "neil", "password": "neil"}
            res = requests.post(BASEURL + "tasks/login", headers=headers, data=json.dumps(data))
            print('SERVER SAYS:', res.text)
            pkg = res.json()
            self.user_token = pkg['token']
        else:
            print("User logged in already!")
        print('')

    def logout(self):
        """
            Logout as user
        """
        if self.user_token is not None:
            headers = {"Content-Type" : "application/json"}
            data = {"token": self.user_token}
            res = requests.post(BASEURL + "tasks/logout", headers=headers, data=json.dumps(data))
            print('SERVER SAYS:', res.text)
            self.user_token = None
        else:
            print("User not logged in!")
        print('')


    def addtask(self):
        """
            Add task
            Place taskid in self.task_id
        """
        if self.user_token is not None:
            headers = {"Content-Type" : "application/json"}
            data = {"token": self.user_token, "task" : "this_task"}
            res = requests.post(BASEURL + "tasks/addtask", headers=headers, data=json.dumps(data))
            print('SERVER SAYS:', res.text)
            pkg = res.json()
            self.task_id = pkg['taskid']
        else:
            print("User not logged in!")
        print('')

    def deletetask(self):
        """
            Delete task
        """
        if self.user_token is not None and self.task_id is not None:
            headers = {"Content-Type" : "application/json"}
            data = {"token": self.user_token, "taskid" : self.task_id}
            res = requests.post(BASEURL + "tasks/deletetask", headers=headers, data=json.dumps(data))
            print('SERVER SAYS:', res.text)
            pkg = res.json()
        else:
            print("User not logged in!")
        print('')

    def querytask(self):
        """
            Query specific task
        """
        if self.user_token is not None and self.task_id is not None:
            params = {"token": self.user_token, "taskid" : self.task_id}
            res = requests.get(BASEURL + "tasks/querytask", params=params)
            print('SERVER SAYS:', res.text)
            pkg = res.json()
        else:
            print("User not logged in!")
        print('')

    def usertasks(self):
        """
            Query all user tasks
        """
        if self.user_token is not None and self.task_id is not None:
            params = {"token": self.user_token}
            res = requests.get(BASEURL + "tasks/usertasks", params=params)
            print('SERVER SAYS:', res.text)
            pkg = res.json()
        else:
            print("User not logged in!")
        print('')


if __name__ == "__main__":
    print('Accessing Docker app server via: http://127.0.0.1:9500/wsgi/')
    tasks = Tasks()

    try:
        while True:
            cmd = raw_input("Enter command (type help for list)> ")
            cmd = cmd.lower()
            if cmd == "exit":
                tasks.logout()
                break
            elif cmd in ["help", "list"]:
                print("LOGIN - user login")
                print("LOGOUT - user logout")
                print("ADDTASK - add a task")
                print("DELETETASK - delete a task")
                print("EXIT - quit")

            else:
                try:
                    meth = getattr(tasks, cmd)
                    meth()
                except:
                    print('UNKWOWN COMMAND')

    except:
        tasks.logout()
        print('')

