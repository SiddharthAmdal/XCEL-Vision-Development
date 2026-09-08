import sqlite3
import json
import uuid
from typing import List, Optional
from datetime import datetime
from xsc_lib.xsc_lib_common.models.recognition import FaceTemplate, Person
from xsc_lib.xsc_lib_common.interfaces.template_repository import FaceTemplateRepository

class SQLiteFaceTemplateRepository(FaceTemplateRepository):
    def __init__(self, db_path: str = "faces.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS persons (
                    person_id TEXT PRIMARY KEY,
                    employee_id TEXT,
                    name TEXT NOT NULL,
                    department TEXT,
                    status TEXT NOT NULL,
                    consent_status TEXT NOT NULL
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS face_templates (
                    template_id TEXT PRIMARY KEY,
                    person_id TEXT NOT NULL,
                    embedding_json TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    quality_score REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    revoked_at TEXT,
                    FOREIGN KEY(person_id) REFERENCES persons(person_id)
                )
            ''')
            conn.commit()

    def save_person(self, person: Person) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO persons (person_id, employee_id, name, department, status, consent_status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (person.person_id, person.employee_id, person.name, person.department, person.status, person.consent_status))
            conn.commit()

    def get_person(self, person_id: str) -> Optional[Person]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT person_id, employee_id, name, department, status, consent_status FROM persons WHERE person_id = ?', (person_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            person = Person(
                person_id=row[0],
                employee_id=row[1],
                name=row[2],
                department=row[3],
                status=row[4],
                consent_status=row[5]
            )
            
            cursor.execute('SELECT template_id, embedding_json, model_version, quality_score, created_at, updated_at, revoked_at FROM face_templates WHERE person_id = ? AND revoked_at IS NULL', (person_id,))
            templates = []
            for t_row in cursor.fetchall():
                templates.append(FaceTemplate(
                    template_id=t_row[0],
                    person_id=person_id,
                    embedding=json.loads(t_row[1]),
                    model_version=t_row[2],
                    quality_score=t_row[3],
                    created_at=datetime.fromisoformat(t_row[4]),
                    updated_at=datetime.fromisoformat(t_row[5]),
                    revoked_at=datetime.fromisoformat(t_row[6]) if t_row[6] else None
                ))
            person.templates = templates
            return person

    def get_all_persons(self) -> List[Person]:
        persons = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT person_id FROM persons')
            for row in cursor.fetchall():
                p = self.get_person(row[0])
                if p:
                    persons.append(p)
        return persons

    def delete_person(self, person_id: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM face_templates WHERE person_id = ?', (person_id,))
            cursor.execute('DELETE FROM persons WHERE person_id = ?', (person_id,))
            conn.commit()

    def save_template(self, template: FaceTemplate) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO face_templates (template_id, person_id, embedding_json, model_version, quality_score, created_at, updated_at, revoked_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                template.template_id,
                template.person_id,
                json.dumps(template.embedding),
                template.model_version,
                template.quality_score,
                template.created_at.isoformat(),
                template.updated_at.isoformat(),
                template.revoked_at.isoformat() if template.revoked_at else None
            ))
            conn.commit()

    def get_active_templates(self) -> List[FaceTemplate]:
        templates = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT template_id, person_id, embedding_json, model_version, quality_score, created_at, updated_at, revoked_at FROM face_templates WHERE revoked_at IS NULL')
            for t_row in cursor.fetchall():
                templates.append(FaceTemplate(
                    template_id=t_row[0],
                    person_id=t_row[1],
                    embedding=json.loads(t_row[2]),
                    model_version=t_row[3],
                    quality_score=t_row[4],
                    created_at=datetime.fromisoformat(t_row[5]),
                    updated_at=datetime.fromisoformat(t_row[6]),
                    revoked_at=datetime.fromisoformat(t_row[7]) if t_row[7] else None
                ))
        return templates

    def revoke_template(self, template_id: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            now_iso = datetime.utcnow().isoformat()
            cursor.execute('UPDATE face_templates SET revoked_at = ?, updated_at = ? WHERE template_id = ?', (now_iso, now_iso, template_id))
            conn.commit()
