import argparse
import jinja2
import json
import pathlib
import shutil


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


# TODO: should be logged to stderr
class Project:
    img_dir = WORKDIR_PATH / 'static' / 'img' / 'projects'

    def __init__(self, header, description, images):
        self.header = header
        self.description = description
        self.images = images
        self.image_links = []

        self._copy_images()

    def _copy_images(self):
        copy_to_dir = self.img_dir / self.images[0].parent.stem

        if (copy_to_dir.is_dir()):
            print('Directory is not empty', copy_to_dir)
            print('Clearing...')
            shutil.rmtree(copy_to_dir)

        copy_to_dir.mkdir(parents=True, exist_ok=True)
        self.images_links = []
        site_img_root = '/'.join(self.img_dir.parts[:2])

        for image in self.images:
            copy_from = image
            project_dirname = image.parent.stem
            copy_to = copy_to_dir / image.name

            print('copying from', copy_from)
            print('          to', copy_to)
            shutil.copyfile(copy_from, copy_to)

            img_link = '/'.join(copy_to.parts[-4:])
            self.image_links.append(img_link)
            print('  image link', img_link)

    @classmethod
    def from_dict(cls, obj: dict, obj_path: pathlib.Path):
        images = [ obj_path.parent / img for img in obj['images'] ]
        return Project(obj['header'], obj['description'], images)


class ProjectsReader:
    projects_dir = WORKDIR_PATH / 'content' / 'projects'
    projects_config = projects_dir / 'config.json'

    def read(self):
        with open(self.projects_config) as io:
            config = json.load(io)
            order = config['order']
        
        for project_dir in order:
            dict_path = self.projects_dir / project_dir / 'content.json'
            
            with open(dict_path) as io:
                project_dict = json.load(io)

            yield Project.from_dict(project_dict, dict_path)


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

    # services
    service_reader = ServiceListReader()
    build_services = service_reader.read(WORKDIR_PATH / 'content' / 'services' / 'building.json')
    finish_services = service_reader.read(WORKDIR_PATH / 'content' / 'services' / 'finishing.json')
    repair_services = service_reader.read(WORKDIR_PATH / 'content' / 'services' / 'repairing.json')
    not_services = service_reader.read(WORKDIR_PATH / 'content' / 'services' / 'notservicing.json')

    # projects
    projects_reader = ProjectsReader()
    projects = list(projects_reader.read())

    index_page = IndexPage()
    index_page.extend_template_variables({
        'services': [build_services, finish_services, repair_services, not_services],
        'projects': projects,
    })

    pages = [index_page]

    for page in pages:
        page.extend_template_variables({
            'isdebug': args.debug,
        })
        pagewriter.write(page)


if __name__ == '__main__':
    main()
