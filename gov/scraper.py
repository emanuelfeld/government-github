from github import Github, UnknownObjectException
from settings import ACCESS_TOKEN
from models import Organization, Repository, Person, Progress
from db import session
import yaml
import time
import logging


##############################
# GitHub response formatters #
##############################


def o_formatter(organization, grouping, type):
    # Organization data formatter
    return {
        "id": organization.id,
        "login": organization.login,
        "name": organization.name,
        "update_date": organization.updated_at,
        "created_date": organization.created_at,
        "grouping": grouping,
        "type": type
    }


def r_formatter(repository):
    # Repository data formatter
    return {
        "id": repository.id,
        "name": repository.name,
        "language": repository.language,
        "license": deep_hasattr(repository, "license", "name"),
        "fork": repository.fork,
        "push_date": repository.pushed_at,
        "created_date": repository.created_at,
        "stargazers_count": repository.stargazers_count,
        "network_count": repository.network_count,
        "watchers_count": repository.watchers_count,
        "forks_count": repository.forks_count,
        "source_repository_id": deep_hasattr(repository, "source", "id"),
        "source_repository_name": deep_hasattr(repository, "source", "name"),
        "source_owner_id": deep_hasattr(repository, "source", "owner", "id"),
        "source_owner_login": deep_hasattr(repository, "source", "owner", "login")
    }


def p_formatter(person):
    # Person (member or contributor) data formatter
    return {
        "id": person.id,
        "login": person.login,
        "name": person.name,
        "update_date": person.updated_at,
        "created_date": person.created_at
    }


####################
# Helper Functions #
####################

def deep_hasattr(object, *names):
    # Determine if an object attribute exists, for any level of nesting
    for name in names:
        if not hasattr(object, name):
            return None
        object = getattr(object, name)
    return object


def reshape_data(data):
    # Reshape GitHub organization data to more easily iterate
    reshaped_data = []
    groupings = data.keys()
    for grouping in groupings:
        reshaped_data.extend([{"grouping": grouping, "entity": entity} for entity in data[grouping]])
    return reshaped_data


def check_rate_limit(data):
    # Stall if exhausting GitHub API rate limit. Has a bit of a buffer.
    # remaining = int(data['x-ratelimit-remaining'])
    remaining = int(data._headers['x-ratelimit-remaining'])
    if remaining < 150:
        reset_time = int(data._headers['x-ratelimit-reset'])
        delay = reset_time - time.time()
        time.sleep(delay)


def upsert(model, unique_key, item, return_new=True, return_existing=True):
    # Update or insert objects into the database.
    # Optionally return updated and/or inserted objects.
    try:
        item_modelled = model(**item)
        session.add(item_modelled)
        session.commit()
        if return_new:
            return item_modelled
    except:
        session.rollback()
        existing = session.query(model).filter(getattr(model, unique_key) == item[unique_key]).first()
        try:
            for arg, value in item.iteritems():
                if getattr(existing, arg) != value:
                    setattr(existing, arg, value)
            session.commit()
            if return_existing:
                return existing
        except:
            session.rollback()


def upsert_organization(name, grouping, type):
    o_data = G.get_organization(name)
    organization = o_formatter(o_data, grouping, type)
    insert = upsert(model=Organization, unique_key='id', item=organization)
    check_rate_limit(o_data)
    return o_data


def upsert_repositories(o_data):
    organization = session.query(Organization).filter(Organization.id==o_data.id).first()

    r_data = o_data.get_repos()
    repositories = []
    for r_item in r_data:
        check_rate_limit(r_item)
        repository = r_formatter(r_item)
        source_login = repository['source_owner_login']
        if source_login:
            repository['source_civic'] = source_login.lower() in organizations_civic            
            repository['source_government'] = source_login.lower() in organizations_government
        else:
            repository['source_government'] = True
        repository = upsert(model=Repository, unique_key='id', item=repository)
        repositories.append(repository)

    organization.repositories = repositories

    try:
        session.add(organization)
        session.commit()
        return r_data
    except:
        session.rollback()


def upsert_members(o_data):
    organization = session.query(Organization).filter(Organization.id==o_data.id).first()

    m_data = o_data.get_members()
    members = []
    for m_item in m_data:
        check_rate_limit(m_item)
        member = p_formatter(m_item)
        member = upsert(model=Person, unique_key='id', item=member)
        members.append(member)

    organization.members = members

    try:
        session.add(organization)
        session.commit()
    except:
        session.rollback()


def upsert_contributors(o_data, r_data):
    organization = session.query(Organization).filter(Organization.id==o_data.id).first()

    contributors = set()
    for r_item in r_data:
        if not r_item.fork:
            c_data = r_item.get_contributors()
            repo_contributors = []
            for c_item in c_data:
                check_rate_limit(c_item)
                contributor = p_formatter(c_item)
                contributor = upsert(model=Person, unique_key='id', item=contributor)
                contributors.add(contributor)
                repo_contributors.append(contributor)

            repository = session.query(Repository).filter(Repository.id==r_item.id).first()
            repository.contributors = repo_contributors
            session.add(repository)
            session.commit()

    contributors = list(contributors)
    organization.contributors = contributors

    try:
        session.add(organization)
        session.commit()
    except:
        session.rollback()


if __name__ == "__main__":
    logging.basicConfig(filename="scraper.log", level=logging.INFO)
    G = Github(ACCESS_TOKEN)
    progress = session.query(Progress).first()
    if not progress:
        progress = Progress(id="progress", value=0)

    with open('government.github.com/_data/governments.yml') as infile:
        _data = yaml.load(infile)
    data = reshape_data(_data)
    organizations_government = set([organization['entity'].lower() for organization in data]) 

    with open('government.github.com/_data/civic_hackers.yml') as infile:
        _data_civic = yaml.load(infile)
    data_civic = reshape_data(_data_civic)
    organizations_civic = set([organization['entity'].lower() for organization in data_civic])

    for i in xrange(progress.value, len(data)):
        logging.info("{} {} {}".format(i, data[i]['entity'], data[i]['grouping']))
        try:
            o_data = upsert_organization(data[i]['entity'], data[i]['grouping'], "government")
            r_data = upsert_repositories(o_data)
            upsert_contributors(o_data, r_data)
            upsert_members(o_data)
            progress.value = i+1
            session.add(progress)
            session.commit()
        except UnknownObjectException:
            pass

    progress.value = 0
