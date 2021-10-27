from django.shortcuts import render

from upload.models import DataPointsVisit, DatamodelAttribute, DatamodelCode, GeneticJson

from .serializers import DataPointsVisitSerializer, GeneticJsonSerializer, DataPointsVisitSerializer_light

from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import api_view,  permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rest_framework.permissions import AllowAny

from django.contrib.auth.decorators import login_required
from django.http.response import JsonResponse, HttpResponse, HttpResponseForbidden

from django.contrib.auth import authenticate

import re
import os

from django.core.cache import cache

from django.conf import settings

from django.core import serializers

import pandas as pd
import numpy as np
import os
import json
import statistics, math
import copy
from scipy import stats
import requests
from .models import UserSession
from datetime import datetime
import traceback
from django.db.models import Max


import plotly.graph_objs as go
from plotly.utils import PlotlyJSONEncoder
import time

#Code by sreeni: TO load the data into RAM before performing other actions.
#Helps in accessing the data faster.
Mdata = DataPointsVisit.objects.all()
if Mdata.exists():

    Mdataall = DataPointsVisitSerializer(Mdata, many=True)
    Mdataframe = pd.read_json(json.dumps(Mdataall.data))
    print(Mdataframe.head())
    maxvisit = Mdataframe.VISIT.dropna().unique().tolist()


colors = ['#ffffff', '#808080', 'blue', 'green', 'orange', 'red', 'yellow', '#0075dc', '#2bce48', '#ff5005',
          'yellow', '#ff0010', '#ffff00', '#5ef1f2', '#f0a3ff',
          '#993f00', '#4c005c', '#191919', '#005c31', '#ffcc99', '#94ffb5', '#8f7c00', '#9dcc00', '#c20088',
          '#003380', '#ffa405', '#ffa8bb', '#426600', '#00998f', '#e0ff66', '#740aff', '#990000', '#ffff80',
          '#808080', '#808080', '#808080', '#808080', '#808080', '#808080', '#808080', '#808080', '#808080',
          '#808080', '#808080', '#808080', '#808080', '#808080', '#808080', '#808080', '#808080', '#808080',
          '#808080', '#808080', '#808080', '#808080', '#808080', '#808080', '#808080', '#808080', '#808080',
          '#808080', '#808080', '#808080', '#808080', '#808080', '#808080', '#808080', '#808080', '#808080',
          '#808080', '#808080', '#808080', '#808080', '#808080', '#808080', '#808080', '#808080', '#808080',
          '#808080', '#808080', '#808080', '#808080', '#808080', '#808080', '#808080', '#808080', '#808080']
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


'''

HELPER METHODS

'''


def get_fig_scatter(plot):
    if plot['titleC']=='PATIENTS':
        mode = 'lines'

        legend = False
    else:
        mode = 'markers'
        legend = True
    fig =  {
        'data':
        [
            go.Scatter(
                name=trace['name'],
                x=trace['X'],
                y=trace['Y'],
                text=trace['label'],
                mode=mode,
                marker={'line': {'width': 0.7, 'color': 'gray'}, 'color': trace['C']},
                legendgroup=trace['name'],
                showlegend = True
            )
            for trace in plot['traces']
        ] +
        [
            go.Scatter(
                name=trace['name']+'_fit',
                x=trace['X'],
                y=trace['Y'],
                mode='lines',
                line = {'color': trace['C']},
                showlegend=False,
                legendgroup=trace['name']
            )
            for trace in plot['fits']
        ],
        'layout': go.Layout(
            clickmode='event'
        )
    }
    fig['data'][1]['mode']='markers'
    return fig


def get_fig_histo(plot, bins, norm, stack):
    traces  = plot['traces']
    # to API
    if bins>0:

        datmin = float(min(traces[0]['X']))
        datmax = float(max(traces[0]['X']))
        #print(traces)
        datrange = datmax - datmin
        binwidth = datrange / bins
    else:
        binwidth=datmin=datmax=0

    if 'norm' in norm:
        norm = 'percent'
    else:
        norm = ''

    return {
        'data': [
            go.Histogram(
                name=trace['name'],
                x=trace['X'],
                text=trace['label'],
                xbins=dict(
                    start=datmin,
                    end=datmax,
                    size=binwidth),
                autobinx=True,
                histnorm=norm,
                marker={'line': {'width': 0.7, 'color': 'gray'}, 'color': trace['C']},
            )
            for trace in traces
        ],
        'layout': go.Layout(
            barmode='overlay',
            clickmode = 'event'
        )
    }


def get_fig_bar(plot, norm, stack):
    traces=plot['traces']
    if 'norm' in norm:
        for t in reversed(traces):
            t.update(Y=[y / traces[0]['Y'][i] * 100 for i, y in enumerate(t['Y'])])

    fig = {
         'data': [
             go.Bar(
                 name=trace['name'],
                 x=trace['X'],
                 y=trace['Y'],
                 marker={'line': {'width': 0.7, 'color': 'gray'}, 'color': trace['C']}
             )
             for i, trace in enumerate(traces)
         ],
         'layout': go.Layout(
             clickmode='event+select'
         )
    }

    if 'stack' in stack:
        fig['layout']['barmode']='stack'
        fig['data'][0]['base']=0
        fig['data'][1]['base']=0
    else:
        fig['layout']['barmode']='group'

    return fig



def get_fig(plot, controls):# type, item1, item2, item3, bins, stack, regression, legend, norm, filters):

    ctrl = json.loads(controls)

    type = ctrl['type']
    bins = ctrl['bins']
    norm = ctrl['norm']
    stack = ctrl['stack']
    regression = ctrl['fit']
    legend = ctrl['legend']

    if plot is None:
        return {}
    plot = json.loads(plot)
    if plot['traces']==[]:
        return {}

    print(plot['traces'])

# --- get specific graph depending on type
    if type == 1:
        fig = get_fig_scatter(plot)
    if type == 2:
        fig = get_fig_histo(plot, bins, norm, stack)
    if type == 3:
        fig = get_fig_bar(plot, norm, stack)
    if type == 4:
        fig = get_fig_scatter(plot)


# --- set common layout
    fig['layout']['margin']={'l': 40, 'b': 40, 't': 20, 'r': 10}
    fig['layout']['hovermode']='closest'
    fig['layout']['showlegend']=('legend' in legend)
    fig['layout']['dragmode'] = 'select'
    fig['layout']['legend']['uirevision']='dataset'
    #fig['layout']['uirevision']='dataset'
    fig['layout']['yaxis']['uirevision']='dataset'
    fig['layout']['xaxis']['uirevision']='dataset'
    #fig['layout']['selectionrevision']=True

    if len(plot['traces'])>3:
        for i in range(len(plot['traces']) - 2):
            fig['data'][i+2]['marker']['opacity']=0.7
    #print(f"PLOT TRACES: {plot['traces']}")
    if len(plot['traces'][1]['C']) > 0 and plot['traces'][1]['C'][0]!='#':
        fig['data'][1]['marker']['colorscale'] = 'Jet'
        fig['data'][1]['marker']['colorbar'] = {'title': {'text': plot['titleC'], 'side': 'right'}, 'thickness': 10}

    fig['layout']['xaxis']['title'] = plot['titleX']
    fig['layout']['yaxis']['title'] = plot['titleY']

    if plot['box'] is None:
        fig['layout']['shapes'] = []
    else:
        fig['layout']['shapes'] = [{**plot['box'], 'type': 'rect', 'line': {'width': 1, 'dash': 'dot',  'color': 'red'}}]
    #print(f"FIGURE {fig}")
    return fig


def meanTS(ts):
    return (ts.mean())

def getdata_append_color(Mdf, df, attC, Dt):
    #creating the dataframe by filtering out for the requested colorM
    Mdf_fallback = Mdf.copy()
    df_fallback = df.copy()





    dfC = Mdf.loc[Mdf['ATTRIBUTE'] == attC]
    
    #Fail proof case if in case the data frame is empty for selected color
    if dfC.empty:
        df.loc[:,'COLOR'] = None
        return df[['PID', 'VISIT', 'FOLLOWUP', 'TIMESTAMP', 'VALUE', 'COLOR']]

    ## PANDAS LOGIC
    dfC.loc[dfC.VISIT == -1, ['TIMESTAMP', 'VISIT']] = None
    df = pd.merge(df, dfC, on='PID', how='left', suffixes=('', '_C'))
    
    df.loc[:, 'DT'] = abs(df.TIMESTAMP - df.TIMESTAMP_C)
    if not df.filter(regex='^VISIT_',axis=1).isna().any().any():
        df = df.sort_values(by=['DT']).groupby(['PID', 'VISIT', 'TIMESTAMP', 'VALUE'], as_index=False).first()
        if Dt == -1:
            df.loc[(df.iloc[:, 1] != df.iloc[:, 5]), 'VALUE_C'] = None
        else:
            df.loc[(abs(df.TIMESTAMP - df.TIMESTAMP_C)) > np.timedelta64(Dt, 'D'), 'VALUE_C'] = None
    df = df.rename(columns={'VALUE_C': 'COLOR'})
    try:
        df['COLOR'] = df['COLOR'].astype(str).astype(float)
        return df[['PID', 'VISIT', 'FOLLOWUP', 'TIMESTAMP', 'VALUE', 'COLOR']]
    except:
        return getdata_append_color(Mdf_fallback, df_fallback, attC, 3000)

    

    

def getdata_X(main_data_frame, attX, attC, Dt):

    ## Pandas Logic
    #Filtering out from the main dataframe for requested attribute, modification by Sreeni...
    eav = main_data_frame.filter(['PID', 'VISIT','TIMESTAMP','VALUE'], axis=1)
    df = main_data_frame.loc[main_data_frame['ATTRIBUTE'] == attX]
    if len(df) == 0:
        return pd.DataFrame([],columns=['PID', 'VISIT','FOLLOWUP' ,'TIMESTAMP', 'VALUE', 'COLOR'])
    df.loc[df.VISIT == -1, ['TIMESTAMP', 'VISIT']] = None
    df['FOLLOWUP'] = df.TIMESTAMP - df.PID.replace(eav[eav.PID.isin(df.PID.unique().tolist())].replace(pd.to_datetime('1900-01-01'), pd.NaT).sort_values(by=('TIMESTAMP')).groupby('PID').first()['TIMESTAMP'].to_dict())
    df = getdata_append_color(main_data_frame, df[['PID', 'VISIT', 'FOLLOWUP', 'TIMESTAMP', 'VALUE']], attC, Dt)
   
    return df

def getdata_T(main_data_frame, attT, attY, attC, Dt):

    #Filtering out from the main dataframe for requested attribute, modification by Sreeni...
    dfT = main_data_frame.loc[main_data_frame['ATTRIBUTE'] == attT] 
    dfY = main_data_frame.loc[main_data_frame['ATTRIBUTE'] == attY] 

    if len(dfT) == 0 or len(dfY) == 0 :
        return pd.DataFrame([], columns=['PID', 'VISIT', 'FOLLOWUP', 'TIMESTAMP', 'VALUE', 'COLOR'])

    eav = main_data_frame.filter(['PID', 'VISIT','TIMESTAMP','VALUE'], axis=1)
    dfT.loc[dfT.VISIT == -1, ['TIMESTAMP', 'VISIT']] = None
    dfY.loc[dfY.VISIT == -1, ['TIMESTAMP', 'VISIT']] = None
    df = pd.merge(dfT, dfY, on='PID', how='inner')
    if not df.filter(regex='^VISIT_',axis=1).isna().any().any():
        if Dt == -1:
            df = df[df.iloc[:, 1] == df.iloc[:, 4]]
        else:
            df = df[(abs(df.TIMESTAMP_x - df.TIMESTAMP_y)) <= np.timedelta64(Dt, 'D')]

    df['time'] = df.TIMESTAMP_y - df.VALUE_x.astype('datetime64[ns]')
    df['time'] = df.time / np.timedelta64(1, 'Y')
    df['VISIT'] = df.filter(regex='^VISIT_',axis=1).apply(meanTS, axis=1).apply(np.floor).astype(object)
    df['TIMESTAMP'] = df.filter(regex='^TIMESTAMP_',axis=1).apply(meanTS, axis=1).astype('datetime64[ns]')
    df['VALUE'] = df[['time', 'VALUE_y']].values.tolist()
    df['VALUE'] = df['VALUE'].map(tuple)
    
    df['FOLLOWUP'] = df.TIMESTAMP - df.PID.replace(eav[eav.PID.isin(df.PID.unique().tolist())].replace(pd.to_datetime('1900-01-01'), pd.NaT).sort_values(by=('TIMESTAMP')).groupby('PID').first()['TIMESTAMP'].to_dict())
    df = getdata_append_color(main_data_frame, df[['PID', 'VISIT', 'FOLLOWUP', 'TIMESTAMP', 'VALUE']], attC, Dt)

    return df


def getdata_XY(main_data_frame, attX, attY, attC, Dt):

    #Filtering out from the main dataframe for requested attribute, modification by Sreeni...
    if not attX:
        dfX = main_data_frame.filter(['PID', 'VISIT','TIMESTAMP','VALUE'], axis=1)
    if not attY:
        dfY = main_data_frame.filter(['PID', 'VISIT','TIMESTAMP','VALUE'], axis=1)
    ## PANDAS Logic
    dfX = main_data_frame.loc[main_data_frame['ATTRIBUTE'] == attX] 
    dfY = main_data_frame.loc[main_data_frame['ATTRIBUTE'] == attY] 
    eav = main_data_frame.filter(['PID', 'VISIT','TIMESTAMP','VALUE'], axis=1)
    

    if len(dfX) == 0 or len(dfY) == 0:
        return pd.DataFrame([], columns=['PID', 'VISIT', 'FOLLOWUP', 'TIMESTAMP', 'VALUE', 'COLOR'])

    dfX.loc[dfX.VISIT == -1, ['TIMESTAMP', 'VISIT']] = None
    dfY.loc[dfY.VISIT == -1, ['TIMESTAMP', 'VISIT']] = None
    if dfX.VISIT.notna().any() and dfY.VISIT.notna().any(): #If both columns are dynamic we care for temporal matching
        if Dt == -1:
            df = pd.merge(dfX, dfY, on=['PID', 'VISIT'], how='inner')
        else:
            df = pd.merge(dfX, dfY, on='PID', how='inner')
            df = df[(abs(df.TIMESTAMP_x - df.TIMESTAMP_y)) <= np.timedelta64(Dt, 'D')]
    else:
        df = pd.merge(dfX, dfY, on='PID', how='inner')
    df['VISIT'] = df.filter(regex='^VISIT_',axis=1).apply(meanTS, axis=1).apply(np.floor).astype(object)
    df['TIMESTAMP'] = df.filter(regex='^TIMESTAMP_',axis=1).apply(meanTS, axis=1).astype('datetime64[ns]')
    df['VALUE'] = df[['VALUE_x', 'VALUE_y']].values.tolist()
    df['VALUE'] = df['VALUE'].map(tuple)
    df['FOLLOWUP'] = df.TIMESTAMP - df.PID.replace(eav[eav.PID.isin(df.PID.unique().tolist())].replace(pd.to_datetime('1900-01-01'), pd.NaT).sort_values(by=('TIMESTAMP')).groupby('PID').first()['TIMESTAMP'].to_dict())
    
    df =  getdata_append_color(main_data_frame, df[['PID', 'VISIT', 'FOLLOWUP', 'TIMESTAMP', 'VALUE']], attC, Dt)

    return df


def getbinning(df,type):
    # Estimate new start settings for bin slider, if type is histogram
    if (type == 2) and (len(df) > 0):
        ## sanitize for date
        '''
        for index, row in df.iterrows():
            if "00:00:00" in row['VALUE']:
                row['VALUE'] = datetime.strptime(row['VALUE'], '%Y-%m-%d %H:%M:%S').timestamp()
                #print(row['VALUE'])
        found = df[df['VALUE'].str.contains(':')]

        print(f"found: {found}")
        '''
        bin_width = 3.5 * statistics.stdev(df.VALUE.astype(float)) / math.pow(len(df), 1 / 3)
        bin_range = df['VALUE'].astype(float).max() - df['VALUE'].astype(float).min()
        bins = math.trunc(bin_range / bin_width)
        bin_max = math.trunc(df['VALUE'].nunique())
    else:
        bins = 0
        bin_max = 2
    return bins, bin_max

def getviscount(df):
    # Count number of Visits per patient and total number of patients
    vis_per_pid = df.sort_values(by=['VISIT','PID']).set_index(['VISIT','PID']).count(level='PID')
    vis_per_pid = vis_per_pid.reset_index().sort_values(by=['PID','TIMESTAMP']).set_index(['PID','TIMESTAMP']).count(level='TIMESTAMP')['FOLLOWUP'].tolist()
    pid_total = df.set_index(['PID','VISIT']).count(level='PID').count(axis='rows').loc['TIMESTAMP']
    vis_per_pid.append(pid_total)
    return vis_per_pid


### FILTERING #########

def filter_apply(constraints, session):
    '''Updated by Sreeni: Code update to check for the common data beetween the constraints'''
    #print(f"SESSION_POPULATION: {session['population']}")
    if len(constraints) > 0:
        population = [[i[0], int(i[1])] for i in session['population']]
        for con in constraints.values():
            selection = list()
            if len(con['set']) == 0: #temporary if condition to handle the y-axis constraints in histogram. can be removed after update in front end
                selection = population
            else:
                selection = [pop for constraint in con['set'] for pop in population if pop == constraint]
                population = selection
        selection = [list(i) for i in selection]
    else:
        
        selection = [[i[0], int(i[1])] for i in session['population']]
        selection = [list(i) for i in selection]
    session['filter']['constraints'] = constraints
    session['filter']['selection'] = selection

    return session



### SUBGROUPS ############

def get_subgroup(att, lower, upper, cat_list):

    data_eav = copy.deepcopy(Mdataframe)
    eav_sub = data_eav.loc[data_eav['ATTRIBUTE'] == att]
    ## PANDAS Logic
    if len(eav_sub) ==0 :
        eav_sub = pd.DataFrame([], columns=['PID', 'VISIT', 'FOLLOWUP', 'TIMESTAMP', 'VALUE', 'COLOR'])
    
    if cat_list == None:
        eav_sub = eav_sub[
            eav_sub.VALUE.astype(float).ge(lower) &
            eav_sub.VALUE.astype(float).le(upper)
        ]
    else:
        values = model_codes[['Key', model_items.loc[att, 'Domain']]].dropna()
        keyval = dict(list(zip(values.iloc[:, 1], values.iloc[:, 0])))
        cat_list = [keyval.get(i) for i in cat_list]
        eav_sub = eav_sub[eav_sub.VALUE.astype(int).isin(cat_list)]

    sel = pd.DataFrame(
        eav_sub.sort_values(by=['PID', 'VISIT']).set_index(['PID', 'VISIT']).index.drop_duplicates().tolist(),
        columns = ['PID', 'VISIT']
    )
    sel = pd.concat([
        pd.DataFrame(
            pd.MultiIndex.from_product( [sel[sel.VISIT==-1].PID.unique(), maxvisit], names=['PID', 'VISIT'] ).tolist(),
            columns = ['PID', 'VISIT']
        ),
        pd.concat([
            sel[sel.VISIT!=-1],
            pd.DataFrame({'PID': sel[sel.VISIT!=-1].PID.unique(), 'VISIT': -1})
        ])
    ]).sort_values(by=['PID', 'VISIT']).drop_duplicates().set_index(['PID', 'VISIT']).index.tolist()
    sel = [list(i) for i in sel]

    return sel


def get_population():
    pop = eav.sort_values(by=['PID', 'VISIT']).set_index(['PID', 'VISIT']).index.drop_duplicates().tolist()
    pop = [list(i) for i in pop]
    return json.dumps(pop)

### MODEL #########

def get_humanreadable(att):
    if att in model_items.index:
        return model_items.loc[att, 'Attribute_Tooltip']
    else:
        return att
#    if att in ['', 'SUBGROUPS']:
#        return ''
#    else:
#        return model_items.loc[att, 'Attribute_Tooltip']


def get_selection(type): # rename to dropdown oder so , selection missverständlich mit subgroup
    if type=='categorical':
        sel = [['',''], ['SUBGROUPS', 'SUBGROUPS'], ['PATIENTS', 'PATIENTS']] + model_items[model_items.metatype == type][['Attribute', 'Attribute_Tooltip']].values.tolist()
    else:
        sel = [['','']] + model_items[model_items.metatype == type][['Attribute', 'Attribute_Tooltip']].values.tolist()



    # if thrd and (type=='categorical'):
    #     sel = [['',''], ['SUBGROUPS', 'SUBGROUPS']] + model_items[model_items.metatype == type][['Attribute', 'Attribute_Tooltip']].values.tolist()
    # else:
    #     sel = [['', '']] + model_items[model_items.metatype == type][['Attribute', 'Attribute_Tooltip']].values.tolist()
    return sel

'''
Decorators for authentification

'''

WITH_AUTH = settings.WITH_AUTH

def custom_permission_classes(permission_classes):
    def decorator(func):
        if WITH_AUTH:
            func.permission_classes = permission_classes
        return func
    return decorator

def use_token_auth(func):
    def wrapper(request, *args, **kwargs):
        if WITH_AUTH:
            t = request.COOKIES.get('idsn_access_token')
            if t is None:
                print("No token found")
                return HttpResponseForbidden()
            request.META['Authorization'] = "Token " + t
        return func(request, *args, **kwargs)
    return wrapper

    
'''
Decorator for debugging

'''
def print_request_data_to_file(func):
    def wrapper(request, *args,**kwargs):
        file = ""
        if isinstance(request.data, dict):
            data = request.data
        else:
            data = json.loads(request.data)

        ## Write data to a file 
        ## The exact file and 
        return func(request, *args,**kwargs)
    return wrapper


'''

API VIEWS

'''



@api_view(['POST'])
@use_token_auth
@custom_permission_classes([IsAuthenticated])
def filter_reset(request):
    if isinstance(request.data, dict):
        token = request.data['usertoken']
    else:
        token = json.loads(request.data)['usertoken']
    session_obj = UserSession.objects.filter(token=token)[0]

    session = json.loads(session_obj.session)
    constraints = {}
    session = filter_apply(constraints, session)
    session_obj.session = json.dumps(session)
    session_obj.save()
    return JsonResponse({'Message': 'Filter reset'})

@api_view(['POST'])
@use_token_auth
@custom_permission_classes([IsAuthenticated])
def filter_edit(request):
    #print(f"FILTER EDIT: {request.data}")
    if isinstance(request.data, dict):
        table = request.data['filter_table']
        token = request.data['usertoken']
    else:
        table = json.loads(request.data)['filter_table']
        token = json.loads(request.data)['usertoken']



    session_obj = UserSession.objects.filter(token=token)[0]
    session=json.loads(session_obj.session)
    constraints = {con['attribute']: con for con in table}
    for con in constraints.values():
        con.update({'set': get_subgroup(con['attribute'], con['lower'], con['upper'], con['list'])})
    session = filter_apply(constraints, session)
    session_obj.session = json.dumps(session)
    session_obj.save()
    constraints = [con for con in constraints.values()]
    #print(constraints)
    #print(constraints)
    return JsonResponse({'constraints':constraints})

@api_view(['POST'])
@use_token_auth
@custom_permission_classes([IsAuthenticated])
def filter_recall(request):
    if isinstance(request.data, dict):
        subgroup = request.data['subgroup']
        token = request.data['usertoken']
    else:
        subgroup = json.loads(request.data)['subgroup']
        token = json.loads(request.data)['usertoken']
    session_obj = UserSession.objects.filter(token=token)[0]
    session= json.loads(session_obj.session)
    constraints = session['subgroups'][subgroup]['constraints']
    session = filter_apply(constraints, session)
    session_obj.session = json.dumps(session)
    session_obj.save()
    constraints = [con for con in constraints.values()]
    #print(constraints)
    return JsonResponse({'constraints':constraints})

@api_view(['POST'])
@use_token_auth
@custom_permission_classes([IsAuthenticated])
def filter_concept(request):
    if isinstance(request.data, dict):
        concept = request.data['concept']
        token = request.data['usertoken']
    else:
        concept = json.loads(request.data)['concept']
        token = json.loads(request.data)['usertoken']
    session_obj = UserSession.objects.filter(token=token)[0]
    session = json.loads(session_obj.session)
    constraints = session['filter']['constraints']
    session['filter']['concept'] = concept
    session = filter_apply(constraints, session)
    session_obj.session = json.dumps(session)
    session_obj.save()
    constraints = [con for con in constraints.values()]
    return JsonResponse({'constraints': constraints})

@api_view(['POST'])
@use_token_auth
@custom_permission_classes([IsAuthenticated])
def filter_plot(request):
    #print(f"FILTER PLOT: {request.data}")

    if isinstance(request.data, dict):
        select = request.data['select']
        #print(select)
        pos = request.data['pos']
        token = request.data['usertoken']
    else:
        select = json.loads(request.data)['select']
        #print(select)
        pos = json.loads(request.data)['pos']
        token = json.loads(request.data)['usertoken']
    session_obj = UserSession.objects.filter(token=token)[0]
    session=json.loads(session_obj.session)
    filter = session['filter']['constraints']

    if True:#any(selects):
#        pos, select = next((i,sel) for i,sel in enumerate(selects) if sel is not None)
        controls = session['plots']['plot_' + str(pos)]['controls']
        if 'range' in select:
            filter[controls['attX']] = {
                "attribute": controls['attX'],
                "lower": select['range']['x'][0],
                "upper": select['range']['x'][1],
                "list": None,
                "set": get_subgroup(controls['attX'], select['range']['x'][0], select['range']['x'][1], None),
                "human_readable": get_humanreadable(controls['attX'])
            }
            if controls['attY']!='':
                filter[controls['attY']] = {
                    "attribute": controls['attY'],
                    "lower": select['range']['y'][0],
                    "upper": select['range']['y'][1],
                    "list": None,
                    "set": get_subgroup(controls['attY'], select['range']['y'][0], select['range']['y'][1], None),
                    "human_readable": get_humanreadable(controls['attY'])
                }
        else:
            filter[controls['attX']] = {
                "attribute": controls['attX'],
                "lower": None,
                "upper": None,
                "list": [i['x'] for i in select['points']],
                "set": get_subgroup(controls['attX'], None, None, [i['x'] for i in select['points']]),
                "human_readable": get_humanreadable(controls['attX'])
            }

    session = filter_apply(filter, session)
    session_obj.session = json.dumps(session)
    session_obj.save()

    filter = [con for con in filter.values()]
    return JsonResponse({'filter': filter})

@api_view(['POST'])
@use_token_auth
@custom_permission_classes([IsAuthenticated])
def subgroup_define(request):
    if isinstance(request.data, dict):
        name = request.data['name']
        token = request.data['usertoken']
    else:
        name = json.loads(request.data)['name']
        token = json.loads(request.data)['usertoken']

    session_obj = UserSession.objects.filter(token=token)[0]
    session = json.loads(session_obj.session)
    if name!='':
        session['subgroups'][name] = copy.deepcopy(session['filter'])

    session_obj.session = json.dumps(session)
    session_obj.save()

    return JsonResponse({'subgroup_define_output': [{'name': key, 'filterset': '', 'set': ''} for key in session['subgroups'].keys()]})

@api_view(['POST'])
@use_token_auth
@custom_permission_classes([IsAuthenticated])
def subgroup_delete(request):
    if isinstance(request.data, dict):
        name = request.data['name']
        token = request.data['usertoken']
    else:
        name = json.loads(request.data)['name']
        token = json.loads(request.data)['usertoken']
    session_obj = UserSession.objects.filter(token=token)[0]
    session = json.loads(session_obj.session)
    if name!='':
        session['subgroups'][name] = {}
    session_obj.session = json.dumps(session)
    session_obj.save()
    return JsonResponse({'Message': 'Deleted Subgroup'})

def get_all_pids_visit():
    list_data =  list(DataPointsVisit.objects.all().values('PID', 'VISIT').distinct())
    tupel_list = []
    for data in list_data:
        tupel_list.append((data['PID'], data['VISIT']))
    return tupel_list

@api_view(['POST'])
@use_token_auth
@custom_permission_classes([IsAuthenticated])
def initialize_session(request):
    #session_id = request.POST.get('session_id')
    #print(request.data)
    #print(request.json)
    #print(request.POST)
    if isinstance(request.data, dict):
        token = request.data['usertoken']
        if 'plot_ids' in request.data.keys():
            plot_ids = request.data['plot_ids']
    else:
        token = json.loads(request.data)['usertoken']
        if 'plot_ids' in json.loads(request.data).keys():
            plot_ids = json.loads(request.data)['plot_ids']

    ##################################################################
    # Data will be cached for 24 hourse so the data access is faster #
    ##################################################################
    try:
        all_data = cache.get(f"data_{token}")
    except:
        all_data = DataPointsVisit.objects.all()
        all_data_serialized = DataPointsVisitSerializer(all_data, many=True)
        all_data_pandas = pd.read_json(json.dumps(all_data_serialized.data))
        cache.set(f"data_{token}", all_data_pandas,60*60*24) 

        

    session = {
    'plots' : {},
    'filter': {
        'concept': 1,
        'constraints': {},
        'selection': get_all_pids_visit()
    },
    'subgroups': {},
    'population': get_all_pids_visit()
    }
    if UserSession.objects.filter(token=token).exists():
        this_session_obj =  UserSession.objects.filter(token=token)[0]
        this_session = json.loads(this_session_obj.session)
        session_plot_ids = this_session['plots'].keys()
        '''
        The snipped below checks if 1. there exists a plot-dict for that plot_id nad 2. removes all plot-dicts that are not in plot_ids
        If plot_ids is not provided a new session obj is populated if none exitsts
        '''
        if plot_ids:
            plots_to_delete = []
            for id in plot_ids:
                if not id in session_plot_ids:
                    this_session['plots'][id] = {}
            for id in session_plot_ids:
                if id not in plot_ids:
                    plots_to_delete.append(id)
                    #del this_session['plots'][id]
            for id in plots_to_delete:
                del this_session['plots'][id]



        this_session_obj.session = json.dumps(this_session)
        this_session_obj.save()
        print(f"SESSION FOUND FOR {token} IN DB")
    else:
        if plot_ids:
            for id in plot_ids:
                session['plots'][id] = {}
        UserSession.objects.create(token=token, session=json.dumps(session))
        print("Session created in DB")
    print(f"Init call from {get_client_ip(request)} with session id:{token}")
    #cache.set(session_id, session)
    response = HttpResponse(json.dumps({'Message': 'Initialized session', 'Session': session}), content_type='application/json')
    return response


@api_view(['GET', 'POST'])
@use_token_auth
@custom_permission_classes([IsAuthenticated])
def datapoints_list(request):
    if request.method == 'GET':
        datapoints = DataPointsVisit.objects.all()
        serializer = DataPointsVisitSerializer(datapoints, many=True)
        return Response(serializer.data)
    else:
        return Response({'Message':'This is currently not implemented...'})


@api_view(['GET'])
@use_token_auth
@custom_permission_classes([IsAuthenticated])
def get_genetic_data(request):
    if request.GET.get('data_id'):
        data = GeneticJson.objects.filter(data_id=request.GET.get('data_id'))
    else:
        data = GeneticJson.objects.all()
    serialized = GeneticJsonSerializer(data, many=True)
    return Response(serialized.data)

@api_view(['POST'])
@use_token_auth
@custom_permission_classes([IsAuthenticated])
def post_genetic_data(request):


    #print(request.data)
    if isinstance(request.data, dict):
        username = request.data['username']
        password = request.data['password']
    else:
        username = json.loads(request.data)['username']
        password = json.loads(request.data)['password']

    try:
        if isinstance(request.data, dict):
            id = request.data['data_id']
            gen_json = request.data['genetic_data']
        else:
            id = json.loads(request.data)['data_id']
            gen_json = json.loads(request.data)['genetic_data']

    except:
        return JsonResponse({'status': 'Failed'})
    if id and gen_json:
        try:
            GeneticJson.objects.create(json_string=json.dumps(gen_json), data_id=id)
        except:
            return JsonResponse({"status": "error", "message": "looks like your data is corrupt or your data_id is already taken. If you want to override the data_id please contact philipp.wegner@scai.fraunhofer.de"})
        return JsonResponse({'status': 'OK', 'data_id': id, 'get_url': "idsn.dzne.de/clinical-backend/api/genetic-data?data_id=" + id})
    else:
        return JsonResponse({'status': 'Failed'})


@api_view(['POST'])
@use_token_auth
@custom_permission_classes([IsAuthenticated])
def getdata(request):
    print(f"Getdata call from: {get_client_ip(request)}")
    if isinstance(request.data, dict):
        ctrl_json = request.data['controls']
        token = request.data['usertoken']
    else:
        ctrl_json = json.loads(request.data)['controls']
        token = json.loads(request.data)['usertoken']

    type, attX, attY, attC, Dt = ctrl_json['type'], ctrl_json['attX'], ctrl_json['attY'], ctrl_json['attC'], ctrl_json['Dt']
    
    plot_id = ctrl_json['plot']

    # Avoid error messages, when dropdown entries are initialized or deleted
    if attX is None:
        attX = ''
    if attY is None:
        attY = ''
    if attC is None:
        attC = ''

    try:
        Dt = int(ctrl_json['Dt'])
    except:
        Dt = -1

    visit = ctrl_json['visit']
    followup = ctrl_json['followup']
    tolerance = ctrl_json['tolerance']

    norm = ctrl_json['norm']
    stack = ctrl_json['stack']
    fit = ctrl_json['fit']
    legend = ctrl_json['legend']

    ## only for testing TODO remove before deploy
    
    if UserSession.objects.filter(token=token).exists():
        session_obj = UserSession.objects.get(token=token)
        session = json.loads(session_obj.session)
    else:
        print("Session not found... rely on default")
        session = {
        'plots' : {},
        'filter': {
            'concept': 1,
            'constraints': {},
            'selection': get_all_pids_visit()
        },
        'subgroups': {},
        'population': get_all_pids_visit()
        }

        session['plots'][plot_id] = {}
        session_obj = UserSession.objects.create(token=token, session=json.dumps(session))
    
    if not (attX) and ('figure' in list(session['plots'][ctrl_json['plot']].keys()) and 'plot' in list(session['plots'][ctrl_json['plot']].keys()) and 'bins' in list(session['plots'][ctrl_json['plot']].keys()) and 'vis_per_pid' in list(session['plots'][ctrl_json['plot']].keys()) and 'max_bin' in list(session['plots'][ctrl_json['plot']].keys())):

        print(f"Found session for {ctrl_json['plot']}")
        plot = session['plots'][ctrl_json['plot']]['plot']
        bins = session['plots'][ctrl_json['plot']]['bins']
        vis_per_pid = session['plots'][ctrl_json['plot']]['vis_per_pid']
        bin_max = session['plots'][ctrl_json['plot']]['max_bin']
        figure = json.loads(session['plots'][ctrl_json['plot']]['figure'])
    else:    # get datapoints from eav
        if type == 1:
            df = getdata_XY(Mdataframe, attX, attY, attC, Dt)
        elif type in [2, 3]:
            df = getdata_X(Mdataframe, attX, attC, Dt)
        elif type == 4:
            df = getdata_T(Mdataframe, attX, attY, attC, Dt)

        df = df.drop_duplicates()
        df = df.reset_index(drop=True)

        try:
            df.loc[:, 'TIMESTAMP'] = df.TIMESTAMP.astype('datetime64[ns]')
            df.loc[df.TIMESTAMP<pd.to_datetime('1970-01-01'), 'TIMESTAMP']=pd.to_datetime(('1900-01-01'))
            df.loc[:, 'VISIT'] = df.VISIT.astype(object)
        except Exception as e:
            print(traceback.format_exc())

    # select one visit per patient (maybe other condese functions re-include here)
        if df.VISIT.notna().all():
            if visit == 'BASELINE':
                df = df[df.VISIT.isin([0, -1])]
            if visit == 'FOLLOW':
                df = df[(df.FOLLOWUP >= np.timedelta64((followup-tolerance), 'M')) & (df.FOLLOWUP <= np.timedelta64((followup+tolerance), 'M'))]

        df.loc[:, 'VISIT'].fillna(-1, inplace=True)

        vis_per_pid = getviscount(df)
        bins, bin_max = getbinning(df,type)

    # select datapoints and create traces on color attribute and define marker colors
        def get_subset(df, selection, concept):
            if concept == 2:
                selection = [tuple(i) for i in selection]
                concept = ['PID', 'VISIT']
            elif concept == 1:
                selection = [i[0] for i in selection]
                concept = ['PID']
            df_sub = df.sort_values(by=concept).set_index(concept)
            return df_sub[df_sub.index.isin(selection)].reset_index()

        if len(df)>0:
            df_sel = get_subset(df, session['filter']['selection'], session['filter']['concept'])

            traces = [[df, 'population', '#FFFFFF'], [df_sel, 'selection', '#808080']]

            if attC!='':
                if attC == 'SUBGROUPS':
                    
                    traces = traces + [[
                        get_subset(df_sel, session['subgroups'][sg]['selection'], session['subgroups'][sg]['concept']),
                        sg,
                        colors[i+2]
                    ] for i, sg in enumerate(session['subgroups'])]

                elif attC=='PATIENTS':
                    traces = traces + [[
                        df_sel[df_sel.PID==pid],
                        pid,
                        '#007bff'
                    ] for pid in df_sel.PID.unique()]

                else: 
                    if model_items.loc[attC,'Datatype'] == 'code':
                        traces = traces + [[
                            df_sel.loc[df_sel['COLOR'] == float(i)],
                            model_codes.loc[i, model_items.loc[attC]['Domain']],
                            colors[i+2]
                        ] for k,i in enumerate(df[df.COLOR.notna()].COLOR.astype(int).sort_values().unique())]

                    if model_items.loc[attC, 'Datatype'] in ['int', 'float']:
                        traces[1][2] = df_sel.COLOR.tolist()
            else:
                
                traces[1][2] = '#007bff'
        else:
            traces=[]

        # up to here data PID/VISIT based
    # convert list of traces to dict
        if type in [1,4]:
            traces = [
                {
                    "name": trace[1],
                    "label":  trace[0].PID.tolist(),
                    "X": [val[0] for val in trace[0].VALUE],
                    "Y": [val[1] for val in trace[0].VALUE],
                    "C": trace[2]
                }
                for trace in traces
            ]
        elif type in [2]:
            traces = [
                {
                    "name": trace[1],
                    "label": None,
                    "X": trace[0].VALUE.tolist(),
                    "Y": None,
                    "C": trace[2]
                }
                for trace in traces
            ]
        elif type in [3]:
            print(traces)
            traces = [
                {
                    "name": trace[1],
                    "label": None,
    #                "X": [str(i)+"/"+str(Key)+ "/"+model_codes.loc[Key, model_items.loc[attX, 'Domain']] for i, Key in enumerate(trace[0].VALUE.astype(int).value_counts().sort_index().index.tolist())],
                    "X": [model_codes.loc[Key, model_items.loc[attX, 'Domain']] for i, Key in enumerate(trace[0].VALUE.astype(int).value_counts().sort_index().index.tolist())],
                    "Y": trace[0].VALUE.value_counts().astype(int).sort_index().tolist(),
                    "C": trace[2]
                }
                for trace in traces
            ]

    # calculate and append fits
        if 'regression' in fit:
            fits = copy.deepcopy(traces)
            for i, trace in enumerate(traces):
                trace['X'] = [float(x) for x in trace['X']]
                trace['Y'] = [float(y) for y in trace['Y']]
                if len(trace['X'])>1:
                    slope, intercept, r_value, p_value, std_err = stats.linregress(trace['X'], trace['Y'])
                    fits[i]['name']=trace['name']
                    fits[i]['X'] = [float(x) for x in fits[i]['X']]
                    fits[i]['Y'] = [float(y) for y in fits[i]['Y']]
                    fits[i]['Y']=[x*slope+intercept for x in fits[i]['X']]
                    fits[0]['Y'] = [None for i in fits[0]['Y']]
        else:
            fits = []

    # filter box
        filter = session['filter']['constraints']
        if attX in filter.keys() and (filter[attX]['lower'] is not None) and (filter[attX]['upper'] is not None):
            box = {'x0': filter[attX]['lower'], 'x1': filter[attX]['upper'], 'xref': 'x'}
        else:
            box = {'x0': 0, 'x1':1, 'xref': 'paper'}
        if attY in filter.keys() and (filter[attY]['lower'] is not None) and (filter[attY]['upper'] is not None):
            box = {**box, 'y0': filter[attY]['lower'], 'y1': filter[attY]['upper'], 'yref': 'y'}
        else:
            box = {**box, 'y0': 0, 'y1': 1, 'yref': 'paper'}

        if (box['xref']=='paper') and (box['yref']=='paper'):
            box= None

        plot = {
            "traces": traces,
            "fits": fits,
            "titleX": get_humanreadable((attX)),
            "titleY": get_humanreadable((attY)),
            "titleC": get_humanreadable((attC)),
            "box": box
        }
        figure = get_fig(json.dumps(plot), json.dumps(ctrl_json))
        session['plots'][ctrl_json['plot']]['controls']=ctrl_json
        session['plots'][ctrl_json['plot']]['plot']=plot
        session['plots'][ctrl_json['plot']]['bins'] = str(bins)
        session['plots'][ctrl_json['plot']]['vis_per_pid'] = str(vis_per_pid)
        session['plots'][ctrl_json['plot']]['max_bin'] = str(bin_max)
        session['plots'][ctrl_json['plot']]['figure'] = json.dumps(figure, cls=PlotlyJSONEncoder)
        session_obj.session = json.dumps(session)
        session_obj.save()

        #print(f"FIGURE: {figure}")

    response = HttpResponse(json.dumps({'Status': 'OK','plot_id': ctrl_json['plot'],'figure': json.dumps(figure, cls=PlotlyJSONEncoder), 'vis_per_pid': str(vis_per_pid), 'bins': str(bins), 'bin_max': str(bin_max),'controls': json.dumps(ctrl_json)}),  content_type="application/json")
    #response.set_cookie('session', json.dumps(session))
    return response




@api_view(['POST'])
@use_token_auth
@custom_permission_classes([IsAuthenticated])
def filter_update(request):
    if isinstance(request.data, dict):
        data = request.data
    else:
        data = json.loads(request.data)

    table = data['filter_table']
    token = data['usertoken']
    concept = data['concept']

    session_obj = UserSession.objects.filter(token=token)[0]
    session=json.loads(session_obj.session)
    constraints = {con['attribute']: con for con in table}
    for con in constraints.values():
        con.update({'set': get_subgroup(con['attribute'], con['lower'], con['upper'], con['list'])})
    session = filter_apply(constraints, session)
    constraints = [con for con in constraints.values()]
    session['filter']['concept'] = concept
    #n_plots = len(session['plots'].keys())
    plots =  {}
    for id in session['plots'].keys():
        ctrl_json = session['plots'][id]['controls']
        type, attX, attY, attC, Dt= ctrl_json['type'], ctrl_json['attX'], ctrl_json['attY'], ctrl_json['attC'], ctrl_json['Dt']

        # Avoid error messages, when dropdown entries are initialized or deleted
        if attX is None:
            attX = ''
        if attY is None:
            attY = ''
        if attC is None:
            attC = ''

        try:
            Dt = int(ctrl_json['Dt'])
        except:
            Dt = -1

        visit = ctrl_json['visit']
        followup = ctrl_json['followup']
        tolerance = ctrl_json['tolerance']

        norm = ctrl_json['norm']
        stack = ctrl_json['stack']
        fit = ctrl_json['fit']
        legend = ctrl_json['legend']
        if type == 1:
            df = getdata_XY(Mdataframe, attX, attY, attC, Dt)
        elif type in [2, 3]:
            df = getdata_X(Mdataframe, attX, attC, Dt)
        elif type == 4:
            df = getdata_T(Mdataframe, attX, attY, attC, Dt)

        df = df.drop_duplicates()
        df = df.reset_index(drop=True)
        #print(f"DATAFRAME {df}")

        try:
            df.loc[:, 'TIMESTAMP'] = df.TIMESTAMP.astype('datetime64[ns]')
            df.loc[df.TIMESTAMP<pd.to_datetime('1970-01-01'), 'TIMESTAMP']=pd.to_datetime(('1900-01-01'))
            df.loc[:, 'VISIT'] = df.VISIT.astype(object)
        except Exception as e:
            print(traceback.format_exc())

    # select one visit per patient (maybe other condese functions re-include here)
        if df.VISIT.notna().all():
            if visit == 'BASELINE':
                df = df[df.VISIT.isin([0, -1])]
            if visit == 'FOLLOW':
                df = df[(df.FOLLOWUP >= np.timedelta64((followup-tolerance), 'M')) & (df.FOLLOWUP <= np.timedelta64((followup+tolerance), 'M'))]

        df.loc[:, 'VISIT'].fillna(-1, inplace=True)
    #    df.loc[:, 'TIMESTAMP'].fillna(-1, inplace=True)

        vis_per_pid = getviscount(df)
        bins, bin_max = getbinning(df,type)

    # select datapoints and create traces on color attribute and define marker colors
        def get_subset(df, selection, concept):
            #print("selection " + str(selection))
            if concept == 2:
                selection = [tuple(i) for i in selection]
                concept = ['PID', 'VISIT']
            elif concept == 1:
                #print(f"SELCETION IN GET_SUBGROUP : {selection}")
                selection = [i[0] for i in selection]
                concept = ['PID']
                #print(f"SELECTION : {selection}")
            df_sub = df.sort_values(by=concept).set_index(concept)
            return df_sub[df_sub.index.isin(selection)].reset_index()

        if len(df)>0:
            print(f" CURRENT SESSION : {session['filter']}")
            df_sel = get_subset(df, session['filter']['selection'], session['filter']['concept'])
            #print(f"SELECTION DATAFRAME {df_sel}")

            traces = [[df, 'population', '#FFFFFF'], [df_sel, 'selection', '#808080']]

            if attC!='':
                if attC == 'SUBGROUPS':
                    traces = traces + [[
                        get_subset(df_sel, session['subgroups'][sg]['selection'], session['subgroups'][sg]['concept']),
                        sg,
                        colors[i+2]
                    ] for i, sg in enumerate(session['subgroups'])]

                elif attC=='PATIENTS':
                    traces = traces + [[
                        df_sel[df_sel.PID==pid],
                        pid,
                        '#007bff'
                    ] for pid in df_sel.PID.unique()]

                else:
                    if model_items.loc[attC,'Datatype'] == 'code':
                        traces = traces + [[
                            df_sel.loc[df_sel['COLOR'] == float(i)],
                            model_codes.loc[i, model_items.loc[attC]['Domain']],
                            colors[i+2]
                        ] for k,i in enumerate(df[df.COLOR.notna()].COLOR.astype(int).sort_values().unique())]

                    if model_items.loc[attC, 'Datatype'] in ['int', 'float']:
                        traces[1][2] = df_sel.COLOR.tolist()
            else:
                traces[1][2] = '#007bff'
        else:
            traces=[]

        # up to here data PID/VISIT based
        #print(f" PROBLEM: {traces}")
    # convert list of traces to dict
        if type in [1,4]:
            traces = [
                {
                    "name": trace[1],
                    "label":  trace[0].PID.tolist(),
                    "X": [val[0] for val in trace[0].VALUE],
                    "Y": [val[1] for val in trace[0].VALUE],
                    "C": trace[2]
                }
                for trace in traces
            ]
        elif type in [2]:
            traces = [
                {
                    "name": trace[1],
                    "label": None,
                    "X": trace[0].VALUE.tolist(),
                    "Y": None,
                    "C": trace[2]
                }
                for trace in traces
            ]
        elif type in [3]:
            traces = [
                {
                    "name": trace[1],
                    "label": None,
    #                "X": [str(i)+"/"+str(Key)+ "/"+model_codes.loc[Key, model_items.loc[attX, 'Domain']] for i, Key in enumerate(trace[0].VALUE.astype(int).value_counts().sort_index().index.tolist())],
                    "X": [model_codes.loc[Key, model_items.loc[attX, 'Domain']] for i, Key in enumerate(trace[0].VALUE.astype(int).value_counts().sort_index().index.tolist())],
                    "Y": trace[0].VALUE.value_counts().astype(int).sort_index().tolist(),
                    "C": trace[2]
                }
                for trace in traces
            ]
            #print(f"PRBLEM: {traces}")

    # calculate and append fits
        if 'regression' in fit:
            fits = copy.deepcopy(traces)
            for i, trace in enumerate(traces):
                trace['X'] = [float(x) for x in trace['X']]
                trace['Y'] = [float(y) for y in trace['Y']]
                if len(trace['X'])>1:
                    slope, intercept, r_value, p_value, std_err = stats.linregress(trace['X'], trace['Y'])
                    fits[i]['name']=trace['name']
                    fits[i]['X'] = [float(x) for x in fits[i]['X']]
                    fits[i]['Y'] = [float(y) for y in fits[i]['Y']]
                    fits[i]['Y']=[x*slope+intercept for x in fits[i]['X']]
                    fits[0]['Y'] = [None for i in fits[0]['Y']]
        else:
            fits = []

    # filter box
        filter = session['filter']['constraints']
        if attX in filter.keys() and (filter[attX]['lower'] is not None) and (filter[attX]['upper'] is not None):
            box = {'x0': filter[attX]['lower'], 'x1': filter[attX]['upper'], 'xref': 'x'}
        else:
            box = {'x0': 0, 'x1':1, 'xref': 'paper'}
        if attY in filter.keys() and (filter[attY]['lower'] is not None) and (filter[attY]['upper'] is not None):
            box = {**box, 'y0': filter[attY]['lower'], 'y1': filter[attY]['upper'], 'yref': 'y'}
        else:
            box = {**box, 'y0': 0, 'y1': 1, 'yref': 'paper'}

        if (box['xref']=='paper') and (box['yref']=='paper'):
            box= None

        plot = {
            "traces": traces,
            "fits": fits,
            "titleX": get_humanreadable((attX)),
            "titleY": get_humanreadable((attY)),
            "titleC": get_humanreadable((attC)),
            "box": box
        }
        figure = get_fig(json.dumps(plot), json.dumps(ctrl_json))
        session['plots'][id]['controls']=ctrl_json
        session['plots'][id]['plot']=plot
        session['plots'][id]['bins'] = str(bins)
        session['plots'][id]['vis_per_pid'] = str(vis_per_pid)
        session['plots'][id]['max_bin'] = str(bin_max)
        session['plots'][id]['figure'] = json.dumps(figure, cls=PlotlyJSONEncoder)
        plots[id] = {}
        plots[id]['figure'] = json.dumps(figure, cls=PlotlyJSONEncoder)
        plots[id]['vis_per_pid'] = str(vis_per_pid)
        plots[id]['bins'] = str(bins)
        plots[id]['bin_max'] = str(bin_max)
        plots[id]['controls'] = json.dumps(ctrl_json)
        
        #print(f"FIGURE: {figure}")
    session_obj.session = json.dumps(session)
    session_obj.save()
    #print(plots)
    
    return JsonResponse({'status': 'ok', 'plots': plots})


    #print(constraints)

## DATAMODEL STUFF



dirname = os.path.dirname(os.path.realpath('__file__'))

path = os.path.join(dirname, 'data/').replace("\\","/")
dm = 'Datamodel.xlsx'
model_items = pd.read_excel(path + dm, sheet_name="Attributes")
model_items.index=model_items.Attribute
model_items['metatype'] = model_items['Datatype'].replace({'int': 'numerical', 'float': 'numerical', 'code': 'categorical'})

model_codes = pd.read_excel(path + dm, sheet_name="Codes")
model_codes = model_codes.pivot(index='Key', columns='Code', values='Value')
model_codes = model_codes.reset_index()


print(model_items.columns)
print(model_codes.columns)

'''
datamodel_attr_all = DatamodelAttribute.objects.all()
model_items = pd.DataFrame(columns=['Active','Topic','Topic_Description','Umbrella','Umbrella_Description','Attribute','Attribute_Description',
       'Attribute_Tooltip','Datatype','Domain','Unit'])
for datamodel_att in datamodel_attr_all:
    
datamodel_codes_all = DatamodelCode.objects.all()
'''


@api_view(['POST'])
@use_token_auth
@custom_permission_classes([IsAuthenticated])
def reset_session(request):
    if isinstance(request.data, dict):
        token = request.data['usertoken']
    else:
        token = json.loads(request.data)['usertoken']
    session = UserSession.objects.filter(token=token)
    #print(session.count())
    if session.exists():
        session_obj = session[0]
        session_obj.delete()
        UserSession.objects.create(token=token, session=json.dumps({
        'plots':{},
        'filter': {
            'concept': 1,
            'constraints': {},
            'selection': get_all_pids_visit()
        },
        'subgroups': {},
        'population': get_all_pids_visit()
        }))
        return JsonResponse({'message': 'OK'})
    else:
        return JsonResponse({'message': "unknown token"})


@api_view(['POST'])
@use_token_auth
@custom_permission_classes([IsAuthenticated])
def acces_token(request):
  

    #print(request.data)
    if isinstance(request.data, dict):
        username = request.data['username']
        password = request.data['password']
    else:
        username = json.loads(request.data)['username']
        password = json.loads(request.data)['password']


    return JsonResponse({'Token': json.loads(response.text)['access_token']})
