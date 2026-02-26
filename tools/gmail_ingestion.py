"""
Gmail ingestion pipeline for resume workflows.

Features:
- Fetches Gmail messages for a query.
- Inserts message body into knowledge base.
- Downloads supported attachments and inserts them into knowledge base.
- Tracks processed message IDs in SQLite for idempotency.
"""
import base64
import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parseaddr
from pathlib import Path
from typing import Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from tools.knowledge_tool import InsertKnowledgeTool

logger = logging.getLogger(__name__)

GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
SUPPORTED_ATTACHMENT_EXTENSIONS = {".pdf", ".txt", ".docx"}


@dataclass
class GmailSyncSummary:
    fetched: int = 0
    skipped_existing: int = 0
    processed: int = 0
    failed: int = 0
    attachments_ingested: int = 0


class GmailIngestionService:
    """Synchronize Gmail messages and attachments into knowledge base."""

    def __init__(
        self,
        knowledge_tool: InsertKnowledgeTool,
        credentials_path: str,
        token_path: str,
        db_path: str = "./knowledge/gmail_ingestion.db",
        attachments_dir: str = "./dropbox/gmail",
        query: str = "in:inbox",
        max_results: int = 20,
        unread_only: bool = False,
    ):
        self.knowledge_tool = knowledge_tool
        self.credentials_path = Path(credentials_path)
        self.token_path = Path(token_path)
        self.db_path = Path(db_path)
        self.attachments_dir = Path(attachments_dir)
        self.query = query.strip() or "in:inbox"
        self.max_results = max_results
        self.unread_only = unread_only

        self.attachments_dir.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_db()

    def _ensure_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS processed_messages (
                    message_id TEXT PRIMARY KEY,
                    thread_id TEXT,
                    from_email TEXT,
                    subject TEXT,
                    processed_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error TEXT
                )
                """
            )
            conn.commit()

    def _is_processed(self, message_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT status FROM processed_messages WHERE message_id = ?",
                (message_id,),
            ).fetchone()
        return bool(row and row[0] == "success")

    def _record_result(
        self,
        message_id: str,
        thread_id: str,
        from_email: str,
        subject: str,
        status: str,
        error: Optional[str] = None,
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO processed_messages (
                    message_id, thread_id, from_email, subject, processed_at, status, error
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(message_id) DO UPDATE SET
                    thread_id = excluded.thread_id,
                    from_email = excluded.from_email,
                    subject = excluded.subject,
                    processed_at = excluded.processed_at,
                    status = excluded.status,
                    error = excluded.error
                """,
                (
                    message_id,
                    thread_id,
                    from_email,
                    subject,
                    datetime.now(timezone.utc).isoformat(),
                    status,
                    error,
                ),
            )
            conn.commit()

    def _load_credentials(self) -> Credentials:
        if not self.token_path.exists():
            raise FileNotFoundError(
                f"Gmail token file not found: {self.token_path}. "
                "Authorize first to generate token.json."
            )
        if not self.credentials_path.exists():
            raise FileNotFoundError(f"Gmail credentials file not found: {self.credentials_path}")

        creds = Credentials.from_authorized_user_file(str(self.token_path), [GMAIL_READONLY_SCOPE])
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            self.token_path.write_text(creds.to_json())
        return creds

    def _build_service(self):
        creds = self._load_credentials()
        return build("gmail", "v1", credentials=creds)

    def _build_query(self) -> str:
        if self.unread_only and "is:unread" not in self.query:
            return f"{self.query} is:unread"
        return self.query

    @staticmethod
    def _decode_data(data: str) -> str:
        raw = base64.urlsafe_b64decode(data.encode("utf-8"))
        return raw.decode("utf-8", errors="ignore")

    def _extract_text_body(self, payload: Dict) -> str:
        mime_type = payload.get("mimeType", "")
        body = payload.get("body", {})
        if mime_type == "text/plain" and body.get("data"):
            return self._decode_data(body["data"])

        text_chunks: List[str] = []
        for part in payload.get("parts", []) or []:
            extracted = self._extract_text_body(part)
            if extracted:
                text_chunks.append(extracted)
        return "\n".join(chunk for chunk in text_chunks if chunk).strip()

    def _collect_attachments(self, payload: Dict) -> List[Dict[str, str]]:
        attachments: List[Dict[str, str]] = []
        for part in payload.get("parts", []) or []:
            filename = part.get("filename")
            body = part.get("body", {})
            attachment_id = body.get("attachmentId")
            if filename and attachment_id:
                attachments.append({"filename": filename, "attachment_id": attachment_id})
            attachments.extend(self._collect_attachments(part))
        return attachments

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        keep = [ch for ch in name if ch.isalnum() or ch in ("-", "_", ".", " ")]
        cleaned = "".join(keep).strip().replace(" ", "_")
        return cleaned or "attachment.bin"

    def _download_attachment(
        self,
        service,
        message_id: str,
        attachment_id: str,
        filename: str,
    ) -> Path:
        attachment = (
            service.users()
            .messages()
            .attachments()
            .get(userId="me", messageId=message_id, id=attachment_id)
            .execute()
        )
        data = attachment.get("data")
        if not data:
            raise ValueError(f"Attachment has no data: message_id={message_id}, filename={filename}")
        binary = base64.urlsafe_b64decode(data.encode("utf-8"))

        target_dir = self.attachments_dir / message_id
        target_dir.mkdir(parents=True, exist_ok=True)
        safe_name = self._sanitize_filename(filename)
        target_path = target_dir / safe_name
        target_path.write_bytes(binary)
        return target_path

    def _insert_email_text(
        self,
        message_id: str,
        thread_id: str,
        from_header: str,
        subject: str,
        date: str,
        body_text: str,
        snippet: str,
    ) -> None:
        from_email = parseaddr(from_header)[1] or from_header
        payload_text = (
            f"Source: gmail\n"
            f"Message-ID: {message_id}\n"
            f"Thread-ID: {thread_id}\n"
            f"From: {from_header}\n"
            f"From-Email: {from_email}\n"
            f"Subject: {subject}\n"
            f"Date: {date}\n\n"
            f"Body:\n{body_text or snippet}"
        )
        self.knowledge_tool.insert_knowledge(text=payload_text)

    def sync(self) -> GmailSyncSummary:
        summary = GmailSyncSummary()
        service = self._build_service()

        query = self._build_query()
        logger.info("Starting Gmail sync: query='%s', max_results=%s", query, self.max_results)
        listed = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=self.max_results)
            .execute()
        )
        messages = listed.get("messages", [])
        summary.fetched = len(messages)

        for item in messages:
            message_id = item["id"]
            if self._is_processed(message_id):
                summary.skipped_existing += 1
                continue

            try:
                msg = service.users().messages().get(userId="me", id=message_id, format="full").execute()
                payload = msg.get("payload", {})
                headers = {
                    h.get("name", "").lower(): h.get("value", "")
                    for h in payload.get("headers", [])
                }

                thread_id = msg.get("threadId", "")
                subject = headers.get("subject", "")
                from_header = headers.get("from", "")
                from_email = parseaddr(from_header)[1] or from_header
                date = headers.get("date", "")
                body_text = self._extract_text_body(payload)
                snippet = msg.get("snippet", "")

                self._insert_email_text(
                    message_id=message_id,
                    thread_id=thread_id,
                    from_header=from_header,
                    subject=subject,
                    date=date,
                    body_text=body_text,
                    snippet=snippet,
                )

                for attachment_meta in self._collect_attachments(payload):
                    filename = attachment_meta["filename"]
                    extension = Path(filename).suffix.lower()
                    if extension not in SUPPORTED_ATTACHMENT_EXTENSIONS:
                        continue
                    attachment_path = self._download_attachment(
                        service=service,
                        message_id=message_id,
                        attachment_id=attachment_meta["attachment_id"],
                        filename=filename,
                    )
                    self.knowledge_tool.insert_knowledge(file_path=str(attachment_path))
                    summary.attachments_ingested += 1

                self._record_result(
                    message_id=message_id,
                    thread_id=thread_id,
                    from_email=from_email,
                    subject=subject,
                    status="success",
                )
                summary.processed += 1
            except Exception as exc:
                logger.exception("Failed processing Gmail message: %s", message_id)
                self._record_result(
                    message_id=message_id,
                    thread_id="",
                    from_email="",
                    subject="",
                    status="failed",
                    error=str(exc),
                )
                summary.failed += 1

        logger.info(
            "Gmail sync done. fetched=%s processed=%s skipped_existing=%s failed=%s attachments_ingested=%s",
            summary.fetched,
            summary.processed,
            summary.skipped_existing,
            summary.failed,
            summary.attachments_ingested,
        )
        return summary

    def read_recent_records(self, limit: int = 20) -> List[Dict[str, str]]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT message_id, thread_id, from_email, subject, processed_at, status, error
                FROM processed_messages
                ORDER BY processed_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        records = []
        for row in rows:
            records.append(
                {
                    "message_id": row[0],
                    "thread_id": row[1],
                    "from_email": row[2],
                    "subject": row[3],
                    "processed_at": row[4],
                    "status": row[5],
                    "error": row[6] or "",
                }
            )
        return records

    def dump_recent_records_json(self, limit: int = 20) -> str:
        return json.dumps(self.read_recent_records(limit=limit), indent=2)
