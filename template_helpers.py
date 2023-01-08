from fastapi.templating import Jinja2Templates


class Jinja2TemplatesCustom(Jinja2Templates):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__add_all_filters_to_template_env()

    def is_dict(self, input):
        if isinstance(input, dict):
            return True 
        return False

    def to_str(self, inp):
        return str(inp)

    def endswith(self, inp):
        s, check = inp.split('||')
        return s.endswith(check)

    def rem_base(self, inp):
        url, rem = inp.split('||')
        return url.replace(rem, '')

    def __add_all_filters_to_template_env(self):
        self.env.filters['isdict'] = self.is_dict
        self.env.filters['tostr'] = self.to_str
        self.env.filters['endswith'] = self.endswith
        self.env.filters['rembase'] = self.rem_base
