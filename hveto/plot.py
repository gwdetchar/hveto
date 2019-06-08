# -*- coding: utf-8 -*-
# Copyright (C) Joshua Smith (2016-)
#
# This file is part of the hveto python package.
#
# hveto is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# hveto is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with hveto.  If not, see <http://www.gnu.org/licenses/>.

"""Plotting routines for hveto
"""

import warnings
from math import (log10, floor)
from io import BytesIO

import numpy

from lxml import etree

from matplotlib import rcParams
from matplotlib.colors import LogNorm

from gwpy.plot import Plot

from gwdetchar.plot import texify

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__credits__ = 'Josh Smith, Joe Areeda, Alex Urban'

rcParams.update({
    # custom Hveto formatting
    'figure.subplot.bottom': 0.17,
    'figure.subplot.left': 0.12,
    'figure.subplot.right': 0.88,
    'figure.subplot.top': 0.90,
    'xtick.labelsize': 16,
    'ytick.labelsize': 16,
    'axes.labelsize': 24,
    'axes.labelpad': 2,
    'axes.titlesize': 24,
    'grid.color': 'gray',
    'grid.alpha': 0.5,
})

SHOW_HIDE_JAVASCRIPT = """
    <script type="text/ecmascript">
    <![CDATA[

    function init(evt) {
        if ( window.svgDocument == null ) {
            svgDocument = evt.target.ownerDocument;
            }
        }

    function ShowTooltip(obj) {
        var cur = obj.id.substr(obj.id.lastIndexOf('-')+1);

        var tip = svgDocument.getElementById('tooltip-' + cur);
        tip.setAttribute('visibility',"visible")
        }

    function HideTooltip(obj) {
        var cur = obj.id.substr(obj.id.lastIndexOf('-')+1);
        var tip = svgDocument.getElementById('tooltip-' + cur);
        tip.setAttribute('visibility',"hidden")
        }

    ]]>
    </script>"""


# -- set up default header plot captions

HEADER_CAPTION = {
    'HISTOGRAM':
        "Histogram of number of triggers in the primary channel before the "
        "heveto analysis, but after the data quality flag cuts (red) compared "
        "with the number after vetoes from all hveto rounds have been applied "
        "(blue) versus the signal-to-noise ratio of those triggers.",
    'ROC':
        "The fraction of the primary channel triggers vetoed (fractional "
        "efficiency) versus the fraction of livetime that is vetoed "
        "(fractional deadtime) for each hveto round (blue dots). Guidelines "
        "are given for efficiency/deadtime of 1 (the value expected for "
        "random chance) and higher.",
    'TIME':
        "Frequency versus time graph of all triggers in the primary channel "
        "before the hveto analysis (black dots) and those triggers that are "
        "vetoed by a given round (symbols).",
    'SNR_TIME':
        "Signal-to-noise ratio versus time graph of all triggers in the "
        "primary channel before the hveto analysis (black dots) and those "
        "triggers that are vetoed by a given round (symbols)."
}


# -- set up default round winner plot captions

ROUND_CAPTION = {
    'HISTOGRAM':
        "Histogram of number of triggers in the primary channel before this "
        "round of hveto (red) compared with the number after vetoes from this "
        "round have been applied (blue) versus the signal-to-noise ratio of "
        "those triggers.",
    'SNR_TIME':
        "Signal-to-noise ratio versus time graph of all triggers in the "
        "primary channel before this round of hveto (black dots) and those "
        "triggers that are vetoed by this round (red plusses).",
    'SNR':
        "Signal-to-noise ratio versus frequency graph of all triggers in the "
        "primary channel before this round of hveto (black dots) and those "
        "triggers that are vetoed by this round (red plusses).",
    'TIME':
        "Frequency versus time graph of all triggers in the primary channel "
        "before this hveto round (dots colored by signal-to-noise ratio) and "
        "those triggers that are vetoed by this round (red plusses).",
    'USED_SNR_TIME':
        "Signal-to-noise ratio versus time graph of all triggers in the "
        "auxiliary channel above the threshold selected for this round (black "
        "dots, these are the triggers used to construct the veto) and the "
        "primary channel triggers that are vetoed in this round (red "
        "plusses). This can indicate whether, for example, louder triggers in "
        "the auxiliary channel are used to veto quieter channels in the "
        "primary channel, as might be expected for an external disturbance.",
    'AUX_SNR_TIME':
        "Signal-to-noise ratio versus time graph of all triggers in the "
        "auxiliary channel before this round (black dots), those above the "
        "threshold selected for this round (yellow plusses, these are the "
        "triggers used to construct the veto), and those triggers that "
        "actually veto one of the primary channel triggers (red plusses).",
    'AUX_SNR_FREQUENCY':
        "Signal-to-noise ratio versus frequency graph of all triggers in the "
        "auxiliary channel before this round (black dots), those above the "
        "threshold selected for this round (yellow plusses, these are the "
        "triggers used to construct the veto), and those triggers that "
        "actually veto one of the primary channel triggers (red plusses).",
    'AUX_FREQUENCY_TIME':
        "Frequency versus time graph of all triggers in the auxiliary channel "
        "before this round (dots colored by signal-to-noise ratio), those "
        "above the threshold selected for this round (yellow plusses, these "
        "are the triggers used to construct the veto), and those triggers "
        "that actually veto one of the primary channel triggers (red "
        "plusses).",
    'SIG_DROP':
        "This plot includes interactive features (channel names appear when "
        "pointed to with your mouse cursor) that can be accessed by opening "
        "the plot in a new tab. The statistical significance value (based on "
        "Poisson statistics) for the best SNR and time window combination for "
        "each auxiliary channel before and after this round are shown as a "
        "baton. The round's winning channel, which had the highest "
        "significance, is shown in yellow. The top of the yellow baton is the "
        "significance of this channel before this round and the bottom of the "
        "baton is its significance in the next round, after its triggers "
        "above this round's SNR threshold and time window have been removed "
        "(note that this channel may have nonzero significance in the next "
        "round because it may still have triggers left at a lower SNR "
        "threshold). Blue batons are for channels whose significance dropped "
        "after this round (indicating that that channel had some trigger "
        "times in common with the winner) and red batons are for channels "
        "whose significance increased in the next round (due to less "
        "livetime)."
}


# -- utilities ----------------------------------------------------------------

COLUMN_LABEL = {
    'peal_frequency': r"Frequency [Hz]",
    'central_freq': r"Frequency [Hz]",
    'frequency': r"Frequency [Hz]",
    'mchirp': r"Chirp mass [M$_\odot$]",
    'new_snr': r"$\chi^2$-weighted signal-to-noise ratio (New SNR)",
    'peak_frequency': r"Frequency [Hz]",
    'rho': r"$\rho$",
    'snr': r"Signal-to-noise ratio (SNR)",
    'template_duration': r"Template duration [s]",
}


def get_column_label(column):
    try:
        return COLUMN_LABEL[column]
    except KeyError:
        return r'\texttt{{{0}}}'.format(column)


# -- Functions ----------------------------------------------------------------

def before_after_histogram(
        outfile, x, y, label1='Before', label2='After',
        bins=100, histtype='stepfilled', range=None, figsize=[9, 6], **kwargs):
    """Plot a histogram of SNR for two event distributions
    """
    # format axis arguments
    axargs = {
        'xscale': 'log',
        'xlabel': 'Loudness',
        'yscale': 'log',
        'ylabel': 'Number of events',
    }
    axargs.update(kwargs)
    # create figure
    plot = Plot(figsize=figsize)
    ax = plot.gca()
    # make histogram
    if range is None:
        range = min(map(numpy.min, (x, y))), max(map(numpy.max, (x, y)))
    axargs.setdefault('xlim', range)
    histargs = {
        'range': range,
        'histtype': histtype,
        'bins': bins,
        'linewidth': 2,
        'logbins': axargs['xscale'] == 'log',
        'alpha': .8,
    }
    ax.hist(x, label=label1, facecolor='red', edgecolor='darkred',
            **histargs)
    ax.hist(y, label=label2, facecolor='dodgerblue', edgecolor='blue',
            **histargs)
    # add legend
    ax.legend(loc='upper right')
    # format axes
    axargs.setdefault('ylim', (.5, ax.yaxis.get_data_interval()[1] * 1.05))
    _finalize_plot(plot, ax, outfile, **axargs)


def veto_scatter(outfile, a, b, label1='All', label2='Vetoed', x='time',
                 y='snr', color=None, clim=None, clabel=None, cmap=None,
                 clog=True, figsize=[9, 6], **kwargs):
    """Plot an x-y scatter of all/vetoed events
    """
    # format axis arguments
    axargs = {
        'yscale': 'log',
        'ylabel': 'Loudness',
    }
    axargs['xscale'] = 'auto-gps' if x == 'time' else 'log'
    if isinstance(y, (list, tuple)):
        ya = y[0]
        yb = y[1]
    else:
        ya = yb = y

    axargs.update(kwargs)
    # create figure
    plot = Plot(figsize=figsize)
    ax = plot.gca()
    # add data
    if color is None:
        ax.scatter(a[x], a[ya], color='black', marker='o', label=label1, s=40)
    else:
        colorargs = {'edgecolor': 'none'}
        if clim:
            colorargs['vmin'] = clim[0]
            colorargs['vmax'] = clim[1]
            if clog:
                colorargs['norm'] = LogNorm(vmin=clim[0], vmax=clim[1])
        a = a.copy()
        a.sort(color)
        m = ax.scatter(a[x], a[ya], c=a[color], label=label1, **colorargs)
        # add colorbar
        ax.colorbar(mappable=m, cmap=cmap, label=clabel)
    if isinstance(b, (list, tuple)) and len(b) == 2:
        # aux channel used/coinc (probably)
        colors = [{'color': c} for c in (
            '#ffd200',  # yellow
            '#d62728',  # red
        )]
    elif isinstance(b, (list, tuple)):
        colors = list(rcParams['axes.prop_cycle'])
    else:
        b = [b]
        label2 = [label2]
        colors = [{'color': '#d62728'}]
    for i, data in enumerate(b):
        # setting the color here looks complicated, but is just a fancy
        # way of looping through the color cycle when scattering, but using
        # red if we only have one other data set
        ax.scatter(data[x], data[yb], marker='+', linewidth=1.5,
                   label=label2[i], s=40, **colors[i % len(colors)])
    # add legend
    if ax.get_legend_handles_labels()[0]:
        legargs = {
            'loc': 'upper left',
            'bbox_to_anchor': (1.01, 1),
            'borderaxespad': 0,
            'numpoints': 1,
            'scatterpoints': 1,
            'handlelength': 1,
            'handletextpad': .5
        }
        legargs.update(dict(
            (x[7:], axargs.pop(x)) for x in list(axargs.keys()) if
            x.startswith('legend_')
        ))
        ax.legend(**legargs)
    # finalize
    for axis in ['x', 'y']:
        # get data limits
        lim = list(getattr(ax, '%saxis' % axis).get_data_interval())
        # use given ybound
        lim[0] = axargs.get('%sbound' % axis, lim[0])
        # scale out for visual
        lim[0] *= 0.95
        lim[1] *= 1.05
        # handle logs
        if axargs.get("%sscale" % axis, "linear") == "log" and lim[0] <= 0.:
            lim[0] = None
        axargs.setdefault('%slim' % axis, lim)
    _finalize_plot(plot, ax, outfile, **axargs)


def _finalize_plot(plot, ax, outfile, bbox_inches=None, close=True, **axargs):
    xlim = axargs.pop('xlim', None)
    ylim = axargs.pop('ylim', None)
    # set title and subtitle
    subtitle = axargs.pop('subtitle', None)
    # format axes
    for key in axargs:
        getattr(ax, 'set_%s' % key)(axargs[key])
    # format subtitle first
    if subtitle:
        pos = list(ax.title.get_position())
        pos[1] += 0.05
        ax.title.set_position(pos)
        ax.text(.5, 1., subtitle, transform=ax.transAxes, va='bottom',
                ha='center')
    # set minor grid for log scale
    if ax.get_xscale() == 'log':
        ax.grid(True, axis='x', which='both')
    if ax.get_yscale() == 'log':
        ax.grid(True, axis='y', which='both')
    # set limits after everything else (matplotlib might undo it)
    if xlim is not None:
        ax.set_xlim(*xlim)
    if ylim is not None:
        ax.set_ylim(*ylim)
    # save and close
    plot.save(outfile, bbox_inches=bbox_inches)
    if close:
        plot.close()


def significance_drop(outfile, old, new, show_channel_names=None, **kwargs):
    """Plot the signifiance drop for each channel
    """
    channels = sorted(old.keys())
    if show_channel_names is None:
        show_channel_names = len(channels) <= 50

    plot = Plot(figsize=(20, 5))
    plot.subplots_adjust(left=.07, right=.93)
    ax = plot.gca()
    if show_channel_names:
        plot.subplots_adjust(bottom=.4)

    winner = sorted(old.items(), key=lambda x: x[1])[-1][0]

    for i, c in enumerate(channels):
        if c == winner:
            color = 'orange'
        elif old[c] > new[c]:
            color = 'dodgerblue'
        else:
            color = 'red'
        ax.plot([i, i], [old[c], new[c]], color=color, linestyle='-',
                marker='o', markeredgecolor='k', markeredgewidth=.5,
                markersize=10, label=c, zorder=old[c])

    ax.set_xlim(-1, len(channels))
    ax.set_ybound(lower=0)

    # set xticks to show channel names
    if show_channel_names:
        ax.set_xticks(range(len(channels)))
        ax.set_xticklabels([texify(c) for c in channels])
        for i, t in enumerate(ax.get_xticklabels()):
            t.set_rotation(270)
            t.set_verticalalignment('top')
            t.set_horizontalalignment('center')
            t.set_fontsize(8)
    # or just show systems of channels
    else:
        plot.canvas.draw()
        systems = {}
        for i, c in enumerate(channels):
            sys = c.split(':', 1)[1].split('-')[0].split('_')[0]
            try:
                systems[sys][1] += 1
            except KeyError:
                systems[sys] = [i, 1]
        systems = sorted(systems.items(), key=lambda x: x[1][0])
        labels, counts = zip(*systems)
        xticks, xmticks = zip(*[(a, a+b/2.) for (a, b) in counts])
        # show ticks at the edge of each group
        ax.set_xticks(xticks, minor=False)
        ax.set_xticklabels([], minor=False)
        # show label in the centre of each group
        ax.set_xticks(xmticks, minor=True)
        for t in ax.set_xticklabels(labels, minor=True):
            t.set_rotation(270)

    kwargs.setdefault('ylabel', 'Significance')

    # create interactivity
    if outfile.endswith('.svg'):
        _finalize_plot(plot, ax, outfile.replace('.svg', '.png'),
                       close=False, **kwargs)
        tooltips = []
        ylim = ax.get_ylim()
        yoffset = (ylim[1] - ylim[0]) * 0.061
        bbox = {'fc': 'w', 'ec': '.5', 'alpha': .9, 'boxstyle': 'round'}
        xthresh = len(channels) / 10.
        for i, l in enumerate(ax.lines):
            x = l.get_xdata()[1]
            if x < xthresh:
                ha = 'left'
            elif x > (len(channels) - xthresh):
                ha = 'right'
            else:
                ha = 'center'
            y = l.get_ydata()[0] + yoffset
            c = l.get_label()
            tooltips.append(ax.annotate(texify(c), (x, y), ha=ha,
                                        zorder=ylim[1], bbox=bbox))
            l.set_gid('line-%d' % i)
            tooltips[-1].set_gid('tooltip-%d' % i)

        f = BytesIO()
        plot.savefig(f, format='svg')
        tree, xmlid = etree.XMLID(f.getvalue())
        tree.set('onload', 'init(evt)')
        for i in range(len(tooltips)):
            try:
                e = xmlid['tooltip-%d' % i]
            except KeyError:
                warnings.warn("Failed to recover tooltip %d" % i)
                continue
            e.set('visibility', 'hidden')
        for i, l in enumerate(ax.lines):
            e = xmlid['line-%d' % i]
            e.set('onmouseover', 'ShowTooltip(this)')
            e.set('onmouseout', 'HideTooltip(this)')
        tree.insert(0, etree.XML(SHOW_HIDE_JAVASCRIPT))
        etree.ElementTree(tree).write(outfile)
        plot.close()
    else:
        _finalize_plot(plot, ax, outfile, **kwargs)


def hveto_roc(outfile, rounds, figsize=[9, 6], constants=[1, 5, 10, 20],
              **kwargs):
    efficiency = []
    deadtime = []
    for r in rounds:
        try:
            efficiency.append(r.cum_efficiency[0] / r.cum_efficiency[1])
        except ZeroDivisionError:
            efficiency.append(0.)
        try:
            deadtime.append(r.cum_deadtime[0] / r.cum_deadtime[1])
        except ZeroDivisionError:
            deadtime.append(0.)
    plot = Plot(figsize=figsize)
    ax = plot.gca()
    ax.plot(deadtime, efficiency, marker='o', linestyle='-')
    try:
        xbound = 10 ** floor(log10(deadtime[0]))
    except ValueError:
        xbound = 1e-4
    try:
        ybound = 10 ** floor(log10(efficiency[0]))
    except ValueError:
        ybound = 1e-4
    bound = min(xbound, ybound)
    axargs = {
        'xlabel': 'Fractional deadtime',
        'ylabel': 'Fractional efficiency',
        'xscale': 'log',
        'yscale': 'log',
        'xlim': (bound, 1.),
        'ylim': (bound, 1.),
    }
    axargs.update(kwargs)
    # draw some eff/dt contours
    if len(constants):
        for i, c in enumerate(constants):
            g = 1 - ((i+1)/len(constants) * .5)
            x = axargs['xlim']
            y = [a * c for a in x]
            ax.plot(x, y, linestyle='--', color=(g, g, g), label=str(c))
        ax.legend(title='Eff/dt:', borderaxespad=0, bbox_to_anchor=(1.01, 1),
                  handlelength=1, handletextpad=.5, loc='upper left')
    # save and close
    _finalize_plot(plot, ax, outfile, **axargs)
