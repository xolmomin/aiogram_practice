from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin, ModelView

import models
from models import Channel, User

app = Starlette()  # FastAPI()

# Create admin
admin = Admin(models.db._engine, base_url='/', title="Aiogram Admin")

# Add view
admin.add_view(ModelView(Channel))
admin.add_view(ModelView(User))

# Mount admin to your app
admin.mount_to(app)
