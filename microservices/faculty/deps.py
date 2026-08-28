from common.bind import EngineBinder
from faculty.models import Base

binder = EngineBinder(Base)
configure = binder.configure
get_db = binder.get_db
