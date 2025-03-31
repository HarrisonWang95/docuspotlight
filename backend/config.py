import os

class Config:
    DEBUG = False
    TESTING = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    EXTRACT_RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extract_results')
    PARSE_RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'parse_results')
    RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
    SCHEMA_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema')
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
    MARKDOWN_ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
    MULTIMODAL_ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}