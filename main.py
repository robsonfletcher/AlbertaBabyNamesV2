import pandas as pd
import plotly.express as px  # (version 4.7.0 or higher)
from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import Levenshtein

app = Dash(
    title="Alberta Baby Names Bot",
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ],
)

# -- Import data (importing csv into pandas)

df = pd.read_csv("https://raw.githubusercontent.com/robsonfletcher/AlbertaBabyNamesBot/49b1a6afb9a3c2e3a9ab7377a94b3248b99bcc88/abbabynames2022.csv", encoding="latin1")

all_names = df['name'].unique().tolist()


def suggest_similar_names(input_name, name_list, num_suggestions):
    # Create a list of tuples (name, distance)
    name_distances = [(name, Levenshtein.distance(input_name, name)) for name in name_list]

    # Sort the list by distance
    name_distances.sort(key=lambda x: x[1])

    # Return the top N names with the lowest distance
    return [name for name, distance in name_distances[:num_suggestions]]

# ------------------------------------------------------------------------------
# App layout
app.layout = html.Div([
    html.H1("Alberta Baby Names Bot", style={'text-align': 'center'}),
    html.H3("Explore baby-name trends over the past 42 years:", style={'text-align': 'left'}),
    html.Br(),
    # html.H4("Enter the name you want to look up:"),
    # html.Br(),

    dcc.Input(
        id='my_txt_input',
        type='text',
        debounce=True,  # changes to input are sent to Dash server only on enter or losing focus
        pattern=r"^[A-Za-z].*",  # Regex: string must start with letters only
        spellCheck=True,
        placeholder="Enter name here",
        inputMode='latin-name',  # provides a hint to browser on type of data that might be entered by the user.
        name='text',  # the name of the control, which is submitted with the form data
        # list='browser',  # identifies a list of pre-defined options to suggest to the user
        n_submit=0,  # number of times the Enter key was pressed while the input had focus
        n_submit_timestamp=-1,  # last time that Enter was pressed
        autoFocus=True,  # the element should be automatically focused after the page loaded
        n_blur=0,  # number of times the input lost focus
        n_blur_timestamp=-1,  # last time the input lost focus.
        # selectionDirection='', # the direction in which selection occurred
        # selectionStart='',     # the offset into the element's text content of the first selected character
        # selectionEnd='',       # the offset into the element's text content of the last selected character
    ),

    html.Br(),
    html.Br(),

    html.H6("Note: Search is case-sensitive."),
    # html.H6("(For example: Results for 'Mckenzie' and 'McKenzie' will be different as they are considered different names.)"),

    html.Br(),

    html.H4(id='output_container', children=[]),

    html.Br(),

    html.H4("Total babies (1980 to 2022):"),

    html.Br(),

    html.H5(id='output_boy_total', children=[]),
    html.H5(id='output_girl_total', children=[]),

    dcc.Graph(id='my_line_chart', figure={}),

    html.Div(id='output_suggestion_buttons', children=[]),

    html.Br(),

    html.H4(id='output_container2', children=[]),

    dcc.Graph(id='my_line_chart2', figure={}),

    html.H5(id='output_boy_rank_high', children=[]),
    html.Br(),
    html.H5(id='output_boy_rank_low', children=[]),
    html.Br(),
    html.H5(id='output_girl_rank_high', children=[]),
    html.Br(),
    html.H5(id='output_girl_rank_low', children=[]),

    html.Br(),

    html.Hr(),

    html.H5('About the Baby Names Bot:'),

    html.Br(),

    dcc.Markdown("**• Created by [Robson Fletcher](https://mas.to/@robsonfletcher)**"),

    dcc.Markdown(
        "*• Data source: [Alberta Open Data - Frequency and Ranking of Baby Names by Year and Gender](https://open.alberta.ca/opendata/frequency-and-ranking-of-baby-names-by-year-and-gender)*")

])


# ------------------------------------------------------------------------------
# Connect the Plotly graphs with Dash Components

@app.callback(
    [Output(component_id='output_container', component_property='children'),
     Output(component_id='output_suggestion_buttons', component_property='children'),
     Output(component_id='output_boy_total', component_property='children'),
     Output(component_id='output_girl_total', component_property='children'),
     Output(component_id='my_line_chart', component_property='figure'),
     Output(component_id='output_container2', component_property='children'),
     Output(component_id='output_boy_rank_high', component_property='children'),
     Output(component_id='output_boy_rank_low', component_property='children'),
     Output(component_id='output_girl_rank_high', component_property='children'),
     Output(component_id='output_girl_rank_low', component_property='children'),
     Output(component_id='my_line_chart2', component_property='figure')],
    [Input(component_id='my_txt_input', component_property='value')],
    [State('my_txt_input', 'value')]
)
def update_graph(option_slctd, *args): # The function argument comes from the component property of the Input
    print(option_slctd)
    print(type(option_slctd))

    container = "Showing results for: {}".format(option_slctd)
    result = df.copy()
    suggestion_links = []
    top_similar_names_filtered = []

    top50 = suggest_similar_names(option_slctd, all_names, 50)

    alltime_name_count = pd.pivot_table(df, values='frequency', index='name', aggfunc='sum').sort_values(
        by='frequency', ascending=False)

    name_frequency_dict = {name: alltime_name_count.loc[name]['frequency'] for name in top50}

    top_similar_names = [name for name, frequency in
                         sorted(name_frequency_dict.items(), key=lambda x: x[1], reverse=True)[:10]]
    top_similar_names_filtered = [name for name in top_similar_names if name != option_slctd]

    suggestion_buttons = html.Div([html.H6('You might also try these similar names:'),
        dcc.RadioItems(options=top_similar_names_filtered, id='my-radio-btn',
                       inputStyle={"margin-left": "20px",
                                   "margin-right": "4px"})
    ])

    # This loop creates a set of tuples in the form of (0, '1st_rank_name'), (1, '2nd_rank_name'), etc.
    # It also creates an individual id for each one as 'suggestion-0', 'suggestion-1', etc.
    for i, name in enumerate(top_similar_names_filtered):
        suggestion_links.append(dcc.Link(name, href='#', className='name-suggestion', id=f'suggestion-{i}'))
        if i < len(top_similar_names_filtered) - 1:
            suggestion_links.append(html.Span(', '))

    # --------- FILTER THE DATA BASED ON USER INPUT ---------

    if isinstance(option_slctd, str):
        result = result[result["name"] == option_slctd.strip()]  # Kill trailing spaces on strings

    else:
        result = result[result["name"] == option_slctd]  # This mainly deals within initial "NoneType" for the variable

    # ---------- CALCULATIONS TO DETERMINE NAME TOTALS  --------- :

    result = result.sort_values(by=['sex', 'year'])
    result.reset_index(drop=True, inplace=True)

    result_boy = result[result['sex'] == 'Boy']
    result_girl = result[result['sex'] == 'Girl']

    total_boy = result_boy['frequency'].sum()
    total_girl = result_girl['frequency'].sum()

    container_boy_total = f" • Total boys named {option_slctd}: {total_boy}"
    container_girl_total = f" • Total girls named {option_slctd}: {total_girl}"

    # ----- CALCULATIONS TO DETERMINE NAME RANKS ----------:

    ranks_boy = result_boy[['year', 'year_rank']].copy()
    ranks_girl = result_girl[['year', 'year_rank']].copy()
    ranks_girl.reset_index(inplace=True)

    if not ranks_boy.empty:
        leastpop_boy_rank = ranks_boy['year_rank'].max()
        mostpop_boy_rank = ranks_boy['year_rank'].min()

        leastpop_boy_index = ranks_boy['year_rank'].idxmax()
        mostpop_boy_index = ranks_boy['year_rank'].idxmin()

        leastpop_boy_year = ranks_boy['year'].iloc[leastpop_boy_index]
        mostpop_boy_year = ranks_boy['year'].iloc[mostpop_boy_index]

    else:
        mostpop_boy_year = "N/A"
        mostpop_boy_rank = "N/A"
        leastpop_boy_year = "N/A"
        leastpop_boy_rank = "N/A"

    if not ranks_girl.empty:

        leastpop_girl_rank = ranks_girl['year_rank'].max()
        mostpop_girl_rank = ranks_girl['year_rank'].min()

        leastpop_girl_index = ranks_girl['year_rank'].idxmax()
        mostpop_girl_index = ranks_girl['year_rank'].idxmin()

        leastpop_girl_year = ranks_girl['year'].iloc[leastpop_girl_index]
        mostpop_girl_year = ranks_girl['year'].iloc[mostpop_girl_index]

    else:
        mostpop_girl_year = "N/A"
        mostpop_girl_rank = "N/A"
        leastpop_girl_year = "N/A"
        leastpop_girl_rank = "N/A"

    container2 = f"Popularity of {option_slctd}:"

    container2_boyrank_high = f" • Among boys, {option_slctd} was most popular as a name in {mostpop_boy_year}, when it ranked #{mostpop_boy_rank} out of all names that year."
    container2_boyrank_low = f" • Among boys, {option_slctd} was least popular as a name in {leastpop_boy_year}, when it ranked #{leastpop_boy_rank} out of all names that year."

    container2_girlrank_high = f" • Among girls, {option_slctd} was most popular as a name in {mostpop_girl_year}, when it ranked #{mostpop_girl_rank} out of all names that year."
    container2_girlrank_low = f" • Among girls, {option_slctd} was least popular as a name in {leastpop_girl_year}, when it ranked #{leastpop_girl_rank} out of all names that year."

    # Plotly Express

    fig = px.line(data_frame=result,
                  x="year",
                  y="frequency",
                  color='sex',
                  # title=f'Babies named {option_slctd} born by year',
                  markers=True,
                  color_discrete_map={"Boy": "blue", "Girl": "red"},
                  labels={"sex": "Sex", "frequency": "Number of babies", "year": "Year"},
                  template="plotly_white"
                  )

    fig.update_layout(dragmode=False)

    fig2 = px.line(data_frame=result,
                   x="year",
                   y="year_rank",
                   color='sex',
                   # title=f'Rank of {option_slctd}, by year',
                   markers=True,
                   color_discrete_map={"Boy": "blue", "Girl": "red"},
                   labels={"sex": "Sex", "year_rank": "Rank", "year": "Year"},
                   )

    fig2.update_layout(dragmode=False)
    fig2.update_yaxes(autorange="reversed")

    return container, suggestion_buttons, container_boy_total, container_girl_total, fig, container2, container2_boyrank_high, container2_boyrank_low, container2_girlrank_high, container2_girlrank_low, fig2


# Define a callback to update the input name when a suggestion is clicked
@app.callback(
    Output(component_id='my_txt_input', component_property='value'),
    Input(component_id='my-radio-btn', component_property='value')
)
def update_input_name1(chosen_name):
    return chosen_name

# ------------------------------------------------------------------------------
if __name__ == '__main__':
    # app.run(host="0.0.0.0", port=5000)  # For localhost testing only
    app.run_server()
