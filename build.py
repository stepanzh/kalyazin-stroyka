import argparse
import jinja2
import json
import pathlib


WORKDIR_PATH = pathlib.Path(__file__).parent
TEMPLATES_PATH = WORKDIR_PATH / 'templates'
OUTPUT_DIR = WORKDIR_PATH / 'deploy'


class Service:
    def __init__(self, header, description = None):
        self.header = header
        self.description = description

    @classmethod
    def from_dict(cls, obj: dict):
        return Service(obj['header'], obj.get('description', None))


class ServiceList:
    def __init__(self, header, service_list = None):
        self.header = header
        self.service_list = service_list if service_list is not None else []

    def add_service(self, x: Service):
        self.service_list.append(x)

    @classmethod
    def from_dict(cls, obj: dict):
        service_list = ServiceList(obj['header'])
        for service_dict in obj['services']:
            service_list.add_service(Service.from_dict(service_dict))
        return service_list


class Page:
    name: str
    template_variables = dict()

    def extend_template_variables(self, variables: dict):
        self.template_variables |= variables


class PageWriter:
    def __init__(self, environment: jinja2.Environment, rootdir: pathlib.Path):
        self.environment = environment
        self.rootdir = rootdir

    def write(self, page: Page):
        filename = page.name + '.html'
        template = self.environment.get_template(filename)
        text = template.render(page.template_variables)

        with open(self.rootdir / filename, 'w') as io:
            print(text, file=io)


class IndexPage(Page):
    name = 'index'
    
    def read_service_list(self, json_path: pathlib.Path, extend_key):
        with open(json_path) as io:
            services_dict = json.load(io)
            services = ServiceList.from_dict(services_dict)
            self.extend_template_variables({extend_key: services})


def parse_commandline():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--output_dir',
        required=True,
        help='output directory for site',
    )
    parser.add_argument('--debug',
        help='generate debuggable version of site',
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    args = parser.parse_args()
    return args


def main():
    args = parse_commandline()
    environment = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATES_PATH))
    pagewriter = PageWriter(environment, pathlib.Path(args.output_dir))

    index_page = IndexPage()
    index_page.read_service_list(WORKDIR_PATH / 'content' / 'services' / 'building.json', 'build_services')
    index_page.read_service_list(WORKDIR_PATH / 'content' / 'services' / 'finishing.json', 'finish_services')

    pages = [index_page]

    for page in pages:
        page.extend_template_variables({
            'isdebug': args.debug,
        })
        pagewriter.write(page)


if __name__ == '__main__':
    main()
