from dataclasses import dataclass
from typing import Any
from uuid import UUID

from fastapi import HTTPException

from app.image_upload.models import ImageUploadModel
from app.image_upload.repository.image_repository import ImageRepository
from app.image_upload.schemas import ImageResponse
from app.broker.producer import KafkaProducer
from settings import settings


@dataclass
class ImageService:
    image_repository: ImageRepository
    kafka_producer: KafkaProducer

    async def upload_image(
            self,
            image: Any,
            user_id: UUID,

    ) -> Any:
        uploaded_image = await self.image_repository.upload_image(image, user_id)

        kafka_message = {
            "id": uploaded_image.id,
            "filename": uploaded_image.filename,
            "size": uploaded_image.size,
            "upload_date": uploaded_image.upload_date.isoformat(),
            "user_id": str(user_id)
        }
        kafka_status = False
        try:
            await self.kafka_producer.produce(
                topic=settings.KAFKA_TOPIC,
                key=str(uploaded_image.id),
                value=kafka_message
            )
            kafka_status = True
        except Exception as e:
            print(f"Error while sending kafka message: {e}")

        return ImageResponse(
            id=uploaded_image.id,
            filename=uploaded_image.filename,
            size=uploaded_image.size,
            upload_date=uploaded_image.upload_date,
            kafka_status=kafka_status,
        )

    async def get_image_by_id(self, image_id: int) -> ImageUploadModel:
        try:
            image = await self.image_repository.get_image_by_id(image_id)
            return image
        except:
            raise HTTPException(status_code=404, detail="Image not found")

    # TODO нужно ли здесь добавлять логику удаления изображения из самой директории ?
    # TODO по идее должно быть в репозитории данная логика
    async def delete_image_by_id(self, image_id: int) -> dict:
        try:
            await self.image_repository.delete_image_by_id(image_id)
            return {
                "msg": f"Image {image_id} deleted successfully"
            }
        except:
            raise HTTPException(status_code=404, detail="Image not found")
