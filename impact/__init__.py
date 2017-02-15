__author__ = 'Naveen Venayak'

import sys
import os


try:
    from pyexcel_xlsx import get_data
except ImportError as e:
    print('Could not import pyexcel')
    print(e)
    pass

if sys.version_info.major < 3:
    raise Exception('Require Python >= 3.5')
elif sys.version_info.minor < 5:
    raise Exception('Require Python >= 3.5')

# Django ORM support
# # Add impact_cloud path and init django
# import django
# def start_db_engine():
#     BASE_DIR = os.path.dirname(os.path.abspath(__file__))
#     sys.path.append(os.path.join(BASE_DIR, '../impact_cloud'))
#     os.environ["DJANGO_SETTINGS_MODULE"] = "impact_main_site.settings"
#     django.setup()

# If in the iPython environment, initialize notebook mode
try:
    temp = __IPYTHON__
except NameError:
    from plotly.offline import plot
    from IPython.display import HTML
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
else:
    import plotly
    plotly.offline.init_notebook_mode()
    from plotly.offline import iplot as plot

try:
    os.remove('../test_impact.db')
except FileNotFoundError:
    pass


# Import the core classes
from .database import Base, init_db
from .core.TrialIdentifier import TrialIdentifier
from .core.AnalyteData import TimeCourse, TimePoint
from .core.SingleTrial import SingleTrial
from .core.ReplicateTrial import ReplicateTrial
from .core.Experiment import Experiment
from .core.Project import Project
from .plotting import *


from .core.settings import settings

from sqlalchemy import create_engine



def bind_engine():
    engine = create_engine('sqlite:///../test_impact.db',echo=settings.verbose)
    return engine

def create_session():
    from sqlalchemy.orm import sessionmaker

    engine = bind_engine()

    session_maker = sessionmaker(bind=engine)
    return session_maker()


engine = bind_engine()
Base.metadata.create_all(engine)
