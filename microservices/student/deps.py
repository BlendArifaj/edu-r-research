from common.bind import EngineBinder
from student.models import Base

binder = EngineBinder(Base)
configure = binder.configure
get_db = binder.get_db
