import pytest
import bus_factor
from aioresponses import aioresponses


def test_make_query():
    params = {
        'sort': 'stars',
        'order': 'desc',
        'per_page': 100,
    }
    assert bus_factor.make_query(params) == 'sort=stars&order=desc&per_page=100'


@pytest.mark.asyncio
async def test_send_get_request():
    json_obj = {'items': [i for i in range(10)]}
    url = f'{bus_factor.BASE_URL}'
    with aioresponses() as m:
        m.get(url, status=200, payload=json_obj)
        response = await bus_factor.send_get_request(url)
        assert response.status == 200
        data = await response.json()
        assert data == json_obj


@pytest.mark.asyncio
async def test_search_repositories():
    http_query = bus_factor.make_query({
        'q': 'language:python',
        'sort': 'stars',
        'order': "desc",
        'per_page': bus_factor.PER_PAGE,
        'page': 1
    })
    url = f'{bus_factor.BASE_URL}/search/repositories?{http_query}'
    json_obj = {'items': [{'id': i, 'name': 'test_name', 'owner': {'id': i, 'login': 'test_login'}}
                          for i in range(10)]}
    with aioresponses() as m:
        m.get(url, status=200, payload=json_obj)
        projects = await bus_factor.search_repositories("language:python", "stars", "desc", 5)
        assert len(projects) == 5


@pytest.mark.asyncio
async def test_search_repositories_error():
    http_query = bus_factor.make_query({
        'q': 'language:python',
        'sort': 'stars',
        'order': "desc",
        'per_page': bus_factor.PER_PAGE,
        'page': 1
    })
    url = f'{bus_factor.BASE_URL}/search/repositories?{http_query}'
    with aioresponses() as m:
        m.get(url, status=400, payload={})
        with pytest.raises(RuntimeError):
            await bus_factor.search_repositories("language:python", "stars", "desc", 5)


@pytest.mark.asyncio
async def test_get_contributors_stats():
    project = bus_factor.Project(304, 'test', bus_factor.User(405, 'test'))
    url = f'{bus_factor.BASE_URL}/repos/{project.owner.login}/{project.name}/contributors?per_page={bus_factor.PER_PAGE}&page=1'
    json_obj = [{'id': i, 'login': 'test', 'contributions': i} for i in range(bus_factor.PER_PAGE)]
    url2 = f'{bus_factor.BASE_URL}/repos/{project.owner.login}/{project.name}/contributors?per_page={bus_factor.PER_PAGE}&page=2'
    with aioresponses() as m:
        m.get(url, status=200, payload=json_obj)
        m.get(url2, status=204, payload={})
        result = await bus_factor.get_contributors_stats(project)
        assert len(result) == bus_factor.PER_PAGE


@pytest.mark.asyncio
async def test_get_contributors_stats_error():
    project = bus_factor.Project(304, 'test', bus_factor.User(405, 'test'))
    url = f'{bus_factor.BASE_URL}/repos/{project.owner.login}/{project.name}/contributors?per_page={bus_factor.PER_PAGE}&page=1'
    with aioresponses() as m:
        m.get(url, status=400, payload={})
        with pytest.raises(RuntimeError):
            await bus_factor.get_contributors_stats(project)


@pytest.mark.asyncio
async def test_process_project():
    project = bus_factor.Project(304, 'test', bus_factor.User(405, 'test'))
    projects_stat = {}
    url = f'{bus_factor.BASE_URL}/repos/{project.owner.login}/{project.name}/contributors?per_page={bus_factor.PER_PAGE}&page=1'
    json_obj = [{'id': i, 'login': 'test', 'contributions': i} for i in range(bus_factor.PER_PAGE)]
    json_obj[-1]['contributions'] = 100000
    url2 = f'{bus_factor.BASE_URL}/repos/{project.owner.login}/{project.name}/contributors?per_page={bus_factor.PER_PAGE}&page=2'
    with aioresponses() as m:
        m.get(url, status=200, payload=json_obj)
        m.get(url2, status=204, payload={})
        await bus_factor.process_project(project, projects_stat)
        assert len(projects_stat.keys()) == 1
        assert projects_stat[project.id] == ('test',
                                             json_obj[-1]['contributions'] / sum([json_obj[-(i+1)]['contributions']
                                             for i in range(bus_factor.TOP_CONTRIBUTORS_COUNT)]))
