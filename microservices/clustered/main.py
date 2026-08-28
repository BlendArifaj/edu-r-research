import os

from clustered.assembly import create_campus_app

app = create_campus_app(library_url=os.environ.get("SEMS_LIBRARY_URL"))
