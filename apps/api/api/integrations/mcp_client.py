from typing import Any, Dict, List, Optional
import os
import httpx


GDRIVE_API_BASE = "https://www.googleapis.com/drive/v3"


class GDriveMCPClient:
    def __init__(self) -> None:
        # API key (public files)
        self.api_key = os.getenv("GDRIVE_API_KEY")
        # OAuth (private workspace files)
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN")
        # Optional folder ID to limit search scope
        self.folder_id = os.getenv("GDRIVE_FOLDER_ID")

    async def _get_access_token(self) -> Optional[str]:
        if not (self.client_id and self.client_secret and self.refresh_token):
            return None
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": self.refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            r.raise_for_status()
            data = r.json()
            return data.get("access_token")

    async def list_files(
        self,
        query: Optional[str] = None,
        mime_types: Optional[List[str]] = None,
        updated_after: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        q_parts: List[str] = ["trashed = false"]
        if query:
            safe_query = query.replace("'", " ")
            # Try both name and fullText search for better results
            q_parts.append(f"(name contains '{safe_query}' or fullText contains '{safe_query}')")
        if mime_types:
            mt_clause = " or ".join([f"mimeType = '{mt}'" for mt in mime_types])
            q_parts.append(f"({mt_clause})")
        if updated_after:
            q_parts.append(f"modifiedTime > '{updated_after}'")
        if self.folder_id:
            q_parts.append(f"'{self.folder_id}' in parents")

        access_token = await self._get_access_token()
        params: Dict[str, Any] = {
            "q": " and ".join(q_parts),
            "fields": "files(id,name,mimeType,webViewLink)",
            "pageSize": 100,
        }
        headers: Dict[str, str] = {}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        elif self.api_key:
            params["key"] = self.api_key
        else:
            print(f"Google Drive: No authentication available (api_key: {bool(self.api_key)}, access_token: {bool(access_token)})")
            return []

        print(f"Google Drive search query: {params['q']}")
        print(f"Google Drive auth method: {'OAuth' if access_token else 'API Key' if self.api_key else 'None'}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(f"{GDRIVE_API_BASE}/files", params=params, headers=headers)
            r.raise_for_status()
            data = r.json()
            files = data.get("files", [])
            print(f"Google Drive returned {len(files)} files")
            return files

    async def get_file(self, file_id: str) -> Dict[str, Any]:
        access_token = await self._get_access_token()
        headers: Dict[str, str] = {}
        params_meta: Dict[str, Any] = {"fields": "id,name,mimeType,webViewLink"}
        params_download: Dict[str, Any] = {}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        elif self.api_key:
            params_meta["key"] = self.api_key
            params_download["key"] = self.api_key
        else:
            return {"file_id": file_id, "text": ""}

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                # Metadata
                meta = await client.get(
                    f"{GDRIVE_API_BASE}/files/{file_id}", params=params_meta, headers=headers
                )
                meta.raise_for_status()
                m = meta.json()
                mime = m.get("mimeType")

                # Google Docs export to text
                if mime == "application/vnd.google-apps.document":
                    try:
                        resp = await client.get(
                            f"{GDRIVE_API_BASE}/files/{file_id}/export",
                            params={"mimeType": "text/plain", **params_download},
                            headers=headers,
                        )
                        resp.raise_for_status()
                        text = resp.text
                        
                        # Sanitize text to remove null bytes and control characters
                        import re
                        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
                        
                        return {"file_id": file_id, "text": text, "meta": m}
                    except httpx.HTTPStatusError as e:
                        if e.response.status_code == 403:
                            print(f"Warning: Cannot access Google Doc {file_id} - permission denied")
                            return {"file_id": file_id, "text": "", "meta": m}
                        raise

                # Download media
                try:
                    resp = await client.get(
                        f"{GDRIVE_API_BASE}/files/{file_id}?alt=media",
                        params=params_download,
                        headers=headers,
                    )
                    resp.raise_for_status()
                    text = resp.text
                    
                    # Sanitize text to remove null bytes and control characters
                    import re
                    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
                    
                    return {"file_id": file_id, "text": text, "meta": m}
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 403:
                        print(f"Warning: Cannot access file {file_id} - permission denied")
                        return {"file_id": file_id, "text": "", "meta": m}
                    raise
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    print(f"Warning: Cannot access file {file_id} - permission denied")
                    return {"file_id": file_id, "text": "", "meta": {"id": file_id, "name": "Unknown", "mimeType": "unknown"}}
                raise


