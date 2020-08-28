import inflection

def snake_case(text):
    return inflection.underscore(inflection.parameterize(text))