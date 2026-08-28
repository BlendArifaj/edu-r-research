from attendance.models import Base
from common.bind import EngineBinder

binder = EngineBinder(Base)
configure = binder.configure
get_db = binder.get_db
