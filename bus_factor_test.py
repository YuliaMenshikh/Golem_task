import pytest
import bus_factor


def test_make_query():
    params = {
        'sort': 'stars',
        'order': 'desc',
        'per_page': 100,
    }
    assert bus_factor.make_query(params) == 'sort=stars&order=desc&per_page=100'


@pytest.mark.asyncio
async def test_send_get_request():
    per_page = 10
    http_query = bus_factor.make_query({
        'q': 'language:rust',
        'sort': 'stars',
        'order': 'desc',
        'per_page': per_page,
        'page': 1
    })
    url = f'{bus_factor.BASE_URL}/search/repositories?{http_query}'
    response = await bus_factor.send_get_request(url)
    data = await response.json()
    projects = data['items']
    assert response.status == 200
    assert len(projects) == per_page


@pytest.mark.asyncio
async def test_search_repositories():
    projects = await bus_factor.search_repositories("language:python", "stars", "desc", 5)
    assert len(projects) == 5


@pytest.mark.asyncio
async def test_get_contributors_stats():
    project = bus_factor.Project(177736533, '996.ICU', bus_factor.User(48942249, '996icu'))
    projects_stat = {}
    await bus_factor.process_project(project, projects_stat)
    assert projects_stat[project.id][0] == '996icu'
