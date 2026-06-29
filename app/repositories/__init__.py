"""
Data access layer and repository pattern implementations
"""

from app.repositories.patient_repository import PatientRepository
from app.repositories.statistics_repository import StatisticsRepository

__all__ = ["PatientRepository", "StatisticsRepository"]
