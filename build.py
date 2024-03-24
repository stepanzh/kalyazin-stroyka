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
    def __init__(self, header, description = None, service_list = None):
        self.header = header
        self.description = description
        self.service_list = service_list if service_list is not None else []

    def add_service(self, x: Service):
        self.service_list.append(x)

    @classmethod
    def from_dict(cls, obj: dict):
        service_list = ServiceList(obj['header'], obj.get('description', None))
        for service_dict in obj.get('services', []):
            service_list.add_service(Service.from_dict(service_dict))
        return service_list


class ServiceListReader:
    def read(self, path: pathlib.Path) -> ServiceList:
        with open(path) as io:
            services_dict = json.load(io)
            services = ServiceList.from_dict(services_dict)
            return services


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

    service_reader = ServiceListReader()
    build_services = service_reader.read(WORKDIR_PATH / 'content' / 'services' / 'building.json')
    finish_services = service_reader.read(WORKDIR_PATH / 'content' / 'services' / 'finishing.json')
    repair_services = service_reader.read(WORKDIR_PATH / 'content' / 'services' / 'repairing.json')
    not_services = service_reader.read(WORKDIR_PATH / 'content' / 'services' / 'notservicing.json')

    index_page = IndexPage()
    index_page.extend_template_variables({'services': [build_services, finish_services, repair_services, not_services]})

    pages = [index_page]

    for page in pages:
        page.extend_template_variables({
            'isdebug': args.debug,
        })
        pagewriter.write(page)


if __name__ == '__main__':
    main()
