from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import List, Optional
import uuid
import cv2
import numpy as np
from datetime import datetime

from xsc_lib.xsc_lib_common.models.recognition import Person, FaceTemplate, RecognitionStatus, FaceRecognitionResult
from xsc_lib.xsc_lib_extn.db.sqlite_template_repository import SQLiteFaceTemplateRepository, FaceTemplateRepository
from xsc_lib.xsc_lib_extn.ai.yunet import YuNetFaceDetector
from xsc_lib.xsc_lib_extn.ai.opencv_quality import OpenCVFaceQualityAnalyzer
from xsc_lib.xsc_lib_extn.ai.arcface_aligner import ArcFaceAligner
from xsc_lib.xsc_lib_extn.ai.arcface_embedding import ArcFaceEmbeddingModel

router = APIRouter(prefix="/api/v1", tags=["Identity Intelligence"])

# Dependencies
def get_repository() -> FaceTemplateRepository:
    return SQLiteFaceTemplateRepository()

def get_detector(): return YuNetFaceDetector()
def get_quality_analyzer(): return OpenCVFaceQualityAnalyzer()
def get_aligner(): return ArcFaceAligner()
def get_embedding_model(): return ArcFaceEmbeddingModel()

@router.post("/people", response_model=Person)
def create_person(person: Person, repo: FaceTemplateRepository = Depends(get_repository)):
    repo.save_person(person)
    return repo.get_person(person.person_id)

@router.get("/people", response_model=List[Person])
def get_people(repo: FaceTemplateRepository = Depends(get_repository)):
    return repo.get_all_persons()

@router.get("/people/{person_id}", response_model=Person)
def get_person(person_id: str, repo: FaceTemplateRepository = Depends(get_repository)):
    person = repo.get_person(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person

@router.delete("/people/{person_id}")
def delete_person(person_id: str, repo: FaceTemplateRepository = Depends(get_repository)):
    repo.delete_person(person_id)
    return {"status": "success"}

@router.post("/faces/enroll", response_model=FaceTemplate)
def enroll_face(
    person_id: str = Form(...),
    file: UploadFile = File(...),
    repo: FaceTemplateRepository = Depends(get_repository),
    detector: YuNetFaceDetector = Depends(get_detector),
    quality_analyzer: OpenCVFaceQualityAnalyzer = Depends(get_quality_analyzer),
    aligner: ArcFaceAligner = Depends(get_aligner),
    embedding_model: ArcFaceEmbeddingModel = Depends(get_embedding_model)
):
    person = repo.get_person(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    contents = file.file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image file")

    faces = detector.detect_faces(img)
    if len(faces) == 0:
        raise HTTPException(status_code=400, detail="NO_FACE: No face detected in the image")
    if len(faces) > 1:
        raise HTTPException(status_code=400, detail="MULTIPLE_FACE: Multiple faces detected, cannot enroll")

    box, conf, landmarks = faces[0]
    fx1, fy1, fx2, fy2 = box
    face_crop = img[fy1:fy2, fx1:fx2]

    quality = quality_analyzer.analyze_quality(face_crop)
    if not quality.meets_threshold:
        raise HTTPException(status_code=400, detail="LOW_QUALITY: Face does not meet quality requirements for enrollment")

    aligned_face = aligner.align(img, landmarks) if landmarks else aligner.align(face_crop, [])
    embedding = embedding_model.generate_embedding(aligned_face)

    template = FaceTemplate(
        template_id=str(uuid.uuid4()),
        person_id=person_id,
        embedding=embedding,
        model_version=embedding_model.model_version,
        quality_score=quality.blur_score, # Or composite quality
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    repo.save_template(template)
    
    # Strip embedding before returning to API as per strict privacy requirements
    resp_template = template.copy(deep=True)
    resp_template.embedding = []
    
    return resp_template

@router.delete("/faces/{template_id}")
def revoke_template(template_id: str, repo: FaceTemplateRepository = Depends(get_repository)):
    repo.revoke_template(template_id)
    return {"status": "success"}
