# Graphql_Azion

Overview:
This code is a Python script that retrieves data from an API endpoint, transforms the data into a Pandas DataFrame, and creates several interactive visualizations using the Dash framework. The visualizations show various metrics related to HTTP requests, including the count of HTTP response status codes (2xx, 3xx, 4xx, and 5xx), the count of requests by remote address and request URI, and the average request time and upstream response time.

Dependencies:
This code requires the following Python libraries to be installed:

requests
pandas
dash
dash_table
plotly
To install these dependencies, you can use the pip package manager. For example, you can run the following command in your terminal or command prompt:
pip install requests pandas dash dash_table plotly

Usage:
To run the script, simply execute it in a Python environment that has the required dependencies installed. If you are running the script for the first time, you will be prompted to enter your authentication token for the API endpoint. The token will be stored in an environment variable for future use. Once the script is running, you can view the interactive visualizations in a web browser by navigating to http://localhost:8050/. The visualizations can be filtered by date range using the date picker components.

Code explanation:
The code starts by importing the required libraries and defining the current date and the date 30 days ago. It then retrieves the user input token from an environment variable or prompts the user to enter it. The script then defines the API endpoint and headers and creates a GraphQL query to retrieve the desired data. The query is sent to the API endpoint using the requests library, and the result is transformed into a Pandas DataFrame.

The script then creates several visualizations using the Dash framework. The visualizations include graphs of the count of HTTP response status codes (2xx, 3xx, 4xx, and 5xx), the count of requests by remote address and request URI, and the average request time and upstream response time. The visualizations can be filtered by date range using the date picker components.

The script uses Dash's callback mechanism to update the visualizations based on the selected date range. The callbacks use the Pandas DataFrame to filter the data and generate the appropriate graphs. The script also creates tables to display the top 5 remote addresses and request URIs by number of accesses. Finally, the script runs the Dash app and starts the web server.
