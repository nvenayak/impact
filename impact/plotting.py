import sqlite3 as sql

import numpy as np
import sys
from warnings import warn

from .core.ReplicateTrial import ReplicateTrial
from .core.settings import plotly_username, plotly_api_key

# If in the iPython environment, initialize notebook mode
try:
    _ = __IPYTHON__
except NameError:
    from plotly.offline import plot
else:
    if 'ipykernel' in sys.modules:
        from plotly.offline import init_notebook_mode
        from plotly.offline import iplot as plot
        from IPython.display import HTML

        # This is required for correct mathjax (latex) and documentation rendering
        HTML(
            """
            <script>
                var waitForPlotly = setInterval( function() {
                    if( typeof(window.Plotly) !== "undefined" ){
                        MathJax.Hub.Config({ SVG: { font: "STIX-Web" }, displayAlign: "center" });
                        MathJax.Hub.Queue(["setRenderer", MathJax.Hub, "SVG"]);
                        clearInterval(waitForPlotly);
                    }}, 250 );
            </script>
            """
        )
        init_notebook_mode(connected=True)
    elif 'IPython' in sys.modules:
        # in a terminal
        from plotly.offline import plot
    else:
        warn('Unknown ipython configuration')
        from plotly.offline import plot

from plotly import tools
import plotly.graph_objs as go
import plotly.plotly as py
import colorlover as cl
import math

# Wrap plotly functions for easy access
go = go
tools = tools
cl = cl
plot = plot


def svg_plot(fig, **kwargs):
    """
    Generates an svg plot from a plotly figure

    Parameters
    ----------
    fig: plotly figure

    """
    from plotly.offline import plot as svg_plot
    svg_plot(fig,
             image_width=fig['layout']['width'],
             image_height=fig['layout']['height'],
             image='svg',
             **kwargs)


def generic_timecourse(impact_core_instance_list=None):
    if impact_core_instance_list is None:
        raise ValueError('No data')


def printGenericTimeCourse_plotly(replicateTrialList=None, dbName=None, strainsToPlot=[], titersToPlot=[],
                                  secondary_y_axis_titers=None, pts_per_hour=4,
                                  output_type='html', stage_indices=None, stage=None,
                                  cl_scales=['10', 'qual', 'Paired'], colors=None,
                                  yieldFlag=False, titerFlag=True, endpointFlag=False, sortBy='strain_id',
                                  img_scale=1, fig_height=None, column_width=400, number_of_columns=3,
                                  horizontal_spacing=0.2, vertical_spacing=0.4, row_height=300,
                                  format='web', single_subplot=False, plot_curve_fit=False):
    """
    Parameters
    ----------
    replicateTrialList: ~class`titer`
        A list of replicate_id trials to be plotted
    dbName : str
        The name/path of the db if you will be loading data
    strainsToPlot : list
        A list of the strain identifiers, a concatenation of the strain.name+id_1+id_2
    titersToPlot : list
        A list of the titers to plot
    output_type : str
        The type of output (html, file, image, iPython)
    stage_indices : list of index pairs defining stages
        The indices of stages to be defined. This will be moved elsewhere
    stage : int
        The stage of interest (as defined in stage_indices)
    cl_scales : list of color scale identifiers
    colors : list of str indicating the color 'rgb(0, 0, 0)'
    yieldFlag : bool
        True to plot yield
    titerFlag : bool
        True to plot titer
    endpointFlag : bool
        True to plot endpoint, otherwise plot timecourse
    sortBy : str
        Identifier to plot by (strain.name, id_1, id_2, None)
    img_scale : int
        The output scale of the image
    fig_height : float
        The height of the figure
    column_width : float
        The width of each column
    number_of_columns : int
        The number of columns
    horizontal_spacing : float
        The horizontal spacing between subplots
    vertical_spacing : float
        The vertical spacing between subplots
    row_height : float
        The height of a row in the plot
    format : str
        The format settings to use, the only option is poster
    """

    if yieldFlag:
        data_to_plot = 'yield'
    elif titerFlag:
        data_to_plot = 'titer'
    else:
        raise Exception('Neither yield nor titer selected')

    # Check for correct inputs
    if replicateTrialList is None and dbName is None:
        print('No replicate_id list or db_name')
        return 'No replicate_id list or db_name'
    elif replicateTrialList is not None and dbName is not None:
        print('Supplied both a replicateTrialList and db_name')
        return 'Supplied both a replicateTrialList and db_name'
    elif dbName is not None:
        # Load data into replciate experiment object
        conn = sql.connect(dbName)
        c = conn.cursor()
        replicateTrialList = []
        for strain in strainsToPlot:
            tempReplicateTrial = ReplicateTrial()
            tempReplicateTrial.db_load(c=c, replicateID=strain)
            replicateTrialList.append(tempReplicateTrial)
        conn.close()

    # Switch the the replicate_id stages if we're looking at data for a specific stage
    if stage_indices is not None and stage is not None:
        newReplicateTrialList = []
        for replicateTrial in replicateTrialList:
            # replicateTrial.calculate_stages(stage_indices=stage_indices)
            newReplicateTrialList.append(replicateTrial.stages[stage])
        replicateTrialList = newReplicateTrialList
    elif stage_indices is not None:
        print('Ignoring stages, no stage selected')
    elif stage is not None:
        print('Ignoring stages, no stage_indices provided')

    # Check if titers provided
    if not titersToPlot:
        raise Exception('No titers defined to plot')

    if colors is None:
        color_scale = cl.scales[cl_scales[0]][cl_scales[1]][cl_scales[2]]
        # https://plot.ly/ipython-notebooks/color-scales/
        if len(replicateTrialList) > int(cl_scales[0]):
            colors = cl.interp(color_scale, 500)
            # Index the list
            colors = [colors[int(x)] for x in np.arange(0, 500, round(500 / len(replicateTrialList)))]
        else:
            colors = color_scale

    # Choose the subplot layout
    rows = math.ceil(len(titersToPlot) / number_of_columns)

    if fig_height is None:
        height = row_height * rows
    else:
        height = fig_height

    # Set default axes
    for titer in titersToPlot:
        if secondary_y_axis_titers is None:
            secondary_y_axis_titers = {}

        if titer not in secondary_y_axis_titers.keys():
            secondary_y_axis_titers[titer] = 'primary'

    supported_formats = ['poster', 'web']
    if format in supported_formats:
        if format == 'poster':
            chart_fonts = {'titlefont': {'size': 18, 'color': '#000000'},
                           'tickfont' : {'size': 18},
                           'color'    : '#000000'}
            layout_margin = {'b': 160, 'r': 100}
            axis_params = dict(linewidth=1.5, showline=True, ticks='outside',
                               showgrid=False, zeroline=False)
            bar_xaxis_params = dict(tickangle=-45, )
            legend_params = {'orientation': 'h', 'font': {'size': 10, 'color': '#000000'}}
        else:
            chart_fonts = {}
            layout_margin = {}
            axis_params = {}
            bar_xaxis_params = {}
            legend_params = {}
    else:
        raise Exception(format, ' is not a valid format, try one of ', supported_formats)

    # fig['layout'].update(height=height, legend={'orientation': 'h', 'font': {'size': 10, 'color': '#000000'}})

    if not (sortBy == 'product_in_legend' or single_subplot):
        fig = tools.make_subplots(rows=rows, cols=number_of_columns,
                                  horizontal_spacing=horizontal_spacing / number_of_columns,
                                  vertical_spacing=vertical_spacing / rows
                                  )
    else:
        fig = tools.make_subplots(rows=1, cols=2,
                                  horizontal_spacing=horizontal_spacing / number_of_columns,
                                  vertical_spacing=vertical_spacing / rows
                                  )

    # Only show the legend entry for the first time a strain is plotted, prevents duplicate entries
    if endpointFlag and sortBy:
        showlegend_flag = False
    else:
        showlegend_flag = True

    dataLabel = ''
    sort_by_flag = True
    sort_by_product_in_legend_flag = False
    pltNum = 0

    prepped_x = dict()
    prepped_y_avg = dict()
    prepped_y_std = dict()
    prepped_legendgroup = dict()
    for name in [str(replicate.trial_identifier.strain.name) + '+'
                         + replicate.trial_identifier.id_1 + ','
                         + replicate.trial_identifier.id_2 for replicate in replicateTrialList]:
        prepped_x[name] = []
        prepped_y_avg[name] = []
        prepped_y_std[name] = []
        prepped_legendgroup[name] = []

    # Most of the plotting functionality is assuming subplots for each product
    for product in titersToPlot:

        if sortBy == 'product_in_legend' or single_subplot:
            # This is to put the legend in the right place, pltNum is not incremented again in this mode
            if pltNum == 0:
                pltNum += 1
        else:
            pltNum += 1

        color_index = 0
        if endpointFlag:
            if (sortBy is not None and sortBy != 'product_in_legend') and sort_by_flag:
                uniques = order_preserve_sort(
                    [getattr(replicate.trial_identifier, sortBy) for replicate in replicateTrialList])
            else:
                if sortBy == 'product_in_legend':
                    sort_by_product_in_legend_flag = True

                uniques = ['']
                sortBy = 'strain_id'  # This is just a placeholder, it can be any attribute of ReplicateTrialIdentifier
                # just so the function call doesn't return an error
                sort_by_flag = False

            if colors is None:
                colors = color_scale

            for i, unique in enumerate(uniques):
                x = unique
                if yieldFlag:
                    y_avg = [replicate.avg.yields[product] for replicate in replicateTrialList
                             if getattr(replicate.trial_identifier, sortBy) == unique or sort_by_flag is False]
                    y_std = [replicate.std.yields[product] for replicate in replicateTrialList
                             if getattr(replicate.trial_identifier, sortBy) == unique or sort_by_flag is False]
                    label = ' yield (g/g)'
                else:
                    y_avg = [replicate.avg.analyte_dict[product].data_vector for replicate in replicateTrialList
                             if getattr(replicate.trial_identifier, sortBy) == unique or sort_by_flag is False]
                    y_std = [replicate.std.analyte_dict[product].data_vector for replicate in replicateTrialList
                             if getattr(replicate.trial_identifier, sortBy) == unique or sort_by_flag is False]
                    label = ' titer (g/L)'

                if sort_by_flag:
                    legendgroup = unique

                    if sortBy == 'strain_id':
                        x = [replicate.trial_identifier.id_1 + ',' +
                             replicate.trial_identifier.id_2
                             for replicate in replicateTrialList
                             if getattr(replicate.trial_identifier, sortBy)
                             == unique or sort_by_flag is False]
                    if sortBy == 'id_1':
                        x = [replicate.trial_identifier.strain.name + ',' +
                             replicate.trial_identifier.id_2
                             for replicate in replicateTrialList
                             if getattr(replicate.trial_identifier, sortBy)
                             == unique or sort_by_flag is False]
                    if sortBy == 'id_2':
                        x = [replicate.trial_identifier.strain.name
                             + '+'
                             + replicate.trial_identifier.id_1
                             for replicate in replicateTrialList
                             if getattr(replicate.trial_identifier, sortBy)
                             == unique or sort_by_flag is False]

                else:
                    if sort_by_product_in_legend_flag:
                        x = [product for _ in replicateTrialList]
                        legendgroup = [replicate.trial_identifier.strain.name + '+' +
                                       replicate.trial_identifier.id_1 + ',' +
                                       replicate.trial_identifier.id_2 for replicate in replicateTrialList]
                    else:
                        legendgroup = None
                        x = [(replicate.trial_identifier.strain.name + '+' +
                              replicate.trial_identifier.id_1 +
                              replicate.trial_identifier.id_2).split('LMSE')[-1]
                             for replicate in replicateTrialList
                             if getattr(replicate.trial_identifier,
                                        sortBy) == unique or sort_by_flag is False]  # TODO remove the LMSE removal

                if sort_by_product_in_legend_flag:
                    showlegend_flag = True
                    for i2, name in enumerate(legendgroup):
                        prepped_x[name].append(x[i2])
                        prepped_y_avg[name].append(y_avg[i2][-1])
                        prepped_y_std[name].append(y_std[i2][-1])
                        prepped_legendgroup[name].append(legendgroup[i2])
                else:
                    trace = go.Bar(x=x,
                                   y=[y[-1] for y in y_avg],
                                   error_y={
                                       'type'   : 'data',
                                       'array'  : [y[-1] for y in y_std],
                                       'visible': True,
                                       'color'  : colors[i]},
                                   marker={'color': colors[i]},
                                   showlegend=showlegend_flag,
                                   legendgroup=legendgroup,
                                   name=legendgroup)

                    if sort_by_product_in_legend_flag:
                        row = 1
                        col = 1
                    else:
                        row = math.ceil(pltNum / number_of_columns)
                        col = pltNum - (row - 1) * number_of_columns
                    if sort_by_flag:
                        fig['layout'].update(barmode='group')
                    fig.append_trace(trace, row, col)
                    final_plot_number = pltNum

                    # Combine all parameters
                    params = dict()
                    for param_list in [axis_params, bar_xaxis_params, chart_fonts]:  params.update(param_list)
                    fig['layout']['xaxis' + str(pltNum)].update(**params)
                    fig['layout']['yaxis' + str(pltNum)].update(title=product + label, rangemode='nonnegative',
                                                                **axis_params, **chart_fonts)
                    fig['layout'].update(height=height, margin=layout_margin, showlegend=False)
                    showlegend_flag = False

        else:  # time course (not end point)
            final_plot_number = print_generic_timecourse_plotly(replicateTrialList, product, colors, pts_per_hour,
                                                                showlegend_flag, fig,
                                                                sortBy, pltNum, number_of_columns, single_subplot,
                                                                axis_params, chart_fonts,
                                                                height, legend_params, plot_curve_fit,
                                                                data_to_plot=data_to_plot)
            showlegend_flag = False

    if sort_by_product_in_legend_flag:
        for name in prepped_x:
            trace = go.Bar(x=prepped_x[name],
                           y=prepped_y_avg[name],
                           error_y={
                               'type'   : 'data',
                               'array'  : prepped_y_std[name],
                               'visible': True},
                           showlegend=showlegend_flag,
                           legendgroup=prepped_legendgroup[name],
                           name=name)
            fig['layout'].update(barmode='group')
            fig.append_trace(trace, 1, 1)
            final_plot_number = pltNum

        fig['layout']['xaxis1'].update(**axis_params, **bar_xaxis_params, **chart_fonts)
        fig['layout']['yaxis1'].update(title=label, rangemode='nonnegative',
                                       **axis_params, **chart_fonts)
        fig['layout'].update(height=height, margin=layout_margin)

    # Clear the empty plots
    if not sort_by_product_in_legend_flag:
        for pltNum in range(final_plot_number + 1, number_of_columns * rows + 1):
            fig['layout']['xaxis' + str(pltNum)].update(showgrid=False, zeroline=False, showline=False,
                                                        autotick=True,
                                                        ticks='', showticklabels=False)
            fig['layout']['yaxis' + str(pltNum)].update(showgrid=False, zeroline=False, showline=False,
                                                        autotick=True,
                                                        ticks='', showticklabels=False)

    return render_output_ploty(output_type, fig, number_of_columns=number_of_columns,
                               column_width_multiplier=column_width, img_scale=img_scale
                               )


def render_output_ploty(output_type, fig, number_of_columns=None, column_width_multiplier=None, img_scale=None):
    if output_type == 'html':
        return plot(fig, show_link=False, output_type='div', include_plotlyjs=False)
    elif output_type == 'file':
        plot(fig, show_link=True)
    elif output_type == 'iPython':
        # from plotly.offline import iplot
        plot(fig, show_link=False)
        # return fig
    elif output_type == 'image':
        import random
        import string
        import plotly

        plotly.tools.set_credentials_file(username=plotly_username, api_key=plotly_api_key)
        fig['layout'].update(width=number_of_columns * column_width_multiplier)
        random_file_name = ''.join(random.choice(string.ascii_letters) for _ in range(10)) + '.png'
        py.image.save_as(fig, random_file_name, scale=img_scale)
        return random_file_name


# An efficient sorting function that preserves order
def order_preserve_sort(seq, idfun=None):
    # order preserving
    if idfun is None:
        def idfun(x): return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        # in old Python versions:
        # if seen.has_key(marker)
        # but in new ones:
        if marker in seen: continue
        seen[marker] = 1
        result.append(item)
    return result


def print_generic_timecourse_plotly(replicate_trial_list, product, colors, pts_per_hour, showlegend_flag, fig,
                                    sortBy, pltNum, number_of_columns, single_subplot, axis_params, chart_fonts, height,
                                    legend_params, plot_curve_fit,
                                    data_to_plot='titer'
                                    ):
    color_index = 0

    if data_to_plot == 'yield':
        yieldFlag = True
        titerFlag = False
    elif data_to_plot == 'titer':
        titerFlag = True
        yieldFlag = False
    else:
        raise Exception('Neither yield nor titer selected to plot')

    for replicate in replicate_trial_list:
        # Determine how many points should be plotted
        required_num_pts = replicate.t[-1] * pts_per_hour
        removePointFraction = int(len(replicate.t) / required_num_pts)
        if removePointFraction < 1:  removePointFraction = 1

        normalize_to = None

        # Get the correct data
        dataLabel = ''
        if yieldFlag:
            if product != 'OD600':
                dataLabel = '<br>yield (g/g)'
            y_avg = replicate.avg.analyte_dict[product].product_yield[::removePointFraction]
            y_std = replicate.std.analyte_dict[product].product_yield[::removePointFraction]
        elif titerFlag:
            if product != 'OD600':
                dataLabel = '<br>titer (g/L)'
            y_avg = replicate.avg.analyte_dict[product].data_vector[::removePointFraction]
            y_std = replicate.std.analyte_dict[product].data_vector[::removePointFraction]
        elif normalize_to is not None:
            y_avg = replicate.avg.analyte_dict[product].get_normalized_data(normalize_to)[
                    ::removePointFraction]
            y_std = replicate.std.analyte_dict[product].get_normalized_data(normalize_to)[
                    ::removePointFraction]

        t = replicate.t[::removePointFraction]

        if product in replicate.avg.analyte_dict:
            if plot_curve_fit:
                mode = 'markers'
            else:
                mode = 'lines+markers'
            trace = go.Scatter(x=t,
                               y=y_avg,
                               error_y={
                                   'type'   : 'data',
                                   'array'  : y_std,
                                   'visible': True,
                                   'color'  : colors[color_index]},
                               mode=mode,
                               marker={
                                   'color': colors[color_index]},
                               line={'color': colors[color_index]},
                               showlegend=showlegend_flag,
                               legendgroup=(replicate.trial_identifier.unique_replicate_trial()).split('LMSE')[-1],
                               name=(replicate.trial_identifier.unique_replicate_trial()).split('LMSE')[-1])  # ,

            # Plot the fit curve
            if plot_curve_fit and len(replicate.avg.analyte_dict[product].fit_params.keys()) > 0:
                # print(replicate_id.avg.titer_dict[product].fit_params)
                trace_fit = go.Scatter(x=np.linspace(min(t), max(t), 50),
                                       y=replicate.avg.analyte_dict[product].data_curve_fit(
                                           np.linspace(min(t), max(t), 50)),
                                       mode='line',
                                       marker={
                                           'color': colors[color_index]},
                                       line={'color': colors[color_index]},
                                       legendgroup=(replicate.trial_identifier.strain.name + '+' +
                                                    replicate.trial_identifier.id_1 +
                                                    replicate.trial_identifier.id_2).split('LMSE')[-1],
                                       name=(replicate.trial_identifier.strain.name + '+' +
                                             replicate.trial_identifier.id_1 +
                                             replicate.trial_identifier.id_2).split('LMSE')[-1])  # ,

            # Append the plot if it was created
            if sortBy == 'product_in_legend' or single_subplot:
                fig.append_trace(trace, 1, 1)
                if plot_curve_fit:
                    fig.append_trace(trace_fit, 1, 1)
            else:
                row = math.ceil(pltNum / number_of_columns)
                col = pltNum - (row - 1) * number_of_columns
                fig.append_trace(trace, row, col)
                if plot_curve_fit:
                    fig.append_trace(trace_fit, row, col)
        # Keep moving color index to keeps colors consistent across plots
        color_index += 1
        final_plot_number = pltNum

    # Set some plot aesthetics
    fig['layout']['xaxis' + str(pltNum)].update(title='Time (hours)', rangemode='tozero', **axis_params,
                                                **chart_fonts)
    fig['layout']['yaxis' + str(pltNum)].update(title=product + ' ' + dataLabel, rangemode='tozero',
                                                **axis_params, **chart_fonts)
    fig['layout'].update(height=height, legend=legend_params)
    showlegend_flag = False
    return final_plot_number


## NEW PLOTTING
# def time_profile_traces(replicate_trials=None, feature='titer', analyte='OD600', colors=None,
#                         cl_scales=['8', 'qual', 'Set1'],
#                         label=lambda replicate: str(replicate.parent.start_date)
#                                                 + ' '
#                                                 + replicate.trial_identifier.strain.name
#                                                 + ' '
#                                                 + replicate.trial_identifier.id_1
#                                                 + ' '
#                                                 + replicate.trial_identifier.id_2,
#                         legendgroup=lambda x: None,
#                         showlegend=True,
#                         pts_per_hour=60
#                         ):
#     traces = []
#
#     if colors is None:
#         color_scale = cl.scales[cl_scales[0]][cl_scales[1]][cl_scales[2]]
#         # https://plot.ly/ipython-notebooks/color-scales/
#         if len(replicate_trials) > int(cl_scales[0]):
#             print(len(replicate_trials))
#             print(int(cl_scales[0]))
#             print('interpolated')
#             num_pts = len(replicate_trials)
#             colors = cl.interp(color_scale, num_pts)
#             # Index the list
#             colors = [colors[int(x)] for x in np.arange(0, num_pts, num_pts / round(len(replicate_trials)))]
#         else:
#             colors = color_scale
#
#     for index, replicate in enumerate(replicate_trials):
#         # Determine how many points should be plotted
#         required_num_pts = replicate.t[-1] * pts_per_hour
#         removePointFraction = int(len(replicate.t) / required_num_pts)
#         if removePointFraction < 1:  removePointFraction = 1
#
#         traces.append(go.Scatter(x=replicate.t[::removePointFraction],
#                                  y=replicate.avg.analyte_dict[analyte].data_vector[::removePointFraction],
#                                  error_y={
#                                      'type'   : 'data',
#                                      'array'  : replicate.std.analyte_dict[analyte].data_vector[::removePointFraction],
#                                      'visible': True,
#                                      'color'  : colors[index]},
#                                  # mode=mode,
#                                  marker={
#                                      'color': colors[index]},
#                                  line={'color': colors[index]},
#                                  showlegend=showlegend,
#                                  legendgroup=legendgroup(replicate),
#                                  name=label(replicate)))  # ,
#     return traces


def get_colors(number_of_colors, colors=None, cl_scales=['8', 'qual', 'Set1']):
    if colors is None:
        color_scale = cl.scales[cl_scales[0]][cl_scales[1]][cl_scales[2]]
        # https://plot.ly/ipython-notebooks/color-scales/
        if number_of_colors > int(cl_scales[0]):
            print('interpolated')
            # num_pts = len(replicate_trials)
            colors = cl.interp(color_scale, 500)
            # Index the list
            # Index the list
            colors = [colors[int(x)] for x in np.arange(0,
                                                        500,
                                                       round( 500 / (number_of_colors)))]
        else:
            colors = color_scale
    return colors


def time_profile_traces_single_trials(replicate_trial=None, feature=None, analyte='OD600', colors=None,
                                      cl_scales=['8', 'qual', 'Set1'],
                                      label=lambda replicate: str(replicate.trial_identifier.replicate_id),
                                      legendgroup=lambda x: None,
                                      showlegend=True,
                                      pts_per_hour=60
                                      ):
    """
    Return traces for the single trials which compose a replicate for a single analyte

    Parameters
    ----------
    replicate_trial (`ReplicateTrial`): replicate to plot
    feature (str): feature to plot
    analyte (str): analyte to plot
    colors (list): colors to use, will use cl_scales if none
    cl_scales (dict): colorlover set of colors
    label (function): lambda function to get identifiers from data
    legendgroup (function):
    showlegend (bool)
    pts_per_hour

    Returns
    -------

    """

    traces = []
    if colors is None:
        colors = get_colors(len(replicate_trial.single_trials), colors=colors, cl_scales=cl_scales)
    trial_list = [trial for trial in replicate_trial.single_trials]
    trial_list = sorted(trial_list, key=lambda rep:str(rep.trial_identifier.replicate_id))
    if feature is None:
        for index, singletrial in enumerate(trial_list):
        # Determine how many points should be plotted
            required_num_pts = singletrial.t[-1] * pts_per_hour
            removePointFraction = int(len(singletrial.t) / required_num_pts)
            if removePointFraction < 1:  removePointFraction = 1

            traces.append(go.Scatter(x=singletrial.t[::removePointFraction],
                                 y=singletrial.analyte_dict[analyte].data_vector[::removePointFraction],
                                 # mode=mode,
                                 marker={
                                     'color': colors[index]},
                                 line={'color': colors[index]},
                                 showlegend=showlegend,
                                 legendgroup=legendgroup(singletrial),
                                 name=label(singletrial)))  # ,
    else:
        for index, singletrial in enumerate(trial_list):
            # Determine how many points should be plotted
            required_num_pts = singletrial.t[-1] * pts_per_hour
            removePointFraction = int(len(singletrial.t) / required_num_pts)
            if removePointFraction < 1:  removePointFraction = 1
            y_data = getattr(singletrial.analyte_dict[analyte], feature)
            y_data = y_data.data
            traces.append(go.Scatter(x=singletrial.t[::removePointFraction],
                                     y=y_data[::removePointFraction],
                                     # mode=mode,
                                     marker={
                                         'color': colors[index]},
                                     line={'color': colors[index]},
                                     showlegend=showlegend,
                                     legendgroup=legendgroup(singletrial),
                                     name=label(singletrial)))  # ,
    return traces

def time_profile_traces(replicate_trials=None, feature=None, analyte='OD600', colors=None,
                        cl_scales=['8', 'qual', 'Set1'],
                        label=lambda replicate: str(replicate.trial_identifier.strain)
                                                + ' '
                                                + str(replicate.trial_identifier.media),
                        legendgroup=lambda x: None,
                        showlegend=True,
                        pts_per_hour=60
                        ):
    traces = []

    if colors is None:
        colors = get_colors(len(replicate_trials), colors=colors, cl_scales=cl_scales)

    for index, replicate in enumerate(replicate_trials):
        # Determine how many points should be plotted
        required_num_pts = replicate.t[-1] * pts_per_hour
        removePointFraction = int(len(replicate.t) / required_num_pts)
        if removePointFraction < 1:  removePointFraction = 1
        if feature is None:
            traces.append(go.Scatter(x=replicate.t[::removePointFraction],
                                 y=replicate.avg.analyte_dict[analyte].data_vector[::removePointFraction],
                                 error_y={
                                     'type'   : 'data',
                                     'array'  : replicate.std.analyte_dict[analyte].data_vector[::removePointFraction],
                                     'visible': True,
                                     'color'  : colors[index]},
                                 # mode=mode,
                                 marker={
                                     'color': colors[index]},
                                 line={'color': colors[index]},
                                 showlegend=showlegend,
                                 legendgroup=legendgroup(replicate),
                                 name=label(replicate)))  # ,
        else:
            y_data = getattr(replicate.avg.analyte_dict[analyte], feature)
            y_err = getattr(replicate.std.analyte_dict[analyte], feature)
            traces.append(go.Scatter(x=replicate.t[::removePointFraction],
                                     y=y_data[::removePointFraction],
                                     error_y={
                                         'type': 'data',
                                         'array': y_err[::removePointFraction],
                                         'visible': True,
                                         'color': colors[index]},
                                     # mode=mode,
                                     marker={
                                         'color': colors[index]},
                                     line={'color': colors[index]},
                                     showlegend=showlegend,
                                     legendgroup=legendgroup(replicate),
                                     name=label(replicate)))
    return traces


def plot_by_strain(expt=None):
    if expt is not None:
        strain_list = list(set([str(rep.trial_identifier.strain) for rep in expt.replicate_trials]))
        strain_list = sorted(strain_list)
        analyte_list = []
        for rep in expt.replicate_trials:
            analyte_list += rep.get_analytes()
        analyte_list = list(set(analyte_list))
        for analyte in analyte_list:
            for strain in strain_list:
                rep_list = [replicate for replicate in expt.replicate_trials if
                            str(replicate.trial_identifier.strain) == strain]
                rep_list = sorted(rep_list, key=lambda rep: str(rep.trial_identifier.media))

                tracelist = time_profile_traces(replicate_trials=rep_list, analyte=analyte,
                                                       label=lambda rep: str(rep.trial_identifier.media),
                                                       legendgroup=lambda rep: str(rep.trial_identifier.strain),
                                                       cl_scales=['8', 'qual', 'Dark2'], showlegend=True,
                                                       pts_per_hour=4)

                fig = go.Figure(data=tracelist)
                fig['layout'].update(title=str(analyte + ' vs time for ' + strain + ' in different media'))
                plot(fig)

    else:
        print("An experiment object must be specified to plot data.")


def plot_by_media(expt=None):
    if expt is not None:
        media_list = list(set([str(rep.trial_identifier.media) for rep in expt.replicate_trials]))
        media_list = sorted(media_list)
        analyte_list = []
        for rep in expt.replicate_trials:
            analyte_list += rep.get_analytes()
        analyte_list = list(set(analyte_list))
        for analyte in analyte_list:
            for media in media_list:
                rep_list = [replicate for replicate in expt.replicate_trials if
                            str(replicate.trial_identifier.media) == media
                            and (replicate.trial_identifier.strain.name) != 'blank']
                rep_list = sorted(rep_list, key=lambda rep: str(rep.trial_identifier.strain))

                tracelist = time_profile_traces(replicate_trials=rep_list, analyte=analyte,
                                                       label=lambda rep: str(rep.trial_identifier.strain),
                                                       legendgroup=lambda rep: str(rep.trial_identifier.media),
                                                       cl_scales=['8', 'qual', 'Dark2'], showlegend=True,
                                                       pts_per_hour=4)

                fig = go.Figure(data=tracelist)
                fig['layout'].update(title=str(analyte + ' vs time for different strains in ' + media + ' media'))
                plot(fig)

    else:
        print("An experiment object must be specified to plot data.")

