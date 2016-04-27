from sqlalchemy import Table, Column, Boolean, DateTime, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from db import Base

person_organization_member = Table('person_organization_member_association', Base.metadata,
    Column('person_id', Integer, ForeignKey('person.id')),
    Column('organization_id', Integer, ForeignKey('organization.id')),
)

person_organization_contributor = Table('person_organization_contributor_association', Base.metadata,
    Column('person_id', Integer, ForeignKey('person.id')),
    Column('organization_id', Integer, ForeignKey('organization.id')),
)

person_repository_contributor = Table('person_repository_contributor_association', Base.metadata,
    Column('person_id', Integer, ForeignKey('person.id')),
    Column('repository_id', Integer, ForeignKey('repository.id')),
)


class Progress(Base):
    __tablename__ = "progress"

    id = Column(Text, primary_key=True, autoincrement=False)
    value = Column(Integer)


class Organization(Base):
    __tablename__ = "organization"

    id = Column(Integer, primary_key=True, autoincrement=False)
    login = Column(Text)
    name = Column(Text)
    update_date = Column(DateTime)
    created_date = Column(DateTime)
    type = Column(Text)
    grouping = Column(Text)
    geography = Column(Text)
    contributors = relationship("Person", secondary=person_organization_contributor, backref="contributor_organizations")
    members = relationship("Person", secondary=person_organization_member, backref="member_organizations")
    repositories = relationship("Repository", backref="organization")


class Repository(Base):
    __tablename__ = "repository"

    id = Column(Integer, primary_key=True, autoincrement=False)
    organization_id = Column(Integer, ForeignKey('organization.id'))
    name = Column(Text)
    fork = Column(Text)
    push_date = Column(DateTime)
    created_date = Column(DateTime)
    language = Column(Text)
    license = Column(Text)
    forks_count = Column(Integer)
    stargazers_count = Column(Integer)
    network_count = Column(Integer)
    watchers_count = Column(Integer)
    source_government = Column(Boolean)
    source_civic = Column(Boolean)
    source_owner_id = Column(Integer)
    source_owner_login = Column(Text)
    source_repository_id = Column(Integer)
    source_repository_name = Column(Text)
    contributors = relationship("Person", secondary=person_repository_contributor, backref="contributor_repositories")


class Person(Base):
    __tablename__ = "person"

    id = Column(Integer, primary_key=True, autoincrement=False)
    login = Column(Text)
    name = Column(Text)
    update_date = Column(DateTime)
    created_date = Column(DateTime)
