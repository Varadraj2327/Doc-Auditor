# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the lines below or read the documentation at
# https://firebase.google.com/docs/functions

from firebase_functions import https_fn
from firebase_admin import initialize_app
from app import app as flask_app

initialize_app()

@https_fn.on_request()
def doc_auditor_api(req: https_fn.Request) -> https_fn.Response:
    with flask_app.request_context(req.environ):
        return flask_app.full_dispatch_request()
