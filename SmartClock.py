import cherrypy, os, sys, traceback

from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket
# from ws4py.messaging import TextMessage

import json
import helpers

class StatusWebSocketHandler(WebSocket):
    def received_message(self, m):
        # print("Message received: ", m)
        if m == 'connected' or m == 'disconnected': return
        try:
            if m.is_text: 
                m = json.loads(m.data)
            if m['type'] == 'settings':
                cherrypy.engine.publish('settings-broadcast', m)
            elif m['type'] == 'alarms':
                cherrypy.engine.publish('alarms-broadcast', m)
        except Exception as e:
            print(e)
            traceback.print_exc()
        # cherrypy.engine.publish('websocket-broadcast', m)
        fsize = os.path.getsize('app.log')
        if fsize > 20000: 
            f = open('app.log', 'r')
            d = f.readlines()
            f.close()
            del d[0:-100]
            f = open('app.log', 'w')
            f.writelines(d)
            f.close()
        # pass

    def closed(self, code, reason="A client left the room without a proper explanation."):
        if type(reason) == bytes: reason = reason.decode('utf-8')
        m = json.dumps({
            'type': 'connection closed',
            'code': code,
            'reason': reason
        })
        cherrypy.engine.publish('websocket-broadcast', m)
        
class SmartClock(object):
    settings = None

    @cherrypy.expose
    def index(self): 
        return helpers.loadTemplate('home')

    @cherrypy.expose
    def ws(self):
        cherrypy.log("Handler created: %s" % repr(cherrypy.request.ws_handler))
        return
        
if __name__ == '__main__':
    WebSocketPlugin(cherrypy.engine).subscribe()
    cherrypy.tools.websocket = WebSocketTool()
    cherrypy.config.update('cherrypy.conf')
    cherrypy.config.namespaces['smartclock'] = {}

    wsConfig = {
        '/ws': {'tools.websocket.on': True,
            'tools.websocket.handler_cls': StatusWebSocketHandler
        }
    }
    cherrypy.config.update(wsConfig)
    
    root = SmartClock()
    app = cherrypy.tree.mount(root, '/', config = 'smartClock.conf')
    app.merge(wsConfig)
    
    # load settings page
    from Settings import Settings
    cherrypy.tree.mount(Settings(), '/settings')
    
    # load alarms page
    from Alarms import Alarms
    alarms = Alarms()
    cherrypy.tree.mount(alarms, '/alarms')

    cherrypy.engine.start()
    cherrypy.engine.block()