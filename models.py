from sqlalchemy import (
    create_engine, Column, Integer, String, Float, ForeignKey, DateTime
)
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
import datetime

# Base do SQLAlchemy (api moderna)
Base = declarative_base()


# ============================================================
#  DATABASE MANAGER — SINGLETON CORRIGIDO
# ============================================================

class DatabaseManager:
    """
    Singleton correto para gerenciar a engine e sessões.
    Não recria o banco nem a engine mais de uma vez.
    """

    _instance = None

    def __new__(cls, db_uri='sqlite:///autoar.db'):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

            cls._instance.engine = create_engine(
                db_uri,
                connect_args={"check_same_thread": False}  # SQLite + Flask fix
            )
            cls._instance.Session = sessionmaker(bind=cls._instance.engine)

        return cls._instance

    def get_session(self):
        return self.Session()

    def create_all(self):
        Base.metadata.create_all(self.engine)


# ============================================================
#  MODELO PRINCIPAL: CLIENTES
# ============================================================

class Client(Base):
    __tablename__ = 'clients'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    address = Column(String(200))
    phone = Column(String(20))
    email = Column(String(100))

    vehicles = relationship(
        "Vehicle",
        back_populates="client",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Client(id={self.id}, name='{self.name}')>"


# ============================================================
#  VEÍCULOS
# ============================================================

class Vehicle(Base):
    __tablename__ = 'vehicles'

    id = Column(Integer, primary_key=True)
    make = Column(String(50), nullable=False)
    model = Column(String(50), nullable=False)
    year = Column(Integer)
    license_plate = Column(String(20), unique=True)
    client_id = Column(Integer, ForeignKey('clients.id'))

    client = relationship("Client", back_populates="vehicles")
    services = relationship(
        "Service",
        back_populates="vehicle",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Vehicle(id={self.id}, plate='{self.license_plate}')>"


# ============================================================
#  SERVIÇOS
# ============================================================

class Service(Base):
    __tablename__ = 'services'

    id = Column(Integer, primary_key=True)
    description = Column(String(200), nullable=False)
    cost = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id'))

    vehicle = relationship("Vehicle", back_populates="services")
    parts = relationship("ServicePart", back_populates="service",
                         cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Service(id={self.id}, desc='{self.description}')>"


# ============================================================
#  PEÇAS
# ============================================================

class Part(Base):
    __tablename__ = 'parts'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)

    service_links = relationship(
        "ServicePart",
        back_populates="part",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Part(id={self.id}, name='{self.name}', stock={self.stock})>"


# ============================================================
#  SERVICE-PART (TABELA ASSOCIATIVA COM QUANTIDADE)
# ============================================================

class ServicePart(Base):
    """
    Modelo da associação entre Serviço e Peça,
    contendo também a QUANTIDADE usada.
    """

    __tablename__ = 'service_part'

    service_id = Column(Integer, ForeignKey('services.id'), primary_key=True)
    part_id = Column(Integer, ForeignKey('parts.id'), primary_key=True)
    quantity = Column(Integer, default=1)

    service = relationship("Service", back_populates="parts")
    part = relationship("Part", back_populates="service_links")

    def __repr__(self):
        return f"<ServicePart(service={self.service_id}, part={self.part_id}, qty={self.quantity})>"


# ============================================================
#  FACTORY METHOD
# ============================================================

class ModelFactory:
    @staticmethod
    def create_model(model_name, **kwargs):
        classes = {
            'Client': Client,
            'Vehicle': Vehicle,
            'Service': Service,
            'Part': Part,
            'ServicePart': ServicePart
        }

        if model_name not in classes:
            raise ValueError(f"Unknown model: {model_name}")

        return classes[model_name](**kwargs)


# ============================================================
#  FACADE — APERFEIÇOADA
# ============================================================

class WorkshopServiceFacade:
    """
    Operação completa para registrar serviços com múltiplas peças.
    """

    def __init__(self, db_manager):
        self.db_manager = db_manager

    def register_service_with_parts(self, vehicle_id, description, cost, parts_list):
        """
        parts_list = [{"part_id": 3, "quantity": 2}, ...]
        """

        session = self.db_manager.get_session()
        try:
            service = Service(
                description=description,
                cost=cost,
                vehicle_id=vehicle_id
            )

            session.add(service)
            session.flush()

            for p in parts_list:
                part = session.get(Part, p["part_id"])
                if not part:
                    continue

                # vínculo com quantidade
                sp = ServicePart(
                    service_id=service.id,
                    part_id=part.id,
                    quantity=p["quantity"]
                )

                session.add(sp)

                # atualiza estoque
                part.stock -= p["quantity"]

            session.commit()
            return service

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()
