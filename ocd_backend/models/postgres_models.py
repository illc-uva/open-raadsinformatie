from sqlalchemy import Column, Sequence, String, ForeignKey, DateTime, SmallInteger, BigInteger, func, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from sqlalchemy_utils.types import UUIDType


Base = declarative_base()


class Source(Base):
    __tablename__ = 'source'

    id = Column(BigInteger, Sequence('source_id_seq'), primary_key=True, index=True)
    iri = Column(String, index=True)
    resource_ori_id = Column(BigInteger, ForeignKey("resource.ori_id"), nullable=False, index=True)
    canonical_iri = Column(String)
    canonical_id = Column(String)
    used_file = Column(String)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now())

    resource = relationship("Resource", back_populates="sources")


class Resource(Base):
    __tablename__ = 'resource'

    ori_id = Column(BigInteger, Sequence('ori_id_seq'), primary_key=True, index=True)
    iri = Column(String)

    sources = relationship("Source", back_populates="resource")
    properties = relationship("Property", back_populates="resource", foreign_keys="Property.resource_id")
    enricher_logs = relationship("EnricherLogModel", back_populates="resource", foreign_keys="EnricherLogModel.resource_id")


class Property(Base):
    __tablename__ = 'property'
    __table_args__ = (
        CheckConstraint('NOT(prop_resource IS NULL AND '
                        'prop_string IS NULL AND '
                        'prop_datetime IS NULL AND '
                        'prop_integer IS NULL AND '
                        'prop_url IS NULL'),
    )

    id = Column(UUIDType(), primary_key=True, index=True)
    resource_id = Column(BigInteger, ForeignKey("resource.ori_id"), nullable=False, index=True)
    predicate = Column(String, nullable=False, index=True)
    order = Column(SmallInteger, nullable=True)
    prop_resource = Column(BigInteger, ForeignKey("resource.ori_id"), nullable=True, index=True)
    prop_string = Column(String, nullable=True)
    prop_datetime = Column(DateTime, nullable=True)
    prop_integer = Column(BigInteger, nullable=True)
    prop_url = Column(String, nullable=True)

    resource = relationship("Resource", back_populates="properties", foreign_keys=resource_id)


class EnricherLogModel(Base):
    __tablename__ = 'enricher_log'

    id = Column(BigInteger, Sequence('enricher_log_id_seq'), primary_key=True, index=True)
    resource_id = Column(BigInteger, ForeignKey("resource.ori_id"), nullable=False, index=True)
    enricher_class = Column(String, nullable=False)
    task = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())

    resource = relationship("Resource", back_populates="enricher_logs", foreign_keys=resource_id)
