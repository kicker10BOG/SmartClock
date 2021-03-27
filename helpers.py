from jinja2 import Environment, PackageLoader, select_autoescape
import json 

env = Environment(
    loader=PackageLoader('SmartClock', 'views'),
    autoescape=select_autoescape(['html', 'xml'])
)

def loadTemplate(templatName, **args): 
    f = open('settings.json', 'r')
    settings = json.load(f)
    f.close()
    template = env.get_template(templatName+'.html.jinja')
    return template.render(args, settings=settings)