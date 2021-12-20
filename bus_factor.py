import argparse
import asyncio
import aiohttp
import os

from contextlib import nullcontext
from dataclasses import dataclass


@dataclass
class User:
    id: int
    login: str


@dataclass
class Project:
    id: int
    name: str
    owner: User


@dataclass
class Contributor:
    user: User
    contributions: int


BASE_URL = 'https://api.github.com'
BOUNDARY_PERCENTAGE = 0.75
PER_PAGE = 100
TOP_CONTRIBUTORS_COUNT = 25


def make_query(params):
    result = ''
    for k, v in params.items():
        if len(result) > 0:
            result = f'{result}&{k}={v}'
        else:
            result = f'{k}={v}'
    return result


async def send_get_request(url, session=None):
    if session is None:
        session = aiohttp.ClientSession()
        context = session
    else:
        context = nullcontext()

    async with context:
        response = await session.get(url, headers={
            'accept': 'application/vnd.github.v3+json',
            'Authorization': f'token {os.getenv("GITHUB_TOKEN")}'
        })
        await response.read()
    return response


async def search_repositories(query, sort, order, project_count, session=None):
    result = [None] * project_count

    async def process_page(i):
        http_query = make_query({
            'q': query,
            'sort': sort,
            'order': order,
            'per_page': PER_PAGE,
            'page': i + 1
        })
        response = await send_get_request(f'{BASE_URL}/search/repositories?{http_query}', session)
        if response.status != 200:
            raise RuntimeError(f'Repositories request failed, code {response.status} body {response.text}')
        data = await response.json()
        projects = data['items']
        if len(projects) < min(project_count, (i + 1) * PER_PAGE) - i * PER_PAGE:
            raise RuntimeError(f'There is not so many repositories')
        if i * PER_PAGE + len(projects) > project_count:
            projects = projects[:project_count - i * PER_PAGE]
        for j in range(min(project_count, (i + 1) * PER_PAGE) - i * PER_PAGE):
            result[j + i * PER_PAGE] = Project(id=projects[j]['id'],
                                               name=projects[j]['name'],
                                               owner=User(id=projects[j]['owner']['id'],
                                               login=projects[j]['owner']['login']))

    await asyncio.gather(*[process_page(i) for i in range((project_count + PER_PAGE - 1) // PER_PAGE)])

    return result


async def get_contributors_stats(project, session=None):
    cur_page = 1
    result = []
    while True:
        http_query = make_query({
            'per_page': PER_PAGE,
            'page': cur_page
        })
        response = await send_get_request(f'{BASE_URL}/repos/{project.owner.login}/{project.name}/contributors?{http_query}', session)
        if response.status == 204:
            break
        if response.status != 200:
            raise RuntimeError(f'Failed request, code {response.status} body {response.text}')
        data = await response.json()
        if len(data) == 0:
            break
        result += [Contributor(user=User(id=contributor['id'], login=contributor['login']),
                               contributions=contributor['contributions'])
                   for contributor in data]
        cur_page += 1
    return result


async def process_project(project, projects_stat):
    contributors = await get_contributors_stats(project)
    contributors.sort(key=lambda x: x.contributions, reverse=True)
    user_name = contributors[0].user.login

    total_sum = 0
    for contrib in contributors[:TOP_CONTRIBUTORS_COUNT]:
        total_sum += contrib.contributions

    percentage = contributors[0].contributions / total_sum
    if percentage > BOUNDARY_PERCENTAGE:
        projects_stat[project.id] = (user_name, percentage)


async def get_projects_stat(language, project_count):
    projects = await search_repositories("language:{}".format(language), "stars", "desc", project_count)

    projects_stat = {}
    await asyncio.gather(*[process_project(project, projects_stat) for project in projects])

    for project in projects:
        if project.id in projects_stat:
            user, percentage = projects_stat[project.id]
            print("project: {:<15}user: {:<15}percentage: {:.2f}".format(project.name, user, percentage))


async def main(args):
    await get_projects_stat(args.language, args.project_count)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--language', type=str, default='rust')
    parser.add_argument('--project_count', type=int, default=50)
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(args))
