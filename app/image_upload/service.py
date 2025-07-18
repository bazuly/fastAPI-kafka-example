# This code snippet defines a Python class `ImageService` that serves as a service layer for handling
# image-related operations in a FastAPI application. Here's a breakdown of what the code is doing:
import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from fastapi import HTTPException

from app.broker.producer import KafkaProducer
from app.exceptions import KafkaImageDataUploadError, RecordMongoException
from app.mongo import UserLogService
from app.image_upload.models import ImageUploadModel
from app.image_upload.repository import ImageRepository
from app.image_upload.schemas import ImageResponse
from app.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class ImageService:
    image_repository: ImageRepository
    kafka_producer: KafkaProducer
    logger: logger
    user_log_service: UserLogService

    async def upload_image(
        self,
        image: Any,
        user_id: UUID,
    ) -> Any:
        uploaded_image = await self.image_repository.upload_image(image, user_id)

        try:
            await self.user_log_service.log_endpoint_call(endpoint="upload_image", user_id=user_id)
        except RecordMongoException as e:
            self.logger.error(
                "Error during data record, MongoDB: {}".format(e))

        kafka_message = {
            "id": uploaded_image.id,
            "filename": uploaded_image.filename,
            "size": uploaded_image.size,
            "upload_date": uploaded_image.upload_date,
            "user_id": str(user_id),
        }
        kafka_status = False
        try:
            await self.kafka_producer.produce(
                topic=settings.KAFKA_TOPIC,
                key=str(uploaded_image.id),
                value=kafka_message,
            )
            kafka_status = True
        except KafkaImageDataUploadError as e:
            self.logger.error("Fail while kafka producing error",
                        extra={"error": str(e)})

        try:
            await self.user_log_service.log_endpoint_call(endpoint="upload_image", user_id=user_id)
        except RecordMongoException as e:
            self.logger.error(
                "Error during data record, MongoDB: {}".format(e))

        return ImageResponse(
            id=uploaded_image.id,
            filename=uploaded_image.filename,
            size=uploaded_image.size,
            upload_date=uploaded_image.upload_date,
            kafka_status=kafka_status,
        )

    async def get_image_by_id(self, image_id: int) -> ImageUploadModel | None:
        try:
            image = await self.image_repository.get_image_by_id(image_id)
            return image
        except HTTPException as e:
            raise e(status_code=404, detail="Image not found or access denied")

        try:
            await self.user_log_service.log_endpoint_call(endpoint="get_image", user_id=None)
        except RecordMongoException as e:
            self.logger.error(
                "Error during data record, MongoDB: {}".format(e))

    async def delete_image_by_id(self, image_id: int, user_id: UUID) -> dict:
        try:
            await self.image_repository.delete_image_by_id(
                image_id=image_id, user_id=user_id
            )
            return {"msg": f"Image {image_id} deleted successfully"}
        except HTTPException as e:
            raise e(status_code=404, detail="Image not found or access denied")
        try:
            await self.user_log_service.log_endpoint_call(endpoint="delete_image", user_id=user_id)
        except RecordMongoException as e:
            self.logger.error(
                "Error during data record, MongoDB: {}".format(e))