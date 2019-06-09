import sys

def catch(msg = ""):
	__func__ = sys._getframe().f_back.f_code.co_name
	exc_type, exc_obj, exc_tb = sys.exc_info()
	print("%s: %s on line %d: %s%s" %(__func__, exc_type, exc_tb.tb_lineno, exc_obj, msg))
