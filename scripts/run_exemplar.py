"""Executes the exemplar notebook in place using nbclient (bypasses the
broken nbconvert CLI entry point caused by a stale jupyter_contrib_nbextensions
plugin in this environment)."""

import os
import nbformat
from nbclient import NotebookClient

ROOT = os.path.join(os.path.dirname(__file__), "..")
NB_PATH = os.path.join(ROOT, "exemplar_data_analysis_portfolio_pharma.ipynb")

nb = nbformat.read(NB_PATH, as_version=4)
client = NotebookClient(nb, timeout=600, kernel_name="python3", resources={"metadata": {"path": ROOT}})
client.execute()

nbformat.write(nb, NB_PATH)
print("Executed and saved:", NB_PATH)
