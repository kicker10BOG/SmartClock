import cherrypy, json, os
from datetime import datetime, timedelta
from dateutil import relativedelta
import helpers


class Alarms(object):
    def __init__(self): 
        self.currentAlarm = None
        self.currentAlarmStartTime = None
        self.snoozeCount = 0
        if not os.path.isfile('alarms.json'):
            with open('alarms.json', 'w') as f:
                d = json.loads('[]')
                json.dump(d, f)
        cherrypy.engine.subscribe('alarms-broadcast', self.listen)
        cherrypy.engine.subscribe('main', self.checkAlarms)
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

            if m['command'] == 'set': 
                alarms = self.set(m, alarms)
                self.updateNextAlarm(alarms)

            if m['command'] == 'delete': 
                alarms = self.delete(m, alarms)
                self.updateNextAlarm(alarms)
            
            if m['command'] == 'getNext': 
                self.updateNextAlarm(alarms)

            if m['command'] == 'dismiss': 
                m1 = {
                    'type': 'alarmDismissed',
                    'name': self.currentAlarm['name']
                    }
                self.currentAlarm = None
                self.snoozeCount = 0
                cherrypy.engine.publish('websocket-broadcast', json.dumps(m1))
                self.updateNextAlarm(alarms)

            if m['command'] == 'snooze': 
                self.snoozeCount += 1
                m1 = {
                    'type': 'alarmSnoozed',
                    'name': self.currentAlarm['name']
                    }
                cherrypy.engine.publish('websocket-broadcast', json.dumps(m1))
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
                alarm['name'] = m['name']
                alarm['days'] = m['days']
                alarm['time'] = m['time']
                alarm['enabled'] = m['enabled']
        print(alarms)
        return alarms

    def set(self, m, alarms):
        print(m)
        m['id'] = int(alarms[-1]['id']) + 1 if len(alarms) > 0 else 1
        alarms.append(m)
        print(alarms)
        return alarms

    def delete(self, m, alarms):
        print(m)
        for (i, alarm) in enumerate(alarms):
            if alarm['id'] == m['id']:
                del alarms[i]
                break
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
        intToDay = {
            0: 'Mon',
            1: 'Tue',
            2: 'Wed',
            3: 'Thu',
            4: 'Fri',
            5: 'Sat',
            6: 'Sun'
        }
        nowDT = datetime.now()
        nextAlarm = None
        nextAlarmDT = None
        if self.currentAlarm: 
            f = open('settings.json', 'r')
            settings = json.load(f)
            f.close()
            nextOccurence = self.currentAlarmStartTime + timedelta(minutes = self.snoozeCount * int(settings['snoozeInterval']))
            maxDT = nowDT + timedelta(minutes = int(settings['snoozeInterval']))
            while (nextOccurence > maxDT) :
                self.snoozeCount -= 1
                nextOccurence = self.currentAlarmStartTime + timedelta(minutes = self.snoozeCount * int(settings['snoozeInterval']))
            if nextOccurence > nowDT:
                nextAlarm = self.currentAlarm
                nextAlarm['day'] = intToDay[nextOccurence.weekday()]
                nextAlarm['enabled'] = True
                nextAlarm['snoozed'] = True
                nextAlarm['time'] = nextOccurence.strftime('%H:%M')
                nextAlarmDT = nextOccurence
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
                        nextAlarm['day'] = intToDay[dayToInt[day]]
                        nextAlarm['enabled'] = True
                        nextAlarm['snoozed'] = False
                        nextAlarmDT = nextDay
        if not nextAlarm: nextAlarm = {'enabled': False}
        nextAlarm['type'] = 'nextAlarm'
        cherrypy.engine.publish('websocket-broadcast', json.dumps(nextAlarm))

    def checkAlarms(self):
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
        if self.currentAlarm: 
            f = open('settings.json', 'r')
            settings = json.load(f)
            f.close()
            nextOccurence = self.currentAlarmStartTime + timedelta(minutes = self.snoozeCount * int(settings['snoozeInterval']))
            if nowDT.hour == nextOccurence.hour and nowDT.minute == nextOccurence.minute:
                m = {
                    'type': 'alarmTriggered',
                    'name': self.currentAlarm['name']
                }
                cherrypy.engine.publish('websocket-broadcast', json.dumps(m))
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
                        if nextDay.hour == nowDT.hour and nextDay.minute == nowDT.minute and nowDT.second == 0:
                            m = {
                                'type': 'alarmTriggered',
                                'name': alarm['name']
                            }
                            # self.triggeredAlarm = alarm
                            cherrypy.engine.publish('websocket-broadcast', json.dumps(m))
                            self.currentAlarm = alarm
                            self.currentAlarmStartTime = nowDT
                            self.snoozeCount = 0
                            self.updateNextAlarm(alarms)
