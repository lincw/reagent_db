# Import all routes
from app.routes.main import *
from app.routes.search import *
from app.routes.add import *
from app.routes.import_export import *
from app.routes.api import *
from app.routes.config import *  # Import configuration routes
from app.routes.detail import *  # Import detail view routes
# Re-enabling BLAST routes with improved implementation
from app.routes.blast import *
