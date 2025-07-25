import logging
from unittest.mock import AsyncMock

import pytest
from fastapi.exceptions import HTTPException

from app.applications import ApplicationResponseSchema, ApplicationService
from app.exceptions import KafkaMessageError
from tests.utils.factories import ApplicationFactory
from tests.utils.utils import kafka_error_detail

logger = logging.getLogger(__name__)

mock_repository = AsyncMock()
mock_kafka = AsyncMock()
user_log_service = AsyncMock()


@pytest.mark.asyncio
async def test_create_application__success():
    global mock_repository
    global mock_kafka
    global user_log_service

    data = await ApplicationFactory.create()

    mock_repository.create_application.return_value = data
    service = ApplicationService(
        mock_repository, mock_kafka, logger, user_log_service)

    result = await service.create_application(data, data.user_id)
    mock_kafka.produce.assert_called_once()
    assert isinstance(result, ApplicationResponseSchema)
    assert result.kafka_status is True


@pytest.mark.asyncio
async def test_create_application__failure():
    global mock_repository
    global mock_kafka
    global user_log_service

    mock_kafka.produce.side_effect = KafkaMessageError(
        details=kafka_error_detail)
    data = await ApplicationFactory.create()

    mock_repository.create_application.return_value = data
    service = ApplicationService(
        mock_repository, mock_kafka, logger, user_log_service)

    result = await service.create_application(data, data.user_id)
    assert result.kafka_status is False


@pytest.mark.asyncio
async def test_get_application_by_title__success():
    global mock_repository
    global mock_kafka
    global user_log_service

    data = await ApplicationFactory.create()
    mock_repository.create_application.return_value = data
    service = ApplicationService(
        mock_repository, mock_kafka, logger, user_log_service)
    created_data = await service.create_application(data, data.user_id)

    get_application_case = await service.get_application_by_title(created_data.title)
    assert get_application_case is not None


@pytest.mark.asyncio
async def test_get_application_by_title__failure():
    global mock_repository
    global mock_kafka
    global user_log_service

    data = await ApplicationFactory.create()
    mock_repository.create_application.return_value = data

    service = ApplicationService(
        mock_repository, mock_kafka, logger, user_log_service)

    get_application_case = await service.get_application_by_title("incorrect_title")
    assert get_application_case == []


@pytest.mark.asyncio
async def test_get_all_applications__success():
    global mock_repository
    global mock_kafka
    global user_log_service

    data_1 = await ApplicationFactory.create()
    data_2 = await ApplicationFactory.create()
    test_data = [data_1, data_2]

    mock_repository.get_all_applications.return_value = test_data
    service = ApplicationService(
        mock_repository, mock_kafka, logger, user_log_service)

    result = await service.get_all_applications(page=1, size=10)

    assert len(result) == 2
    assert result[0].title == data_1.title
    assert result[1].title == data_2.title


@pytest.mark.asyncio
async def test_get_all_applications__empty():
    mock_repository = AsyncMock()
    mock_kafka = AsyncMock()
    user_log_service = AsyncMock()

    mock_repository.get_all_applications.return_value = []

    service = ApplicationService(
        mock_repository, mock_kafka, logger, user_log_service)

    with pytest.raises(HTTPException) as exc_info:
        await service.get_all_applications(page=1, size=10)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "No applications found"
    mock_repository.get_all_applications.assert_awaited_once_with(
        page=1, size=10)
