import json, datetime

from pymongo import MongoClient
from flask import Flask, Response

from wtforms import form, fields
from wtforms.fields.html5 import DateTimeField
from flask_admin.form.widgets import DateTimePickerWidget
from flask_admin.contrib.pymongo import ModelView
# from flask_admin.form import Select2Widget
import flask_admin as admin
from flask_admin.model.fields import InlineFormField, InlineFieldList

app = Flask(__name__)

# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'

# Create models
conn = MongoClient()
db = conn.ft


class PointField(fields.TextField):

    def process_formdata(self, valuelist):
        if valuelist:
            coordinates = valuelist[0].split(',')
            self.data = {
                "type": "Point",
                "coordinates": [
                        float(coordinates[0]),
                        float(coordinates[1])
                        ]
                }
        else:
            self.data = ''

    def _value(self):
        print(self.data)
        if self.data:
            return ','.join([str(x) for x in self.data['coordinates']])
        else:
            return ''


class EventsForm(form.Form):
    name = fields.TextField('Name')
    start = DateTimeField('Start Time', widget=DateTimePickerWidget())
    end = DateTimeField('End Time', widget=DateTimePickerWidget())


class PlaceForm(form.Form):
    name = fields.TextField('Name')
    address = fields.TextField('Address')
    location = PointField('Coordinates')

    events = InlineFieldList(InlineFormField(EventsForm))


class PlaceView(ModelView):
    column_list = ('name', 'address', 'location')
    column_sortable_list = ('name', 'address', 'location')

    form = PlaceForm


@app.route('/')
def index():
    return """<a href="/admin/">Click me to get to Admin!</a></br>
            <a href="/places/">Click me to get places!</a></br>

    """

# db.place.find({location:{$near:{$geometry:{type:'Point',coordinates:[49.8,24.0]},$maxDistance:20000}},}).toArray()
# db.place.ensureIndex({ "location": "2dsphere" })



@app.route('/places/<coordinates>/<maxdistance>/', )
@app.route('/places/', defaults={'coordinates': None,'maxdistance':20000}, methods=['GET'])
def places(coordinates, maxdistance):

    if coordinates:
        places = list(db.place.find({
           "location": {
               "$near": {
                   "$geometry": {
                       "type": "Point",
                       "coordinates": [float(x) for x in coordinates.split(',')]
                   },
                   "$maxDistance": int(maxdistance)
               }
           },
       },
      ))
    else:
        places = list(db.place.find())

    for place in places:
        place.pop("_id", None)
        if 'events' in place:
            events_to_check = place['events'][:]
            place['events'] = []
            for event in events_to_check:
                if event['end'] > datetime.datetime.now():
                    event['start'] = event['start'].isoformat().replace('T', ' ')
                    event['end'] = event['end'].isoformat().replace('T', ' ')
                    place['events'].append(event)

    resp = Response(json.dumps(places), status=200, mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    resp.headers.add('Access-Control-Allow-Methods', 'GET')
    print(resp.headers)

    return resp

if __name__ == '__main__':
    admin = admin.Admin(app, name='Places')
    admin.add_view(PlaceView(db.place, 'Places'))

    # Start app
    # app.run(host= '0.0.0.0', debug=True, ssl_context='adhoc')
    app.run(host='0.0.0.0', debug=True)
