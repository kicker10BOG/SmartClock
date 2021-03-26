import cherrypy, os, sys, json, time, threading
from datetime import datetime, timedelta
from dateutil import relativedelta
import helpers


class Alarms(object):
    def __init__(self): 
        cherrypy.engine.subscribe('alarms-broadcast', self.listen)
        return

    def listen(self, m): 
        if m['type'] == 'alarms':
            print("Alarms message received: ", m)
            f = open('alarms.json', 'r')
            alarms = json.load(f)
            f.close()

            if m['command'] == 'update': 
                alarms = self.update(m, alarms)
                self.updateNextAlarm(alarms)
            
            if m['command'] == 'getNext': 
                self.updateNextAlarm(alarms)

            cherrypy.engine.publish('websocket-broadcast', json.dumps(alarms))
            f = open('alarms.json', 'w')
            json.dump(alarms, f)
            f.close()
        return

    @cherrypy.expose
    def index(self): 
        f = open('alarms.json', 'r')
        alarms = json.load(f)
        f.close()
        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        return helpers.loadTemplate('alarms', alarms=alarms, days=days)

    def update(self, m, alarms):
        print(m)
        for alarm in alarms:
            if alarm['id'] == m['id']:
                alarm['days'] = m['days']
                alarm['time'] = m['time']
                alarm['enabled'] = m['enabled']
        print(alarms)
        return alarms
    
    def updateNextAlarm(self, alarms=None):
        if not alarms:
            f = open('alarms.json', 'r')
            alarms = json.load(f)
            f.close()
        dayToInt = {
            'Monday': 0,
            'Tuesday': 1,
            'Wednesday': 2,
            'Thursday': 3,
            'Friday': 4,
            'Saturday': 5,
            'Sunday': 6
        }
        nowDT = datetime.now()
        nextAlarm = None
        nextAlarmDT = None
        for alarm in alarms:
            if not alarm['enabled']: continue
            hour, minute = alarm['time'].split(':')
            hour = int(hour)
            minute = int(minute)
            for day in alarm['days']: 
                if alarm['days'][day]:
                    nextDay = nowDT + relativedelta.relativedelta(weekday = dayToInt[day])
                    nextDay = nextDay.replace(hour=hour, minute=minute, second=0)
                    if nextDay < nowDT: 
                        nextDay += timedelta(days=7)
                    if not nextAlarmDT or nextDay <= nextAlarmDT:
                        nextAlarm = alarm
                        nextAlarm['day'] = day
                        nextAlarm['enabled'] = True
                        nextAlarmDT = nextDay
        if not nextAlarm: nextAlarm = {'enabled': False}
        nextAlarm['type'] = 'nextAlarm'
        cherrypy.engine.publish('websocket-broadcast', json.dumps(nextAlarm))

    @classmethod 
    def checkAlarms(cls):
        f = open('alarms.json', 'r')
        alarms = json.load(f)
        f.close()
        dayToInt = {
            'Monday': 0,
            'Tuesday': 1,
            'Wednesday': 2,
            'Thursday': 3,
            'Friday': 4,
            'Saturday': 5,
            'Sunday': 6
        }
        nowDT = datetime.now()
        for alarm in alarms:
            if not alarm['enabled']: continue
            hour, minute = alarm['time'].split(':')
            hour = int(hour)
            minute = int(minute)
            for day in alarm['days']: 
                if alarm['days'][day]:
                    nextDay = nowDT + relativedelta.relativedelta(weekday = dayToInt[day])
                    nextDay = nextDay.replace(hour=hour, minute=minute, second=0)
                    if nextDay <= nowDT: 
                        if nextDay.hour == nowDT.hour and nextDay.minute == nowDT.minute:
                            m = {
                                'type': 'alarmTriggered'
                            }
                            # cls.triggeredAlarm = alarm
                            cherrypy.engine.publish('websocket-broadcast', json.dumps(m))
                            cls.updateNextAlarm(alarms)
        threading.Timer(60 - nowDT.second + 1, cls.checkAlarms).start()
