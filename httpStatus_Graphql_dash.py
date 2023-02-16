import requests
import pandas as pd
import dash
from dash import html
from dash import dcc
import datetime

# Define the current date and the date 30 days ago
current_date = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
last_month_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S")

# Define the GraphQL query
query = f"""query EventsQuery{{
    
    httpEvents(
        limit: 10000,
        filter: {{
     tsRange: {{begin:"{last_month_date}", end:"{current_date}"}}
   }},
        aggregate: {{count: ts}}
        groupBy: [ts,requestUri,status,host, upstreamStatus, requestTime, upstreamResponseTime]
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
            count
        }}
}}"""

# Define the API endpoint and headers ( https://www.azion.com/en/documentation/products/guides/graphql-aggregated-data/ )
url = "https://api.azionapi.net/events/graphql"
headers = {
    "Authorization": "Token azionYOURACCESSKEYHERE123456789123123",
    "Content-Type": "application/json"
}
data = {"query": query}

# Send the request to the GraphQL API endpoint
result = requests.post(url, headers=headers, json=data).json()
print(result)
# Transform the JSON data from the query result into a pandas DataFrame
df = pd.DataFrame(result["data"]["httpEvents"])


# Count the occurrences of each status for each timestamp
df['ts'] = pd.to_datetime(df['ts'])
df['ts'] = df['ts'].dt.round('min')
status_counts = df.groupby(['ts', 'status']).size().reset_index(name='counts')

# Group the data by timestamp and upstream status, and count the occurrences of each status
upstream_status_counts = df.groupby(['ts', 'upstreamStatus']).size().reset_index(name='counts')


# Create a bar chart for the upstream status counts
upstream_status_chart = {
    'data': [
        {
            'x': upstream_status_counts[upstream_status_counts['upstreamStatus'] == status]['ts'],
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
                plot_bgcolor='darkgray'
            )
}

# Initialize the Dash app
app = dash.Dash(__name__)

def generate_chart(start, end, color, title):
    status_counts_filtered = status_counts[(status_counts['status'] >= start) & (status_counts['status'] <= end)]

    return {
        'data': [
            dict(
                x=status_counts_filtered[status_counts_filtered['status'] == s]['ts'],
                y=status_counts_filtered[status_counts_filtered['status'] == s]['counts'],
                type='bar',
                name=str(s),
                marker=dict(
                    color=color
                )
            ) for s in status_counts_filtered['status'].unique()
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
            plot_bgcolor='darkgray'
        )
    }

# Define the styles for the page
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# Add the styles to the app
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(children=[
    html.Div(children=[
        html.Img(src='https://gcdnb.pbrd.co/images/O6iBZZwrjq9U.png?o=1',
                style={'width': '50%'})
    ],
    style={'backgroundColor': 'darkgray', 'text-align': 'center'}),
    dcc.Graph(
        id="Status 2xx",
        figure=generate_chart(200, 299, 'green', "Status 2XX"),
        style={'backgroundColor': 'darkgray'}
    ),
    dcc.Graph(
        id="Status 3xx",
        figure=generate_chart(300, 399, 'red', "Status 3XX"),
        style={'backgroundColor': 'darkgray'}
    ),
    dcc.Graph(
        id="statys 4xx",
        figure=generate_chart(400, 499, 'blue', "Status 4XX"),
        style={'backgroundColor': 'darkgray'}
    ),
    dcc.Graph(
        id="status 5xx",
        figure=generate_chart(500, 599, 'orange', "Status 5XX"),
        style={'backgroundColor': 'darkgray'}
    ),
    dcc.Graph(
        id='upstream-status-graph',
        figure=upstream_status_chart,
        style={'backgroundColor': 'darkgray'}
    ),
], style={'backgroundColor': 'darkgray'}




)

# Set the background color for the charts to black
for chart in ['status-bars-1', 'status-bars-2', 'status-bars-3', 'status-bars-4']:
    app.config.suppress_callback_exceptions = True
    @app.callback(
        dash.dependencies.Output(chart, 'figure'),
        [dash.dependencies.Input('interval-component', 'n_intervals')]
    )
    def update_graph(n):
        return generate_chart(200, 299, 'darkgray')

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
