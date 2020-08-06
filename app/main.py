# for file reading
import base64
import datetime
import io

# for creating the new total_score.xlsx
import create_total_score

# for auth
import dash_auth
from flask import Flask 

# for downloading excel file
import dash_table_experiments as dte
from flask import send_file
import zipfile

# for turning excel into csv
import csv
import xlrd
import sys

# for app
import os
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
import dash

# for adding basic Auth 
VALID_USERNAME_PASSWORD_PAIRS = {
    'mit': 'solve'
}

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}

app = Flask(__name__) 

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server # the Flask app
auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)



# Creating the graph 
xls_file_total_score = pd.ExcelFile('total_score.xlsx')
df_total_score = xls_file_total_score.parse('Sheet1')
# list of solvers
Solvers = list(df_total_score.columns[1:])
# List of mentors
Mentors = list(df_total_score["Org_y"])

# Sort total score df to top 5 for initial selected solver -> Solvers[0]
# sorted_df = df_total_score.sort_values(Solvers[0], ascending=False)
#print(cropped_total_dcore_df)

# bar graph of total score for a specific solver
total_fig = px.bar(df_total_score.sort_values(Solvers[0], ascending=False)[:5], x=Solvers[0], 
y="Org_y", labels = {'Org_y':'MENTOR',Solvers[0]:'Total Score'})
total_fig.update_layout(yaxis={'categoryorder':'total ascending'})
# Format the bar graph
total_fig.update_layout(
    autosize=True,
    # width=700,
    height=500,
    margin=dict(
        l=50,
        r=50,
        b=100,
        t=100,
        pad=4
    )
    #paper_bgcolor="LightSteelBlue",
)

# Getting first Solver Table from dropdown bar
solver_needs_df = pd.read_csv("unused_files/excel_to_csv/solver_team_data.csv")
selected_solver_row_info = solver_needs_df[solver_needs_df['Org']==Solvers[0]].dropna(axis='columns')
selected_solver_row_info_list = list(solver_needs_df[solver_needs_df['Org']==Solvers[0]].dropna(axis='columns'))

# Getting first Mentor Table - will be blank initially
mentor_data_df = pd.read_csv("unused_files/excel_to_csv/partner_data.csv")
selected_mentor_row_info = mentor_data_df[mentor_data_df['Org']==Mentors[0]].dropna(axis='columns')
selected_mentor_row_info_list = list(mentor_data_df[mentor_data_df['Org']==Mentors[0]].dropna(axis='columns'))


# Creates a dictionary of all the Solver info to put in the options of selected_solver_table
selected_solver_row_list = []
for col in selected_solver_row_info:
    ind_row_dict = {}
    ind_row_dict["label"] = col
    ind_row_dict["value"] = selected_solver_row_info[col]
    selected_solver_row_list.append(ind_row_dict)


# Creates a dictionary to put all Solvers as options of drop down menu
solver_list_dict = []
for solver in Solvers:
    ind_solver_dict = {}
    ind_solver_dict["label"]=solver
    ind_solver_dict["value"]=solver
    solver_list_dict.append(ind_solver_dict)

# Method that generates tables
# Used to for the selected_solver_table and clicked_on_mentor_table
def generate_table(dataframe, max_rows=10):
    return html.Table([
        html.Thead(
            html.Tr([html.Th(col) for col in dataframe.columns])
        ),
        html.Tbody([
            html.Tr([
                html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
            ]) for i in range(min(len(dataframe), max_rows))
        ])
    ])


# This allows the input excel file to be turned into csv files which will be used
# to calculate the information required for pairing
def ExceltoCSV(excel_file, csv_file_base_path, csv_folder = "uploaded_excel_to_csv/"):
    """
    inputs:
    Excel file, str - name of the original file
    csv_file_base_path, str - folder location where each file will be stored
    excel_folder, str - a folder with this name will be created in csv_base_file_path with sheet names
                        with excel file. If excel file has sheets then each sheet will be stored as
                        a seperte csv file

    """    

    if not os.path.isdir(csv_file_base_path+csv_folder): 
        os.mkdir(csv_file_base_path+csv_folder)
    full_path = csv_file_base_path+csv_folder
    workbook = xlrd.open_workbook(excel_file)

    for sheet_name in workbook.sheet_names():
        print('processing - ' + sheet_name)
        worksheet = workbook.sheet_by_name(sheet_name)
        csv_file_full_path = full_path + sheet_name.lower().replace(" - ", "_").replace(" ","_") + '.csv'
        csvfile = open(csv_file_full_path, 'w',encoding='utf-8')
        writetocsv = csv.writer(csvfile, quoting = csv.QUOTE_ALL, )
        for rownum in range(worksheet.nrows):
            writetocsv.writerow(
    #                 list(x.encode('utf-8') if type(x) == type(u'') else x for x in worksheet.row_values(rownum)
                    worksheet.row_values(rownum)
                )
            
        csvfile.close()
        print( "{} has been saved at {}".format(sheet_name, csv_file_full_path))


# Method used to parse files from upload button
def parse_contents(contents, filename, date):
    '''
    contents - contents of the file being uploaded
    filename - name of the file being uploaded
    date - time the file is uploaded

    This method will take in the excel file that is
    uploaded and will create csv files of each sheet
    in the directory 'uploaded_excel_to_csv' which is 
    in the root directory

    It also has to potential to print out sheets that
    are uploaded
    '''
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            return html.Div([
            'Please upload an excel sheets.'
        ])
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])
    ExceltoCSV(excel_file=filename , csv_file_base_path ="" )
    # Returns an html table of the df to be printed currently
    # return html.Div([
    #     html.H5(filename),
    #     dash_table.DataTable(
    #         data=df.to_dict('records'),
    #         columns=[{'name': i, 'id': i} for i in df.columns]
    #     ),
    # ])
    return None



# APP LAYOUT
app.layout = html.Div(children=[
    html.H1(
        children='MIT SOLVE',
        style={
            'textAlign': 'center'
            
        }
    ),

    # Upload files
    dcc.Upload(
        id='upload-data',
        children=html.Button('Upload Excel File'),
        style={
            'height': '60px',
            'textAlign': 'center',
        },
        # Allow multiple files to be uploaded
        multiple=True
    ),

    # Download all excel files
    html.Div(children=[
        html.A(html.Button('Download All Excel Files'), href="/download_all/",
        ),
    ],
    style={
        'height': '60px',
        'textAlign': 'center',
    }),

    # Drop down menu
    html.Label('Select a Solver'),
        dcc.Dropdown(
            id='Solver_dropdown',
            options= solver_list_dict,
            value = solver_list_dict[0]['value'], 
           ),

    html.P(children=html.Br(), style={'textAlign': 'center'}),
    html.P(children=html.Br(), style={'textAlign': 'center'}),
    html.H2(children='Total Outputs Graph', style={'textAlign': 'center'}),

    # Display graph for total score
    dcc.Graph( 
        id='output_bargraph',
        figure= total_fig
    ),

    # Comment box
    # dcc.Textarea(
    #     id='textarea-for-comments',
    #     value='Textarea for comments',
    #     style={'width': '50%', 'height': 200, 'Align-items': 'center'},
    # ),

    # Generates the table for the selected solver from the dropdown
    html.H4(children='Selected Solver Information',style={'textAlign': 'center'}),
    dash_table.DataTable(
        id='selected_solver_table',
        columns=[{"name": i, "id": i} for i in selected_solver_row_info.columns],
        data=selected_solver_row_info.to_dict('records'),
        style_cell={
        'whiteSpace': 'normal',
        'height': 'auto',
        'textAlign': 'center',
        'font_family': 'helvetica',
        'font_size': '20px',
        },
        style_header={
        'backgroundColor': 'rgb(30, 30, 30)',
        'color': 'white',
        },
    ),


    html.P(children=html.Br(), style={'textAlign': 'center'}),
    html.P(children=html.Br(), style={'textAlign': 'center'}),

    # Generates table for the clicked on mentor
    html.H4(children='Clicked on Mentor Information',style={'textAlign': 'center'}),
    dash_table.DataTable(
        id='clicked_on_mentor_table',
        columns=[{"name": i, "id": i} for i in selected_mentor_row_info.columns],
        data=selected_mentor_row_info.to_dict('records'),
        style_cell={
        'whiteSpace': 'normal',
        'height': 'auto',
        'textAlign': 'center',
        'font_family': 'helvetica',
        'font_size': '20px',
        
        },
        style_header={
        'backgroundColor': 'rgb(30, 30, 30)',
        'color': 'white',
        },
    ),

    html.P(children=html.Br(), style={'textAlign': 'center'}),
    html.P(children=html.Br(), style={'textAlign': 'center'}),
    html.P(children=html.Br(), style={'textAlign': 'center'}),
    html.P(children=html.Br(), style={'textAlign': 'center'}),

    # printing df from uploaded file
    html.Div(id='output-data-upload'),

])

# This method allows for you to download all of the generated excel files as a zip file
# Files are challenge_match.xlsx, geo_match.xlsx, needs_match.xlsx, stage_match.xlsx,
# total_score_from_upload.xlsx
@app.server.route('/download_all/')
def download_all():
    zipf = zipfile.ZipFile('app/MIT_Solve_Excel_Files.zip','w', zipfile.ZIP_DEFLATED)
    for root,dirs, files in os.walk('MIT_SOLVE_downloadable_excel_files/'):
        for file in files:
            zipf.write('MIT_SOLVE_downloadable_excel_files/'+file)
    zipf.close()
    return send_file('MIT_Solve_Excel_Files.zip',
            mimetype = 'zip',
            attachment_filename= 'MIT_Solve_Excel_Files.zip',
            as_attachment = True)


# This method will update the table displaying more information
# on any mentor that is clicked on in the graph
@app.callback(
    dash.dependencies.Output('clicked_on_mentor_table', 'data'),
    [dash.dependencies.Input('output_bargraph', 'clickData')])
def display_click_data(clickData):
    if clickData != None:
        mentor_name = clickData['points'][0]['label']
        mentor_data_df = pd.read_csv("uploaded_excel_to_csv/partner_data.csv")
        selected_mentor_row_info = mentor_data_df[mentor_data_df['Org']==mentor_name].dropna(axis='columns')
        generate_table(selected_mentor_row_info)  
        return selected_mentor_row_info.to_dict('records')


# This method updates the table displaying more information on a solver
# everytime a new solver is selected from the dropdown
@app.callback(
    dash.dependencies.Output('selected_solver_table', 'data'),
    [dash.dependencies.Input('Solver_dropdown', 'value')])
def update_solver_table(value):
    try:
        solver_needs_df = pd.read_csv("uploaded_excel_to_csv/solver_team_data.csv")
        selected_solver_row_info = solver_needs_df[solver_needs_df['Org']==value].dropna(axis='columns')
        generate_table(selected_solver_row_info)  
        return selected_solver_row_info.to_dict('records')
    except:
        solver_needs_df = pd.read_csv("unused_files/excel_to_csv/solver_team_data.csv")
        selected_solver_row_info = solver_needs_df[solver_needs_df['Org']==value].dropna(axis='columns')
        generate_table(selected_solver_row_info)  
        return selected_solver_row_info.to_dict('records')


# This method updates the graph when a new solver is selected from the dropdown
@app.callback(
    dash.dependencies.Output('output_bargraph', 'figure'),
    [dash.dependencies.Input('Solver_dropdown', 'value')])
def update_graph_from_solver_dropdown(value):
    # create new df here of uploaded info
    try:
        xls_file_total_score = pd.ExcelFile('MIT_SOLVE_downloadable_excel_files/total_score_from_upload.xlsx')
        uploaded_df_total_score = xls_file_total_score.parse('Sheet1')
    except:
        uploaded_df_total_score = df_total_score
    # Sort and crop top 5 values for new selected solver
    total_fig = px.bar(uploaded_df_total_score.sort_values(value, ascending=False)[:5], x=value, 
    y="Org_y", labels = {'Org_y':'MENTOR',value:'Total Score'})
    total_fig.update_layout(yaxis={'categoryorder':'total ascending'})
    return total_fig


# This method will create csv files for each sheet
# from the uploaded file. The file must be in the format of
# a singular excel file consisting of 2 sheets, which are the 
# partner_data and solver_team_data
@app.callback(
    dash.dependencies.Output('output-data-upload', 'children'),
    [dash.dependencies.Input('upload-data', 'contents')],
    [dash.dependencies.State('upload-data', 'filename'),
    dash.dependencies.State('upload-data', 'last_modified')])
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        # list_of_uploaded_files is fully available here
        new_total_score = create_total_score.create_total_score_excel()
        new_total_score.insert(0, "Partners", Mentors, True)
        children = [
            # parse_contents prints out the files as tables
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        
        # Returns an html table of the df to be printed currently
        return html.Div([
            html.H5("Calculate Total Score Table"),
            dash_table.DataTable(
                data=new_total_score.to_dict('records'),
                columns=[{'name': item, 'id': item} for item in new_total_score.columns]
            ),
        ])


# This callback will create a new bar chart with the data from the uploaded excel
# files instead of the preloaded old excel files
@app.callback(
    dash.dependencies.Output('Solver_dropdown', 'value'),
    [dash.dependencies.Input('upload-data', 'contents')],
)
def point_graph_to_uploaded_files(contents):

    try:
        # create new df from uploaded file
        xls_file_total_score = pd.ExcelFile('MIT_SOLVE_downloadable_excel_files/total_score_from_upload.xlsx')
        uploaded_df_total_score = xls_file_total_score.parse('Sheet1')
        # Create new graph with uploaded data instead of hardcoded
        new_solvers = list(uploaded_df_total_score.columns[1:])
        return new_solvers[8]
    except:
        return Solvers[0]
    


if __name__ == '__main__':
    app.run_server(debug=True)