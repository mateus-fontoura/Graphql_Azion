import requests
import pandas as pd
import dash
from dash import html
from dash import dcc
#from django.shortcuts import render
from dash.dependencies import Input, Output, State
import datetime
import dash_table
import plotly.graph_objs as go
import os
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# Define the current date and the date 30 days ago
current_date = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
days_to_retrieve = 30
last_month_date = (datetime.datetime.now() - datetime.timedelta(days=days_to_retrieve)).strftime("%Y-%m-%dT%H:%M:%S")



# Get the user input token, if it's not already set
if "AUTH_TOKEN" in os.environ:
    user_token = os.environ["AUTH_TOKEN"]
else:
    user_token = input("Enter your authentication token: ")
    os.environ["AUTH_TOKEN"] = user_token  # store the token in the environment variable for future use


# Define the API endpoint and headers
url = "https://api.azionapi.net/events/graphql"
headers = {
    "Authorization": f"Token {user_token}",
    "Content-Type": "application/json"
}

# Define the GraphQL query
query = f"""query EventsQuery{{
    httpEvents(
        limit: 10000,
        filter: {{
        tsRange: {{begin:"{last_month_date}", end:"{current_date}"}}
    }},
        aggregate: {{count: ts}}
        groupBy: [ts,requestUri,status,host, upstreamStatus, requestTime, upstreamResponseTime, remoteAddress, requestUri]
        orderBy: [count_DESC]
        )
        {{
            ts
            host
            requestUri
            status
            upstreamStatus
            requestTime
            upstreamResponseTime
            remoteAddress
            requestUri
            count
        }}
}}"""

data = {"query": query}

# Send the request to the GraphQL API endpoint
result = requests.post(url, headers=headers, json=data).json()
print(result)

# Transform the JSON data from the query result into a pandas DataFrame
df = pd.DataFrame(result["data"]["httpEvents"])

# Count the occurrences of each status for each timestamp
df['ts'] = pd.to_datetime(df['ts'])
df.loc[:, 'ts'] = pd.to_datetime(df['ts'].dt.round('min'))

status_counts = df.groupby(['ts', 'status']).size().reset_index(name='counts').copy()

# Get the top five remote addresses and their occurrence counts
top_remote_addresses = df.groupby('remoteAddress')['count'].sum().reset_index().sort_values('count', ascending=False).head(10).loc[:, ['remoteAddress', 'count']]

# Get the top five RequestUri's and their occurrence counts
top_requestUri = df.groupby('requestUri')['count'].sum().reset_index().sort_values('count', ascending=False).head(10).loc[:, ['requestUri', 'count']]



# Create the table for remote address number of accesses
table_remoteaddress = dash_table.DataTable(
    id='top-remote-addresses',
    columns=[        {'name': 'Remote Address', 'id': 'remoteAddress'},        {'name': 'Count', 'id': 'count'},    ],
    data=top_remote_addresses.loc[:, ['remoteAddress', 'count']].copy().to_dict('records'),
    style_cell={'backgroundColor': 'darkgray'}
)


# Create the table for remote address number of accesses
table_requesturi = dash_table.DataTable(
    id='top-requestUri',
    columns=[        {'name': 'requestUri', 'id': 'requestUri'},        {'name': 'Count', 'id': 'count'},    ],
    data=top_requestUri.loc[:, ['requestUri', 'count']].copy().to_dict('records'),
    style_cell={'backgroundColor': 'darkgray'}
)

app = dash.Dash(__name__)

app.layout = html.Div(children=[
    html.H1([
        html.Link(rel='stylesheet', href='https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css')
    ]),

    html.Div(children=[
        dcc.DatePickerRange(
            id='status-date-range',
            start_date=last_month_date,
            end_date=datetime.datetime.now().strftime("%Y-%m-%d"),
        ),
        dcc.DatePickerRange(
            id='upstream-status-date-range',
            start_date=last_month_date,
            end_date=datetime.datetime.now().strftime("%Y-%m-%d")
        )
    ], style={'background-color': 'darkgray', 'display': 'none'}),

    html.Div(className='row', children=[
        html.Div(className='col-md-6', children=[
            dcc.Graph(
                id='status-2xx-graph',
            )
        ]),
        html.Div(className='col-md-6', children=[
            dcc.Graph(
                id='status-3xx-graph',
            )
        ])
    ], style={'background-color': 'darkgray'}),

    html.Div(className='row', children=[
        html.Div(className='col-md-6', children=[
            dcc.Graph(
                id='status-4xx-graph',
            )
        ]),
        html.Div(className='col-md-6', children=[
            dcc.Graph(
                id='status-5xx-graph',
            )
        ])
    ], style={'background-color': 'darkgray'}),

    html.Div(className='row', children=[
        html.Div(className='col-md-12', children=[
            dcc.Graph(
                id='upstream-status-graph',
            )
        ])
    ], style={'background-color': 'darkgray'}),
    html.Div(className='row', children=[
        html.Div(className='col-md-6', children=[
            dcc.Graph(
                id='status-429-444-200-graph'
            )
        ]),
        html.Div(className='col-md-6', children=[
            dcc.Graph(
                id='upstream-request-time-graph'
            )
        ])
    ]),
    # Add the table of the remote address top 5 and table of the requesturi top 5
    html.Div(className='row', children=[
        html.Div(className='col-md-6', children=[
            table_remoteaddress
        ]),
        html.Div(className='col-md-6', children=[
            table_requesturi
        ])
    ], style={'background-color': 'darkgray'})
], style={'background-color': 'darkgray'})



def generate_comparison_chart(status_codes, title, filtered_data):
    data = []
    colors = ['green', 'blue', 'yellow']
    for i, s in enumerate(status_codes):
        data.append(
            dict(
                x=filtered_data[filtered_data['status'] == s]['ts'],
                y=filtered_data[filtered_data['status'] == s]['counts'],
                type='bar',
                name=str(s),
                marker=dict(
                    color=colors[i]
                )
            )
        )

    return {
        'data': data,
        'layout': dict(
            title=title,
            xaxis=dict(
                title='Timestamp',
            ),
            yaxis=dict(
                title='Count'
            ),
            paper_bgcolor='darkgray',
            plot_bgcolor='lightgray'
        )
    }

def generate_request_time_chart(title, filtered_data):
    # calculate the average request time and limit the maximum value to 120 seconds
    filtered_data['requestTime'] = pd.to_numeric(filtered_data['requestTime'], errors='coerce')
    filtered_data['requestTime'] = filtered_data['requestTime'].fillna(0)
    filtered_data['requestTime'] = filtered_data['requestTime'].apply(lambda x: min(x, 120))
    filtered_data['upstreamResponseTime'] = pd.to_numeric(filtered_data['upstreamResponseTime'], errors='coerce')
    filtered_data['upstreamResponseTime'] = filtered_data['upstreamResponseTime'].fillna(0)
    filtered_data['upstreamResponseTime'] = filtered_data['upstreamResponseTime'].apply(lambda x: min(x, 120))
    avg_request_time = filtered_data.groupby('ts').agg({'requestTime': 'mean', 'upstreamResponseTime': 'mean'}).reset_index()

    data = [
        go.Bar(
            x=avg_request_time['ts'],
            y=avg_request_time['requestTime'],
            name='requestTime',
            marker=dict(
                color='green'
            )
        ),
        go.Bar(
            x=avg_request_time['ts'],
            y=avg_request_time['upstreamResponseTime'],
            name='upstreamResponseTime',
            marker=dict(
                color='lightyellow'
            )
        )
    ]

    return {
        'data': data,
        'layout': dict(
            title=title,
            xaxis=dict(
                title='Timestamp'
            ),
            yaxis=dict(
                title='Average Time (s)',
                range=[0, 120]
            ),
            paper_bgcolor='darkgray',
            plot_bgcolor='lightgray',
            barmode='group'
        )
    }


def generate_chart(start, end, color, title, filtered_data):
    filtered_data = filtered_data[(filtered_data['status'] >= start) & (filtered_data['status'] <= end)]

    return {
        'data': [
            dict(
                x=filtered_data[filtered_data['status'] == s]['ts'],
                y=filtered_data[filtered_data['status'] == s]['counts'],
                type='bar',
                name=str(s),
                marker=dict(
                    color=color
                )
            ) for s in filtered_data['status'].unique()
        ],
        'layout': dict(
            title=title,
            xaxis=dict(
                title='Timestamp',
                
            ),
            yaxis=dict(
                title='Count'
            ),
            paper_bgcolor='darkgray',
            plot_bgcolor='lightgray'
        )
    }



@app.callback(
    Output('status-2xx-graph', 'figure'),
    [Input('status-date-range', 'start_date'),
     Input('status-date-range', 'end_date')]
)
def update_status_2xx_graph(start_date, end_date):
    filtered_data = status_counts.loc[(status_counts['status'] >= 200) & (status_counts['status'] <= 299), :]

    filtered_data = filtered_data.loc[(filtered_data['ts'] >= start_date) & (filtered_data['ts'] <= end_date), :]

    return generate_chart(200, 299, 'green', "Status 2XX", filtered_data)


@app.callback(
    Output('status-3xx-graph', 'figure'),
    [Input('status-date-range', 'start_date'),
     Input('status-date-range', 'end_date')]
)
def update_status_3xx_graph(start_date, end_date):
    filtered_data = status_counts[(status_counts['status'] >= 300) & (status_counts['status'] <= 399)]
    filtered_data = filtered_data[(filtered_data['ts'] >= start_date) & (filtered_data['ts'] <= end_date)]
    return generate_chart(300, 399, 'blue', "Status 3XX", filtered_data)


@app.callback(
    Output('status-4xx-graph', 'figure'),
    [Input('status-date-range', 'start_date'),
     Input('status-date-range', 'end_date')]
)
def update_status_4xx_graph(start_date, end_date):
    filtered_data = status_counts[(status_counts['status'] >= 400) & (status_counts['status'] <= 499)]
    filtered_data = filtered_data[(filtered_data['ts'] >= start_date) & (filtered_data['ts'] <= end_date)]
    return generate_chart(400, 499, 'yellow', "Status 4XX", filtered_data)


@app.callback(
    Output('status-5xx-graph', 'figure'),
    [Input('status-date-range', 'start_date'),
     Input('status-date-range', 'end_date')]
)
def update_status_5xx_graph(start_date, end_date):
    filtered_data = status_counts[(status_counts['status'] >= 500) & (status_counts['status'] <= 599)]
    filtered_data = filtered_data[(filtered_data['ts'] >= start_date) & (filtered_data['ts'] <= end_date)]
    return generate_chart(500, 599, 'red', "Status 5XX", filtered_data)

@app.callback(
    Output('status-429-444-200-graph', 'figure'),
    [Input('status-date-range', 'start_date'),
     Input('status-date-range', 'end_date')]
)
def update_status_429_444_200_graph(start_date, end_date):
    filtered_data = status_counts[(status_counts['status'] == 429) | (status_counts['status'] == 444) | (status_counts['status'] == 200)]
    filtered_data = filtered_data[(filtered_data['ts'] >= start_date) & (filtered_data['ts'] <= end_date)]
    return generate_comparison_chart([429, 444, 200], "Status 429 x 444 x 200", filtered_data)

@app.callback(
    Output('upstream-request-time-graph', 'figure'),
    [Input('status-date-range', 'start_date'),
     Input('status-date-range', 'end_date')]
)
def update_upstream_request_time_graph(start_date, end_date):
    filtered_data = df[(df['ts'] >= start_date) & (df['ts'] <= end_date)]

    return generate_request_time_chart('Request Time and Upstream Response Time', filtered_data)


##########################################################################################
@app.callback(
    Output('upstream-status-graph', 'figure'),
    [Input('upstream-status-date-range','start_date'),
     Input('upstream-status-date-range','end_date')]
)
def update_upstream_status_graph(start_date, end_date):
    filtered_data = df[(df['ts'] >= start_date) & (df['ts'] <= end_date)]
    upstream_status_counts = filtered_data.groupby(['ts', 'upstreamStatus']).size().reset_index(name='counts')

    return {
        'data': [            {                'x': upstream_status_counts[upstream_status_counts['upstreamStatus'] == status]['ts'],
                'y': upstream_status_counts[upstream_status_counts['upstreamStatus'] == status]['counts'],
                'type': 'bar',
                'name': f"Status: {str(status)}"
            } for status in upstream_status_counts['upstreamStatus'].unique()
        ],
        'layout': dict(
                    title='Upstream status counts by timestamp',
                    xaxis=dict(title='Timestamp'),
                    yaxis=dict(title='Count'),
                    paper_bgcolor='darkgray',
                    plot_bgcolor='lightgray'
                )
    }


if __name__ == '__main__':
    app.run_server(debug=True)
