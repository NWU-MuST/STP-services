#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function #Py2

import requests
import sys
import json
import os

BASEURL = "http://127.0.0.1:9500/wsgi/"


class jobs:

    def __init__(self):
        self.user_token = None
        self.job_id = None

    def login(self):
        """
            Login as user
            Place user 'token' in self.user_token
        """
        if self.user_token is None:
            headers = {"Content-Type" : "application/json"}
            data = {"username": "neil", "password": "neil"}
            res = requests.post(BASEURL + "jobs/login", headers=headers, data=json.dumps(data))
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
            res = requests.post(BASEURL + "jobs/logout", headers=headers, data=json.dumps(data))
            print('SERVER SAYS:', res.text)
            self.user_token = None
        else:
            print("User not logged in!")
        print('')


    def addjob(self):
        """
            Add job
            Place jobid in self.job_id
        """
        if self.user_token is not None:
            headers = {"Content-Type" : "application/json"}
            data = {"token": self.user_token, "service" : "diarize", "subsystem" : "default", "getaudio" : "http://127.0.0.1/~ntkleynhans/test.ogg", "postresult" : "http://127.0.0.1:9950"}
            res = requests.post(BASEURL + "jobs/addjob", headers=headers, data=json.dumps(data))
            print('SERVER SAYS:', res.text)
            pkg = res.json()
            self.job_id = pkg['jobid']
        else:
            print("User not logged in!")
        print('')

    def deletejob(self):
        """
            Delete job
        """
        if self.user_token is not None and self.job_id is not None:
            headers = {"Content-Type" : "application/json"}
            data = {"token": self.user_token, "jobid" : self.job_id}
            res = requests.post(BASEURL + "jobs/deletejob", headers=headers, data=json.dumps(data))
            print('SERVER SAYS:', res.text)
            pkg = res.json()
        else:
            print("User not logged in!")
        print('')

    def queryjob(self):
        """
            Query specific job
        """
        if self.user_token is not None and self.job_id is not None:
            params = {"token": self.user_token, "jobid" : self.job_id}
            res = requests.get(BASEURL + "jobs/queryjob", params=params)
            print('SERVER SAYS:', res.text)
            pkg = res.json()
        else:
            print("User not logged in!")
        print('')

    def userjobs(self):
        """
            Query all user jobs
        """
        if self.user_token is not None and self.job_id is not None:
            params = {"token": self.user_token}
            res = requests.get(BASEURL + "jobs/userjobs", params=params)
            print('SERVER SAYS:', res.text)
            pkg = res.json()
        else:
            print("User not logged in!")
        print('')


if __name__ == "__main__":
    print('Accessing Docker app server via: http://127.0.0.1:9500/wsgi/')
    jobs = jobs()

    try:
        while True:
            cmd = raw_input("Enter command (type help for list)> ")
            cmd = cmd.lower()
            if cmd == "exit":
                jobs.logout()
                break
            elif cmd in ["help", "list"]:
                print("LOGIN - user login")
                print("LOGOUT - user logout")
                print("ADDjob - add a job")
                print("DELETEjob - delete a job")
                print("EXIT - quit")

            else:
                try:
                    meth = getattr(jobs, cmd)
                    meth()
                except:
                    print('UNKWOWN COMMAND')

    except:
        jobs.logout()
        print('')

