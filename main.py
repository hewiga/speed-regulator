from dash import Dash, html, dcc, Input, Output, State, dash_table, ctx
from dash.exceptions import PreventUpdate
from simulator import Simulator
import plotly.graph_objects as go
import pandas as pd
import threading
import base64
import io
import json

app = Dash(__name__)
app.title = 'Symulator'

def blank_figure():
    #stylizuje pusty wykres na czarny motyw
    fig = go.Figure(go.Scatter(x=[], y=[]))
    fig.update_layout(template='plotly_dark')
    return fig

#stylizowanie strony
app.layout = html.Div(children=[
    
    #belka menu
    html.Div(id='menu-bar', children=[      
        html.Button(id='show-road', className='display-button', n_clicks=0),
        html.Button(id='show-results', className='display-button', n_clicks=0),
        html.Div(id='options', children=[
            html.Button(children='Calculate', id='simulation-button'),
            html.Button(children='Download', id='download-button'),
            dcc.Upload(id='upload-data', children=html.Button(
                children='Upload', 
                id='upload-button'
            ))
        ])
    ]),

    #wykres trasy oraz tabela pojazdów
    html.Div(id='left-side', style={'display':'block', 'width': '46%'}, children=[
        dcc.Graph(id='road-graph', style={'width':'100%', 'margin':'0'}, figure=blank_figure()),
        html.Div(id='input-point', children=[
            dcc.Input(id='x-input', className='input-field'),
            dcc.Input(id='y-input', className='input-field'),
            html.Button(id='add-point-button', children='Add Point', n_clicks=0),
            html.Button(id='delete-point-button', children='Delete Point', n_clicks=0)
        ]),
        html.Div(id='car-stats-table', children=[
            dash_table.DataTable(columns=[
                {'name': i, 'id': i, 'selectable': True} for i in ['Name', 'Max speed', 'Max acceleration', 'Min acceleration', 'Mass']
            ],  data=[], 
                row_selectable='multi',
                selected_rows= [],
                id='car-table',
                style_header={'background-color': 'rgb(47, 47, 47)', 'color': 'white'}
            ),
        ]),
        html.Div(id='car-stats-input-fields', children=[
            dcc.Input(id='name-input', className='input-field'),
            dcc.Input(id='speed-input', className='input-field'),
            dcc.Input(id='max-acc-input', className='input-field'),
            dcc.Input(id='min-acc-input', className='input-field'),
            dcc.Input(id='mass-input', className='input-field'),
            html.Button(id='add-car-button', children='Add', n_clicks=0),
            html.Button(id='del-car-button', children='Delete', n_clicks=0),
            dcc.Store(id='cars')
        ]),
    ]),
    
    #wykresy z wynikami symulacji
    html.Div(id='right-side', style={'display':'block', 'width': '46%'}, children=[
        dcc.Graph(id='graph-velocity', figure=blank_figure()),
        dcc.Graph(id='graph-acceleration', figure=blank_figure())
    ]),
    dcc.Store(id='road'),
    dcc.Store(id='results'),
    dcc.Download(id='download_data')
])

@app.callback(
        Output(component_id='cars', component_property='data', allow_duplicate=True),
        Output(component_id='car-table', component_property='data', allow_duplicate=True),
        Input(component_id='add-car-button', component_property='n_clicks'),
        Input(component_id='del-car-button', component_property='n_clicks'),
        State(component_id='name-input', component_property='value'),
        State(component_id='speed-input', component_property='value'),
        State(component_id='max-acc-input', component_property='value'),
        State(component_id='min-acc-input', component_property='value'),
        State(component_id='mass-input', component_property='value'),
        State(component_id='cars', component_property='data'),
        State(component_id='car-table', component_property='selected_rows'),
        prevent_initial_call=True
)
def handle_car_table(click_add, click_del, name, speed, max_acc, min_acc, mass, data, selected_rows):
    #obslugiwanie akcji związanych z tabelą pojazdów

    triggered_id = ctx.triggered_id
    if triggered_id == 'add-car-button':
        return add_new_car(name, speed, max_acc, min_acc, mass, data)
    elif triggered_id == 'del-car-button':
        return delete_car(data, selected_rows)

def add_new_car(name, speed, max_acc, min_acc, mass, data):
    if name == '' or speed == '' or max_acc == '' or min_acc == '' or mass == '':
        raise PreventUpdate

    data = data or []
    data.append({'Name': name, 'Max speed': speed, 'Max acceleration': max_acc, 'Min acceleration': min_acc, 'Mass': mass})
    cars = data
    return data, cars

def delete_car(data, selected_rows):
    if selected_rows == []:
        raise PreventUpdate
    
    for element in selected_rows:
        data.pop(element)

    return data, data


@app.callback(
        Output(component_id='road', component_property='data', allow_duplicate=True),
        Output(component_id='road-graph', component_property='figure', allow_duplicate=True),
        Input(component_id='add-point-button', component_property='n_clicks'),
        State(component_id='x-input', component_property='value'),
        State(component_id='y-input', component_property='value'),
        State(component_id='road', component_property='data'),
        prevent_initial_call=True
)
def add_point(click, x_value, y_value, road):
    #dodawanie punktów na trasie
    if x_value == '' or y_value == '':
        raise PreventUpdate

    data = road or {'x': [], 'y': []}
    
    data['x'].append(float(x_value))
    data['y'].append(float(y_value))

    fig = go.Figure(go.Scatter(x=data['x'], y=data['y']))
    fig.update_layout(template='plotly_dark', title='Road')

    return data, fig

@app.callback(
        Output(component_id='road', component_property='data', allow_duplicate=True),
        Output(component_id='road-graph', component_property='figure', allow_duplicate=True),
        Input(component_id='delete-point-button', component_property='n_clicks'),
        State(component_id='road', component_property='data'),
        prevent_initial_call=True
)
def delete_point(click, road):
    #usuwanie punktów z trasy

    if road == None or road['x'] == []:
        raise PreventUpdate
    
    road['x'].pop(-1)
    road['y'].pop(-1)

    fig = go.Figure(go.Scatter(x=road['x'], y=road['y']))
    fig.update_layout(template='plotly_dark', title='Road')

    return road, fig


@app.callback(        
        Output(component_id='right-side', component_property='style'),
        Output(component_id='left-side', component_property='style'),
        Input(component_id='show-road', component_property='n_clicks'),
        Input(component_id='show-results', component_property='n_clicks'),
        State(component_id='right-side', component_property='style'),
        State(component_id='left-side', component_property='style'),
        prevent_initial_call=True
)
def display_section(click1, click2, style_result, style_road):
    #włącza i wyłącza konkretne sekcje na ekranie
    triggered_id = ctx.triggered_id

    if triggered_id == 'show-road':
        if style_road['display']=='none':
            style_road['display']='block'
            style_result['width'] = '46%'
        elif style_road['display']=='block':
            style_road['display']='none'
            style_result['width'] = '92%'

    elif triggered_id == 'show-results':
        if style_result['display']=='none':
            style_result['display']='block'
            style_road['width'] = '46%'
        elif style_result['display']=='block':
            style_result['display']='none'
            style_road['width'] = '92%'
        
    return style_result, style_road


@app.callback(
        Output(component_id='graph-velocity', component_property='figure', allow_duplicate=True),
        Output(component_id='graph-acceleration', component_property='figure', allow_duplicate=True),
        Output(component_id='results', component_property='data', allow_duplicate=True),
        Input(component_id='simulation-button', component_property='n_clicks'),
        State(component_id='road', component_property='data'),
        State(component_id='cars', component_property='data'),
        prevent_initial_call=True
)
def run_simulation(click, road_data, cars):
    
    #dla każdego auta utworzonego w tabeli pojazdów tworzy obiekt klasy Simulator
    simulations = []
    for car in cars:
        simulations.append(Simulator(int(car['Max speed']), int(car['Max acceleration']), int(car['Min acceleration']), int(car['Mass'])))

    #przygotowuje trasę
    i = 0
    road = []
    while i < len(road_data['x']):
        road.append([road_data['x'][i], road_data['y'][i]])
        i += 1   
    
    #dla każdego symulowanego pojazdu tworzony jest osobny wątek w którym przeprowadzana jest symulacja
    threads = []
    for simulation in simulations:
        threads.append(threading.Thread(target=simulation.simulate, args=(road, )))
        threads[-1].start()
    
    for thread in threads:
        thread.join()

    #przygotowuje wykresy wyników symulacji
    fig_velocity = go.Figure()
    fig_velocity.update_layout(template='plotly_dark', title="Velocity", xaxis_title='Time [s]', yaxis_title='Velocity [m/s]')
    fig_acceleration = go.Figure()
    fig_acceleration.update_layout(template='plotly_dark', title="Acceleration", xaxis_title='Time [s]', yaxis_title='Acceleration [m/s^2]')
    i = 0
    for simulation in simulations:
        fig_velocity.add_trace(go.Scatter(x=simulation.time, y=simulation.velocity, name=cars[i]['Name']))
        fig_acceleration.add_trace(go.Scatter(x=simulation.time, y=simulation.acceleration, name=cars[i]['Name']))
        i += 1

    #zapisuje dane w pamięci przeglądarki
    result = []
    for simulation in simulations:
        result.append({
            'velocity': simulation.velocity,
            'acceleration': simulation.acceleration,
            'time': simulation.time
        })

    return fig_velocity, fig_acceleration, result

@app.callback(
        
    Output(component_id='download_data', component_property='data'),
    Input(component_id='download-button', component_property='n_clicks'),
    State(component_id='results', component_property='data'),
    State(component_id='road', component_property='data'),
    State(component_id='cars', component_property='data'),
    prevent_initial_call=True
)
def download_data(click, results, road, cars):

    road = [road]
    for x in cars[1:]:
        road.append(None)    

    output = {
        "road": road,
        "cars": cars,
        "results": results
    }
    df = pd.DataFrame(output)
    return dcc.send_data_frame(df.to_json, 'plik.json')


@app.callback(
    Output(component_id='car-table', component_property='data', allow_duplicate=True),
    Output(component_id='cars', component_property='data', allow_duplicate=True),
    Output(component_id='road', component_property='data', allow_duplicate=True),
    Output(component_id='road-graph', component_property='figure', allow_duplicate=True),
    Output(component_id='graph-velocity', component_property='figure', allow_duplicate=True),
    Output(component_id='graph-acceleration', component_property='figure', allow_duplicate=True),
    Output(component_id='results', component_property='data', allow_duplicate=True),
    Input(component_id='upload-data', component_property='contents'),
    State(component_id='upload-data', component_property='filename'),
    prevent_initial_call=True
)
def upload_data(content, filename):
    content_type, content_string = content.split(',')
    decoded = base64.b64decode(content_string)

    data = json.load(io.StringIO(decoded.decode('utf-8')))
    data_size = len(data['road'])

    road = data['road']['0']

    cars=[]
    results=[]
    for x in range(data_size):
        cars.append(data['cars'][str(x)])
        results.append(data['results'][str(x)])

    fig = go.Figure(go.Scatter(x=road['x'], y=road['y']))
    fig.update_layout(template='plotly_dark', title='Road')

    fig_velocity = go.Figure()
    fig_velocity.update_layout(template='plotly_dark', title="Velocity", xaxis_title='Time [s]', yaxis_title='Velocity [m/s]')

    fig_acceleration = go.Figure()
    fig_acceleration.update_layout(template='plotly_dark', title="Acceleration", xaxis_title='Time [s]', yaxis_title='Acceleration [m/s^2]')

    i = 0
    for data in results:
        fig_velocity.add_trace(go.Scatter(x=data['time'], y=data['velocity'], name=cars[i]['Name']))
        fig_acceleration.add_trace(go.Scatter(x=data['time'], y=data['acceleration'], name=cars[i]['Name']))
        i += 1

    return cars, cars, road, fig, fig_velocity, fig_acceleration, results

if __name__ == "__main__":
    app.run_server(debug=True)
