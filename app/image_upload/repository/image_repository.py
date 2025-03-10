import os
import aiofiles
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.image_upload.models import ImageUploadModel
from app.logger import logger
from app.exceptions import ImageUploadRepositoryException


class ImageRepository:
    def __init__(self, db_session: AsyncSession, upload_dir: str):
        self.db_session = db_session
        self.upload_dir = upload_dir
        self.logger = logger.getChild(self.__class__.__name__)

    async def upload_image(self, image: Any, user_id: UUID) -> ImageUploadModel:
        try:
            os.makedirs(self.upload_dir, exist_ok=True)

            file_path = os.path.join(self.upload_dir, image.filename)

            async with aiofiles.open(file_path, "wb") as f:
                content = await image.read()
                await f.write(content)

            image = ImageUploadModel(
                filename=image.filename,
                upload_date=datetime.utcnow(),
                size=len(content) / 1024 / 1024,
                user_id=user_id,
            )

            self.db_session.add(image)
            await self.db_session.commit()
            await self.db_session.refresh(image)
            self.logger.info(
                "Image uploaded successfully",
                extra={
                    "user_id": str(user_id),
                    "file_size": f"{image.size:.2f}MB",
                    "file_path": file_path
                }
            )
            return image
        except SQLAlchemyError as e:
            self.logger.error(
                f"Database error during image upload or image with name {image.filename} already exists",
                extra={"user_id": str(user_id), "error": str(e)},
                exc_info=True
            )
            await self.db_session.rollback()
            print(image.filename)
            raise ImageUploadRepositoryException.database_query_error()

    async def get_image_by_id(self, image_id: int) -> ImageUploadModel | None:
        try:
            result = await self.db_session.execute(
                select(ImageUploadModel).where(ImageUploadModel.id == image_id)
            )
            image = result.scalar_one_or_none()
            if not result:
                self.logger.warning(
                    "Image not found",
                    extra={"image_id": image_id}
                )
            return image
        except SQLAlchemyError as e:
            self.logger.error(
                "Database error fetching image",
                extra={"image_id": image_id, "error": str(e)},
            )
            raise ImageUploadRepositoryException.image_not_found_error(image_id)

    async def delete_image_by_id(self, image_id: int | UUID, user_id: UUID) -> None:
        try:
            image = await self.db_session.execute(
                select(ImageUploadModel).where(
                    ImageUploadModel.id == image_id,
                    ImageUploadModel.user_id == user_id
                )
            )
            image_model = image.scalar_one_or_none()
            if not image_model:
                self.logger.error(
                    "Image not found",
                    extra={"image_id": image_id},
                )

            file_path = os.path.join(self.upload_dir, image_model.filename)
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except OSError as e:
                self.logger.error(
                    "File deletion failed",
                    extra={"image_id": image_id, "error": str(e)},
                )
            await self.db_session.delete(image_model)
            await self.db_session.commit()

            self.logger.info(
                "Image deleted successfully",
                extra={"image_id": image_id}
            )
        except SQLAlchemyError as e:
            self.logger.error(
                "Database error during image deletion",
                extra={"image_id": image_id, "error": str(e)},
                exc_info=True
            )
            await self.db_session.rollback()
            raise ImageUploadRepositoryException.database_query_error()

        except Exception as e:
            self.logger.warning(
                "Delete attempt for non-existent image",
                extra={"image_id": image_id, "error": str(e)},
            )
            raise ImageUploadRepositoryException.image_not_found_error(image_id)
