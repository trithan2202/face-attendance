# from sqlalchemy import delete, select

# from backend.app.core.embedding_codec import (
#     decode_embedding,
#     encode_embedding
# )
# from backend.app.models import Employee, FaceEmbedding


# class FaceRepository:
#     @staticmethod
#     def add_embedding(
#         db,
#         employee_id,
#         embedding,
#         embedding_type="sample"
#     ):
#         record = FaceEmbedding(
#             employee_id=employee_id,
#             embedding=encode_embedding(
#                 embedding
#             ),
#             embedding_type=embedding_type
#         )

#         db.add(record)
#         db.flush()

#         return record

#     @staticmethod
#     def delete_employee_embeddings(
#         db,
#         employee_id
#     ):
#         stmt = delete(FaceEmbedding).where(
#             FaceEmbedding.employee_id
#             == employee_id
#         )

#         db.execute(stmt)

#     @staticmethod
#     def get_centroid_embeddings(db):
#         stmt = (
#             select(
#                 Employee.employee_code,
#                 Employee.full_name,
#                 FaceEmbedding.embedding
#             )
#             .join(
#                 FaceEmbedding,
#                 FaceEmbedding.employee_id
#                 == Employee.id
#             )
#             .where(
#                 Employee.is_active.is_(True),
#                 FaceEmbedding.embedding_type
#                 == "centroid"
#             )
#         )

#         rows = db.execute(stmt).all()

#         result = {}

#         for code, full_name, embedding_data in rows:
#             result[code] = {
#                 "employee_code": code,
#                 "full_name": full_name,
#                 "embedding": decode_embedding(
#                     embedding_data
#                 )
#             }

#         return result

from sqlalchemy import delete, select

from backend.app.core.embedding_codec import (
    decode_embedding,
    encode_embedding
)
from backend.app.models import Employee, FaceEmbedding


class FaceRepository:
    @staticmethod
    def add_embedding(
        db,
        employee_id,
        embedding,
        sample_index=None,
        quality_score=None,
        detection_score=None,
        is_centroid=False,
        model_name="buffalo_l"
    ):
        record = FaceEmbedding(
            employee_id=employee_id,
            embedding=encode_embedding(
                embedding
            ),
            sample_index=sample_index,
            quality_score=quality_score,
            detection_score=detection_score,
            is_centroid=is_centroid,
            model_name=model_name
        )

        db.add(record)
        db.flush()

        return record

    @staticmethod
    def delete_employee_embeddings(
        db,
        employee_id
    ):
        db.execute(
            delete(FaceEmbedding).where(
                FaceEmbedding.employee_id
                == employee_id
            )
        )

    @staticmethod
    def get_centroids(db):
        stmt = (
            select(
                Employee.id,
                Employee.employee_code,
                Employee.full_name,
                FaceEmbedding.embedding
            )
            .join(
                FaceEmbedding,
                FaceEmbedding.employee_id
                == Employee.id
            )
            .where(
                Employee.status == "ACTIVE",
                FaceEmbedding.is_centroid.is_(True)
            )
        )

        rows = db.execute(stmt).all()

        return {
            code: {
                "employee_id": employee_id,
                "employee_code": code,
                "full_name": name,
                "embedding": decode_embedding(data)
            }
            for employee_id, code, name, data in rows
        }