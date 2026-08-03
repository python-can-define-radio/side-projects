# TODO
# assert translate_ni("""
# '''trapure-output-only
# listconcat a b = a ++ b
# '''

# def listconcat(a, b):
#     # trapure-ignore
#     return a + b

# def itemAtEnd(list_, newitem):
#     return listconcat(list_, [newitem])
# """) == """\
# and some more stuff
# itemAtEnd list_ newitem = listconcat list_ [newitem]"""
