import cherrypy, os, sys, json
import helpers

class Settings(object):
    def __init__(self): 
        cherrypy.engine.subscribe('settings-broadcast', self.listen)
        return

    def listen(self, m): 
        if m['type'] == 'settings':
            # print(m)
            f = open('settings.json', 'r')
            settings = json.load(f)
            f.close()
            settings['format'] = m['format']
            settings['snoozeInterval'] = m['snoozeInterval']
            settings['seconds'] = m['seconds']
            settings['date'] = m['date']

            if hasattr(self, 'settings') and self.settings != settings :
                self.settings = settings
                m = {
                    "type": "update",
                    "format": self.settings['format'],
                    "seconds": self.settings['seconds'],
                    "date": self.settings['date']
                }
                cherrypy.engine.publish('websocket-broadcast', json.dumps(m))
            if not hasattr(self, 'settings'): 
                self.settings = settings
            
            f = open('settings.json', 'w')
            json.dump(settings, f)
            f.close()
        return

    @cherrypy.expose
    def index(self): 
        return helpers.loadTemplate('settings')