from urllib.parse import quote
import requests
import os.path

path_template = 'https://www.demirramon.com/gen/undertale_text_box.png?{}'


class UndertaleTextBox:
    props = ['box', 'boxcolor', 'character', 'expression', 'url', 'charcolor',
                    'font', 'asterisk', 'small', 'border', 'mode']

    def __init__(self, text, **params):
        self.text = text
        self._params = params

        def prop(key):
            def getter(self):
                if key in self._params:
                    return self._params[key]
                return None
            return property(getter)

        for key in UndertaleTextBox.props:
            setattr(self, key, prop(key))

    @property
    def url(self):
        pass



def url_from_params(message, **params):
    before_params = ' '.join(key+'='+value for key, value in params.items())
    return path_template.format('message='+quote(before_params + ' ' + message))


def fetch_text_box(url, filename=None):
    r = requests.get(url, stream=True)
    if filename is None:
        counter = 0
        filename = 'undertale_text_box.png'
        while os.path.exists(filename):
            counter += 1
            filename = f'undertale_text_box_{counter}.png'

    with open(filename, 'wb') as f:
        f.write(r.content)
    return filename


if __name__ == '__main__':
    url = url_from_params('looking good, kiddo', character='sans')
    image = fetch_text_box(url)

