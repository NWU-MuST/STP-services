#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function #Py2

import requests
import sys
import json
import os
import readline

readline.parse_and_bind('tab: complete')
readline.parse_and_bind('set editing-mode vi')

BASEURL = "http://127.0.0.1:9950/wsgi/"
GETAUDIO = "http://127.0.0.1/~ntkleynhans/test.ogg"
GETTEXT = "http://127.0.0.1/~ntkleynhans/test.txt"
POSTRESULT = "http://127.0.0.1:9000" # Fix port in dumper.py to be the same
ROOTPASSWORD = "b4MuhQ9ZFMQxx5wq"
PASSWORD = "VFKNZd4mD832VDcV"

class Jobs:

    def __init__(self):
        self.user_token = None
        self.job_id = None
        self.admin_token = None
        self.adjob_id = None

    def adlin(self):
        """
            Admin login
        """
        if self.admin_token is None:
            headers = {"Content-Type" : "application/json"}
            data = {"username": "root", "password": ROOTPASSWORD}
            res = requests.post(BASEURL + "jobs/admin/login", headers=headers, data=json.dumps(data))
            print('SERVER SAYS:', res.text)
            pkg = res.json()
            self.admin_token = pkg['token']
        else:
            print("Admin logged in already!")
        print('')

    def adlout(self):
        """
            Admin logout
        """
        if self.admin_token is not None:
            headers = {"Content-Type" : "application/json"}
            data = {"token": self.admin_token}
            res = requests.post(BASEURL + "jobs/admin/logout", headers=headers, data=json.dumps(data))
            print('SERVER SAYS:', res.text)
            self.admin_token = None
        else:
            print("Admin not logged in!")
        print('')

    def loadjobs(self):
        """
            Load all jobs in db
        """
        if self.admin_token is not None:
            headers = {"Content-Type" : "application/json"}
            data = {"token": self.admin_token}
            res = requests.post(BASEURL + "jobs/admin/loadjobs", headers=headers, data=json.dumps(data))
            print('SERVER SAYS:', res.text)
            pkg = res.json()
            self.adjob_id = pkg["data"][0]["jobid"]
        else:
            print("Admin not logged in!")
        print('')

    def loadjobinfo(self):
        """
            Load job info
        """
        if self.admin_token is not None and self.adjob_id is not None:
            headers = {"Content-Type" : "application/json"}
            data = {"token": self.admin_token, "jobid" : self.adjob_id}
            res = requests.post(BASEURL + "jobs/admin/loadjobinfo", headers=headers, data=json.dumps(data))
            print('SERVER SAYS:', res.text)
            pkg = res.json()
        else:
            print("Admin not logged in!")
        print('')

    def schedstop(self):
        """
            Load job info
        """
        if self.admin_token is not None:
            headers = {"Content-Type" : "application/json"}
            data = {"token": self.admin_token}
            res = requests.post(BASEURL + "jobs/admin/schedstop", headers=headers, data=json.dumps(data))
            print('SERVER SAYS:', res.text)
        else:
            print("Admin not logged in!")
        print('')

    def schedstart(self):
        """
            Load job info
        """
        if self.admin_token is not None:
            headers = {"Content-Type" : "application/json"}
            data = {"token": self.admin_token}
            res = requests.post(BASEURL + "jobs/admin/schedstart", headers=headers, data=json.dumps(data))
            print('SERVER SAYS:', res.text)
        else:
            print("Admin not logged in!")
        print('')

    def schedstatus(self):
        """
            Load job info
        """
        if self.admin_token is not None:
            headers = {"Content-Type" : "application/json"}
            data = {"token": self.admin_token}
            res = requests.post(BASEURL + "jobs/admin/schedstatus", headers=headers, data=json.dumps(data))
            print('SERVER SAYS:', res.text)
        else:
            print("Admin not logged in!")
        print('')


    def login(self):
        """
            Login as user
            Place user 'token' in self.user_token
        """
        if self.user_token is None:
            headers = {"Content-Type" : "application/json"}
            data = {"username": "appserver", "password": PASSWORD}
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

    def addjob_diarize(self):
        """
            Add diarization job
            Place jobid in self.job_id
        """
        if self.user_token is not None:
            headers = {"Content-Type" : "application/json"}
            data = {"token": self.user_token, "service" : "diarize", "subsystem" : "default", "getaudio" : GETAUDIO, "postresult" : POSTRESULT}
            res = requests.post(BASEURL + "jobs/addjob", headers=headers, data=json.dumps(data))
            print('SERVER SAYS:', res.text)
            pkg = res.json()
            self.job_id = pkg['jobid']
        else:
            print("User not logged in!")
        print('')

    def addjob_recognize(self):
        """
            Add recognition job
            Place jobid in self.job_id
        """
        if self.user_token is not None:
            headers = {"Content-Type" : "application/json"}
            data = {"token": self.user_token, "service" : "recognize", "subsystem" : "en-ZA", "getaudio" : GETAUDIO, "postresult" : POSTRESULT}
            res = requests.post(BASEURL + "jobs/addjob", headers=headers, data=json.dumps(data))
            print('SERVER SAYS:', res.text)
            pkg = res.json()
            self.job_id = pkg['jobid']
        else:
            print("User not logged in!")
        print('')

    def addjob_align(self):
        """
            Add alignment job
            Place jobid in self.job_id
        """
        if self.user_token is not None:
            headers = {"Content-Type" : "application/json"}
            data = {"token": self.user_token, "service" : "align", "subsystem" : "en-ZA", "gettext" : GETTEXT, "getaudio" : GETAUDIO, "postresult" : POSTRESULT}
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

    def discover(self):
        """
            Disciover all services
        """
        if self.user_token is not None:
            params = {"token": self.user_token}
            res = requests.get(BASEURL + "jobs/discover", params=params)
            print('SERVER SAYS:', res.text)
            pkg = res.json()
        else:
            print("User not logged in!")
        print('')


if __name__ == "__main__":
    print('Accessing Docker app server via: {}'.format(BASEURL))
    jobs = Jobs()

    try:
        while True:
            cmd = raw_input("Enter command (type help for list)> ")
            cmd = cmd.lower()
            if cmd == "exit":
                jobs.logout()
                break
            elif cmd in ["help", "list"]:
                print("ADLIN - admin login")
                print("ADLOUT - admin logout")
                print("LOGIN - user login")
                print("LOGOUT - user logout")
                print("ADDJOB_DIARIZE - add a job")
                print("ADDJOB_RECOGNIZE - add a job")
                print("ADDJOB_ALIGN - add a job")
                print("DELETEJOB - delete a job")
                print("QUERYJOBS - query jobs")
                print("USERJOBS - display user's jobs")
                print("DISCOVER - discover the services")
                print("EXIT - quit")

            else:
                try:
                    meth = getattr(jobs, cmd)
                    meth()
                except Exception as e:
                    print(e, 'UNKWOWN COMMAND')

    except:
        jobs.logout()
        print('')

