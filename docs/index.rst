.. impact framework documentation master file, created by
   sphinx-quickstart on Fri Apr 22 14:25:15 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Documentation
=============================================================================
The impact framework helps scientists and engineers analyze data for characterizing microbial physiology.
Data can be imported from analytical equipment such as HPLC and plate reader using native data
formats. From here, data is parsed into a hierarchical data structure based on the logical organization
of trials in an experiment, based on its identifying metadata. Then, this data can be used to generate
visualizations using a plotting package, there are many options but we rely on plotly because
it is mostly open-source, is written in js and provides interactivity within a browser, and provides
numerous interfaces to other languages such as matlab and python.

This documentation describes use of the core impact module, which does most of the heavy-lifting.
Use of the module is demonstrated using the jupyter notebook, which is a web-based user interface
allowing scientists to store prose describing experiments and code to analyze data and generate visualizations
together, greatly increasing the transparency of data analysis.

For first time users, visit :doc:`quick_install` to install the package.
Then, head over to the :doc:`quickstart` tutorial to begin importing and
analyzing data.

To learn more about the features which are automatically extracted from the
data and visualization of these features, follow the :doc:`1_features_0` tutorial.

Finally, all of the classes and methods which compose the module are documented
:doc:`impact`

Contents
-----
.. toctree::
   :maxdepth: 2

   quick_install
   quickstart
   0_getting_started
   1_features_0
   2_features_1
   3_import_experiment_data
   impact


Indices and tables
-----

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

